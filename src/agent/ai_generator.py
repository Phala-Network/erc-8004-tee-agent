"""AI-Assisted Script Generator with TEE Attestation"""

import os
import json
import secrets
import httpx
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class AIScriptGenerator:
    """Generate code using RedPill Confidential AI with TEE attestation"""

    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or os.getenv("REDPILL_API_KEY")
        self.api_url = api_url or os.getenv("REDPILL_API_URL", "https://api.redpill.ai")

        if not self.api_key:
            raise ValueError("REDPILL_API_KEY not set")

        self.model = os.getenv("AI_MODEL", "phala/qwen-2.5-7b-instruct")
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "2000"))

        print(f"🤖 AI Generator: {self.model}")

    async def generate_python_script(
        self,
        task_description: str,
        context: Dict[str, Any] = None,
        include_attestation: bool = True
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Generate Python code from natural language with TEE attestation.

        Returns:
            (code, attestation_data) tuple
        """
        prompt = self._build_prompt("python", task_description, context)
        code, attestation = await self._call_ai(prompt, include_attestation)
        return code, attestation

    async def generate_javascript_script(
        self,
        task_description: str,
        context: Dict[str, Any] = None,
        include_attestation: bool = True
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Generate JavaScript code from natural language with TEE attestation.

        Returns:
            (code, attestation_data) tuple
        """
        prompt = self._build_prompt("javascript", task_description, context)
        code, attestation = await self._call_ai(prompt, include_attestation)
        return code, attestation

    def _build_prompt(
        self,
        language: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build optimized prompt for code generation"""

        # Handle retry context with previous errors
        if context and "previous_code" in context:
            base_prompt = f"""The previous code failed. Generate a corrected version.

Previous code:
```{language}
{context['previous_code']}
```

Error:
{context.get('error', 'Unknown error')}

Task: {task}

Generate corrected code that fixes the error. Return only the code, no explanations."""
        else:
            base_prompt = f"""You are an expert {language} programmer. Generate clean, efficient code for the following task.

Task: {task}

Requirements:
- Write production-quality code
- Include error handling
- Add brief comments for complex logic
- Return only the code, no markdown fences or explanations
- Ensure code is self-contained and runnable"""

        if language == "python":
            base_prompt += """

Available libraries: numpy, pandas, matplotlib, requests, web3, eth_account, json, os, sys
Output format: Pure Python code only"""
        elif language == "javascript":
            base_prompt += """

Available libraries: ethers, axios, crypto, fs
Output format: Pure JavaScript code only"""

        if context and "previous_code" not in context:
            base_prompt += f"\n\nContext:\n{json.dumps(context, indent=2)}"

        return base_prompt

    async def _call_ai(
        self,
        prompt: str,
        include_attestation: bool
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Call RedPill Confidential AI API with attestation.

        Returns:
            (code, attestation_data) tuple
        """
        # Generate fresh nonce for attestation
        nonce = secrets.token_hex(32) if include_attestation else None

        async with httpx.AsyncClient() as client:
            # 1. Make inference request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            if nonce:
                headers["X-Attestation-Nonce"] = nonce

            try:
                inference_response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert programmer. Generate clean, runnable code."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    },
                    timeout=60.0
                )

                if inference_response.status_code != 200:
                    raise Exception(f"AI API returned status {inference_response.status_code}: {inference_response.text}")

                result = inference_response.json()

                # Extract generated code
                code = result["choices"][0]["message"]["content"]
                code = self._extract_code(code)

                # 2. Fetch attestation if requested
                attestation_data = None
                if include_attestation:
                    try:
                        attestation_data = await self._fetch_attestation(
                            nonce=nonce,
                            inference_timestamp=result.get("created"),
                            model=self.model
                        )

                        # Add inference metadata
                        attestation_data["inference"] = {
                            "model": self.model,
                            "prompt_hash": self._hash_prompt(prompt),
                            "response_hash": self._hash_response(code),
                            "timestamp": result.get("created"),
                            "usage": result.get("usage")
                        }
                    except Exception as e:
                        print(f"⚠️ Attestation fetch failed (code generation succeeded): {e}")
                        attestation_data = {"error": f"Attestation unavailable: {str(e)}"}

                return code, attestation_data

            except Exception as e:
                raise Exception(f"AI generation failed: {str(e)}")

    async def _fetch_attestation(
        self,
        nonce: str,
        inference_timestamp: Optional[int],
        model: str
    ) -> Dict[str, Any]:
        """Fetch TEE attestation report for the inference"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v1/attestation/report",
                params={
                    "model": model,
                    "nonce": nonce
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )

            attestation = response.json()

            # Add verification metadata
            attestation["verification"] = {
                "nonce": nonce,
                "fetched_at": datetime.utcnow().isoformat(),
                "inference_timestamp": inference_timestamp
            }

            return attestation

    def _extract_code(self, ai_response: str) -> str:
        """Extract code from AI response, removing markdown fences"""
        code = ai_response.strip()

        # Remove markdown code fences
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```javascript"):
            code = code[13:]
        elif code.startswith("```js"):
            code = code[5:]
        elif code.startswith("```"):
            code = code[3:]

        if code.endswith("```"):
            code = code[:-3]

        return code.strip()

    def _hash_prompt(self, prompt: str) -> str:
        """Hash prompt for verification"""
        import hashlib
        return hashlib.sha256(prompt.encode()).hexdigest()

    def _hash_response(self, response: str) -> str:
        """Hash response for verification"""
        import hashlib
        return hashlib.sha256(response.encode()).hexdigest()


    async def generate_mcp_tool_call(
        self,
        task_description: str,
        include_attestation: bool = True
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Generate MCP tool call from natural language with TEE attestation.

        Returns:
            (mcp_call_dict, attestation_data) tuple
        """
        prompt = self._build_mcp_prompt(task_description)
        mcp_json, attestation = await self._call_ai(prompt, include_attestation)

        try:
            # Extract JSON from response (handle cases where AI adds extra text)
            mcp_json = self._extract_json(mcp_json)

            # Parse the JSON response
            mcp_call = json.loads(mcp_json)
            return mcp_call, attestation
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse MCP call JSON: {str(e)}\nGenerated: {mcp_json}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text that may contain extra content"""
        text = text.strip()

        # Find the first { and last }
        start = text.find('{')
        end = text.rfind('}')

        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        return text

    def _build_mcp_prompt(self, task: str) -> str:
        """Build optimized prompt for MCP tool call generation"""
        return f"""Task: {task}

Available MCP tools:
- mcp__sandbox__exec_command: Execute shell commands
  Parameters: {{"command": "string", "timeout": number (optional), "async_mode": bool (optional)}}

- mcp__sandbox__read_file: Read file contents
  Parameters: {{"file": "absolute_path", "start_line": number (optional), "end_line": number (optional)}}

- mcp__sandbox__write_file: Write file contents
  Parameters: {{"file": "absolute_path", "content": "string", "append": bool (optional)}}

- mcp__sandbox__list_path: List directory contents
  Parameters: {{"path": "directory_path", "recursive": bool (optional), "show_hidden": bool (optional)}}

- mcp__sandbox__find_files: Find files by pattern
  Parameters: {{"path": "directory_path", "glob": "pattern"}}

- mcp__sandbox__search_in_file: Search in file content
  Parameters: {{"file": "absolute_path", "regex": "pattern"}}

- mcp__sandbox__execute_jupyter_code: Execute Python code
  Parameters: {{"code": "python_code", "timeout": number (optional)}}

- mcp__sandbox__execute_nodejs_code: Execute JavaScript code
  Parameters: {{"code": "javascript_code", "timeout": number (optional)}}

CRITICAL: Your response must be ONLY valid JSON. Do not include any text before or after the JSON.
Output the JSON object directly without any preamble, explanation, or markdown formatting.

JSON format:
{{
    "tool": "mcp__sandbox__tool_name",
    "parameters": {{ ... }}
}}"""

    async def generate_browser_workflow(
        self,
        task_description: str,
        include_attestation: bool = True
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Generate multi-step browser workflow from natural language with TEE attestation.

        Returns:
            (workflow_dict, attestation_data) tuple where workflow_dict contains:
            - workflow_id: str
            - name: str
            - description: str
            - steps: List[dict] with step_number, description, tool, parameters
        """
        prompt = self._build_browser_workflow_prompt(task_description)
        workflow_json, attestation = await self._call_ai(prompt, include_attestation)

        try:
            # Extract JSON from response (handle cases where AI adds extra text)
            workflow_json = self._extract_json_array(workflow_json)

            # Parse the JSON response
            steps_data = json.loads(workflow_json)

            if not isinstance(steps_data, list):
                raise ValueError("Expected array of steps")

            # Build workflow dict
            workflow_dict = {
                "workflow_id": f"workflow-{secrets.token_hex(8)}",
                "name": task_description[:100],
                "description": task_description,
                "steps": steps_data,
                "variables": {},
                "created_by": "ai",
                "attestation_mode": "aggregate"
            }

            return workflow_dict, attestation

        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f"Failed to parse browser workflow JSON: {str(e)}\nGenerated: {workflow_json}")

    def _extract_json_array(self, text: str) -> str:
        """Extract JSON array from text that may contain extra content"""
        text = text.strip()

        # Find the first [ and last ]
        start = text.find('[')
        end = text.rfind(']')

        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        # Fallback to object extraction
        return self._extract_json(text)

    def _build_browser_workflow_prompt(self, task: str) -> str:
        """Build optimized prompt for browser workflow generation"""
        return f"""Task: {task}

Generate a browser automation workflow as a JSON array of steps.

Available browser tools:
- mcp__sandbox__browser_navigate: Navigate to URL
  Parameters: {{"url": "string"}}

- mcp__sandbox__browser_form_input_fill: Fill form input field
  Parameters: {{"index": number, "value": "string", "clear": boolean (optional)}}

- mcp__sandbox__browser_click: Click element by index
  Parameters: {{"index": number}}

- mcp__sandbox__browser_wait_for: Wait for text to appear
  Parameters: {{"text": "string"}}

- mcp__sandbox__browser_screenshot: Take screenshot
  Parameters: {{}}

- mcp__sandbox__browser_get_clickable_elements: Get list of clickable elements
  Parameters: {{}}

- mcp__sandbox__browser_get_markdown: Get page content as markdown
  Parameters: {{}}

CRITICAL: Your response must be ONLY a valid JSON array. No text before or after.
Each step must have:
- step_number: Sequential number (1, 2, 3, ...)
- description: Human-readable description
- tool: MCP tool name (mcp__sandbox__browser_*)
- parameters: Object with tool parameters

Example format:
[
  {{"step_number": 1, "description": "Navigate to login page", "tool": "mcp__sandbox__browser_navigate", "parameters": {{"url": "https://github.com/login"}}}},
  {{"step_number": 2, "description": "Get clickable elements", "tool": "mcp__sandbox__browser_get_clickable_elements", "parameters": {{}}}},
  {{"step_number": 3, "description": "Fill username field", "tool": "mcp__sandbox__browser_form_input_fill", "parameters": {{"index": 0, "value": "user@example.com"}}}}
]

Be specific and thorough. Include all necessary steps."""


async def verify_ai_attestation(attestation_data: Dict[str, Any]) -> bool:
    """
    Verify TEE attestation for AI inference (lightweight check).

    For full verification, use the verification tools in verify_ai_attestation.py
    """
    try:
        # Basic checks
        if not attestation_data.get("verified"):
            return False

        # Check timestamp freshness (within 10 minutes)
        from datetime import datetime, timedelta
        timestamp = attestation_data["attestation"]["timestamp"]
        att_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        age = datetime.utcnow() - att_time.replace(tzinfo=None)

        if age > timedelta(minutes=10):
            return False

        # Check nonce is present
        if not attestation_data.get("verification", {}).get("nonce"):
            return False

        return True
    except Exception:
        return False
