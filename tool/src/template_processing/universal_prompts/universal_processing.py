from jinja2 import Environment, FileSystemLoader
import os, json
import re, time
from src.llms_and_prompts.llm_gpt import LLMChatGPT
from src.llms_and_prompts.llm_vertex import LLMVertexAI
from src.config import OPENAI_API_KEY_PROF
from src.joern_processing.joern_processor import JoernProcessor

class UniversalProcessing:
    def __init__(self, dir, best_json):
        self.dir = dir
        self.env1 = ""
        self.env2 = ""
        self.llm_paths = {
            1: "gpt-3.5-turbo",
            2: "gpt-4o-mini",
            3: "gpt-4.1",
            4: "gpt-4.1-mini",
            5: "gemini-2.5-flash"
        }
        self.allowed_parents = {"tpcapp", "tpcw"}
        self.allowed_files = {"NewCustomer_Vx0.java", "NewCustomer_Vx101.java", "NewCustomer_Vx138.java", "NewCustomer_Vx158.java", "NewCustomer_Vx197.java", "NewCustomer_VxA.java", "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java", "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"}
        # self.allowed_files = {"NewCustomer_VxA.java", "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java", "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"}


        with open(best_json, "r") as f:
            self.data = json.load(f)

        self.joern_summary = "./src/joern_processing/processing_output/summary.json"

        with open (self.joern_summary, "r", encoding='utf-8') as json_file:
            self.joern = json.load(json_file)

        self.accepted_answers = {"yes;", "no;"}


    def template(self, template_name, env):
        """Lê o conteúdo do arquivo de template e retorna como uma string."""
        # Ensure the template name ends with .txt
        if not template_name.endswith(".txt"):
            template_name += ".txt"
        template_path = os.path.join(env.loader.searchpath[0], template_name)
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        return template_content
    
    def get_method(self, filename, method, project_path, java_processor):
        # filename é algo como "NewCustomer_Vx0.java"
        for root, dirs, files in os.walk(project_path):
            if filename in files:
                file_path = os.path.join(root, filename)
                methods = java_processor.process_java_file(file_path)
                for name, line, source in methods:
                    if name == method:
                        return source
        return None


    def create_llm_1_2(self, version, valor, tipo):
        match version:
            case 1:
                MODEL_NAME = "gpt-3.5-turbo"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
            case 2:
                MODEL_NAME = "gpt-4o-mini"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME,f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
            case 3:
                MODEL_NAME = "gpt-4.1"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME,f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
            case 4:
                MODEL_NAME = "gpt-4.1-mini"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME,f"/system_roles/system_role_{valor}/rules_t{valor}_{tipo}")
            case 5:
                MODEL_NAME = "gemini-2.5-flash"


    def create_llm_4_5(self, version, valor, tipo, p):
        match version:
            case 1:
                MODEL_NAME = "gpt-3.5-turbo"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
            case 2:
                MODEL_NAME = "gpt-4o-mini"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
            case 3:
                MODEL_NAME = "gpt-4.1"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
            case 4:
                MODEL_NAME = "gpt-4.1-mini"
                return LLMChatGPT(OPENAI_API_KEY_PROF, MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")
            case 5:
                MODEL_NAME = "gemini-2.5-flash"
                return LLMVertexAI("./src/llms_and_prompts/tanzania-473817-h5-449bfa644462.json", MODEL_NAME, f"/system_roles/system_role_{valor}/{tipo}/a/p{p}")


    def parse_llm_response(self, response):
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


    def run(
        self, java_processor, save_practices,
        llm_version):

        if not os.path.exists(self.dir):
            print(f"Diretório {self.dir} não encontrado.")
            return

        # === Iterar pelos ficheiros Java ===
        for root, dirs, files in os.walk(self.dir):
            parts = root[len(self.dir):].strip(os.sep).split(os.sep)

            if len(parts) >= 2 and parts[-1] == "versions" and parts[-2] in self.allowed_parents:
                for file in files:
                    if not (file.endswith(".java") and file in self.allowed_files):
                        continue

                    file_path = os.path.join(root, file)
                    methods = java_processor.process_java_file(file_path)
                    if not methods:
                        continue

                    print(f"\nFicheiro: {file_path}")

                    self.run_applicability(root, file, methods, llm_version, save_practices, java_processor)
 

    def run_applicability(self, root, file, methods, llm_version, save_practices, java_processor):

        for name, line, source in methods:
            print("Method:", name)
            question_answers = {}
            applicable_list = []

            for i in range(1,17):
                llm_name = self.llm_paths.get(llm_version, "gpt-3.5-turbo")
                prompt = self.data[llm_name][str(i)]

                base_split = llm_name.split("-")

                if base_split[0] == "gpt":
                    base = "GPT"

                    followed_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{prompt}/followed/a"
                    applicable_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{prompt}/applicability/a"

                else:
                    base = "Vertex AI"
                    
                    followed_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{prompt}/followed/a"
                    applicable_path = f"./src/llms_and_prompts/prompts/{base}/individual_practices_prompts/prompt_{prompt}/applicability/a"

                self.env1 = Environment(loader=FileSystemLoader(followed_path), autoescape=True)
                self.env2 = Environment(loader=FileSystemLoader(applicable_path), autoescape=True)

                if prompt == 1 or prompt == 2:
                    llm = self.create_llm_1_2(llm_version, prompt, "ap")
                else:
                    llm = self.create_llm_4_5(llm_version, prompt, "applicability", i)
                template_name = f"p{i}.txt"
                template = self.template(template_name, self.env2)

                while True:
                    response = llm.response_template_individual_practices(template, source)
                    print("[DEBUG] Raw LLM Response:", repr(response))
                    parsed, valid = self.parse_llm_response(response)
                    if valid and parsed:
                        ans = parsed[0]
                        applicable_list.append(i if ans == "yes;" else 0)
                        break
                    time.sleep(5)

                question_answers["applicable"] = applicable_list


            print(f"[OK] Aplicable for {name}: {applicable_list}")

            time.sleep(5)  # Wait before retrying

            self.run_followed(root, source, name, file, llm_version, save_practices, question_answers, java_processor)


    def run_followed(self, root, source, name, file, llm_version, save_practices, question_answers, java_processor):

        new_list = []

        for k in question_answers["applicable"]:
            if k == 0:
                new_list.append(2)
                continue

            template_name = f"p{k}.txt"
            llm_name = self.llm_paths.get(llm_version, "gpt-3.5-turbo")
            valor = self.data[llm_name][str(k)]

            if valor == 1 or valor == 2:
                llm = self.create_llm_1_2(llm_version, valor, "f")
            elif valor == 5:
                llm = self.create_llm_4_5(llm_version, valor, "followed", k)
            elif valor == 4:
                called_methods, list_methods = self.run_called_prompt(java_processor, name, file)
                llm = self.create_llm_4_5(llm_version, valor, "followed", k)
            
            template = self.template(template_name, self.env1)

            while True:
                if valor == 4:
                    if not called_methods:
                        response = llm.response_template_4(template, source, called_methods)
                    else:
                        response = llm.response_template_4(template, source, list_methods)

                    print("[DEBUG] Raw LLM Response:", repr(response))
                    parsed, valid = self.parse_llm_response(response)
                    if valid and parsed:
                        ans = parsed[0]
                        new_list.append(1 if ans == "yes;" else 0)
                        break
                    time.sleep(5)
                else:
                    response = llm.response_template_individual_practices(template, source)
                    print("[DEBUG] Raw LLM Response:", repr(response))
                    parsed, valid = self.parse_llm_response(response)
                    if valid and parsed:
                        ans = parsed[0]
                        new_list.append(1 if ans == "yes;" else 0)
                        break
                    time.sleep(5)
                    
            question_answers["results"] = new_list

            parent_file = os.path.relpath(root, self.dir)
            save_practices.save_individual_practices(parent_file, file, name, question_answers)


    def run_called_prompt(self, java_processor, name, file):

        file_file = file.split(".")[0]
        
        called_methods = []  # evita UnboundLocalError se não houver match

        file_file = os.path.splitext(file)[0]  # mais robusto que split(".")
        for entry in self.joern:
            if entry["filename"] == file_file and entry["main_method"] == name:
                called_methods = entry.get("called_methods", [])
                break
        
        list_methods = []
        if called_methods:
            for called in called_methods:
                parts = called.split(".")
                if len(parts) != 2:
                    continue
                class_name, method_name = parts

                # 1) filtros de exclusão
                if class_name in {"PreparedStatement", "ResultSet", "Connection", "Statement", "Database"} and method_name.startswith(("get", "set")):
                    continue

                # 2) procurar no ficheiro correto
                target_filename = f"{class_name}.java"
                method_info = self.get_method(target_filename, method_name, self.dir, java_processor)
                if method_info:
                    list_methods.append(method_info)

            return called_methods, list_methods
        else: 
            return called_methods, list_methods