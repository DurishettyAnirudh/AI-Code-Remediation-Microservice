from __future__ import annotations
import json
from typing import Any, Dict, List
import requests


def query_ollama(
	system_prompt: str,
	user_prompt: str,
	*,
	endpoint: str = "http://localhost:11434/api/generate",
	model: str = "phi3:mini",
	timeout: float = 100,
	return_metadata: bool = False,
) -> Dict[str, Any]:
	

	payload = {
		"model": model,
		"system": system_prompt,
		"prompt": user_prompt,
		"stream": False,
		"format": "json",
	}

	response = requests.post(endpoint, json=payload, timeout=timeout)
	response.raise_for_status()

	body = response.json()
	raw_response = body.get("response", "")
	try:
		parsed = _parse_response_json(raw_response)
	except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
		raise ValueError(
			"Model response was not valid JSON: "
			+ raw_response[:200]
		) from exc
	if not return_metadata:
		return parsed
	metadata = {
		"model": body.get("model", model),
		"prompt_eval_count": body.get("prompt_eval_count", 0),
		"eval_count": body.get("eval_count", 0),
		"total_duration": body.get("total_duration", 0),
	}
	return parsed, metadata


def get_available_models(endpoint: str = "http://localhost:11434/api/tags") -> List[str]:
    """Fetch the list of available models from the Ollama API."""
    try:
        response = requests.get(endpoint, timeout=5)
        response.raise_for_status()
        return [model["name"] for model in response.json().get("models", [])]
    except requests.RequestException:
        return []


def _parse_response_json(raw_text: str) -> Dict[str, Any]:
	"""Coerce the model response into JSON even if wrapped in code fences."""
	cleaned = raw_text.strip()
	if cleaned.startswith("```"):
		cleaned = cleaned[3:]
		if cleaned.lower().startswith("json"):
			cleaned = cleaned[4:]
		cleaned = cleaned.split("```", 1)[0]
		cleaned = cleaned.strip()
	return json.loads(cleaned)

if __name__ == "__main__":
	system_prompt = "You are a professional security analyst, penetration tester and also senior developer."
	user_prompt = """
You are given the following vulnerable input description:
{
  "language": "java",
  "cwe": "CWE-89",
  "code": "String id = request.getParameter('id');\nString query = \"SELECT * FROM accounts WHERE username = '" + id + "'\";\nStatement stmt = conn.createStatement();\nResultSet rs = stmt.executeQuery(query);"
}
Identify how the snippet leads to SQL injection (CWE-89), then reply strictly as JSON matching {"fixed_code": str, "explanation": str} with a safe rewrite and a concise rationale.
"""
	result = query_ollama(system_prompt, user_prompt)
	print(json.dumps(result, indent=2))

