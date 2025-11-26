# AI Code Remediation Microservice

This project provides a local, AI-powered microservice for identifying and fixing vulnerabilities in code snippets. It uses a local Ollama instance to run large language models, a FastAPI backend to expose the logic, a Streamlit UI for interaction, and a Retrieval-Augmented Generation (RAG) pipeline to provide context-specific guidance.

## Features

- **Local First**: Runs entirely on your local machine. No data is sent to external cloud services.
- **FastAPI Backend**: A robust API to handle code remediation requests.
- **Streamlit UI**: An easy-to-use web interface for testing and interacting with the service.
- **Retrieval-Augmented Generation (RAG)**: Uses a local vector store (FAISS) to retrieve relevant security guidance from a knowledge base, improving the quality of the AI-generated fixes.
- **Dynamic Model Selection**: Allows users to choose from any model available in their local Ollama instance.
- **Automated Setup**: A simple batch script to set up the environment and run the application.
- **Testing Suite**: A dedicated script to validate the functionality of the entire pipeline.

## Assignment Checklist

This table summarizes the project's status against the assignment requirements.

| Requirement | Status | Notes |
| :--- | :--- | :--- |
| **Local LLM Inference** | ✅ Implemented | Using Ollama to serve `gemma3:1b`. |
| **FastAPI Microservice** | ✅ Implemented | `POST /local_fix` with correct schemas. |
| **Logging & Metrics** | ✅ Implemented | Logging to console and `metrics.csv`. |
| **Testing Script** | ✅ Implemented | `test_local.py` validates the full pipeline. |
| **RAG Component (Optional)** | ✅ Implemented | A full RAG pipeline with FAISS is complete. |
| **Dockerization (Optional)** | ❌ Not Implemented | No `Dockerfile` has been created. |
| **Unit Tests (Optional)** | 🟡 Partially Implemented | An integration test (`test_local.py`) exists, but no formal unit tests for individual functions. |

## Setup Instructions

A setup script is provided to automate the entire process.

**Prerequisites:**
1.  **Python**: Python 3.8+ must be installed and added to your system's PATH.
2.  **Ollama**: The Ollama application must be installed and running. You can download it from [ollama.com](https://ollama.com/).

**Automated Setup:**
(May take some time for initial setup.)
Simply double-click the `setup.bat` file. It will perform the following steps:
1.  Check for Python and a running Ollama instance.
2.  Pull the default model (`gemma3:1b`) if it's not already available.
3.  Create a Python virtual environment (`venv`).
4.  Install all required dependencies from `requirements.txt`.
5.  Start the FastAPI server in a new terminal window.
6.  Launch the Streamlit UI in your default web browser.

## How the Model is Run

The application interacts with a locally running Large Language Model (LLM) via the Ollama API.

- **API Endpoint**: The core logic in `main.py` sends prompts to Ollama's `/api/generate` endpoint.
- **Model Selection**: The default model is `gemma3:1b`, which is automatically pulled by the setup script. You can select any other model you have downloaded in Ollama directly from the dropdown menu in the Streamlit UI.
- **RAG Augmentation**: Before sending a prompt to the model, the system retrieves relevant security information (checklists, fix ideas) from the `recipes/` directory using a FAISS vector store. This context is added to the prompt to guide the model toward a better, more accurate fix.
- **JSON Mode**: The application instructs Ollama to use its `json` mode to ensure the model's output is always a syntactically correct JSON object, improving reliability.

## Example Input and Output

Here is an example of a request sent to the API and the corresponding response.

**Example Input (CWE-89: SQL Injection)**
```json
{
  "language": "python",
  "cwe": "CWE-89",
  "code": "import sqlite3\n\ndef get_user(username):\n    conn = sqlite3.connect('example.db')\n    cursor = conn.cursor()\n    query = \"SELECT * FROM users WHERE username = '\" + username + \"'\"\n    cursor.execute(query)\n    user = cursor.fetchone()\n    conn.close()\n    return user",
  "model": "gemma3:1b"
}
```

**Example Output**
```json
{
    "fixed_code": "import sqlite3\n\ndef get_user(username):\n    conn = sqlite3.connect('example.db')\n    cursor = conn.cursor()\n    query = \"SELECT * FROM users WHERE username = ?\"\n    cursor.execute(query, (username,))\n    user = cursor.fetchone()\n    conn.close()\n    return user",
    "diff": "--- \n+++ \n@@ -5,7 +5,7 @@\n def get_user(username):\n     conn = sqlite3.connect('example.db')\n     cursor = conn.cursor()\n-    query = \"SELECT * FROM users WHERE username = '\" + username + \"'\"\n-    cursor.execute(query)\n+    query = \"SELECT * FROM users WHERE username = ?\"\n+    cursor.execute(query, (username,))\n     user = cursor.fetchone()\n     conn.close()\n     return user",
    "explanation": "The original code was vulnerable to SQL injection because it used string concatenation to build the SQL query. This allows an attacker to manipulate the query by providing malicious input. The fix uses a parameterized query, which separates the SQL code from the data. This ensures that user input is treated as data and not as executable code, preventing SQL injection attacks.",
    "model_used": "gemma3:1b",
    "token_usage": {
        "input_tokens": 834,
        "output_tokens": 136
    },
    "latency_ms": 4947,
    "retrieved_context": "**SQL Injection**\n\nThe software constructs all or part of a SQL command..."
}
```

## Observations about Performance

- **Latency**: With the default `gemma3:1b` model on standard hardware, response times are typically between **4 to 7 seconds**.
- **Hardware Dependency**: Performance is highly dependent on your machine's CPU, RAM, and whether you have a dedicated GPU. Larger models will require more resources and have higher latency.
- **RAG Overhead**: The vector search for RAG is very fast (typically < 50ms) and adds negligible overhead to the total response time. The main bottleneck is the model's generation speed.
- **Model Quality**: The quality of the `fixed_code` and `explanation` varies by model. Smaller models like `gemma3:1b` are fast but may sometimes provide incomplete or incorrect fixes. Larger, more capable models will likely yield better results at the cost of higher latency.

## Assumptions and Limitations

- **Ollama Dependency**: The application is entirely dependent on a running Ollama instance. If the Ollama server is down, the application will not work.
- **Windows-Centric Setup**: The `setup.bat` script is designed for Windows. Users on macOS or Linux will need to follow the steps manually (create a venv, `pip install -r requirements.txt`, run `uvicorn` and `streamlit`).
- **RAG Knowledge Base**: The effectiveness of the RAG pipeline is limited by the content in the `recipes/` directory. If no relevant recipe is found, the model will not receive any specific guidance.
- **Model Reliability**: The correctness of the code fix is not guaranteed. All AI-generated code should be carefully reviewed by a human expert before being used in a production environment.
- **Vector Store Updates**: The FAISS vector store does not update automatically. If you add or modify files in the `recipes/` folder, you must manually delete the `faiss_*.bin` and `documents.json` files and restart the server to force the index to be rebuilt.