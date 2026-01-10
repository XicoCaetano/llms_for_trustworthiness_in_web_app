import os
import pandas as pd
import plotly.express as px
import numpy as np
from collections import defaultdict
import json
import argparse
from pathlib import Path


def process_score_divide_na(weights_path, expected_excel, output_score, output_json):

        # Carregar dados
        df = pd.read_excel(expected_excel)

        df.columns = [str(c).strip() for c in df.columns]

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

        # Guardar Excel atualizado
        df.to_excel(output_score, index=False)
        # print(f"Exportado para {output_file}")
        # print(df)

        df.to_json(output_json, orient='records')


real = "tool/src/dashboard_llms/input/Missing Practices in WsvdBench_GroundTruth_V3.xlsx"
qm_weights = "tool/src/dashboard_llms/output_weights/qm_weights.json"

output_gt_score_excel = "tool/src/dashboard_llms/output_gt/gt_scores.xlsx"
output_gt_score_json = "tool/src/dashboard_llms/output_gt/gt_scores.json"

process_score_divide_na(qm_weights, real, output_gt_score_excel, output_gt_score_json)