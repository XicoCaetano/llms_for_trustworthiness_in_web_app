from jinja2 import Environment, FileSystemLoader
import os, json
from src.classification.fetch_cves import Association
import time
from src.llms_and_prompts.llm_chatgpt35_turbo import LLMChatGPT
from src.llms_and_prompts.llm_chatgpt4o_mini import LLMChatGPT4oMini
from src.llms_and_prompts.llm_chatgpt41_mini import LLMChatGPT41Mini
from src.config import OPENAI_API_KEY, MODEL_NAME, OPENAI_API_KEY_PROF

class Processor:
    def __init__(self, template_dir):
        # Configuração do ambiente Jinja2 para carregar templates do diretório especificado
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        self.association = Association()

    def _setDir(self, template_dir):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def template(self, template_name):
        """Lê o conteúdo do arquivo de template e retorna como uma string."""
        # Ensure the template name ends with .txt
        if not template_name.endswith(".txt"):
            template_name += ".txt"
        template_path = os.path.join(self.env.loader.searchpath[0], "t3/" + template_name)
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        return template_content
    
    def get_results(self, data, parent_name, filename, method):
        try:
            parent_name = parent_name.split("\\")[0].split("/")[-1]
            file_key = os.path.basename(str(filename))
            return data[parent_name]["versions"][file_key][method]["results"]
        except KeyError as e:
            raise KeyError(f"Chave em falta: {e}. Verifica parent_name/filename/method.") from e
        
    def replace_2_with_NA_and_format(self, results):
        # substitui 2 (int) ou "2" (str) por "NA"
        norm = ["NA" if (r == 2 or r == "2") else r for r in results]
        # "1. valor;\n2. valor; ..."
        formatted = "\n".join(f"{i+1}. {val};" for i, val in enumerate(norm))
        return norm, formatted
    
    def get_method (self, filename, method, project_path, java_processor):
        # Implementar a lógica para obter o método específico
        method_info = None
        for root, dirs, files in os.walk(project_path):
            if filename in files:
                file_path = os.path.join(root, filename)
                methods = java_processor.process_java_file(file_path)
                for name, line, source in methods:
                    if name == method:
                        method_info = {
                            "name": name,
                            "line": line,
                            "source": source
                        }
                        break
        return method_info

    def processing_template(self, template_name, llm_version, java_processor, dir, json_output_structure, joern_results, joern_processor, save_csv, id):
        print(f"\n[+] Processing template: {template_name}")
        template = self.template(template_name)

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
                                    if id == 1:
                                        if llm_version == 1:
                                            llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, "rules_t1")

                                        else: 
                                            llm = LLMChatGPT4oMini(OPENAI_API_KEY_PROF, "rules_t1")

                                        response = llm.response_template_1(template, source)
                                        parent_file = os.path.relpath(root, dir)
                                        save_csv.save_to_json(1, parent_file, file, name, response)
                                        template_name = template_name.split(".")[0]
                                            
                                        print(f"FileName: {file}.{name}")

                                        time.sleep(1)
                                    elif id == 2:
                                        if llm_version == 1:
                                            llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, "rules_t2_1")

                                        else: 
                                            llm = LLMChatGPT4oMini(OPENAI_API_KEY_PROF, "rules_t2_1")

                                        response = llm.response_template_2(template, source)
                                        # print(f"Response: {response.content}")
                                        parent_file = os.path.relpath(root, dir)
                                        print(response)
                                        save_csv.save_to_json(2, parent_file, file, name, response)

                                        template_name = template_name.split(".")[0]

                                        # self.association.cwes_cves_association(response.content, file, name, 2, template_name)

                                        print(f"FileName: {file}.{name}")

                                    elif id == 3:
                                        if llm_version == 1:
                                            llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, "rules_t3")

                                        else: 
                                            llm = LLMChatGPT4oMini(OPENAI_API_KEY_PROF, "rules_t3")

                                        parent_file = os.path.relpath(root, dir)

                                        # Carregar JSON
                                        with open("./src/test_results/tests_individual_practices_t2_b/template_practices_result_13.json", 'r', encoding='utf-8') as fson:
                                            data = json.load(fson)

                                        resultsT2 = self.get_results(data, parent_file, file, name)
                                        resultsT2, formatted_results = self.replace_2_with_NA_and_format(resultsT2)
                                        
                                        response = llm.response_template_3(template, source, formatted_results)
                                        save_csv.save_to_json(3, parent_file, file, name, response)

                                        print(f"FileName: {file}.{name}")

                                    elif id == 4:
                                        if llm_version == 1:
                                            llm = LLMChatGPT(OPENAI_API_KEY, MODEL_NAME, "rules_t3")

                                        else: 
                                            llm = LLMChatGPT4oMini(OPENAI_API_KEY_PROF, "rules_t3")
                                        
                                        # Carregar o JSON com todas as funções do projeto
                                        with open(joern_results, 'r', encoding='utf-8') as json_file:
                                            joern_called_methods = json.load(json_file)

                                        for i in joern_called_methods:
                                            if i["filename"] == file and i["main_method"] == name:
                                                called_methods = i["called_methods"]

                                        if called_methods == []:
                                            response = llm.response_template_4(template, source, called_methods)
                                        
                                        else: 
                                            list_methods = []
                                            for i in called_methods:
                                                parts = i.split["."]
                                                filename = parts[0]
                                                method = parts[1]

                                                if filename == "PreparedStatement" or method.startswith("set_") or method.startswith("get_"):
                                                    continue
                                                else:
                                                    method_info = self.get_method(file, method, dir, java_processor)
                                                    if method_info:
                                                        list_methods.append(method_info)

                                            response = llm.response_template_4(template, source, list_methods)

                            else:
                                print("Nenhum método encontrado.")