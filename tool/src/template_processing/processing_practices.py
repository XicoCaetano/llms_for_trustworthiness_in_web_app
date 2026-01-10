from jinja2 import Environment, FileSystemLoader
import os, json
import re, time
from src.llms_and_prompts.llm_gpt import LLMChatGPT
from src.llms_and_prompts.llm_vertex import LLMVertexAI
from src.config import OPENAI_API_KEY_PROF

class ProcessingPractices:
    def __init__(self, template_dir, template_dir_ap):
        self.env1 = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        self.env2 = Environment(loader=FileSystemLoader(template_dir_ap), autoescape=True)
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
    
    def parse_llm_response(self, response):
        if not response or response.strip() == "":
            print("[!] Empty response — retrying...")
            return [], False
        
        if not re.search(r'\d+\.', response):
            print("[!] No pattern found — retrying...")
            return [], False
        
        parts = [p.strip() for p in re.split(r'(\d+\.)', response) if p.strip()]
        
        if len(parts) < 2:
            print("[!] Not enough parts — retrying...")
            return [], False
        
        parsed = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                ans = parts[i + 1].strip().lower()
                if ans not in self.accepted_answers:
                    print(f"[!] Invalid answer: {ans}")
                    return [], False
                parsed.append(ans)
        
        return parsed, True
    
    def query_llm_with_retry(self, llm, template, source, max_retries=20):
        for attempt in range(max_retries):
            response = llm.response_template_individual_practices(template, source)
            print("[DEBUG] Raw LLM Response:", repr(response))
            
            parsed_answers, success = self.parse_llm_response(response)
            if success:
                return parsed_answers
            
            print(f"[!] Retrying... (attempt {attempt + 1}/{max_retries})")
            time.sleep(5)
        
        raise Exception(f"Failed to get valid response after {max_retries} attempts")
    
    def query_llm_with_methods(self, llm, template, source, methods, max_retries=20):
        for attempt in range(max_retries):
            response = llm.response_template_4(template, source, methods)
            print("[DEBUG] Raw LLM Response:", repr(response))
            
            parsed_answers, success = self.parse_llm_response(response)
            if success:
                return parsed_answers
            
            print(f"[!] Retrying... (attempt {attempt + 1}/{max_retries})")
            time.sleep(5)
        
        raise Exception(f"Failed to get valid response after {max_retries} attempts")
    
    def get_called_methods_source(self, file, name, dir, java_processor):
        with open("./src/joern_processing/processing_output/summary.json", 'r', encoding='utf-8') as json_file:
            joern_called_methods = json.load(json_file)
        
        file_name = os.path.splitext(file)[0]
        called_methods = []
        
        for entry in joern_called_methods:
            if entry["filename"] == file_name and entry["main_method"] == name:
                called_methods = entry.get("called_methods", [])
                break
        
        if not called_methods:
            return []
        
        list_methods = []
        for called in called_methods:
            parts = called.split(".")
            if len(parts) != 2:
                continue
            
            class_name, method_name = parts
            
            # Filtros de exclusão
            if class_name in {"PreparedStatement", "ResultSet", "Connection", "Statement", "Database"} and \
               method_name.startswith(("get", "set")):
                continue
            
            target_filename = f"{class_name}.java"
            method_info = self.get_method(target_filename, method_name, dir, java_processor)
            if method_info:
                list_methods.append(method_info)
        
        return list_methods
    
    def process_applicable_practices(self, choice_version, llm_version, practice_num, template, source):
        """Processa a aplicabilidade de uma prática."""
        system_role = f"/system_roles/system_role_{choice_version}/rules_t{choice_version}_ap"
        llm = self.get_llm(llm_version, system_role)
        answers = self.query_llm_with_retry(llm, template, source)
        return practice_num if answers and answers[0] == "yes;" else 0
    
    def process_followed_practice(self, choice_version, llm_version, template, source):
        """Processa se uma prática foi seguida."""
        system_role = f"/system_roles/system_role_{choice_version}/rules_t{choice_version}_f"
        llm = self.get_llm(llm_version, system_role)
        answers = self.query_llm_with_retry(llm, template, source)
        return 1 if answers and answers[0] == "yes;" else 0
    
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

    def run(self, choice_version, java_processor, dir, save_practices, llm_version):
        # print("\n[+] Processing individual practices template")
        
        if not os.path.exists(dir):
            print(f"Diretório {dir} não encontrado.")
            return
        
        for parent_file, file, methods in self.iterate_files_and_methods(dir, java_processor):
            for name, line, source in methods:
                print("Method: ", name)
                
                applicable_list = []
                
                # Fase 1: Verificar aplicabilidade
                for j in range(1, 17):
                    template_name = f"p{j}.txt"
                    template = self.template(template_name, self.env2)
                    result = self.process_applicable_practices(choice_version, llm_version, j, template, source)
                    applicable_list.append(result)
                
                time.sleep(5)
                print("Applicable:", applicable_list)
                
                # Fase 2: Verificar se foi seguida
                new_list = []
                for k in applicable_list:
                    if k == 0:
                        new_list.append(2)
                    else:
                        template_name = f"p{k}.txt"
                        template = self.template(template_name, self.env1)
                        result = self.process_followed_practice(choice_version, llm_version, template, source)
                        new_list.append(result)
                
                question_answers = {
                    "applicable": applicable_list,
                    "results": new_list
                }
                
                save_practices.save_individual_practices(parent_file, file, name, question_answers)

    def run_prompt4(self, java_processor, dir, save_practices, llm_version):
        # print("\n[+] Processing individual practices template (Prompt 4)")
        
        if not os.path.exists(dir):
            print(f"Diretório {dir} não encontrado.")
            return
        
        for parent_file, file, methods in self.iterate_files_and_methods(dir, java_processor):
            for name, line, source in methods:
                print("Method: ", name)
                
                applicable_list = []
                
                # Fase 1: Verificar aplicabilidade
                for j in range(1, 17):
                    template_name = f"p{j}.txt"
                    template = self.template(template_name, self.env2)
                    
                    system_role = f"/system_roles/system_role_4/applicability/a/p{j}"
                    llm = self.get_llm(llm_version, system_role)
                    answers = self.query_llm_with_retry(llm, template, source)
                    
                    applicable_list.append(j if answers[0] == "yes;" else 0)
                
                time.sleep(5)
                print("Applicable:", applicable_list)
                
                # Fase 2: Verificar se foi seguida (com contexto de métodos)
                new_list = []
                for k in applicable_list:
                    if k == 0:
                        new_list.append(2)
                    else:
                        template_name = f"p{k}.txt"
                        template = self.template(template_name, self.env1)
                        
                        called_methods = self.get_called_methods_source(file, name, dir, java_processor)
                        
                        system_role = f"/system_roles/system_role_4/followed/a/p{k}"
                        llm = self.get_llm(llm_version, system_role)
                        
                        time.sleep(5)
                        answers = self.query_llm_with_methods(llm, template, source, called_methods)
                        new_list.append(1 if answers[0] == "yes;" else 0)
                
                question_answers = {
                    "applicable": applicable_list,
                    "results": new_list
                }
                
                save_practices.save_individual_practices(parent_file, file, name, question_answers)

    def run_prompt5(self, java_processor, dir, save_practices, llm_version):

        # print("\n[+] Processing individual practices template (Prompt 5)")
        
        if not os.path.exists(dir):
            print(f"Diretório {dir} não encontrado.")
            return
        
        for parent_file, file, methods in self.iterate_files_and_methods(dir, java_processor):
            for name, line, source in methods:
                print("Method: ", name)
                
                applicable_list = []
                
                # Fase 1: Verificar aplicabilidade
                for j in range(1, 17):
                    template_name = f"p{j}.txt"
                    template = self.template(template_name, self.env2)
                    
                    system_role = f"/system_roles/system_role_5/applicability/a/p{j}"
                    llm = self.get_llm(llm_version, system_role)
                    answers = self.query_llm_with_retry(llm, template, source)
                    
                    applicable_list.append(j if answers[0] == "yes;" else 0)
                
                time.sleep(5)
                print("Applicable:", applicable_list)
                
                # Fase 2: Verificar se foi seguida
                new_list = []
                for k in applicable_list:
                    if k == 0:
                        new_list.append(2)
                    else:
                        template_name = f"p{k}.txt"
                        template = self.template(template_name, self.env1)
                        
                        system_role = f"/system_roles/system_role_5/followed/a/p{k}"
                        llm = self.get_llm(llm_version, system_role)
                        answers = self.query_llm_with_retry(llm, template, source)
                        
                        new_list.append(1 if answers[0] == "yes;" else 0)
                
                question_answers = {
                    "applicable": applicable_list,
                    "results": new_list
                }
                
                save_practices.save_individual_practices(parent_file, file, name, question_answers)