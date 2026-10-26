"""
Quick smoke-test for the Ollama integration.

Run from the tool/ directory:
    python test_ollama.py
"""

import requests
from src.config import OLLAMA_ENDPOINT, OLLAMA_USERNAME, OLLAMA_PASSWORD
from src.llms_and_prompts.llm_ollama import LLMOllama

MODEL = "qwen2.5-coder:1.5b"


def test_connection():
    """Check that the Ollama server is reachable and the model is loaded."""
    ps_url = OLLAMA_ENDPOINT.rsplit("/api/", 1)[0] + "/api/ps"
    auth = (
        requests.auth.HTTPBasicAuth(OLLAMA_USERNAME, OLLAMA_PASSWORD)
        if OLLAMA_USERNAME
        else None
    )
    r = requests.get(ps_url, auth=auth, timeout=10)
    r.raise_for_status()
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"[connection] OK — loaded models: {models or '(none)'}")
    return models


def test_raw_chat():
    """Send a minimal chat request directly via requests (no wrapper)."""
    auth = (
        requests.auth.HTTPBasicAuth(OLLAMA_USERNAME, OLLAMA_PASSWORD)
        if OLLAMA_USERNAME
        else None
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly: hello"}],
        "stream": False,
        "options": {"temperature": 0.0},
    }
    r = requests.post(OLLAMA_ENDPOINT, json=payload, auth=auth, timeout=60)
    r.raise_for_status()
    content = r.json()["message"]["content"]
    print(f"[raw chat]   OK — response: {repr(content)}")


def test_wrapper():
    """Test LLMOllama with the actual system role and prompt used in the pipeline."""
    system_role = "system_roles/system_role_1/rules_t1_ap"
    llm = LLMOllama(MODEL, system_role)

    # Read one real practice template (applicability, practice 1)
    with open(
        "./src/llms_and_prompts/prompts/GPT/individual_practices_prompts"
        "/prompt_1/applicability/a/p1.txt",
        encoding="utf-8",
    ) as f:
        template = f.read()

    sample_code = """
public void doPost(HttpServletRequest request, HttpServletResponse response) {
    String user = request.getParameter("username");
    String query = "SELECT * FROM users WHERE name = '" + user + "'";
    // execute query...
}
"""
    response = llm.response_template_individual_practices(template, sample_code)
    print(f"[wrapper]    OK — response: {repr(response)}")


if __name__ == "__main__":
    print(f"Testing model: {MODEL}\n")
    try:
        test_connection()
    except Exception as e:
        print(f"[connection] FAIL — {e}")

    try:
        test_raw_chat()
    except Exception as e:
        print(f"[raw chat]   FAIL — {e}")

    try:
        test_wrapper()
    except Exception as e:
        print(f"[wrapper]    FAIL — {e}")
