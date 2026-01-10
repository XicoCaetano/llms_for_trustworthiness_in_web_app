import json
import os
from collections import defaultdict

NVD_folder = "tool/src/new_classification/input_weights/nvd_json"

# Mapeamento das práticas (1–16) para CWEs
practice_to_cwes = {
    "1": ["CWE-20", "CWE-602", "CWE-522", "CWE-807", "CWE-345"],
    "2": ["CWE-20", "CWE-707", "CWE-601", "CWE-1173", "CWE-807", "CWE-73", "CWE-184"],
    "3": ["CWE-1173", "CWE-20", "CWE-115", "CWE-707", "CWE-693"],
    "4": ["CWE-116", "CWE-172", "CWE-176"],
    "5": ["CWE-180", "CWE-176", "CWE-177", "CWE-178", "CWE-179", "CWE-116"],
    "6": ["CWE-20", "CWE-636", "CWE-703", "CWE-754"],
    "7": ["CWE-176", "CWE-177", "CWE-178", "CWE-180", "CWE-172", "CWE-116"],
    "8": ["CWE-20", "CWE-707", "CWE-601", "CWE-642", "CWE-113", "CWE-116"],
    "9": ["CWE-93", "CWE-116", "CWE-113", "CWE-644"],
    "10": ["CWE-601", "CWE-1325", "CWE-807", "CWE-285"],
    "11": ["CWE-20", "CWE-119", "CWE-1284", "CWE-129", "CWE-704"],
    "12": ["CWE-1284", "CWE-129", "CWE-190", "CWE-125", "CWE-787"],
    "13": ["CWE-1286", "CWE-170", "CWE-20", "CWE-119", "CWE-120"],
    "14": ["CWE-20", "CWE-89", "CWE-79", "CWE-116", "CWE-74", "CWE-77", "CWE-95"],
    "15": ["CWE-116", "CWE-79", "CWE-80", "CWE-74", "CWE-94", "CWE-117"],
    "16": ["CWE-180", "CWE-73", "CWE-176", "CWE-177", "CWE-178", "CWE-179", "CWE-23"]
}

# Estrutura de template para armazenar pesos
structure_template = {
  "Input Validation": {
    "children": {
      "Validation Procedure": {
        "children": {
          "4": {},
          "7": {},
          "16": {}
        }
      },
      "Data Source": {
        "children": {
          "2": {},
          "3": {}
        }
      },
      "Input Entry": {
        "children": {
          "1": {},
          "5": {},
          "6": {},
          "8": {},
          "9": {},
          "12": {},
          "13": {},
          "14": {},
          "15": {},
          "16": {}
        }
      },
      "App Request": {
        "children": {
          "10": {},
          "11": {}
        }
      }
    }
  }
}


cwe_to_practices = defaultdict(list)
for practice, cwes in practice_to_cwes.items():
    for cwe in cwes:
        cwe_to_practices[cwe].append(practice)    # Inverter para CWE → práticas

# Função para extrair CVEs dos ficheiros NVD e agrupar por CWE
# Esta função extrai os CVEs e os agrupa por CWE.
# Cada CVE é armazenado com seu ID e descrição.
def extract_cves_by_cwe(folder):
    cwe_cve_data = defaultdict(list)

    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("CVE_Items", []):
                cve_id = item.get("cve", {}).get("CVE_data_meta", {}).get("ID", "")
                description_data = item.get("cve", {}).get("description", {}).get("description_data", [])
                description = " ".join(d.get("value", "") for d in description_data)

                problemtypes = item.get("cve", {}).get("problemtype", {}).get("problemtype_data", [])
                for pt in problemtypes:
                    for desc in pt.get("description", []):
                        cwe_id = desc.get("value", "").strip()
                        if cwe_id.startswith("CWE-"):
                            cwe_cve_data[cwe_id].append({
                                "id": cve_id,
                                "description": description
                            })
    return cwe_cve_data

# Guardar ficheiro detalhado com CVEs por CWE
def save_cwe_cve_data(cwe_cve_data, output_file):
    cwe_details = {
        cwe: [entries, len(entries)] for cwe, entries in cwe_cve_data.items()
    }
    with open(output_file, "w") as f:
        json.dump(cwe_details, f, indent=2)
    print(f"✅ Detailed CWE-CVE data saved to {output_file}")

def compute_weights_from_cwe_data(cwe_cve_data):
    practice_counts = defaultdict(int)
    for cwe, entries in cwe_cve_data.items():
        for practice in cwe_to_practices.get(cwe, []):
            practice_counts[practice] += len(entries)

    total = sum(practice_counts.values())
    if total == 0:
        print("⚠️ No CVEs found for given CWEs/practices.")
        return {}

    # Criar dicionário com pesos das práticas (string keys)
    weights = {k: round(v / total, 6) for k, v in practice_counts.items()}

    with open("tool/src/new_classification/output_weights/weights.json", "w") as f:
        json.dump(weights, f, indent=2)
    print("✅ Weights saved to tool/src/new_classification/output_weights/weights.json")

    # Construir a estrutura final com pesos no lugar certo
    # Esta função percorre a structure_template recursivamente e insere os pesos onde a key for prática (string numérica)
    def insert_weights(node):
        if not isinstance(node, dict):
            return
        children = node.get("children", None)
        if children:
            for key, child in children.items():
                # Se a key for prática (número string), inserir peso, senão continuar a descer
                if key in weights:
                    children[key] = weights[key]
                else:
                    insert_weights(child)

    final_structure = json.loads(json.dumps(structure_template))  # deepcopy
    insert_weights(final_structure["Input Validation"])

    with open("tool/src/new_classification/output_weights/qm_weights.json", "w") as f:
        json.dump(final_structure, f, indent=2)
    print("✅ QM Weights saved to tool/src/new_classification/output_weights/qm_weights.json")


if __name__ == "__main__":
    cwe_cve_data = extract_cves_by_cwe(NVD_folder)
    save_cwe_cve_data(cwe_cve_data, "tool/src/new_classification/output_weights/cwe_cve_data.json")
    compute_weights_from_cwe_data(cwe_cve_data)