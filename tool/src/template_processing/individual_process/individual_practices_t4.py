from jinja2 import Environment, FileSystemLoader
import os, json
import re, time
from src.llms_and_prompts.llm_gpt import LLMChatGPT
from src.config import OPENAI_API_KEY, MODEL_NAME, OPENAI_API_KEY_4, MODEL_NAME_4
from src.joern_processing.joern_processor import JoernProcessor

class IndividualPracticesT4:
    def __init__(self, template_dir, template_dir_ap):
        # Configuração do ambiente Jinja2 para carregar templates do diretório especificado
        self.env1 = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        self.env2 = Environment(
            loader=FileSystemLoader(template_dir_ap),
            autoescape=True
        )

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

    
    def run_prompt4(self,java_processor, dir, save_practices, llm_version):
        
        print("\n[+] Processing individual practices template")        

        if not os.path.exists(dir):
            print(os.path.curdir)
            print(f"Diretório {dir} não encontrado.")
            return

        allowed_parents = {"tpcapp", "tpcw"}
        allowed_files = {"NewCustomer_Vx0.java", "NewCustomer_Vx101.java", "NewCustomer_Vx138.java", "NewCustomer_Vx158.java", "NewCustomer_Vx197.java", "NewCustomer_VxA.java", "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java", "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"}
        for root, dirs, files in os.walk(dir):
            parts = root[len(dir):].strip(os.sep).split(os.sep)

            if len(parts) >= 2 and parts[-1] == "versions" and parts[-2] in allowed_parents:
                for file in files:
                    if file.endswith(".java"):
                        if file in allowed_files:
                            file_path = os.path.join(root, file)
                            methods = java_processor.process_java_file(file_path)
                            if methods:
                                print(f"\nFicheiro: {file_path}")
                                for name, line, source in methods:

                                    print("Method: ", name)

                                    new_list = []
                                    applicable_list = []

                                    question_answers = {}

                                    accepted_answers = {"yes;", "no;"}

                                    # Process the response of applicable practices

                                    for j in range(1, 17): # 16 praticas
                                        template_name = f"p{j}.txt"

                                        practice = j

                                        while True:
                                            
                                            # if llm_version == 1:
                                                # llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, f"rules_t{llm_version}_ap")

                                            # else: 
                                            #     llm = LLMChatGPT(OPENAI_API_KEY_4, MODEL_NAME_4, f"rules_t{llm_version}_ap")

                                            # llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, f"rules_t2_ap")
                                            if llm_version == 1:
                                                llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, f"/system_roles/t4_system_role/t4_ap/p{j}")

                                            # else: 
                                            #     llm = LLMChatGPT4oMini(OPENAI_API_KEY_4, MODEL_NAME_4, f"/system_roles/t4_system_role/t4_ap/p{j}")

                                            template = self.template(template_name, self.env2)
                                            
                                            response = llm.response_template_individual_practices(template, source)
                                            parent_file = os.path.relpath(root, dir)

                                            print("[DEBUG] Raw LLM Response:", repr(response))

                                            if re.search(r'\d+\.', response):
                                                response_parts = re.split(r'(\d+\.)', response)
                                                response_parts = [part.strip() for part in response_parts if part.strip()]

                                                if len(response_parts) >= 2:
                                                    valid_format = True

                                                    for i in range(0, len(response_parts), 2):
                                                        if i + 1 < len(response_parts):
                                                            answer = response_parts[i + 1].strip().lower()

                                                            if answer not in accepted_answers:
                                                                print(f"[!] Invalid answer format: '{answer}' — retrying...")
                                                                valid_format = False
                                                                break
                                                            else:
                                                                applicable_list.append(practice if answer == "yes;" else 0)
                                                        else:
                                                            print(f"[!] Skipping unmatched part: '{response_parts[i]}'")
                                                            valid_format = False

                                                    if valid_format:
                                                        break  # resposta válida, sai do loop
                                                else:
                                                    print("[!] Not enough parts in response — retrying...")
                                            else:
                                                print("[!] No question pattern (\\d+.) detected — retrying...")

                                            time.sleep(5)  # Wait before retrying

                                        question_answers["applicable"] = applicable_list

                                    time.sleep(5)  # Wait before retrying
                                    print(question_answers["applicable"])

                                    for k in question_answers["applicable"]:
                                        if k == 0:
                                            new_list.append(2)
                                        else:
                                            template_name = f"p{k}.txt"

                                            # Carregar o JSON com todas as funções do projeto
                                            with open("./src/joern_processing/output_joern_process/summary.json", 'r', encoding='utf-8') as json_file:
                                                joern_called_methods = json.load(json_file)

                                            file_file = file.split(".")[0]
                                            
                                            called_methods = []  # evita UnboundLocalError se não houver match

                                            file_file = os.path.splitext(file)[0]  # mais robusto que split(".")
                                            for entry in joern_called_methods:
                                                if entry["filename"] == file_file and entry["main_method"] == name:
                                                    called_methods = entry.get("called_methods", [])
                                                    break

                                            if not called_methods:
                                                continue

                                            list_methods = []
                                            for called in called_methods:
                                                parts = called.split(".")
                                                if len(parts) != 2:
                                                    continue
                                                class_name, method_name = parts

                                                # 1) filtros de exclusão
                                                if class_name in {"PreparedStatement", "ResultSet", "Connection", "Statement", "Database"}:
                                                    continue
                                                if method_name.startswith(("get", "set")):
                                                    continue

                                                # 2) procurar no ficheiro correto
                                                target_filename = f"{class_name}.java"
                                                method_info = self.get_method(target_filename, method_name, dir, java_processor)
                                                if method_info:
                                                    list_methods.append(method_info)

                                            # # Se quiseres também manter a lista “bonita” dos nomes:
                                            # called = [m for m in (called_methods or []) if isinstance(m, str)]
                                            # other_content = "\n".join(f"- {m}" for m in called) if called else ""


                                            # time.sleep(5)  # Wait before retrying

                                            while True:
                                                if llm_version == 1:
                                                    llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, f"/system_roles/t4_system_role/t4_p/p{j}")

                                                # else: 
                                                #     llm = LLMChatGPT4oMini(OPENAI_API_KEY_4, MODEL_NAME_4, f"/system_roles/t4_system_role/t4_p/p{j}")

                                                template = self.template(template_name, self.env1)

                                                parent_file = os.path.relpath(root, dir)

                                                if not called_methods:
                                                    response = llm.response_template_4(template, source, called_methods)
                                                else:
                                                    response = llm.response_template_4(template, source, list_methods)

                                                print("[DEBUG] Raw LLM Response:", repr(response))

                                                if re.search(r'\d+\.', response):
                                                    response_parts = re.split(r'(\d+\.)', response)
                                                    response_parts = [part.strip() for part in response_parts if part.strip()]

                                                    if len(response_parts) >= 2:
                                                        valid_format = True

                                                        for i in range(0, len(response_parts), 2):
                                                            if i + 1 < len(response_parts):
                                                                answer = response_parts[i + 1].strip().lower()

                                                                if answer not in accepted_answers:
                                                                    print(f"[!] Invalid answer format: '{answer}' — retrying...")
                                                                    valid_format = False
                                                                    break
                                                                else:
                                                                    new_list.append(1 if answer == "yes;" else 0)
                                                            else:
                                                                print(f"[!] Skipping unmatched part: '{response_parts[i]}'")
                                                                valid_format = False

                                                        if valid_format:
                                                            break  # resposta válida, sai do loop
                                                    else:
                                                        print("[!] Not enough parts in response — retrying...")
                                                else:
                                                    print("[!] No question pattern (\\d+.) detected — retrying...")

                                                time.sleep(5)  # Wait before retrying

                                            question_answers["results"] = new_list

                                            save_practices.save_individual_practices(parent_file, file, name, question_answers)