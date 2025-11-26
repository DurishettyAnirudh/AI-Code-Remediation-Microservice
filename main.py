"""CLI tool that requests secure fixes from Ollama and returns structured JSON."""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, Tuple

from ollama import query_ollama
from toolkit import diff_code, log_metrics
from vector_store import VectorStore
from retriever import Retriever

# Initialize components
vector_store = VectorStore()
retriever = Retriever(vector_store)

SYSTEM_PROMPT = (
    "You are a senior application security engineer. Your tasks are to analyze "
    "vulnerable code, explain the flaw, and provide a secure fix. "
    "Instructions:\n"
    "1. You must respond strictly with a JSON object: {\"fixed_code\": \"...\", \"explanation\": \"...\"}.\n"
    "2. The 'fixed_code' should only contain the corrected lines, not the entire original code block.\n"
    "3. Do not include any text, markdown, or prose outside of this JSON object."
)


def build_user_prompt(payload: Dict[str, Any], context: str) -> str:
    """Compose the user instructions for the LLM."""
    language = payload.get("language", "unknown language")
    cwe = payload.get("cwe", "unspecified CWE")
    code = payload.get("code", "").strip()
    return (
        f"Analyze the following vulnerable {language} code snippet, flagged as {cwe}.\n\n"
        f"Relevant Guidance:\n---\n{context}\n---\n\n"
        f"Vulnerable Code:\n{code}"
    )


def generate_fix(payload: Dict[str, Any], model: str = "gemma3:1b") -> Tuple[Dict[str, Any], str]:
	"""
    Send the payload to Ollama, assemble the required response JSON,
    and return it along with the retrieved context.
    """
	context = retriever.retrieve(
        cwe=payload.get("cwe", ""),
        language=payload.get("language", ""),
        code=payload.get("code", "")
    )
	user_prompt = build_user_prompt(payload, context)
	with open("Last_prompt.txt", "w") as f:
		f.write(SYSTEM_PROMPT + "\n\n\n"+ user_prompt)
	
	start_time = time.perf_counter()
	model_response, metadata = query_ollama(
		SYSTEM_PROMPT,
		user_prompt,
		model=model,
		return_metadata=True,
	)
	latency_ms = _extract_latency(metadata, start_time)
	fixed_code = model_response.get("fixed_code", "").strip()
	if not fixed_code:
		raise ValueError("Model response did not include 'fixed_code'.")
	diff = diff_code(payload.get("code", ""), fixed_code)
	token_usage = {
		"input_tokens": int(metadata.get("prompt_eval_count", 0)),
		"output_tokens": int(metadata.get("eval_count", 0)),
	}
	log_metrics(
		input_tokens=token_usage["input_tokens"],
		output_tokens=token_usage["output_tokens"],
		latency_ms=latency_ms,
	)
	result = {
		"fixed_code": fixed_code,
		"diff": diff,
		"explanation": model_response.get("explanation", "").strip(),
		"model_used": metadata.get("model", "unknown"),
		"token_usage": token_usage,
		"latency_ms": latency_ms,
	}
	return result, context


def _extract_latency(metadata: Dict[str, Any], start_time: float) -> int:
	"""Prefer Ollama's timing data but fall back to a local measurement."""
	total_duration = metadata.get("total_duration", 0)
	if isinstance(total_duration, (int, float)) and total_duration:
		return int(total_duration / 1_000_000)  # Ollama returns nanoseconds
	return int((time.perf_counter() - start_time) * 1000)



def main() -> None:
    """Read vulnerability JSON from stdin and print the structured fix JSON."""
    stdin_payload = sys.stdin.read().strip()
    if not stdin_payload:
        raise SystemExit("Provide the vulnerability JSON via stdin.")
    payload = json.loads(stdin_payload)
    result, context = generate_fix(payload)

    print("\n=== Retrieved Context ===\n")
    print(context)
    
    # Pretty print the result
    print("\n=== Fixed Code ===\n")
    print(result["fixed_code"])
    print("\n=== Diff ===\n")
    print(result["diff"])
    print("\n=== Explanation ===\n")
    print(result["explanation"])
    print("\n=== Model Used ===\n")
    print(result["model_used"])
    print("\n=== Token Usage ===\n")
    print(json.dumps(result["token_usage"], indent=2))
    print("\n=== Latency (ms) ===\n")
    print(result["latency_ms"])


if __name__ == "__main__":
	main()
