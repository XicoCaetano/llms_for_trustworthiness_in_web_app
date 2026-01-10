import os
import pandas as pd
import plotly.express as px
import numpy as np
from collections import defaultdict
import json
import argparse
from pathlib import Path

class XLSXProcessorScore1:
    def __init__(self, input_folder):
        self.input_folder = input_folder

    def get_xlsx_files(self):
        return [f for f in os.listdir(self.input_folder) if f.endswith('.xlsx')]

    def process_files(self):
        dataframes = []
        for filename in self.get_xlsx_files():
            file_path = os.path.join(self.input_folder, filename)
            df = pd.read_excel(file_path)
            # Add your processing logic here
            dataframes.append((filename, df))
        return dataframes


    def save_excel(self, input, output_excel):
        # Carregar JSON
        with open(input, 'r') as file:
            data = json.load(file)

        # Lista para guardar entradas
        rows = []

        # Lista das 16 práticas
        practices = [str(i) for i in range(1, 17)]
        rows = []

        rows_nan = []

        # Apenas processar subpasta 'versions' de cada top-level
        for top_level_folder, subfolders in data.items():
            versions = subfolders.get("versions", {})
            for file_name, methods in versions.items():
                for Method, details in methods.items():
                    file_name_clean = file_name.replace(".java", "")
                    entry = {
                        "Parent File": f"{top_level_folder}",
                        "FileName": file_name_clean,
                        "Method": Method
                    }

                    if "results" in details:
                        # results é uma lista com 0 e 1, por exemplo: [1,0,0,1]

                        lista = details["results"]

                        if len(lista) < 16:
                            for i in range(16 - len(lista)):
                                lista.append(2)

                        for p in practices:
                            entry[p] = lista[int(p) - 1]
                    else:
                        # Se não houver nenhuma das perguntas, marcar tudo como NA
                        for p in practices:
                            entry[p] = "NA"

                    rows.append(entry)

        # Criar DataFrame
        df = pd.DataFrame(rows)

        # print("Exportado para", output_file)
        df.replace(2, np.nan, inplace=True)
        # print(df)

        df.to_excel(output_excel, index=False)

    def process_score (self, weights_path, input, output_score):
        # Carregar dados
        df = pd.read_excel(input)

        with open(weights_path, "r") as f:
            weights_json = json.load(f)

        # Extrair pesos: somar se o mesmo número de prática aparece mais do que uma vez
        weights = {}

        def extract_weights(d):
            if not isinstance(d, dict):
                return
            for k, v in d.items():
                if isinstance(v, dict):
                    if "weight" in v and k.isdigit():
                        weights[k] = weights.get(k, 0.0) + v["weight"]
                    extract_weights(v)

        extract_weights(weights_json)

        # print("[DEBUG] Pesos finais por prática:", weights)

        # Práticas numeradas de 1 a 16 (strings)
        practices = [str(i) for i in range(1, 17)]

        # Função para calcular score
        def calc_score(row):
            total_missing = 0.0
            total_na_weight = 0.0
            rated_weights = {}

            # Primeiro ciclo: somar pesos de práticas normais e NAs
            for p in practices:
                val = row.get(p)
                w = weights.get(p, 0.0)
                if pd.isna(val) or val == "NA":
                    total_na_weight += w
                else:
                    rated_weights[p] = w

            # Calcular soma dos pesos avaliados
            sum_rated_weights = sum(rated_weights.values())

            # Se houver NAs e práticas avaliadas
            if total_na_weight > 0 and sum_rated_weights > 0:
                # Distribuir o peso das NAs proporcionalmente ao rating
                for p in rated_weights:
                    extra = (rated_weights[p] / sum_rated_weights) * total_na_weight
                    rated_weights[p] += extra

            # Segundo ciclo: calcular score final considerando os novos pesos
            for p in practices:
                val = row.get(p)
                if val == 1:
                    total_missing += rated_weights.get(p, weights.get(p, 0.0))

            # Normalizar entre 0 e 1
            return min(1.0, max(0.0, total_missing))


        df["score"] = df.apply(calc_score, axis=1)

        df.at[0, "FileName"] = "CreateNewCustomer_Vx1"

        # Guardar Excel atualizado
        df.to_excel(output_score, index=False)
        # print(f"Exportado para {output_file}")
        # print(df)

        df.to_json(output_score.replace('xlsx', 'json'), orient='records')

    def create_scores_json(self, llm_model, prompt, input_score_1, input_qm, input_manual, output_json_path):
    
        # --- Carregar ficheiros ---
        df_input = pd.read_excel(input_score_1)
        # print(df_input)
        df_qm = pd.read_excel(input_qm)
        df_manual = pd.read_excel(input_manual)
        
        # --- Inicializar JSON ---
        
        if os.path.exists(output_json_path):
            try:
                with open(output_json_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        result_json = json.loads(content)
                        # print(f"📂 JSON existente carregado. Modelos atuais: {list(result_json.keys())}")
                    else:
                        result_json = {}
                        # print(f"📄 JSON vazio encontrado. Criando nova estrutura")
            except json.JSONDecodeError as e:
                # print(f"⚠️  Erro ao ler JSON: {e}. Criando novo JSON")
                result_json = {}
        else:
            result_json = {}
            # print(f"📄 Criando novo JSON")

        # --- Filtrar método específico ---
        method_filter = "enterAddress"
        df_input = df_input[df_input["Method"] == method_filter].copy()
        df_qm = df_qm[df_qm["Method"] == method_filter].copy()
        df_manual = df_manual[df_manual["Method"] == method_filter].copy()
        
        # --- Inicializar estrutura para este LLM model se não existir ---
        if llm_model not in result_json:
            result_json[llm_model] = {}
            # print(f"✨ Criando entrada para modelo: {llm_model}")
 
        prompt_key = f"prompt_{prompt}"
        if prompt_key not in result_json[llm_model]:
            result_json[llm_model][prompt_key] = {}
            # print(f"✨ Criando entrada para prompt: {prompt_key}")

        
        # --- Processar cada DataFrame ---
        datasets = {
            "input": df_input,
            "qm": df_qm,
            "manual": df_manual
        }
        
        for source_name, df in datasets.items():
            # print(f"  📊 Processando {source_name}: {len(df)} linhas")
            
            for _, row in df.iterrows():
                # Extrair informações do filename (formato: CreateNewCustomer_Vx1)
                filename_full = row.get("FileName", "unknown")
                if "_" in filename_full:
                    filename = filename_full.split("_")[0]
                    version = filename_full.split("_")[1]
                else:
                    filename = filename_full
                    version = "V0"
                
                method = row.get("Method", "unknown")
                
                # Criar estrutura aninhada preservando o que já existe
                if filename not in result_json[llm_model][prompt_key]:
                    result_json[llm_model][prompt_key][filename] = {}
                
                if version not in result_json[llm_model][prompt_key][filename]:
                    result_json[llm_model][prompt_key][filename][version] = {}
                
                if method not in result_json[llm_model][prompt_key][filename][version]:
                    result_json[llm_model][prompt_key][filename][version][method] = {}
                
                # Extrair score e practices
                score = float(row.get("score", 0))
                
                # Identificar colunas de practices (colunas numéricas de 1 a 16)
                practice_cols = [col for col in df.columns if isinstance(col, int) or 
                            (isinstance(col, str) and col.isdigit())]
                
                practices = {}
                for col in practice_cols:
                    if col in row.index and not pd.isna(row[col]):
                        practices[int(col)] = int(row[col])
                
                # Adicionar/atualizar dados para esta source
                result_json[llm_model][prompt_key][filename][version][method][source_name] = {
                    "score": score,
                    "practices": practices
                }
        
        # --- Salvar JSON atualizado ---
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
        
        # print(f"\n✅ JSON atualizado: {output_json_path}")
        # print(f"   Modelos no JSON: {list(result_json.keys())}")
        # print(f"   Ficheiros processados para {llm_model}: {list(result_json[llm_model].keys())}")
        


if __name__ == "__main__":

    llm_paths = {
        1: "gpt-3.5-turbo",
        2: "gpt-4o-mini",
        3: "gpt-4.1",
        4: "gpt-4.1-mini"
    }

    # parser = argparse.ArgumentParser(description="Run LLM Individual Practices Evaluation")
    # parser.add_argument("--llm", type=int, choices=llm_paths.keys(), required=True, help="LLM model to use")
    # parser.add_argument("--p", type=int, choices=prompt_choices.keys(), required=True, help="Prompt version")
    # parser.add_argument("--v1", type=int, choices=version_applicability.keys(), required=True, help="Prompt applicability version")
    # parser.add_argument("--v2", type=int, choices=version_following.keys(), required=True, help="Prompt sub-version")

    # args = parser.parse_args()

    processor = XLSXProcessorScore1('tool/src/new_classification/input')
    

    # GERAL Inputs and Outputs
    # GERAL Inputs
    real = "tool/src/new_classification/input/Missing Practices in WsvdBench_GroundTruth_V3.xlsx"
    manual_weights = "tool/src/new_classification/input/manual_weights.json"
    qm_weights = "tool/src/new_classification/output_weights/qm_weights.json"
    paper_score = "tool/src/new_classification/input/score_cristiano_paper.json"

    lista_llm = [1,2,3,4]
    lista_prompt = [1,2,5]

    
    for i in lista_llm:
        llm_version = i
        for p in lista_prompt:
            prompt = p

            print(f"\n\n🚀 Processando LLM {llm_paths.get(llm_version)} e Prompt {prompt}\n")

            # Bases para não repetir
            base = "tool/src/new_classification/output"
            base_output = "tool/src/new_classification/output_score_1"
            base_excel = "tool/src/new_classification/output_score_1/excels"

            llm = llm_paths.get(llm_version, "unknown")

            base_prompt_score = f"{base_output}/{llm}"
            os.makedirs(base_prompt_score, exist_ok=True)
            base_prompt = f"{base}/prompt_{prompt}/{llm}"

            # Input
            score_1 = f"tool/src/test_results/individual_practices/{llm}/score_1/{prompt}/score_1_prompt_{prompt}.json"

            score_qm_excel = f"{base_prompt}/score/qm_new_score.xlsx"
            score_manual_excel = f"{base_prompt}/score/manual_new_weights.xlsx"
            
            # Outputs Excel principais
            output_prompt_excel = f"{base_excel}/{llm}_{prompt}.xlsx"

            # Output
            output_score_1 = f"{base_prompt_score}/score 1.xlsx"
            output_score_1_json = f"{base_prompt_score}/score 1.json"
            output_comparasion_score = f"{base_prompt_score}/score_comparasion.json"

            output_unic_json = f"{base_output}/unic_json.json"

            
            processor.save_excel(score_1, output_prompt_excel)

            processor.process_score(qm_weights, output_prompt_excel, output_score_1)

            processor.create_scores_json(llm, prompt, output_score_1, score_qm_excel, score_manual_excel, output_unic_json)