import json
import re
import os
from cpgqls_client import CPGQLSClient, import_code_query

class JoernProcessor:
    def __init__(self, ip, project_path, json_path, output_path):
        self.project_path = project_path
        self.json_path = json_path
        self.output_path = output_path
        self.server_endpoint = ip

        out_dir = self.output_path if not self.output_path.endswith(".json") else os.path.dirname(self.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        self.joern_results = {}

    def _extract_methods(self, data, parent_path=""):
        """Extrai métodos do JSON agrupando por pasta; aceita 'str', ['file','Class.method'] e {'file':..,'method':..}."""
        methods_by_folder = {}

        def add(folder, file_name, method_name):
            if not file_name or not method_name:
                return
            methods_by_folder.setdefault(folder, []).append((file_name, method_name))

        # --- Caso A: ficheiro é uma LISTA (all_methods.json) ---
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str) and "." in item:
                    cls, _meth = item.split(".", 1)
                    # usamos o nome do ficheiro = nome da classe
                    add(parent_path, cls, item)  # guardamos "Class.method" como method_name
            total = sum(len(v) for v in methods_by_folder.values())
            print(f"[DBG] _extract_methods(all_methods): {total} métodos")
        return methods_by_folder

    def _clean_response(self, response):
        """Limpa a resposta da Joern, removendo caracteres ANSI e extraindo a lista de resultados."""
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")  # Expressão regular para remover códigos ANSI
        cleaned_response = ansi_escape.sub("", response)

        # Extrair corretamente a lista dentro de List(...)
        match = re.search(r"List\((.*)\)", cleaned_response, re.DOTALL)
        if match:
            extracted = match.group(1)
            elements = re.findall(r'"(.*?)"', extracted)  # Extrair valores entre aspas
            return elements if elements else None
        return None

    def _process_methods_in_folder(self, client, folder, methods_by_folder):
        """Processa cada pasta e os seus métodos, acumulando resultados em memória para 1 ficheiro final."""
        # Garante a estrutura agregada
        if not hasattr(self, "joern_results") or self.joern_results is None:
            self.joern_results = {}  # {folder: {file_name: {method_name: [callees...]}}}

        self.joern_results.setdefault(folder, {})

        for file_name, method_name in methods_by_folder[folder]:
            print(f"\n[+] A processar método: {file_name}.{method_name}")

            # Extrair apenas o nome do método (assume formato Classe.metodo)
            try:
                method_simple = method_name.split(".")[1]
            except IndexError:
                method_simple = method_name  # fallback se já vier simples

            query = (
                f'cpg.method.name("{method_simple}")'
                f'.where(_.file.name(".*{file_name}.java$")).callee.fullName.l'
            )

            result = client.execute(query)
            if result and "stdout" in result:
                print(f"Resposta bruta: {result['stdout']}")
                cleaned_response = self._clean_response(result["stdout"])

                if not cleaned_response:
                    print(f"[-] Nenhum resultado encontrado para {method_simple} em {file_name}.")
                    # Mesmo sem resultados, criamos a entrada vazia
                    self.joern_results.setdefault(folder, {}).setdefault(file_name, {})[method_simple] = []
                    continue

                # Acumula em memória
                self.joern_results.setdefault(folder, {}).setdefault(file_name, {})[method_simple] = cleaned_response
                print(f"[+] Resultado agregado em memória: {file_name}.{method_simple}")
            else:
                print(f"[-] Erro ao executar a consulta para {method_simple}: {result}")
                # Regista erro como lista vazia (ou podes guardar um objeto com erro)
                self.joern_results.setdefault(folder, {}).setdefault(file_name, {})[method_simple] = []

    def _flush_joern_results_single_file(self, base_name="joern_results_"):
        """
        Grava self.joern_results num único ficheiro JSON.
        - Se self.output_path terminar em .json, usa exatamente esse ficheiro.
        - Caso contrário, cria <base_name><i>.json incremental dentro de self.output_path.
        """
        # Decide diretório e nome
        if self.output_path.endswith(".json"):
            out_dir = os.path.dirname(self.output_path) or "."
            out_path = self.output_path
        else:
            out_dir = self.output_path
            base = base_name
            existing = [f for f in os.listdir(out_dir) if f.startswith(base) and f.endswith(".json")]
            indices = []
            for fname in existing:
                try:
                    indices.append(int(fname.replace(".json", "").split("_")[-1]))
                except (IndexError, ValueError):
                    continue
            next_idx = (max(indices) + 1) if indices else 1
            out_path = os.path.join(out_dir, f"{base}{next_idx}.json")

        # Gravar
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(getattr(self, "joern_results", {}), f, indent=2, ensure_ascii=False)

        print(f"[+] Resultados Joern (agregados) gravados em: {out_path}")
        return out_path

    def process_methods(self, client):
        """Método principal para processar os métodos agrupados por pasta."""
        with open(self.json_path, "r", encoding="utf-8") as file:
            methods_data = json.load(file)

        methods_by_folder = self._extract_methods(methods_data)

        for folder, methods in methods_by_folder.items():
            print(f"[+] A processar pastas")
            self._process_methods_in_folder(client, folder, methods_by_folder)


    def import_project_to_joern(self, client):
        """Importa o projeto para a Joern antes de processar os métodos."""
        print("[+] A importar o projeto para a Joern...")
        import_query = import_code_query(self.project_path, "my-project")
        print(import_query)
        import_result = client.execute(import_query)
        print(import_result)

        if not import_result or "stdout" not in import_result:
            print("[-] Falha ao importar o projeto para a Joern.")
            return False

        print("[+] Projeto importado com sucesso.")
        return True
    
    def joern_output_render(self, root, file, dir):
        """Renderiza a saída da Joern para um ficheiro JSON."""
        json_file_name = f"joern_{os.path.basename(root)}_{file.replace('.java', '')}.json"
        json_file_path = os.path.join(dir, json_file_name)

        print(f"Procurando JSON: {json_file_path}")

        if not os.path.exists(json_file_path):
            print(f"Arquivo JSON {json_file_path} não encontrado.")
        else:
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)

            valid_methods = []

            for entry in data:
                # Ignorar operadores e construtores
                if "<operator>" in entry or "<init>" in entry:
                    continue  

                # Extrair caminho do método
                if ":" in entry:
                    method_path = entry.split(":")[0]
                    parts = method_path.split(".")
                    if len(parts) > 1:
                        class_name = parts[-2]  # Penúltimo elemento (classe)
                        method_name = parts[-1]  # Último elemento (método)
                        valid_methods.append((class_name, method_name))
        return valid_methods

    def run(self):
        """
        Executa todo o processo:
        1) Importa o projeto para o Joern
        2) Processa os métodos (queries Joern) acumulando em self.joern_results
        3) Grava um único JSON agregado (nome incremental OU o nome em self.output_path se for .json)
        """
        def _normalize_for_cpgqls(endpoint: str) -> str:
            # CPGQLSClient quer "host:port"
            e = (endpoint or "").strip()
            for prefix in ("ws://", "wss://", "http://", "https://"):
                if e.startswith(prefix):
                    e = e[len(prefix):]
            # remove paths tipo ".../graphql" se vierem
            return e.split("/")[0]
    
        # --- Joern ---
        endpoint = _normalize_for_cpgqls(self.server_endpoint)
        client = CPGQLSClient(endpoint)

        if not self.import_project_to_joern(client):
            print("[!] Falha ao importar projeto para o Joern")
            return

        # --- Processar métodos e acumular resultados ---
        self.process_methods(client)

        # --- Gravar JSON único agregado ---
        # Se já gravei no process_methods, podes comentar a linha abaixo.
        self._flush_joern_results_single_file()