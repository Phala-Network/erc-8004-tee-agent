"""Server Agent - AIO Sandbox Integration"""

import os
import httpx
from datetime import datetime
from typing import Dict, Any, Optional
from ..agent.base import BaseAgent, AgentConfig, RegistryAddresses


class ServerAgent(BaseAgent):
    """Server agent with AIO Sandbox integration and AI-assisted code generation."""

    def __init__(self, config: AgentConfig, registries: RegistryAddresses, sandbox_url: str = None):
        super().__init__(config, registries)
        self.sandbox_url = sandbox_url or os.getenv("SANDBOX_URL", "http://localhost:8080")
        print(f"📦 Sandbox: {self.sandbox_url}")

        # Initialize AI generator if API key is available
        self.ai_generator = None
        if os.getenv("REDPILL_API_KEY"):
            try:
                from ..agent.ai_generator import AIScriptGenerator
                self.ai_generator = AIScriptGenerator()
            except Exception as e:
                print(f"⚠️ AI Generator disabled: {e}")

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task via AIO Sandbox."""
        data = task_data.get('data', {})
        task_type = data.get('type', 'shell')

        if task_type == 'shell':
            return await self._execute_shell(data.get('command', 'echo "No command"'))
        elif task_type == 'file_read':
            return await self._read_file(data.get('path'))
        elif task_type == 'file_write':
            return await self._write_file(data.get('path'), data.get('content'))
        elif task_type == 'jupyter':
            return await self._execute_jupyter(
                data.get('code', 'print("No code provided")'),
                data.get('session_id'),
                data.get('timeout', 30)
            )
        elif task_type == 'nodejs':
            return await self._execute_nodejs(
                data.get('code', 'console.log("No code provided")'),
                data.get('files'),
                data.get('timeout', 30)
            )
        elif task_type == 'ai_generate_and_execute':
            return await self._ai_generate_and_execute(
                data.get('description', 'No description provided'),
                data.get('language', 'python'),
                data.get('context'),
                data.get('max_retries', 2),
                data.get('include_attestation', True)
            )
        elif task_type == 'ai_mcp_control':
            return await self._ai_mcp_control(
                data.get('description', 'No description provided'),
                data.get('include_attestation', True),
                data.get('show_mcp_call', True),
                data.get('confirm_dangerous', True)
            )
        else:
            return {"error": "Unknown task type", "type": task_type}

    async def _execute_shell(self, command: str) -> Dict[str, Any]:
        """Execute shell command via sandbox."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.sandbox_url}/v1/shell/exec",
                    json={"command": command},
                    timeout=30.0
                )
                return resp.json()
            except Exception as e:
                return {"error": str(e)}

    async def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file via sandbox."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.sandbox_url}/v1/file/read",
                    json={"file": path},
                    timeout=10.0
                )
                return resp.json()
            except Exception as e:
                return {"error": str(e)}

    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file via sandbox."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.sandbox_url}/v1/file/write",
                    json={"file": path, "content": content},
                    timeout=10.0
                )
                return resp.json()
            except Exception as e:
                return {"error": str(e)}

    def _parse_jupyter_response(self, jupyter_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Jupyter response into standardized format."""
        status = jupyter_result.get('status', 'error')
        outputs = jupyter_result.get('outputs', [])

        stdout_parts = []
        stderr_parts = []
        result = None
        error_msg = None

        for output in outputs:
            output_type = output.get('output_type')

            if output_type == 'stream':
                text = output.get('text', '')
                if output.get('name') == 'stdout':
                    stdout_parts.append(text)
                elif output.get('name') == 'stderr':
                    stderr_parts.append(text)

            elif output_type == 'execute_result':
                # This is the return value
                data = output.get('data', {})
                result = data.get('text/plain', str(data))

            elif output_type == 'error':
                error_msg = output.get('evalue', 'Unknown error')
                traceback = output.get('traceback', [])
                stderr_parts.extend(traceback)

        return {
            'success': status == 'ok',
            'stdout': ''.join(stdout_parts),
            'stderr': ''.join(stderr_parts),
            'result': result,
            'error': error_msg
        }

    async def _execute_jupyter(self, code: str, session_id: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code via Jupyter kernel."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {"code": code, "timeout": timeout}
                if session_id:
                    payload["session_id"] = session_id

                resp = await client.post(
                    f"{self.sandbox_url}/v1/jupyter/execute",
                    json=payload,
                    timeout=float(timeout + 5)  # Add buffer to HTTP timeout
                )
                sandbox_response = resp.json()

                # Sandbox wraps response in {"success": true, "data": {...}}
                if sandbox_response.get('success') and 'data' in sandbox_response:
                    jupyter_result = sandbox_response['data']
                    return self._parse_jupyter_response(jupyter_result)
                else:
                    error = sandbox_response.get('message', 'Unknown sandbox error')
                    return {"success": False, "error": error, "stdout": "", "stderr": ""}
            except Exception as e:
                return {"success": False, "error": str(e), "stdout": "", "stderr": ""}

    def _parse_nodejs_response(self, nodejs_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Node.js response into standardized format."""
        status = nodejs_result.get('status', 'error')
        exit_code = nodejs_result.get('exit_code', 1)

        # Extract result from outputs if present
        result = None
        outputs = nodejs_result.get('outputs', [])
        if outputs:
            # Look for return value in last output
            last_output = outputs[-1]
            if last_output.get('output_type') == 'execute_result':
                data = last_output.get('data', {})
                result = data.get('text/plain', str(data))

        return {
            'success': status == 'ok' and exit_code == 0,
            'stdout': nodejs_result.get('stdout', ''),
            'stderr': nodejs_result.get('stderr', ''),
            'result': result,
            'error': nodejs_result.get('stderr') if status != 'ok' else None
        }

    async def _execute_nodejs(self, code: str, files: Dict[str, str] = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute JavaScript code via Node.js."""
        async with httpx.AsyncClient() as client:
            try:
                payload = {"code": code, "timeout": timeout}
                if files:
                    payload["files"] = files

                resp = await client.post(
                    f"{self.sandbox_url}/v1/nodejs/execute",
                    json=payload,
                    timeout=float(timeout + 5)  # Add buffer to HTTP timeout
                )
                sandbox_response = resp.json()

                # Sandbox wraps response in {"success": true, "data": {...}}
                if sandbox_response.get('success') and 'data' in sandbox_response:
                    nodejs_result = sandbox_response['data']
                    return self._parse_nodejs_response(nodejs_result)
                else:
                    error = sandbox_response.get('message', 'Unknown sandbox error')
                    return {"success": False, "error": error, "stdout": "", "stderr": ""}
            except Exception as e:
                return {"success": False, "error": str(e), "stdout": "", "stderr": ""}

    async def _ai_generate_and_execute(
        self,
        description: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
        include_attestation: bool = True
    ) -> Dict[str, Any]:
        """
        Generate code with AI and execute it with TEE attestation.

        Returns verifiable result with attestation data for end-user verification.
        Matches existing API response format for UI compatibility.
        """
        if not self.ai_generator:
            return {
                "success": False,
                "error": "AI generator not available. Set REDPILL_API_KEY environment variable.",
                "message": "Please configure RedPill API key in environment"
            }

        if language not in ['python', 'javascript']:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
                "message": "Supported languages: python, javascript"
            }

        # 1. Generate code with AI (includes TEE attestation)
        try:
            if language == 'python':
                code, attestation = await self.ai_generator.generate_python_script(
                    description, context, include_attestation
                )
            else:  # javascript
                code, attestation = await self.ai_generator.generate_javascript_script(
                    description, context, include_attestation
                )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "AI code generation failed",
                "language": language
            }

        # 2. Execute the generated code
        if language == 'python':
            exec_result = await self._execute_jupyter(code)
        else:  # javascript
            exec_result = await self._execute_nodejs(code)

        # 3. Check if execution succeeded
        execution_success = exec_result.get('success', False) and not exec_result.get('error')

        if execution_success:
            return {
                "success": True,
                "message": "Code generated and executed successfully",
                "language": language,
                "generated_code": code,
                "output": exec_result.get('stdout', ''),
                "result": exec_result.get('result'),
                "execution_details": {
                    "success": True,
                    "stdout": exec_result.get('stdout', ''),
                    "stderr": exec_result.get('stderr', ''),
                    "result": exec_result.get('result')
                },
                "attestation": attestation if include_attestation else None,
                "retries_used": 0,
                "verification_url": "/verify-attestation" if attestation else None
            }

        # 4. Retry with error feedback if failed
        if max_retries > 0:
            retry_context = {
                **(context or {}),
                "previous_code": code,
                "error": exec_result.get('error', exec_result.get('stderr', 'Unknown error'))
            }

            retry_result = await self._ai_generate_and_execute(
                description,
                language,
                retry_context,
                max_retries - 1,
                include_attestation
            )

            # Update retries_used counter
            if retry_result.get('success'):
                retry_result['retries_used'] = retry_result.get('retries_used', 0) + 1
                retry_result['message'] = f"Code generated and executed successfully (after {retry_result['retries_used']} retries)"

            return retry_result

        # Failed after all retries
        return {
            "success": False,
            "error": exec_result.get('error', exec_result.get('stderr', 'Execution failed')),
            "message": f"Code execution failed after {max_retries + 1} attempts",
            "language": language,
            "generated_code": code,
            "output": exec_result.get('stderr', ''),
            "execution_details": exec_result,
            "attestation": attestation if include_attestation else None,
            "retries_used": max_retries
        }

    async def _ai_mcp_control(
        self,
        description: str,
        include_attestation: bool = True,
        show_mcp_call: bool = True,
        confirm_dangerous: bool = True
    ) -> Dict[str, Any]:
        """
        Generate MCP tool call from natural language and execute it with TEE attestation.

        Returns verifiable result with attestation data for end-user verification.
        """
        if not self.ai_generator:
            return {
                "success": False,
                "error": "AI generator not available. Set REDPILL_API_KEY environment variable.",
                "message": "Please configure RedPill API key in environment"
            }

        # 1. Generate MCP tool call with AI (includes TEE attestation)
        try:
            mcp_call, attestation = await self.ai_generator.generate_mcp_tool_call(
                description, include_attestation
            )
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "AI MCP call generation failed"
            }

        # 2. Validate MCP call structure
        if not isinstance(mcp_call, dict) or 'tool' not in mcp_call or 'parameters' not in mcp_call:
            return {
                "success": False,
                "error": "Invalid MCP call structure",
                "message": "Generated MCP call is malformed",
                "mcp_call": mcp_call if show_mcp_call else None
            }

        # 3. Check if dangerous operation (optional confirmation)
        dangerous_tools = ['exec_command', 'write_file', 'cleanup']
        if confirm_dangerous and any(d in mcp_call['tool'] for d in dangerous_tools):
            # In production, you might want to add a confirmation step here
            # For now, we'll just log it
            print(f"⚠️ Executing potentially dangerous MCP tool: {mcp_call['tool']}")

        # 4. Execute the MCP tool call
        try:
            result = await self._execute_mcp_tool(mcp_call['tool'], mcp_call['parameters'])
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "MCP tool execution failed",
                "mcp_call": mcp_call if show_mcp_call else None,
                "attestation": attestation if include_attestation else None
            }

        # 5. Return success response
        return {
            "success": True,
            "message": "MCP operation completed successfully",
            "mcp_call": mcp_call if show_mcp_call else None,
            "result": result,
            "attestation": attestation if include_attestation else None,
            "verification_url": "/verify-attestation" if attestation else None
        }

    async def _execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute an MCP tool via the sandbox.

        Maps MCP tool names to sandbox API endpoints.
        """
        # Map MCP tool names to sandbox endpoints
        tool_mapping = {
            # File and shell operations
            'mcp__sandbox__exec_command': '/v1/shell/exec',
            'mcp__sandbox__read_file': '/v1/file/read',
            'mcp__sandbox__write_file': '/v1/file/write',
            'mcp__sandbox__list_path': '/v1/file/list',
            'mcp__sandbox__find_files': '/v1/file/find',
            'mcp__sandbox__search_in_file': '/v1/file/search',
            'mcp__sandbox__execute_jupyter_code': '/v1/jupyter/execute',
            'mcp__sandbox__execute_nodejs_code': '/v1/nodejs/execute',

            # Browser automation tools
            'mcp__sandbox__browser_navigate': '/v1/browser/navigate',
            'mcp__sandbox__browser_go_back': '/v1/browser/go-back',
            'mcp__sandbox__browser_go_forward': '/v1/browser/go-forward',
            'mcp__sandbox__browser_form_input_fill': '/v1/browser/form-input-fill',
            'mcp__sandbox__browser_get_markdown': '/v1/browser/get-markdown',
            'mcp__sandbox__browser_get_text': '/v1/browser/get-text',
            'mcp__sandbox__browser_read_links': '/v1/browser/read-links',
            'mcp__sandbox__browser_new_tab': '/v1/browser/new-tab',
            'mcp__sandbox__browser_tab_list': '/v1/browser/tab-list',
            'mcp__sandbox__browser_switch_tab': '/v1/browser/switch-tab',
            'mcp__sandbox__browser_close_tab': '/v1/browser/close-tab',
            'mcp__sandbox__browser_evaluate': '/v1/browser/evaluate',
            'mcp__sandbox__browser_vision_screen_capture': '/v1/browser/vision-screen-capture',
            'mcp__sandbox__browser_vision_screen_click': '/v1/browser/vision-screen-click',
            'mcp__sandbox__browser_get_download_list': '/v1/browser/get-download-list',
            'mcp__sandbox__browser_screenshot': '/v1/browser/screenshot',
            'mcp__sandbox__browser_click': '/v1/browser/click',
            'mcp__sandbox__browser_select': '/v1/browser/select',
            'mcp__sandbox__browser_hover': '/v1/browser/hover',
            'mcp__sandbox__browser_get_clickable_elements': '/v1/browser/get-clickable-elements',
            'mcp__sandbox__browser_scroll': '/v1/browser/scroll',
            'mcp__sandbox__browser_close': '/v1/browser/close',
            'mcp__sandbox__browser_press_key': '/v1/browser/press-key'
        }

        endpoint = tool_mapping.get(tool_name)
        if not endpoint:
            raise ValueError(f"Unknown MCP tool: {tool_name}")

        # Execute via sandbox
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.sandbox_url}{endpoint}",
                    json=parameters,
                    timeout=60.0
                )

                result = resp.json()

                # Handle different response formats
                if result.get('success') and 'data' in result:
                    return result['data']
                elif result.get('success'):
                    return result
                else:
                    raise Exception(result.get('message', 'Unknown error'))

            except Exception as e:
                raise Exception(f"MCP tool execution failed: {str(e)}")

    def _get_verification_instructions(self) -> Dict[str, str]:
        """Get instructions for end-user verification"""
        return {
            "message": "This result includes TEE attestation. Verify using the verification tools.",
            "verification_script": "python verify_ai_attestation.py",
            "docs_url": "https://docs.redpill.ai/confidential-ai/attestation"
        }

    async def _create_agent_card(self) -> Dict[str, Any]:
        """Create ERC-8004 agent card."""
        from ..agent.agent_card import create_tee_agent_card

        agent_address = await self._get_agent_address()

        capabilities = [
            ("shell-execution", "Execute shell commands via AIO Sandbox"),
            ("file-operations", "Read/write files in sandbox"),
            ("jupyter-execution", "Run Python/Node.js code"),
            ("ai-code-generation", "Generate and execute code from natural language with TEE attestation"),
            ("ai-mcp-control", "Control sandbox via MCP tools using natural language with TEE attestation")
        ]

        # Only add AI capabilities if generator is available
        if not self.ai_generator:
            capabilities = [c for c in capabilities if c[0] not in ["ai-code-generation", "ai-mcp-control"]]

        return create_tee_agent_card(
            name=f"TEE Server Agent - {self.config.domain}",
            description="TEE-secured agent with AIO Sandbox integration for secure code execution",
            domain=self.config.domain,
            agent_address=agent_address,
            agent_id=self.agent_id if self.is_registered else None,
            signature=None,
            capabilities=capabilities,
            chain_id=self.config.chain_id
        )
