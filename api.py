"""FastAPI server exposing the local remediation endpoint."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import generate_fix, vector_store

app = FastAPI(title="Local Secure Fix Service")


class VulnerabilityRequest(BaseModel):
    language: str
    cwe: str
    code: str
    model: str = "gemma3:1b"


@app.post("/local_fix")
async def local_fix(request: VulnerabilityRequest):
    """Generate a secure fix for the incoming vulnerable snippet."""
    try:
        # Pass the model from the request to the generate_fix function
        result, context = generate_fix(
            request.dict(exclude={"model"}), model=request.model
        )
        # Also return the context
        result["retrieved_context"] = context
        return result
    except ValueError as exc:
        # Handle cases where the model response is invalid
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Catch-all for any other unexpected errors (e.g., Ollama connection error)
        error_message = f"An unexpected error occurred: {type(exc).__name__}: {exc}"
        raise HTTPException(status_code=500, detail=error_message) from exc
