import requests
import json
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import argparse
import re
from pathlib import Path
import csv

# Load environment variables from .env
load_dotenv()
API_KEY = os.getenv("NVD_API_KEY")

# Constants
CWE_FILE = "cwe_list.json"
OUTPUT_FILE = "cves_cwes_list.json"
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
SQL_XSS = "sql_xss.json"
HEADERS = {"apiKey": API_KEY}

class Association:
    def __init__(self, force_update=False):
        self.force_update = force_update
        # self.cwe_practices = self.load_cwes()
        # self.output_data = self.load_existing_output()

    # Function to load CWEs from the JSON file
    def load_cwes(self):
        with open(CWE_FILE, "r") as f:
            return json.load(f)

    # Function to load the existing output file
    def load_existing_output(self):
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r") as f:
                return json.load(f)
        return {}

    # Function to save the updated output file
    def save_output(self, data):
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # Function to fetch CVEs by CWE ID
    def fetch_cves_by_cwe(self, cwe_id, max_results=100):
        cves = []
        start_index = 0
        total = 1  # initialize to enter the loop

        while start_index < total:
            params = {
                "cweId": cwe_id,
                "startIndex": start_index,
                "resultsPerPage": 100,
                "pubStartDate": "2002-01-01T00:00:00:000 UTC-00:00"
            }
            response = requests.get(NVD_API_URL, headers=HEADERS, params=params)

            if response.status_code != 200:
                print(f"[{cwe_id}] Error fetching CVEs: {response.status_code}")
                break

            data = response.json()
            total = data.get("totalResults", 0)
            for item in data.get("vulnerabilities", []):
                cve_data = item.get("cve", {})
                cves.append({
                    "id": cve_data.get("id"),
                    "description": cve_data.get("descriptions", [{}])[0].get("value", ""),
                    "publishedDate": cve_data.get("published", ""),
                    "severity": self.extract_severity(cve_data)
                })

            start_index += 100
            time.sleep(1)  # avoid API rate limits

        return cves

    # Function to extract the severity of CVEs
    def extract_severity(self, cve_data):
        metrics = cve_data.get("metrics", {})
        cvss = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30") or metrics.get("cvssMetricV2")
        if cvss and isinstance(cvss, list):
            return cvss[0].get("cvssData", {}).get("baseSeverity", "UNKNOWN")
        return "UNKNOWN"

    # Function to check if an update is needed based on the date
    def needs_update(self):
        if self.force_update:
            return True
        for cwe_id, data in self.output_data.items():
            last_updated = data.get("last_updated", "")
            if not last_updated:
                return True
            # Check if the last update was more than 7 days ago
            last_updated_date = datetime.fromisoformat(last_updated)
            if (datetime.utcnow() - last_updated_date).days > 7:
                return True
        return False

    # Function to update CVEs
    def update_cves(self):
        if self.needs_update():
            print("🔄 Updating CVE data...")
            for cwe_id, practices in self.cwe_practices.items():
                print(f"🔎 Fetching CVEs for {cwe_id}...")
                cves = self.fetch_cves_by_cwe(cwe_id)

                self.output_data[cwe_id] = {
                    "name": practices["name"],
                    "practices": practices["practices"],
                    "last_updated": datetime.utcnow().isoformat(),
                    "cves": cves
                }

                print(f"✅ {len(cves)} CVEs found for {cwe_id}")

            self.save_output(self.output_data)
            print("✅ Output file updated successfully.")
        else:
            print("📅 Data recently updated. No update needed.")


    def cwes_cves_association(self, response, file_name, method_name, template_id, template_name):
        # Caminhos já definidos: sql_xss_path e cwe_attack_map_path
        with open("src/classification/input/sql_xss.json") as f:
            sql_xss_data = json.load(f)

        # Caminho para o ficheiro de output
        output_path = f"src/classification/output/practices_classification_{template_id}_{template_name}.json"

        # Verifica se o ficheiro já existe e carrega o conteúdo, senão cria um dicionário vazio
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, "r") as f:
                output = json.load(f)
        else:
            output = {}

        # Processar a response para extrair respostas numeradas
        question_answers = {}
        if re.search(r'\d+\.', response):
            response_parts = re.split(r'(\d+\.)', response)
            response_parts = [part.strip() for part in response_parts if part.strip()]
            for i in range(0, len(response_parts), 2):
                if i + 1 < len(response_parts):
                    question_number = response_parts[i].strip('.')
                    answer = response_parts[i + 1].strip()
                    question_answers[f"question_{question_number}"] = answer

        # Processar CWEs associados (da resposta à questão 2)
        question_2 = question_answers.get("question_2", "")
        list_question_2 = [int(x.strip()) for x in question_2.split(",") if x.strip().isdigit()]

        # Adicionar ao dicionário de output
        key = f"{file_name}::{method_name}"
        output[key] = {
            "cwes": []
        }

        for number in list_question_2:
            number_str = str(number)
            if number_str in sql_xss_data:
                cwes_data = sql_xss_data[number_str].get("cwes", [])
                output[key]["cwes"].extend(cwes_data)

        # Remover duplicados, se existirem
        output[key]["cwes"] = list(set(output[key]["cwes"]))

        # Guardar o JSON atualizado
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"✅ File Practices Classification updated successfully.")

    # # Main function for execution
    # def main():
    #     parser = argparse.ArgumentParser(description="Update CVE data and best practices.")
    #     parser.add_argument("--force-update", action="store_true", help="Force update of all CVEs")
    #     args = parser.parse_args()

    #     cve_updater = CVEUpdater(force_update=args.force_update)
    #     cve_updater.update_cves()

    # if __name__ == "__main__":
    #     main()