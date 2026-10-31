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
    # Ollama (self-hosted) — folder names, ':' replaced by '_' (model names are in processing_practices.py)
    6: "qwen2.5-coder_1.5b",
    7: "qwen2.5-coder_7b",
    8: "qwen2.5_1.5b",
    9: "qwen2.5_7b",
    10: "devstral-32k_latest",
    11: "gemma4_31b_custom",
    12: "qwen3-coder_30b",
    13: "qwen3.8_27b",
    14: "granite4.2_30b",
    15: "gemma4_31b",
    16: "llama3.1_70b",
    17: "gemma3_27b",
    18: "gpt-oss_120b",
    19: "gpt-oss_120b_custom",
    20: "gemma3_12b-it-fp16",
    21: "qwen2.5_14b-instruct-fp16",
    22: "llama3.1_8b",
    23: "devstral_latest",
    24: "gemma3_12b",
    25: "codellama_7b",
    26: "qwen3.6_35b",
    27: "qwen2.5_32b",
    28: "qwen2.5-coder_32b",
    29: "qwen2.5_14b",
    30: "qwen2.5-coder_14b",
    31: "deepseek-coder-v2_latest",
    32: "codestral_22b",
    33: "deepseek-coder_33b",
    34: "deepseek-coder_6.7b",
    35: "deepseek-coder_1.3b",
    36: "qwen3.6_35b_custom",
    37: "gpt-oss_20b"
}

# Ollama models use the same prompts as the GPT models
OLLAMA_LLM_IDS = set(range(6, 38))

def run(llm, prompt):
    try:
        base_name = llm_paths.get(llm, "unknown")
        choice = prompt_choices.get(prompt, "1")
        version =  "a"
        version_2 = "a"

        base_split = base_name.split("-")

        print(f"🚀 Running Individual Practices with LLM: {base_name}, Prompt: {choice}")


        if base_split[0] == "gpt" or llm in OLLAMA_LLM_IDS:
            base = "GPT"

            followed_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/followed/{version_2}"
            applicable_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/applicability/{version}"
            results_path = f"./src/test_results/individual_practices/{base_name}/prompt_{choice}_{version_2}"

        else:
            base = "Vertex AI"

            followed_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/followed/{version_2}"
            applicable_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{choice}/applicability/{version}"
            results_path = f"./src/test_results/individual_practices/{base_name}/prompt_{choice}_{version_2}"

        runner = ProcessingPractices(followed_path, applicable_path)

        save_individual = SaveIndividual(PROJECT_PATH, results_path)
        save_individual.run()

        if choice == "4":
            runner.run_prompt4(java_processor, PROJECT_PATH, save_individual, llm)
        elif choice == "5":
            runner.run_prompt5(java_processor, PROJECT_PATH, save_individual, llm)
        else:
            runner.run(choice, java_processor, PROJECT_PATH, save_individual, llm)

        print("✅ Individual practices processing completed successfully!")

    except Exception:
        error_msg = f"❌ Error in individual practices processing!\n{traceback.format_exc()}"
        print(error_msg)

def run_prompt3(llm, prompts):
    try:
        base_name = llm_paths.get(llm, "unknown")
        choice = 3
        version =  "V5"

        base_split = base_name.split("-")

        llm_suffix = {
            1: "3_5",        # gpt-3.5-turbo
            2: "4o",         # gpt-4o-mini
            3: "4_1",        # gpt-4.1
            4: "4_1_mini",   # gpt-4.1-mini
            5: "2_5",        # gemini-2.5-flash
            6: "qwen_coder_1b5",   # qwen2.5-coder:1.5b
            7: "qwen_coder_7b",    # qwen2.5-coder:7b
            8: "qwen_1b5",         # qwen2.5:1.5b
            9: "qwen_7b",          # qwen2.5:7b
            10: "devstral",        # devstral-32k:latest
            11: "gemma4_31b",      # gemma4:31b_custom
            12: "qwen3_coder_30b", # qwen3-coder:30b
            13: "qwen3_8_27b",               # qwen3.8:27b
            14: "granite4_2_30b",            # granite4.2:30b
            15: "gemma4_31b_base",           # gemma4:31b
            16: "llama3_1_70b",              # llama3.1:70b
            17: "gemma3_27b",                # gemma3:27b
            18: "gpt_oss_120b",              # gpt-oss:120b
            19: "gpt_oss_120b_custom",       # gpt-oss:120b_custom
            20: "gemma3_12b_it_fp16",        # gemma3:12b-it-fp16
            21: "qwen2_5_14b_instruct_fp16", # qwen2.5:14b-instruct-fp16
            22: "llama3_1_8b",               # llama3.1:8b
            23: "devstral_base",             # devstral:latest
            24: "gemma3_12b",                # gemma3:12b
            25: "codellama_7b",              # codellama:7b
            26: "qwen3_6_35b",               # qwen3.6:35b
            27: "qwen_32b",                  # qwen2.5:32b
            28: "qwen_coder_32b",            # qwen2.5-coder:32b
            29: "qwen_14b",                  # qwen2.5:14b
            30: "qwen_coder_14b",            # qwen2.5-coder:14b
            31: "deepseek_coder_v2",         # deepseek-coder-v2:latest
            32: "codestral_22b",             # codestral:22b
            33: "deepseek_coder_33b",        # deepseek-coder:33b
            34: "deepseek_coder_6b7",        # deepseek-coder:6.7b
            35: "deepseek_coder_1b3",        # deepseek-coder:1.3b
            36: "qwen3_6_35b_custom",        # qwen3.6:35b_custom
            37: "gpt_oss_20b"                # gpt-oss:20b
        }

        def get_previous_prompt_result_path(base_name, i, llm_version, llm_suffix):
            suffix = llm_suffix.get(llm_version, "unknown")
            # Exemplo final: scenario 3_4_1.json
            scenario_file = f"scenario {i}_{suffix}.json"
            return f"./src/test_results/individual_practices/{base_name}/prompt_{i}_a/{scenario_file}"



        print(f"🚀 Running Individual Practices with LLM: {base_name}, Prompt: {choice}")


        if base_split[0] == "gpt" or llm in OLLAMA_LLM_IDS:
            base = "GPT"
            followed_path = f"./src/llms_and_prompts/prompts/{base}/prompt_3"
        
        else:
            base = "Vertex AI"
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

    # llms = [1, 2, 3, 4, 5]
    llms = [15, 13]     # 15=gemma4:31b  13=qwen3.8:27b  (Ollama ids: see llm_paths, 6–37)
    prompts = [1, 2, 4, 5]

    # Optional override from the command line, e.g.: python main2.py --llms 15 --prompts 1 2 4 5
    parser = argparse.ArgumentParser(description="Run LLM Individual Practices Evaluation")
    parser.add_argument("--llms", type=int, nargs="+", choices=llm_paths.keys(), default=llms, help="LLM ids (see llm_paths)")
    parser.add_argument("--prompts", type=int, nargs="+", choices=prompt_choices.keys(), default=prompts, help="Prompt numbers")
    args = parser.parse_args()
    llms, prompts = args.llms, args.prompts

    for llm in llms:
        for prompt in prompts:
            run(llm, prompt)