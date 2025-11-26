"""
Test script for the local code fixing API.

This script sends multiple test vulnerabilities to the /local_fix endpoint
and validates the responses based on several criteria:
- API availability and success (200 OK).
- API response schema correctness.
- RAG retrieval logic (context is successfully retrieved).
- Latency of the response.
"""
import time
import requests

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/local_fix"
MODEL_TO_TEST = "gemma3:1b"  # Change this to test different models

# --- ANSI Color Codes for Terminal Output ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

# --- Test Cases ---
TEST_CASES = [
    {
        "name": "CWE-89: SQL Injection",
        "payload": {
            "cwe": "CWE-89",
            "language": "python",
            "code": "import sqlite3\n\ndef get_user(username):\n    conn = sqlite3.connect('example.db')\n    cursor = conn.cursor()\n    query = \"SELECT * FROM users WHERE username = '\" + username + \"'\"\n    cursor.execute(query)\n    user = cursor.fetchone()\n    conn.close()\n    return user"
        }
    },
    {
        "name": "CWE-78: OS Command Injection",
        "payload": {
            "cwe": "CWE-78",
            "language": "python",
            "code": "import os\n\ndef list_directory_contents(directory):\n    # This is dangerous! A user could input `'; ls -la'`\n    command = 'ls ' + directory\n    os.system(command)"
        }
    },
    {
        "name": "CWE-22: Path Traversal",
        "payload": {
            "cwe": "CWE-22",
            "language": "python",
            "code": "import os\n\ndef read_file_content(base_path, filename):\n    # Vulnerable to path traversal: filename could be '../secrets.txt'\n    file_path = os.path.join(base_path, filename)\n    with open(file_path, 'r') as f:\n        return f.read()"
        }
    }
]

def print_test_header(name):
    print(f"\n{Colors.BLUE}--- Running Test: {name} ---{Colors.ENDC}")

def print_validation_result(check_name, success, message=""):
    status = f"{Colors.GREEN}PASS{Colors.ENDC}" if success else f"{Colors.RED}FAIL{Colors.ENDC}"
    print(f"  - {check_name}: {status} {message}")

def run_tests():
    """Iterates through test cases, sends requests, and validates responses."""
    passed_tests = 0
    total_tests = len(TEST_CASES)

    for test in TEST_CASES:
        print_test_header(test["name"])
        is_test_passed = True
        
        try:
            # --- Send Request and Record Latency ---
            payload = test["payload"]
            payload["model"] = MODEL_TO_TEST
            
            start_time = time.perf_counter()
            response = requests.post(API_URL, json=payload, timeout=180)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            print(f"  - API Latency: {Colors.YELLOW}{latency_ms:.2f} ms{Colors.ENDC}")

            # --- Validations ---
            # 1. Model Loading & API Response
            if response.status_code == 200:
                print_validation_result("Model Loading & API Response", True, f"(Status: {response.status_code})")
            else:
                print_validation_result("Model Loading & API Response", False, f"(Status: {response.status_code}) - {response.text}")
                is_test_passed = False
                continue # Skip further checks if the request failed

            result = response.json()

            # 2. API Response Schema
            expected_keys = ["fixed_code", "explanation", "diff", "retrieved_context", "model_used", "token_usage", "latency_ms"]
            missing_keys = [key for key in expected_keys if key not in result]
            if not missing_keys:
                print_validation_result("API Response Schema", True)
            else:
                print_validation_result("API Response Schema", False, f"Missing keys: {missing_keys}")
                is_test_passed = False

            # 3. RAG Retrieval Logic
            retrieved_context = result.get("retrieved_context", "")
            if retrieved_context and "No specific guidance found" not in retrieved_context:
                print_validation_result("RAG Retrieval Logic", True)
            else:
                print_validation_result("RAG Retrieval Logic", False, "Context was not retrieved.")
                is_test_passed = False
            
            # Display response details
            print(f"  - {Colors.YELLOW}Explanation:{Colors.ENDC} {result.get('explanation', 'N/A')[:100]}...")
            print(f"  - {Colors.YELLOW}Fixed Code:{Colors.ENDC}\n{result.get('fixed_code', 'N/A')}")


        except requests.exceptions.RequestException as e:
            print_validation_result("API Availability", False, f"Request failed: {e}")
            is_test_passed = False

        if is_test_passed:
            passed_tests += 1

    # --- Final Summary ---
    print(f"\n{Colors.BLUE}--- Test Summary ---{Colors.ENDC}")
    color = Colors.GREEN if passed_tests == total_tests else Colors.RED
    print(f"{color}Passed {passed_tests}/{total_tests} tests.{Colors.ENDC}")

if __name__ == "__main__":
    run_tests()
