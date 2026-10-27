import os
import time
import re

from jinja2 import Environment, FileSystemLoader
from src.llms_and_prompts.llm_gpt import LLMChatGPT
from src.llms_and_prompts.llm_ollama import LLMOllama
from src.config import OPENAI_API_KEY_PROF

try:
    from src.llms_and_prompts.llm_vertex import LLMVertexAI
    _VERTEX_AVAILABLE = True
except ImportError:
    _VERTEX_AVAILABLE = False
    LLMVertexAI = None

from src.java_processing.juliet_processor import JulietProcessor

LLM_CONFIGS = {
    1: "gpt-3.5-turbo",
    2: "gpt-4o-mini",
    3: "gpt-4.1",
    4: "gpt-4.1-mini",
    5: "gemini-2.5-flash",
    # Ollama models (self-hosted at 10.3.1.226)
    6: "qwen2.5-coder:1.5b",
    7: "qwen2.5-coder:7b",
    8: "qwen2.5:1.5b",
    9: "qwen2.5:7b",
    10: "devstral-32k:latest",
    11: "gemma4:31b_custom",
    12: "qwen3-coder:30b",
}

OLLAMA_MODEL_IDS = set(range(6, 13))

GEMINI_SA_PATH = "./src/llms_and_prompts/tanzania-473817-h5-449bfa644462.json"

ACCEPTED = {"yes;", "no;"}


class ProcessingPracticesJuliet:
    """
    Runs the two-step LLM assessment (applicability + followed) on Juliet
    CWE89 methods, using the same prompt files as the WSVD-bench pipeline.
    """

    def __init__(self, followed_dir: str, applicability_dir: str):
        self.env_followed = Environment(
            loader=FileSystemLoader(followed_dir), autoescape=True
        )
        self.env_applicability = Environment(
            loader=FileSystemLoader(applicability_dir), autoescape=True
        )

    # ------------------------------------------------------------------
    # LLM factory — identical to ProcessingPractices.get_llm()
    # ------------------------------------------------------------------

    def get_llm(self, llm_version: int, system_role_path: str):
        model_name = LLM_CONFIGS[llm_version]
        if llm_version == 5:
            if not _VERTEX_AVAILABLE:
                raise RuntimeError("google-cloud-aiplatform not installed.")
            return LLMVertexAI(GEMINI_SA_PATH, model_name, system_role_path)
        if llm_version in OLLAMA_MODEL_IDS:
            return LLMOllama(model_name, system_role_path)
        return LLMChatGPT(OPENAI_API_KEY_PROF, model_name, system_role_path)

    # ------------------------------------------------------------------
    # Template loading
    # ------------------------------------------------------------------

    def _read_template(self, practice_num: int, env: Environment) -> str:
        name = f"p{practice_num}.txt"
        path = os.path.join(env.loader.searchpath[0], name)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # ------------------------------------------------------------------
    # LLM querying with retry
    # ------------------------------------------------------------------

    def _query(self, llm, template: str, source: str, max_retries: int = 20):
        for attempt in range(max_retries):
            response = llm.response_template_individual_practices(template, source)
            print(f"[DEBUG] Raw response: {repr(response)}")
            parsed, ok = self._parse(response)
            if ok:
                return parsed
            print(f"[!] Retry {attempt + 1}/{max_retries}")
            time.sleep(5)
        raise RuntimeError(f"No valid response after {max_retries} attempts")

    @staticmethod
    def _parse(response: str):
        if not response or not re.search(r"\d+\.", response):
            return [], False
        parts = [p.strip() for p in re.split(r"(\d+\.)", response) if p.strip()]
        if len(parts) < 2:
            return [], False
        parsed = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                ans = parts[i + 1].strip().lower()
                if ans not in ACCEPTED:
                    return [], False
                parsed.append(ans)
        return parsed, True

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self, choice_version: str, juliet_processor: JulietProcessor,
            save, llm_version: int):
        """
        Iterate over Juliet files/methods, run LLM assessment for all 16
        OWASP Input Validation practices, and persist results via `save`.

        choice_version : prompt version string, e.g. "1", "2", "4"
        save           : SaveIndividualJuliet instance
        llm_version    : int key from LLM_CONFIGS
        """
        for subfolder, filename, methods in juliet_processor.iter_files_and_methods():
            for method_name, _, source in methods:
                print(f"\n[+] {subfolder}/{filename} :: {method_name}")

                applicable_list = []

                # Phase 1 — applicability
                for j in range(1, 17):
                    system_role = (
                        f"/system_roles/system_role_{choice_version}/"
                        f"rules_t{choice_version}_ap"
                    )
                    llm = self.get_llm(llm_version, system_role)
                    template = self._read_template(j, self.env_applicability)
                    answers = self._query(llm, template, source)
                    applicable_list.append(j if answers[0] == "yes;" else 0)

                time.sleep(5)
                print("    Applicable:", applicable_list)

                # Phase 2 — followed
                new_list = []
                for k in applicable_list:
                    if k == 0:
                        new_list.append(2)  # NA
                    else:
                        system_role = (
                            f"/system_roles/system_role_{choice_version}/"
                            f"rules_t{choice_version}_f"
                        )
                        llm = self.get_llm(llm_version, system_role)
                        template = self._read_template(k, self.env_followed)
                        answers = self._query(llm, template, source)
                        new_list.append(1 if answers[0] == "yes;" else 0)

                save.save_individual_practices(
                    subfolder, filename, method_name,
                    {"applicable": applicable_list, "results": new_list}
                )

    def run_prompt4(self, choice_version: str, juliet_processor: JulietProcessor,
                    save, llm_version: int):
        """Prompt 4 (Rule-Based) variant — per-practice system roles."""
        for subfolder, filename, methods in juliet_processor.iter_files_and_methods():
            for method_name, _, source in methods:
                print(f"\n[+] {subfolder}/{filename} :: {method_name}")

                applicable_list = []

                for j in range(1, 17):
                    system_role = f"/system_roles/system_role_4/applicability/a/p{j}"
                    llm = self.get_llm(llm_version, system_role)
                    template = self._read_template(j, self.env_applicability)
                    answers = self._query(llm, template, source)
                    applicable_list.append(j if answers[0] == "yes;" else 0)

                time.sleep(5)
                print("    Applicable:", applicable_list)

                new_list = []
                for k in applicable_list:
                    if k == 0:
                        new_list.append(2)
                    else:
                        system_role = f"/system_roles/system_role_4/followed/a/p{k}"
                        llm = self.get_llm(llm_version, system_role)
                        template = self._read_template(k, self.env_followed)
                        answers = self._query(llm, template, source)
                        new_list.append(1 if answers[0] == "yes;" else 0)

                save.save_individual_practices(
                    subfolder, filename, method_name,
                    {"applicable": applicable_list, "results": new_list}
                )
