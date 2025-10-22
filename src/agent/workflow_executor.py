"""Workflow execution engine for browser automation"""

import asyncio
import secrets
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import time

from .workflow_types import (
    Workflow,
    WorkflowStep,
    WorkflowStepResult,
    WorkflowExecutionResult,
    BrowserState,
    RetryConfig
)


class WorkflowExecutor:
    """
    Executes multi-step browser workflows with state tracking,
    error handling, and retry logic.
    """

    def __init__(self, agent):
        """
        Initialize workflow executor.

        Args:
            agent: ServerAgent instance for MCP tool execution
        """
        self.agent = agent
        self.state_history = []
        self.current_execution_id = None

    async def execute_workflow(
        self,
        workflow: Workflow,
        progress_callback: Optional[Callable] = None
    ) -> WorkflowExecutionResult:
        """
        Execute a complete workflow.

        Args:
            workflow: Workflow to execute
            progress_callback: Optional async callback function called after each step
                             Signature: async def callback(step_number, total_steps, result)

        Returns:
            WorkflowExecutionResult with execution details
        """
        execution_id = f"exec-{secrets.token_hex(8)}"
        self.current_execution_id = execution_id
        self.state_history = []

        started_at = datetime.utcnow()
        results = []
        completed_steps = 0
        failed_step = None
        error_message = None

        print(f"🔄 Starting workflow execution: {workflow.workflow_id}")
        print(f"   Name: {workflow.name}")
        print(f"   Steps: {len(workflow.steps)}")

        for step in workflow.steps:
            step_start_time = time.time()

            try:
                print(f"   Step {step.step_number}/{len(workflow.steps)}: {step.description}")

                # Execute step with retry logic
                result = await self._execute_step_with_retry(step)

                step_duration = time.time() - step_start_time

                step_result = WorkflowStepResult(
                    step_id=step.step_id,
                    step_number=step.step_number,
                    success=True,
                    result=result,
                    duration_seconds=step_duration,
                    retries_used=result.get("retries_used", 0)
                )

                results.append(step_result)
                completed_steps += 1

                # Call progress callback
                if progress_callback:
                    try:
                        await progress_callback(step.step_number, len(workflow.steps), step_result)
                    except Exception as e:
                        print(f"⚠️ Progress callback error: {e}")

                print(f"   ✅ Step {step.step_number} completed ({step_duration:.2f}s)")

            except Exception as e:
                step_duration = time.time() - step_start_time
                error_msg = str(e)

                print(f"   ❌ Step {step.step_number} failed: {error_msg}")

                step_result = WorkflowStepResult(
                    step_id=step.step_id,
                    step_number=step.step_number,
                    success=False,
                    error=error_msg,
                    duration_seconds=step_duration
                )

                results.append(step_result)
                failed_step = step.step_number
                error_message = f"Step {step.step_number} failed: {error_msg}"

                # Call progress callback for failure
                if progress_callback:
                    try:
                        await progress_callback(step.step_number, len(workflow.steps), step_result)
                    except Exception as callback_error:
                        print(f"⚠️ Progress callback error: {callback_error}")

                # Stop on first failure
                break

        completed_at = datetime.utcnow()
        total_duration = (completed_at - started_at).total_seconds()

        success = failed_step is None

        print(f"{'✅' if success else '❌'} Workflow {'completed' if success else 'failed'}: {completed_steps}/{len(workflow.steps)} steps ({total_duration:.2f}s)")

        return WorkflowExecutionResult(
            workflow_id=workflow.workflow_id,
            success=success,
            steps=results,
            total_duration_seconds=total_duration,
            completed_steps=completed_steps,
            failed_step=failed_step,
            error_message=error_message,
            execution_id=execution_id,
            started_at=started_at,
            completed_at=completed_at
        )

    async def _execute_step_with_retry(self, step: WorkflowStep) -> Dict[str, Any]:
        """
        Execute a step with retry logic.

        Args:
            step: WorkflowStep to execute

        Returns:
            Result dictionary with execution details

        Raises:
            Exception: If step fails after all retries
        """
        if not step.retry_config:
            # No retry config, execute once
            return await self._execute_step(step)

        # Execute with retry logic
        retry_config = step.retry_config
        last_error = None
        backoff = retry_config.backoff_seconds

        for attempt in range(retry_config.max_retries + 1):
            try:
                result = await self._execute_step(step)
                result["retries_used"] = attempt
                return result

            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)

                # Check if we should retry this error type
                if error_type not in retry_config.retry_on_errors:
                    raise e

                # If this was the last attempt, raise
                if attempt >= retry_config.max_retries:
                    raise e

                # Wait before retry
                print(f"   ⏳ Retry {attempt + 1}/{retry_config.max_retries} after {backoff:.1f}s...")
                await asyncio.sleep(backoff)

                # Increase backoff for next attempt
                backoff *= retry_config.backoff_multiplier

        # Should never reach here, but just in case
        raise last_error

    async def _execute_step(self, step: WorkflowStep) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: WorkflowStep to execute

        Returns:
            Result dictionary from MCP tool execution
        """
        # Substitute variables in parameters
        parameters = self._substitute_variables(step.parameters)

        # Execute the MCP tool
        result = await self.agent._execute_mcp_tool(step.tool, parameters)

        return result

    def _substitute_variables(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute variables in step parameters.

        Variables are in format ${variable_name}

        Args:
            parameters: Original parameters dict

        Returns:
            Parameters with variables substituted
        """
        # For now, simple string replacement
        # TODO: Implement full variable substitution from workflow.variables
        import json
        params_str = json.dumps(parameters)

        # Replace ${var} patterns (to be implemented with actual variable storage)

        return json.loads(params_str)

    def _classify_error(self, error: Exception) -> str:
        """
        Classify error type for retry logic.

        Args:
            error: Exception to classify

        Returns:
            Error type string (timeout, element_not_found, network_error, unknown)
        """
        error_msg = str(error).lower()

        if "timeout" in error_msg or "timed out" in error_msg:
            return "timeout"
        elif "element not found" in error_msg or "selector" in error_msg:
            return "element_not_found"
        elif "network" in error_msg or "connection" in error_msg:
            return "network_error"
        else:
            return "unknown"

    async def _capture_browser_state(self) -> BrowserState:
        """
        Capture current browser state for debugging and validation.

        Returns:
            BrowserState snapshot
        """
        try:
            # Get current URL
            url_result = await self.agent._execute_mcp_tool(
                "mcp__sandbox__browser_evaluate",
                {"script": "() => window.location.href"}
            )

            # Get page title
            title_result = await self.agent._execute_mcp_tool(
                "mcp__sandbox__browser_evaluate",
                {"script": "() => document.title"}
            )

            # Take screenshot (optional, can be expensive)
            # screenshot = await self.agent._execute_mcp_tool(
            #     "mcp__sandbox__browser_screenshot",
            #     {}
            # )

            return BrowserState(
                url=url_result.get("result", "unknown"),
                title=title_result.get("result", "unknown"),
                loaded_elements=[],
                screenshot_b64=None,  # screenshot.get("data") if needed
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            print(f"⚠️ Failed to capture browser state: {e}")
            return BrowserState(
                url="error",
                title="error",
                loaded_elements=[],
                timestamp=datetime.utcnow()
            )
