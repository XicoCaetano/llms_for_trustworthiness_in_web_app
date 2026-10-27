"""
Entry point for running the OWASP Input Validation assessment on the
Juliet Java 1.3 CWE-89 (SQL Injection) dataset.

Usage (from the tool/ directory):
    python main_juliet.py

Results are saved to:
    src/test_results/juliet/<model_name>/prompt_<N>_a/
"""

import traceback
from src.java_processing.juliet_processor import JulietProcessor
from src.template_processing.processing_practices_juliet import ProcessingPracticesJuliet
from src.template_processing.saves.save_individual_juliet import SaveIndividualJuliet

# ── Dataset path ──────────────────────────────────────────────────────────────
JULIET_ROOT = "./Dataset/Java/src/testcases/CWE89_SQL_Injection"

# ── Model registry (same as main2.py) ────────────────────────────────────────
LLM_PATHS = {
    1: "gpt-3.5-turbo",
    2: "gpt-4o-mini",
    3: "gpt-4.1",
    4: "gpt-4.1-mini",
    5: "gemini-2.5-flash",
    # Ollama models 
    6: "qwen2.5-coder:1.5b",
    7: "qwen2.5-coder:7b",
    8: "qwen2.5:1.5b",
    9: "qwen2.5:7b",
    10: "devstral-32k:latest",
    11: "gemma4:31b_custom",
    12: "qwen3-coder:30b",
}

# ── Prompt base folders (GPT) ─────────────────────────────────────────────────
GPT_PROMPT_BASE = "./src/llms_and_prompts/prompts/GPT/individual_practices_prompts"
VERTEX_PROMPT_BASE = "./src/llms_and_prompts/prompts/Vertex AI/individual_practices_prompts"


def _path_safe(model_name: str) -> str:
    """Replace characters invalid in Windows paths (e.g. colon in 'qwen2.5:7b')."""
    return model_name.replace(":", "_")


def _prompt_dirs(llm_version: int, prompt_choice: str):
    """Return (followed_dir, applicability_dir) for the given LLM and prompt."""
    base = GPT_PROMPT_BASE if llm_version != 5 else VERTEX_PROMPT_BASE
    followed = f"{base}/prompt_{prompt_choice}/followed/a"
    applicability = f"{base}/prompt_{prompt_choice}/applicability/a"
    return followed, applicability


def run(llm_version: int, prompt_choice: str):
    try:
        model_name = LLM_PATHS[llm_version]
        print(f"\n{'='*60}")
        print(f"  LLM: {model_name}   Prompt: {prompt_choice}")
        print(f"{'='*60}")

        followed_dir, applicability_dir = _prompt_dirs(llm_version, prompt_choice)

        runner = ProcessingPracticesJuliet(followed_dir, applicability_dir)

        results_path = (
            f"./src/test_results/juliet/{_path_safe(model_name)}/prompt_{prompt_choice}_a"
        )
        juliet_processor = JulietProcessor(JULIET_ROOT)
        save = SaveIndividualJuliet(JULIET_ROOT, results_path)
        save.run()

        if prompt_choice == "4":
            runner.run_prompt4(prompt_choice, juliet_processor, save, llm_version)
        else:
            runner.run(prompt_choice, juliet_processor, save, llm_version)

        print(f"\n[OK] Finished: {model_name} / prompt {prompt_choice}")

    except Exception:
        print(f"[ERROR] {traceback.format_exc()}")


if __name__ == "__main__":
    # Run GPT models with Prompts 1, 2 and 4 — same scope as the WSVD paper
    llms = [1, 2, 3, 4]       # skip 5 (Gemini) unless you have the SA file
    prompts = ["1", "2", "4"]

    for llm in llms:
        for prompt in prompts:
            run(llm, prompt)

    # ── Ollama models (self-hosted) ───────────────────────────────────────────
    # Uncomment and adjust to run specific Ollama models:
    #
    # ollama_llms = [6]          # 6=qwen2.5-coder:1.5b  7=qwen2.5-coder:7b
    #                            # 8=qwen2.5:1.5b         9=qwen2.5:7b
    #                            # 10=devstral-32k:latest 11=gemma4:31b_custom
    #                            # 12=qwen3-coder:30b
    # ollama_prompts = ["1", "2", "4"]
    #
    # for llm in ollama_llms:
    #     for prompt in ollama_prompts:
    #         run(llm, prompt)
