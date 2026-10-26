import argparse
from src.template_processing.individual_process.individual_practices import IndividualPractices
from src.template_processing.universal_prompts.universal_processing import UniversalProcessing
from src.template_processing.processing_practices import ProcessingPractices
from src.template_processing.prompt3_process.processing_prompt_3 import ProcessingPrompt3
from src.template_processing.saves.save_individual import SaveIndividual
from src.java_processing.java_processor import JavaProcessor
from src.config import PROJECT_PATH, OUTPUT_JSON_DIR
import traceback
import json

java_processor = JavaProcessor(PROJECT_PATH, OUTPUT_JSON_DIR)

prompt_choices = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5"
}

version_following = {
    1: "a",
    2: "b"
}

version_applicability = {
    1: "a",
    2: "b",
}

llm_paths = {
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
}

OLLAMA_LLM_IDS = set(range(6, 12))


def _path_safe(model_name: str) -> str:
    """Replace characters invalid in Windows paths (e.g. colon in 'qwen2.5:7b')."""
    return model_name.replace(":", "_")

def run(llm, prompt, max_practices=16):
    try:
        base_name = llm_paths.get(llm, "unknown")
        choice = prompt_choices.get(prompt, "1")
        version = "a"
        version_2 = "a"

        print(f"🚀 Running Individual Practices with LLM: {base_name}, Prompt: {choice}")

        # Ollama and GPT share the same prompt files; Vertex AI uses its own.
        if llm == 5:
            base = "Vertex AI"
        else:
            base = "GPT"

        followed_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/followed/{version_2}"
        applicable_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/applicability/{version}"
        results_path = f"./src/test_results/individual_practices/{_path_safe(base_name)}/prompt_{choice}_{version_2}"

        runner = ProcessingPractices(followed_path, applicable_path)

        save_individual = SaveIndividual(PROJECT_PATH, results_path)
        save_individual.run()

        if choice == "4":
            runner.run_prompt4(java_processor, PROJECT_PATH, save_individual, llm)
        elif choice == "5":
            runner.run_prompt5(java_processor, PROJECT_PATH, save_individual, llm)
        else:
            runner.run(choice, java_processor, PROJECT_PATH, save_individual, llm, max_practices=max_practices)

        print("✅ Individual practices processing completed successfully!")

    except Exception:
        error_msg = f"❌ Error in individual practices processing!\n{traceback.format_exc()}"
        print(error_msg)

def run_prompt3(llm, prompts):
    try:
        base_name = llm_paths.get(llm, "unknown")
        choice = 3
        version =  "V5"

        llm_suffix = {
            1: "3_5",             # gpt-3.5-turbo
            2: "4o",              # gpt-4o-mini
            3: "4_1",             # gpt-4.1
            4: "4_1_mini",        # gpt-4.1-mini
            5: "2_5",             # gemini-2.5-flash
            6: "qwen_coder_1b5",  # qwen2.5-coder:1.5b
            7: "qwen_coder_7b",   # qwen2.5-coder:7b
            8: "qwen_1b5",        # qwen2.5:1.5b
            9: "qwen_7b",         # qwen2.5:7b
            10: "devstral",       # devstral-32k:latest
            11: "gemma4_31b",     # gemma4:31b_custom
        }

        def get_previous_prompt_result_path(base_name, i, llm_version, llm_suffix):
            suffix = llm_suffix.get(llm_version, "unknown")
            # Exemplo final: scenario 3_4_1.json
            scenario_file = f"scenario {i}_{suffix}.json"
            return f"./src/test_results/individual_practices/{base_name}/prompt_{i}_a/{scenario_file}"



        print(f"🚀 Running Individual Practices with LLM: {base_name}, Prompt: {choice}")


        if llm == 5:
            base = "Vertex AI"
        else:
            base = "GPT"
        followed_path = f"./src/llms_and_prompts/prompts/{base}/prompt_3"

        system_role_path = f"system_roles/system_role_3/rules_t3"
        runner_prompt3 = ProcessingPrompt3(followed_path,system_role_path)

        for i in prompts:

            print(f"--- Processing Prompt 3, Scenario {i} ---")

            results_path = f"./src/test_results/prompt_3/{base_name}/{version}_prompt_{i}"

            save_individual = SaveIndividual(PROJECT_PATH, results_path)
            save_individual.run()

            result_path_previous_prompt = get_previous_prompt_result_path(base_name, i, llm, llm_suffix)
            runner_prompt3.run_prompt(java_processor, PROJECT_PATH, save_individual, llm, f"t3_{version}.txt", result_path_previous_prompt)

        print("✅ Individual practices processing completed successfully!")

    except Exception:
        error_msg = f"❌ Error in individual practices processing!\n{traceback.format_exc()}"
        print(error_msg)

def run_universal(llm):
    try:
        base_name = llm_paths.get(llm, "unknown")

        print(f"🚀 Running Individual Practices with LLM: {base_name}")

        results_path = f"./src/test_results/individual_practices/{base_name}/universal"

        best_json = "./src/llms_and_prompts/prompts/best_prompts_followed.json"

        runner = UniversalProcessing(PROJECT_PATH, best_json)

        with open(best_json, "r") as f:
            data = json.load(f)

        save_individual = SaveIndividual(PROJECT_PATH, results_path)
        save_individual.run()

        runner.run(java_processor, save_individual, llm)

        print("✅ Individual practices processing completed successfully!")

    except Exception:
        error_msg = f"❌ Error in individual practices processing!\n{traceback.format_exc()}"
        print(error_msg)




if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Run LLM Individual Practices Evaluation")
    # parser.add_argument("--llm", type=int, choices=llm_paths.keys(), required=True, help="LLM model to use")
    # parser.add_argument("--p", type=int, choices=prompt_choices.keys(), required=True, help="Prompt version")

    # args = parser.parse_args()

    # run(args.llm, args.p)

    # lista = [5]
    # prompts = [1,2,5]
    # for i in lista:
    #     print("Universal Processing...")
    #     print(f"Processing LLM: {llm_paths.get(i, "unknown")}")
    #     run_universal(i)

    # ── Ollama models (self-hosted) ───────────────────────────────────────────
    # max_practices=1 for a quick smoke-test; max_practices=16 for the full run.
    ollama_llms = [11]         # 6=qwen2.5-coder:1.5b  7=qwen2.5-coder:7b
                               # 8=qwen2.5:1.5b         9=qwen2.5:7b
                               # 10=devstral-32k:latest 11=gemma4:31b_custom
    ollama_prompts = [1, 2, 4]

    for llm in ollama_llms:
        for prompt in ollama_prompts:
            run(llm, prompt, max_practices=16)