"""Workflow data models for browser automation"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RetryConfig(BaseModel):
    """Configuration for step retry behavior"""
    max_retries: int = Field(default=3, ge=0, le=10)
    backoff_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=5.0)
    retry_on_errors: List[str] = Field(
        default=["timeout", "element_not_found", "network_error"]
    )


class WorkflowStep(BaseModel):
    """A single step in a browser workflow"""
    step_id: str = Field(description="Unique identifier for this step")
    step_number: int = Field(description="Sequential step number (1-based)", ge=1)
    description: str = Field(description="Human-readable description of what this step does")
    tool: str = Field(description="MCP tool name to execute")
    parameters: Dict[str, Any] = Field(description="Parameters to pass to the tool")
    retry_config: Optional[RetryConfig] = Field(default=None, description="Retry configuration for this step")
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout in seconds")
    requires_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Expected browser state before execution (for validation)"
    )


class Workflow(BaseModel):
    """A multi-step browser automation workflow"""
    workflow_id: str = Field(description="Unique workflow identifier")
    name: str = Field(description="Workflow name")
    description: str = Field(description="Detailed workflow description")
    steps: List[WorkflowStep] = Field(description="Ordered list of workflow steps")
    variables: Dict[str, str] = Field(
        default={},
        description="Variables that can be substituted in step parameters"
    )
    created_by: str = Field(default="ai", description="Creator of the workflow (ai or user)")
    attestation_mode: str = Field(
        default="aggregate",
        description="How to handle attestation (aggregate or per_step)"
    )
    created_at: Optional[datetime] = Field(default=None, description="Workflow creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow-abc123",
                "name": "Login to GitHub",
                "description": "Authenticate with GitHub using username and password",
                "steps": [
                    {
                        "step_id": "step-1",
                        "step_number": 1,
                        "description": "Navigate to GitHub login page",
                        "tool": "mcp__sandbox__browser_navigate",
                        "parameters": {"url": "https://github.com/login"},
                        "timeout": 30
                    },
                    {
                        "step_id": "step-2",
                        "step_number": 2,
                        "description": "Fill username field",
                        "tool": "mcp__sandbox__browser_form_input_fill",
                        "parameters": {"selector": "#login_field", "value": "${username}"},
                        "timeout": 10
                    }
                ],
                "variables": {"username": "user@example.com"},
                "created_by": "ai",
                "attestation_mode": "aggregate"
            }
        }


class BrowserState(BaseModel):
    """Snapshot of browser state at a point in time"""
    url: str = Field(description="Current URL")
    title: str = Field(description="Page title")
    loaded_elements: List[str] = Field(default=[], description="List of loaded element selectors")
    screenshot_b64: Optional[str] = Field(default=None, description="Base64-encoded screenshot")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="State capture timestamp")


class WorkflowStepResult(BaseModel):
    """Result of executing a single workflow step"""
    step_id: str
    step_number: int
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries_used: int = 0
    duration_seconds: float = 0.0
    state_before: Optional[BrowserState] = None
    state_after: Optional[BrowserState] = None


class WorkflowExecutionResult(BaseModel):
    """Result of executing an entire workflow"""
    workflow_id: str
    success: bool
    steps: List[WorkflowStepResult]
    total_duration_seconds: float
    completed_steps: int
    failed_step: Optional[int] = None
    error_message: Optional[str] = None
    attestation: Optional[Dict[str, Any]] = None
    execution_id: str = Field(description="Unique execution identifier")
    started_at: datetime
    completed_at: Optional[datetime] = None
