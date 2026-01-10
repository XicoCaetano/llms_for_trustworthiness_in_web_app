import os
import json
from datetime import datetime
import javalang
import time
import re

class SaveIndividual:
    def __init__(self, root_folder, workdir):
        self.workdir = workdir
        os.makedirs(self.workdir, exist_ok=True)
        self.root_folder = root_folder
        self.structure = {}

    def run(self):
        # Build the nested structure
        self.build_nested_structure()

        base_name = f"template_practices_result_"
        existing_files = [
            fname for fname in os.listdir(self.workdir)
            if fname.startswith(base_name) and fname.endswith(".json")
        ]

        # Extrai o número de cada ficheiro existente
        indices = []
        for fname in existing_files:
            try:
                # Exemplo: template_practices_result_V1_3.json
                parts = fname.replace(".json", "").split("_")
                last_part = parts[-1]  # deve ser o número (ex: 3)
                index = int(last_part)
                indices.append(index)
            except (IndexError, ValueError):
                continue

        i = max(indices, default=0) + 1  # Se não houver, começa em 1

        self.filepaths = {
            f"template_practices": os.path.join(self.workdir, f"template_practices_result_{i}.json"),
        }

        for path in self.filepaths.values():
            with open(path, mode='w', encoding='utf-8') as file:
                json.dump(self.structure, file, indent=4)


    def build_nested_structure(self):
        """
        Build the nested directory structure from the root folder.
        Each directory can contain .java files and subfolders.
        """
        allowed_parents = {"tpcapp", "tpcc", "tpcw"}
        allowed_files = {"NewCustomer_Vx0.java", "NewCustomer_Vx101.java", "NewCustomer_Vx138.java", "NewCustomer_Vx158.java", "NewCustomer_Vx197.java", "NewCustomer_VxA.java", "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java", "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"}
        # allowed_files = {"NewCustomer_VxA.java", "CreateNewCustomer_Vx0.java", "CreateNewCustomer_Vx078.java", "CreateNewCustomer_Vx103.java", "CreateNewCustomer_Vx113.java", "CreateNewCustomer_Vx132.java", "CreateNewCustomer_VxA.java"}
        for subdir, _, files in os.walk(self.root_folder):
            parts = subdir[len(self.root_folder):].strip(os.sep).split(os.sep)
            
            # Exemplo: parts = ['tcpapp', 'version']
            if len(parts) >= 2 and parts[-1] == "versions" and parts[-2] in allowed_parents:
                system = parts[-2]

                if system not in self.structure:
                    self.structure[system] = {"versions": {}}

                for file in files:
                    if file in allowed_files and file.endswith(".java"):
                        file_path = os.path.join(subdir, file)
                        methods = self.process_java_file(file_path)
                        self.structure[system]["versions"][file] = {method: "" for method in methods}
    
    def process_java_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as java_file:
            code = java_file.read()

        tree = javalang.parse.parse(code)
        methods = []

        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                methods.append(node.name)

        return methods

    def save_individual_practices(self, parent_name, file_name, method_name, question_answers):
        """Save the response to the JSON file for the specific method within the .java file."""
        template_key = f"template_practices"
        
        if template_key not in self.filepaths:
            raise ValueError("Invalid template number")
        
        filepath = self.filepaths[template_key]
        
        # Load the existing JSON
        with open(filepath, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            
        # Access the specific file in the structure
        current = data

        parts = parent_name.split(os.sep)
        for part in parts:
            if part not in current:
                current[part] = {}  # Create the directory if it doesn't exist
            current = current[part]
        
        # Navigate to the specific file
        parts = file_name.split(os.sep)
        for part in parts:
            if part in current:
                current = current[part]
            else:
                raise KeyError(f"File {file_name} not found in the structure")

        if method_name in current:
            current[method_name] = question_answers
        else:
            raise KeyError(f"Method {method_name} not found in {file_name}")
        
            
        # Write back to the JSON file
        time.sleep(1)
        with open(filepath, mode='w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    def structure_score_1(self, prompt):
        data = {
            "tpcw": {
                "versions": {
                    "CreateNewCustomer_VxA.java": {
                        "enterAddress": {}
                    }
                }
            }
        }

        # 2️⃣ Guardar no ficheiro
        with open(os.path.join(self.workdir, f"score_1_prompt_{prompt}.json"), "w") as f:
            json.dump(data, f, indent=4)

    def save_score_1 (self, parent_name, file_name, method_name, question_answers, prompt):
        """Save the response to the JSON file for the specific method within the .java file."""
        
        filepath = os.path.join(self.workdir, f"score_1_prompt_{prompt}.json")
        
        # Load the existing JSON
        with open(filepath, mode='r', encoding='utf-8') as file:
            data = json.load(file)

        # 3️⃣ Atualizar a lista (por exemplo, substituir ou adicionar)
        data[parent_name]["versions"][file_name][method_name] = question_answers

        # 4️⃣ Guardar de volta no ficheiro
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)

    
    def load_individual_practices(self, json_path, parent_name, file_name, method_name):
        """
        Carrega o array 'results' e troca 0 -> 'NA'.
        Garante que parent_name é sempre só 'tpcapp', 'tpcw' ou 'tpcc'.
        """

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON não encontrado: {json_path}")

        # 🧹 1️⃣ Limpar parent_name caso venha como: "tpcapp/version", "tpcapp\\versions"
        parent_clean = parent_name.replace("/", "\\").split("\\")[0]

        # 2️⃣ Carregar JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 3️⃣ Validar parent
        if parent_clean not in data:
            raise KeyError(
                f"Sistema '{parent_clean}' não encontrado no JSON {json_path}. "
                f"Parent recebido: '{parent_name}'"
            )

        # 4️⃣ Aceder ao método
        try:
            method_block = data[parent_clean]["versions"][file_name][method_name]
        except KeyError:
            raise KeyError(
                f"Não foi possível encontrar {parent_clean} → {file_name} → {method_name} em {json_path}"
            )

        # 5️⃣ Validar 'results'
        if "results" not in method_block:
            raise KeyError(f"'results' não existe no método {method_name} em {json_path}")

        # 6️⃣ Converter valores
        results = method_block["results"]
        cleaned = ["NA" if v == 2 else v for v in results]

        return cleaned


    
    def save_prompt3_score(self, parent_name, file_name, method_name, score):
        """
        Guarda o score final da Prompt 3 no ficheiro JSON correspondente.
        
        Estrutura:
        parent_name → versions → file_name → method_name → {score}
        """

        if not self.workdir:
            raise ValueError("workdir não está definido na classe SaveIndividual.")

        # Criar diretório se não existir
        full_path = os.path.join(self.workdir, "prompt3_score.json")

        # Se já existir, carregar para atualizar
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # Garantir a estrutura base
        if parent_name not in data:
            data[parent_name] = {"versions": {}}

        if file_name not in data[parent_name]["versions"]:
            data[parent_name]["versions"][file_name] = {}

        # Guardar score do método
        data[parent_name]["versions"][file_name][method_name] = {"score": score}

        # Gravar tudo no ficheiro
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
