"""A simple Streamlit UI to test the local code fixing API."""

import requests
import streamlit as st

from ollama import get_available_models

# --- Page Configuration ---
st.set_page_config(
    page_title="Local Code Fixer",
    page_icon="🤖",
    layout="wide",
)

# --- Data Loading ---
@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_models():
    """Fetch the list of available Ollama models."""
    return get_available_models()

available_models = fetch_models()
default_model = "gemma3:1b" if "gemma3:1b" in available_models else (available_models[0] if available_models else None)

# --- UI Components ---
st.title("AI Code Remediation Microservice")
st.markdown("An interface to test the RAG-enhanced code fixing service.")

# API Endpoint
API_URL = "http://127.0.0.1:8000/local_fix"

with st.form("vulnerability_form"):
    st.subheader("Vulnerability Details")
    
    # Model selection
    selected_model = st.selectbox(
        "Select Model",
        options=available_models,
        index=available_models.index(default_model) if default_model else 0,
        help="Choose the model to use for generating the fix."
    )

    # Input fields
    language = st.text_input("Language", "java", help="The programming language of the code snippet.")
    cwe = st.text_input("CWE ID", "CWE-89", help="The CWE identifier for the vulnerability (e.g., CWE-89).")
    code = st.text_area(
        "Vulnerable Code Snippet",
        """String id = request.getParameter("id");
String query = "SELECT * FROM accounts WHERE username = '" + id + "'";
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(query);""",
        height=200,
        help="Paste the vulnerable code here."
    )

    # Submit button
    submitted = st.form_submit_button("✨ Generate Fix")

# --- Logic ---
if submitted:
    if not language or not cwe or not code or not selected_model:
        st.error("Please fill out all fields and select a model.")
    else:
        with st.spinner(f"Generating fix with {selected_model}..."):
            try:
                # Prepare the request payload
                payload = {
                    "language": language,
                    "cwe": cwe,
                    "code": code,
                    "model": selected_model,
                }
                
                # Send the request to the API
                response = requests.post(API_URL, json=payload, timeout=120)
                response.raise_for_status()  # Raise an exception for bad status codes
                
                result = response.json()

                # --- Display Results ---
                st.success("Fix generated successfully!")
                
                st.subheader("Fixed Code")
                st.code(result.get("fixed_code", "No fixed code provided."), language=language)

                st.subheader("Diff")
                st.code(result.get("diff", "No diff available."), language="diff")

                st.subheader("Explanation")
                st.markdown(result.get("explanation", "No explanation provided."))

                # Display metadata in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Model Used", result.get("model_used", "N/A"))
                with col2:
                    st.metric("Latency (ms)", result.get("latency_ms", 0))
                with col3:
                    input_tokens = result.get("token_usage", {}).get("input_tokens", 0)
                    output_tokens = result.get("token_usage", {}).get("output_tokens", 0)
                    st.metric("Tokens (In/Out)", f"{input_tokens} / {output_tokens}")

                st.subheader("Retrieved Context")
                st.markdown(f"```\n{result.get('retrieved_context', 'No context was retrieved.')}\n```")

            except requests.exceptions.RequestException as e:
                st.error(f"API Request Failed: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
