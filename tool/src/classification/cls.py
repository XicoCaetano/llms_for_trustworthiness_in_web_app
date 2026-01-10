import json
import csv
import os
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

class Classification:
    def __init__(self):
        self.labels = ["CWE-89", "CWE-79"]
        # self.expanded_cwes = self.expand_cwes()

    def expand_cwes(self):
        with open("tool/src/classification/input/cwe_attack_map.json") as f:
            cwe_map = json.load(f)

        expanded = set()
        for cwe in self.labels:
            if cwe in cwe_map:
                expanded.add(cwe)
                expanded.update(cwe_map[cwe].get("related_cwes", {}).keys())
        return expanded

    def classify_methods(self, template_id, labels_path="tool/src/classification/output/method_labels.json"):
        classification_path = f"tool/src/classification/output/practices_classification_labels_format_1_t1_V7.json"
        output_csv = f"tool/src/classification/output/cwe_classification_1_t1_V7.csv"
        metrics_json = f"tool/src/classification/metrics_output/classification_metrics_1_t1_V7.json"

        with open(classification_path) as f:
            method_data = json.load(f)
        with open(labels_path) as f:
            labels_data = json.load(f)

        headers = ["parent", "file_name", "version", "method_name", "real", "esperado"]
        rows = []

        y_true = []
        y_pred = []

        for method_key, data in method_data.items():
            method_cwes = set(data.get("cwes", []))

            if method_key.count(":") != 2:
                continue
            file_name, version, method_name = method_key.split(":")

            matched_key = None
            for label_key in labels_data:
                if label_key.endswith(f"{file_name}:{version}:{method_name}"):
                    matched_key = label_key
                    break

            if matched_key is None:
                continue

            real_value = labels_data[matched_key].get("real", "NA")
            if real_value == "NA":
                continue

            parent = matched_key.split(":")[0]
            esperado = 1 if any(cwe in self.expanded_cwes for cwe in method_cwes) else 0

            row = [parent, file_name, version, method_name, real_value, esperado]
            rows.append(row)

            y_true.append(int(real_value))
            y_pred.append(esperado)

        # Save CSV
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)

        # Compute and save metrics
        cm = confusion_matrix(y_true, y_pred).tolist()
        metrics = {
            "accuracy": round(accuracy_score(y_true, y_pred), 2),
            "precision": round(precision_score(y_true, y_pred, zero_division=0), 2),
            "recall": round(recall_score(y_true, y_pred, zero_division=0), 2),
            "f1_score": round(f1_score(y_true, y_pred, zero_division=0), 2),
            "confusion_matrix": cm
        }

        with open(metrics_json, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"✅ CSV saved to: {output_csv}")
        print(f"📊 Metrics saved to: {metrics_json}")

    def compare_data(self, real_data, expected_data):
        print(f"[DEBUG] expected_data keys: {list(expected_data.keys())}")
        print(f"[DEBUG] real_data keys: {list(real_data.keys())}")

        for top_level_key, top_level_value in expected_data.items():
            if top_level_key not in real_data:
                print(f"[!] Subfolder '{top_level_key}' not found in real data.")
                continue

            for second_level_key, second_level_value in top_level_value.items():
                # Caso seja ficheiro com métodos diretamente (ex: tpcapp/ProductDetail.java)
                if isinstance(second_level_value, dict) and all(isinstance(v, dict) and "question_2" in v for v in second_level_value.values()):
                    if second_level_key not in real_data[top_level_key]:
                        print(f"[!] File '{second_level_key}' not found in real data at folder '{top_level_key}'.")
                        continue

                    for method_name, questions in second_level_value.items():
                        expected_answer = questions.get("question_2", "").strip()
                        real_entry = real_data[top_level_key][second_level_key].get(method_name, "")
                        
                        if isinstance(real_entry, dict):
                            print(f"[!] Skipped {top_level_key}/{second_level_key}/{method_name}: real data is a dict, not a string.")
                            continue
                        
                        real_answer = real_entry.strip()

                        if real_answer == "":
                            print(f"[ ] {top_level_key}/{second_level_key}/{method_name}: No answer provided in real data.")
                        elif real_answer == expected_answer:
                            print(f"[✓] {top_level_key}/{second_level_key}/{method_name}: Match")
                        else:
                            print(f"[✗] {top_level_key}/{second_level_key}/{method_name}:")
                            print(f"     → Expected: {expected_answer}")
                            print(f"     → Found:    {real_answer}")
                
                # Caso seja subpasta (ex: tpcapp/input)
                elif isinstance(second_level_value, dict):
                    if second_level_key not in real_data[top_level_key]:
                        print(f"[!] Subfolder '{second_level_key}' not found in real data at folder '{top_level_key}'.")
                        continue

                    for file_name, methods in second_level_value.items():
                        if file_name not in real_data[top_level_key][second_level_key]:
                            print(f"[!] File '{file_name}' not found in real data at path '{top_level_key}/{second_level_key}'.")
                            continue

                        for method_name, questions in methods.items():
                            if not isinstance(questions, dict):
                                print(f"[!] Unexpected data type at method {method_name} in {top_level_key}/{second_level_key}: expected dict, got {type(questions).__name__}")
                                continue

                            expected_answer = questions.get("question_2", "").strip()
                            real_entry = real_data[top_level_key][second_level_key][file_name].get(method_name, "")

                            if isinstance(real_entry, dict):
                                print(f"[!] Skipped {top_level_key}/{second_level_key}/{file_name}/{method_name}: real data is a dict, not a string.")
                                continue
                            
                            real_answer = real_entry.strip()

                            if real_answer == "":
                                print(f"[ ] {top_level_key}/{second_level_key}/{file_name}/{method_name}: No answer provided in real data.")
                            elif real_answer == expected_answer:
                                print(f"[✓] {top_level_key}/{second_level_key}/{file_name}/{method_name}: Match")
                            else:
                                print(f"[✗] {top_level_key}/{second_level_key}/{file_name}/{method_name}:")
                                print(f"     → Expected: {expected_answer}")
                                print(f"     → Found:    {real_answer}")
                else:
                    print(f"[!] Unexpected structure at {top_level_key}/{second_level_key}.")

            

    def practices_association(self, practices_real_path="tool/src/real.json", expected_path="tool/src/test_results"):

        with open(practices_real_path) as f:
            real_data = json.load(f)

        real_data = {k: v for k, v in real_data.items() if k}

        expected_files = [f for f in os.listdir(expected_path) if f.endswith(".json")]
        if not expected_files:
            print("❌ Nenhum ficheiro .json encontrado no caminho de expected.")
            return

        print("Ficheiros disponíveis:")
        for i, fname in enumerate(expected_files):
            print(f"  [{i}] {fname}")

        idx = int(input("Escolhe o ficheiro de expected por índice: "))
        selected_file = expected_files[idx]
        print(f"Você selecionou: {selected_file}")

        with open(os.path.join(expected_path, selected_file)) as f:
            expected_data = json.load(f)

        expected_data = {k: v for k, v in expected_data.items() if k}

        print(f"[DEBUG] expected_data keys: {list(expected_data.keys())}")
        print(f"[DEBUG] real_data keys: {list(real_data.keys())}")

        for key in expected_data.keys():
            if key not in real_data:
                print(f"[!] Subfolder '{key}' not found in real data")
            else:
                subfolders = list(real_data[key].keys())
                print(f"[DEBUG] Subfolders in '{key}': {subfolders}")

                for subfolder in expected_data[key].keys():
                    if subfolder not in subfolders:
                        print(f"[!] Subfolder '{subfolder}' not found in real data at path '{key}'")

        self.compare_data(real_data, expected_data)
        print(f"✅ Comparação realizada com sucesso para {selected_file}")


if __name__ == "__main__":
    # f = input("Enter the template ID (1, 2, or 3): ").strip()
    # if f not in ["1", "2", "3"]:
    #     print("Invalid template ID. Please enter 1, 2, or 3.")
    #     exit(1)
    clf = Classification()
    clf.classify_methods(template_id=1)
    # clf.practices_association()