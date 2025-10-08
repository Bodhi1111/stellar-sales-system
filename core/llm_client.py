"""
Centralized LLM client with timeout, retry logic, and error handling.
Optimized for DeepSeek-Coder 33B model which has slower inference times.
"""
import requests
import json
import time
from typing import Dict, Any, Optional
from config.settings import Settings


class LLMClient:
    """
    Wrapper for Ollama API calls with robust error handling.

    Features:
    - Configurable timeouts for large models (33B)
    - Retry logic with exponential backoff
    - Proper error messages
    - JSON validation
    """

    def __init__(self, settings: Settings, timeout: int = 120, max_retries: int = 3):
        """
        Initialize LLM client.

        Args:
            settings: Application settings with Ollama configuration
            timeout: Request timeout in seconds (default 120s for 33B model)
            max_retries: Maximum number of retry attempts (default 3)
        """
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME
        self.timeout = timeout
        self.max_retries = max_retries

    def generate(
        self,
        prompt: str,
        format_json: bool = False,
        stream: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM with retry logic.

        Args:
            prompt: The prompt to send to the LLM
            format_json: Whether to request JSON formatted output
            stream: Whether to stream the response (not recommended for reliability)
            timeout: Override default timeout for this request

        Returns:
            Dict containing:
                - success: bool
                - response: str (if successful)
                - error: str (if failed)
                - elapsed_time: float (seconds)
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream
        }

        if format_json:
            payload["format"] = "json"

        use_timeout = timeout if timeout is not None else self.timeout

        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()

                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=use_timeout
                )
                response.raise_for_status()

                elapsed = time.time() - start_time

                result = response.json()
                llm_response = result.get("response", "")

                # Validate JSON if requested
                if format_json:
                    try:
                        json.loads(llm_response)
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "error": f"LLM returned invalid JSON: {e}",
                            "raw_response": llm_response,
                            "elapsed_time": elapsed
                        }

                return {
                    "success": True,
                    "response": llm_response,
                    "elapsed_time": elapsed,
                    "attempt": attempt
                }

            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    print(
                        f"   ⚠️ LLM request timed out (attempt {attempt}/{self.max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return {
                        "success": False,
                        "error": f"LLM request timed out after {attempt} attempts ({use_timeout}s each)",
                        "elapsed_time": use_timeout * attempt
                    }

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    print(
                        f"   ⚠️ LLM request failed (attempt {attempt}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return {
                        "success": False,
                        "error": f"LLM request failed after {attempt} attempts: {str(e)}",
                        "elapsed_time": time.time() - start_time if 'start_time' in locals() else 0
                    }

            except Exception as e:
                return {
                    "success": False,
                    "error": f"Unexpected error: {type(e).__name__}: {str(e)}",
                    "elapsed_time": time.time() - start_time if 'start_time' in locals() else 0
                }

        # Should never reach here, but just in case
        return {
            "success": False,
            "error": "Maximum retries exceeded",
            "elapsed_time": use_timeout * self.max_retries
        }

    def generate_json(self, prompt: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Convenience method for generating JSON responses.

        Args:
            prompt: The prompt to send to the LLM
            timeout: Override default timeout

        Returns:
            Dict with 'success' bool and either 'data' (parsed JSON) or 'error'
        """
        result = self.generate(prompt, format_json=True, timeout=timeout)

        if not result["success"]:
            return result

        try:
            parsed_data = json.loads(result["response"])
            return {
                "success": True,
                "data": parsed_data,
                "elapsed_time": result["elapsed_time"],
                "attempt": result.get("attempt", 1)
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON: {e}",
                "raw_response": result["response"],
                "elapsed_time": result["elapsed_time"]
            }
