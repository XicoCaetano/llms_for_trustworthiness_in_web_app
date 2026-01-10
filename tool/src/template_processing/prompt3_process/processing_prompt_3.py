from jinja2 import Environment, FileSystemLoader
import os, json
import re, time
from src.llms_and_prompts.llm_gpt import LLMChatGPT
from src.llms_and_prompts.llm_vertex import LLMVertexAI
from src.config import OPENAI_API_KEY_PROF

class ProcessingPrompt3:
    def __init__(self, template_dir, system_role_path):
        self.env1 = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        self.system_role = system_role_path
        self.allowed_parents = {"tpcapp", "tpcw"}
        self.allowed_files = {
            "NewCustomer_Vx0.java", "NewCustomer_Vx101.java", "NewCustomer_Vx138.java",
            "NewCustomer_Vx158.java", "NewCustomer_Vx197.java", "NewCustomer_VxA.java",
            "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", 
            "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java",
            "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"
        }
        self.accepted_answers = {"yes;", "no;"}

    def template(self, template_name, env):
        if not template_name.endswith(".txt"):
            template_name += ".txt"
        template_path = os.path.join(env.loader.searchpath[0], template_name)
        with open(template_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def get_llm(self, llm_version, system_role_path):
        llm_configs = {
            1: ("gpt-3.5-turbo", LLMChatGPT),
            2: ("gpt-4o-mini", LLMChatGPT),
            3: ("gpt-4.1", LLMChatGPT),
            4: ("gpt-4.1-mini", LLMChatGPT),
            5: ("gemini-2.5-flash", LLMVertexAI)
        }
        
        model_name, llm_class = llm_configs[llm_version]
        
        if llm_version == 5:
            return llm_class(
                "./src/llms_and_prompts/tanzania-473817-h5-449bfa644462.json",
                model_name,
                system_role_path
            )
        return llm_class(OPENAI_API_KEY_PROF, model_name, system_role_path)
    
    def get_method(self, filename, method, project_path, java_processor):
        for root, dirs, files in os.walk(project_path):
            if filename in files:
                file_path = os.path.join(root, filename)
                methods = java_processor.process_java_file(file_path)
                for name, line, source in methods:
                    if name == method:
                        return source
        return None
    
    def parse_llm_score(self, response):
        if not response: 
            return None, False
        
        m = re.search(r'1\.\s*([0-9]+,[0-9]+);', response)
        if not m:
            print("[!] Score format not found — retrying...")
            return None, False
        
        score_str = m.group(1).replace(",", ".")
        return float(score_str), True

    
    def query_llm_score(self, llm, template, source, results, max_retries=20):
        for attempt in range(max_retries):
            response = llm.response_template_3(template, source, results)
            print("[DEBUG] Raw LLM Response:", repr(response))

            score, ok = self.parse_llm_score(response)
            if ok:
                return score
            
            print(f"[!] Retrying score... attempt {attempt+1}/{max_retries}")
            time.sleep(5)
        
        raise Exception("Failed to get valid trustworthiness score.")
    
    def iterate_files_and_methods(self, dir, java_processor):
        for root, dirs, files in os.walk(dir):
            parts = root[len(dir):].strip(os.sep).split(os.sep)
            
            if len(parts) >= 2 and parts[-1] == "versions" and parts[-2] in self.allowed_parents:
                for file in files:
                    if file.endswith(".java") and file in self.allowed_files:
                        file_path = os.path.join(root, file)
                        methods = java_processor.process_java_file(file_path)
                        if methods:
                            print(f"\nFicheiro: {file_path}")
                            parent_file = os.path.relpath(root, dir)
                            yield parent_file, file, methods

    def run_prompt(self, java_processor, dir, save_practices, llm_version, template_name, previous_prompt_results_path):

        if not os.path.exists(dir):
            print(f"Diretório {dir} não encontrado.")
            return
        
        # percorre ficheiros e métodos como nas outras prompts
        for parent_file, file, methods in self.iterate_files_and_methods(dir, java_processor):
            for name, line, source in methods:
                
                print("Method:", name)

                # 1. Carregar resultados das outras prompts (1,2,4,5)
                previous_answers = save_practices.load_individual_practices(previous_prompt_results_path, parent_file, file, name)

                # lista final: apenas "results"
                result_list = previous_answers

                # 2. carregar o template 3
                template = self.template(template_name, self.env1)

                # 3. inicializar o LLM correto
                llm = self.get_llm(llm_version, self.system_role)

                # 4. enviar para a LLM com retry
                score = self.query_llm_score(llm, template, source, result_list)

                # 5. guardar o resultado
                save_practices.save_prompt3_score(parent_file, file, name, score)