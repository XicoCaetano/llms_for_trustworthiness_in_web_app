import os
import json
from datetime import datetime
import javalang
import time
import re

class JSONHandler:
    def __init__(self, root_folder, workdir="./src/test_results"):
        self.workdir = workdir
        os.makedirs(self.workdir, exist_ok=True)
        self.root_folder = root_folder
        self.structure = {}

    def run(self, version, template_number):
        # Build the nested structure
        self.build_nested_structure()

        # Create a unique filename for each execution
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.filepaths = {
            f"template_{template_number}": os.path.join(self.workdir, f"template_{template_number}_result_V{version}_{timestamp}.json"),
        }

        # Initialize each JSON file with the directory structure
        for path in self.filepaths.values():
            with open(path, mode='w', encoding='utf-8') as file:
                json.dump(self.structure, file, indent=4)

    def build_nested_structure(self):
        """
        Build the nested directory structure from the root folder.
        Each directory can contain .java files and subfolders.
        """
        allowed_parents = {"tpcapp", "tpcc", "tpcw"}
        for subdir, _, files in os.walk(self.root_folder):
            parts = subdir[len(self.root_folder):].strip(os.sep).split(os.sep)
            
            # Exemplo: parts = ['tcpapp', 'version']
            if len(parts) >= 2 and parts[-1] == "versions" and parts[-2] in allowed_parents:
                system = parts[-2]

                if system not in self.structure:
                    self.structure[system] = {"versions": {}}

                for file in files:
                    if file.endswith(".java"):
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

    def save_to_json(self, template_number, parent_name, file_name, method_name, response):
        """Save the response to the JSON file for the specific method within the .java file."""
        template_key = f"template_{template_number}"
        
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
        
        import re

        if template_number in [1, 2, 3]:
            # Check if the response has at least one question marker tipo "1." ou "2."
            if re.search(r'\d+\.', response):
                response_parts = re.split(r'(\d+\.)', response)

                # Remove strings vazias e espaços desnecessários
                response_parts = [part.strip() for part in response_parts if part.strip()]

                question_answers = {}
                for i in range(0, len(response_parts), 2):
                    if i + 1 < len(response_parts):
                        question_number = response_parts[i].strip('.')
                        answer = response_parts[i + 1].strip()
                        question_answers[f"question_{question_number}"] = answer
                    else:
                        print(f"[!] ⚠️ Skipping unmatched part: '{response_parts[i]}'")

                if method_name in current:
                    current[method_name] = question_answers
                else:
                    raise KeyError(f"Method {method_name} not found in {file_name}")
            else:
                print("[!] ⚠️ Response not structured with numbered questions. Saving raw response.")
                if method_name in current:
                    current[method_name] = response.strip()
                else:
                    raise KeyError(f"Method {method_name} not found in {file_name}")
        else:
            # Para outros templates, guarda tudo como está
            if method_name in current:
                current[method_name] = response.strip()
            else:
                raise KeyError(f"Method {method_name} not found in {file_name}")

        
        # Write back to the JSON file
        time.sleep(1)
        with open(filepath, mode='w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)


    def save_to_json_individual_practices(self, template_number, parent_name, file_name, method_name, response):
        """Save the response to the JSON file for the specific method within the .java file."""
        template_key = f"template_{template_number}"
        
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
        
        if template_number in [1, 2, 3]:
            # Check if the response has at least one question marker tipo "1." ou "2."
            if re.search(r'\d+\.', response):
                response_parts = re.split(r'(\d+\.)', response)

                # Remove strings vazias e espaços desnecessários
                response_parts = [part.strip() for part in response_parts if part.strip()]

                question_answers = {}
                for i in range(0, len(response_parts), 2):
                    if i + 1 < len(response_parts):
                        question_number = response_parts[i].strip('.')
                        answer = response_parts[i + 1].strip()
                        question_answers[f"question_{question_number}"] = answer
                    else:
                        print(f"[!] ⚠️ Skipping unmatched part: '{response_parts[i]}'")

                if method_name in current:
                    current[method_name] = question_answers
                else:
                    raise KeyError(f"Method {method_name} not found in {file_name}")
            else:
                print("[!] ⚠️ Response not structured with numbered questions. Saving raw response.")
                if method_name in current:
                    current[method_name] = response.strip()
                else:
                    raise KeyError(f"Method {method_name} not found in {file_name}")
        else:
            # Para outros templates, guarda tudo como está
            if method_name in current:
                current[method_name] = response.strip()
            else:
                raise KeyError(f"Method {method_name} not found in {file_name}")

        
        # Write back to the JSON file
        time.sleep(1)
        with open(filepath, mode='w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)