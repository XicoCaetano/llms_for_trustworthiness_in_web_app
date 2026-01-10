import os
import javalang
import json

class JavaProcessor:
    def __init__(self, root_folder, output_dir):
        self.root_folder = root_folder
        self.output_dir = output_dir
        self.structure = {}
        self.methods_json = []
        os.makedirs(self.output_dir, exist_ok=True)  # Criar diretório de saída se não existir


    def build_nested_structure(self):
        for subdir, _, files in os.walk(self.root_folder):
            parts = subdir[len(self.root_folder):].strip(os.sep).split(os.sep)
            
            # Exemplo: parts = ['tcpapp', 'version']
            if len(parts) >= 2 and parts[-1] == "version" and parts[-2] in {"tcpapp", "tpcc", "tpcw"}:
                # OK, vamos processar este diretório
                current = self.structure

                # Criar estrutura aninhada
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                current["methods"] = []

                for file in files:
                    if file.endswith(".java"):
                        file_path = os.path.join(subdir, file)
                        methods = self.process_java_file(file_path)
                        current["methods"].extend(methods)

    def process_java_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as java_file:
            code = java_file.read()

        tree = javalang.parse.parse(code)
        file_name = os.path.basename(file_path).replace(".java", "")

        methods = []

        for path, node in tree:
            if isinstance(node, javalang.tree.MethodDeclaration):
                start = node.position.line if node.position else "?"
                method_source = self.extract_method_source(code, node)
                methods.append((node.name, start, method_source))

                # Adicionando o nome do ficheiro ao dicionário
                self.methods_json.append(f"{file_name}.{node.name}")  

        return methods

    
    def extract_methods(self, data, parent_path=""):
        methods_by_folder = {}
        for key, value in data.items():
            if key == "methods":
                for method in value:
                    file_name, method_name = method.split(".", 1)
                    if parent_path not in methods_by_folder:
                        methods_by_folder[parent_path] = []
                    methods_by_folder[parent_path].append((file_name, method_name))

            elif isinstance(value, dict):
                new_path = f"{parent_path}/{key}" if parent_path else key
                sub_methods = self.extract_methods(value, new_path)
                for sub_path, methods in sub_methods.items():
                    if sub_path not in methods_by_folder:
                        methods_by_folder[sub_path] = []
                    methods_by_folder[sub_path].extend(methods)
        return methods_by_folder

    def extract_method_source(self, code, method_node):
        lines = code.splitlines()
        start_line = (method_node.position.line - 1) if method_node.position else 0

        # Encontrar a primeira '{' a partir da linha do cabeçalho
        i = start_line
        while i < len(lines) and "{" not in lines[i]:
            i += 1

        # Se não houver '{', devolve só a assinatura
        if i >= len(lines):
            return "\n".join(lines[start_line:start_line+1])

        brace = 0
        started = False
        out = []

        for j in range(start_line, len(lines)):
            line = lines[j]
            out.append(line)

            # começar a contar quando entramos no bloco (primeira '{' vista)
            if j >= i:
                brace += line.count("{")
                brace -= line.count("}")
                started = True

            # sair quando fecharmos o bloco aberto
            if started and brace == 0:
                break

        return "\n".join(out)


    def save_to_json(self, output_path):
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(self.structure, json_file, indent=2, ensure_ascii=False)
        print(f"\nArquivo JSON salvo em: {output_path}")

    def save_methods_to_json(self, output_path):
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(self.methods_json, json_file, indent=2, ensure_ascii=False)
        print(f"\nArquivo JSON com métodos salvo em: {output_path}")

    def print_structure(self):
        print(json.dumps(self.structure, indent=2))