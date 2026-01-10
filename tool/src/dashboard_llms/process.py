import os
import pandas as pd
import plotly.express as px
import numpy as np
from collections import defaultdict
import json
import argparse
from pathlib import Path

class XLSXProcessor:
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
    
    # def save_to_excel(self, output_file, json_path):
    #     # Carregar JSON
    #     with open(json_path, 'r') as file:
    #         data = json.load(file)

    #     # Lista das 16 práticas
    #     practices = [str(i) for i in range(1, 17)]
    #     rows = []

    #     # Apenas processar subpasta 'versions' de cada top-level
    #     for top_level_folder, subfolders in data.items():
    #         versions = subfolders.get("versions", {})
    #         for file_name, methods in versions.items():
    #             if file_name == "TPCWUtil.java":
    #                 pass
    #             else:
    #                 for method, details in methods.items():
    #                     file_name_clean = file_name.replace(".java", "")
    #                     entry = {
    #                         "parent_name": f"{top_level_folder}",
    #                         "FileName": file_name_clean,
    #                         "Method": method
    #                     }

    #                     if details.get("question_1", "").strip().lower() == "yes;":
    #                         # Todas as práticas são seguidas (1)
    #                         for p in practices:
    #                             entry[p] = "NA"
    #                     elif "question_2" in details:
    #                         # Algumas práticas em falta (0), restantes NA
    #                         missing = details["question_2"].replace(";", "").split(", ")
    #                         for p in practices:
    #                             entry[p] = 0 if p in missing else "NA"
    #                     else:
    #                         # Se não houver nenhuma das perguntas, marcar tudo como NA
    #                         for p in practices:
    #                             entry[p] = "NA"

    #                     rows.append(entry)

    #     # Criar DataFrame e exportar
    #     df = pd.DataFrame(rows)
    #     df.to_excel(output_file, index=False)

    #     # print("Exportado para only_versions_methods.xlsx")
    #     # print(df)

    def save_to_excel_individual_practice(self, json_path, output_file1, output_file2):
        # Carregar JSON
        with open(json_path, 'r') as file:
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
                if file_name == "TPCWUtil.java":
                    pass
                else:
                    for Method, details in methods.items():
                        file_name_clean = file_name.replace(".java", "")
                        entry = {
                            "Parent File": f"{top_level_folder}",
                            "FileName": file_name_clean,
                            "Method": Method
                        }

                        nan = {
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

                        if "applicable" in details:

                            nan_list = details["applicable"]

                            for p in practices:
                                if nan_list[int(p) - 1] == 0:
                                    nan[p] = 1
                                else:
                                    nan[p] = 0

                        rows.append(entry)
                        rows_nan.append(nan)

        # Criar DataFrame
        df = pd.DataFrame(rows)

        df_nan = pd.DataFrame(rows_nan)

        # print("Exportado para", output_file)
        df.replace(2, np.nan, inplace=True)
        # print(df)

        df.to_excel(output_file1, index=False)
        df_nan.to_excel(output_file2, index=False)


    def nan_compare(self, file1, file2, output_file, output_detailed, output_metrics):
        df_output = pd.read_excel(file1)
        df_real = pd.read_excel(file2)

        # Garantir colunas como string
        df_real.columns = df_real.columns.map(str)
        df_output.columns = df_output.columns.map(str)

        # id_cols = ['Parent File', 'FileName', 'Method']
        practice_cols = [col for col in df_real.columns if col.isdigit()]

        detailed = []

        for idx, row_real in df_real.iterrows():
            mask = (
                (df_output['Parent File'] == row_real['Parent File']) &
                (df_output['FileName'] == row_real['FileName']) &
                (df_output['Method'] == row_real['Method'])
            )
            row_output = df_output[mask]
            if row_output.empty:
                continue

            row_output = row_output.iloc[0]

            for p in practice_cols:
                real = row_real[p]
                expected = row_output[p]

                # Caso especial: ambos NaN → correto
                if pd.isna(real) and expected == 1:
                    correct = 1
                # Se real for 0 e expected também for 0 → correto
                else:
                    correct = 0

                
                detailed.append({
                    'Parent File': row_real['Parent File'],
                    'FileName': row_real['FileName'],
                    'Method': row_real['Method'],
                    'practice': p,
                    'real': real,
                    'expected': expected,
                    'correct': correct
                })

        df_detailed = pd.DataFrame(detailed)
        df_detailed.to_excel(output_file, index=False)

        # Métricas globais
        df = df_detailed

        TP = ((df["real"].isna()) & (df["expected"] == 1)).sum()
        FP = ((df["real"].notna()) & (df["expected"] == 1)).sum()
        FN = ((df["real"].isna()) & (df["expected"] == 0)).sum()
        TN = ((df["real"].notna()) & (df["expected"] == 0)).sum()
        

        total = TP + TN + FP + FN
        correct = TP + TN
        accuracy = (TP + TN) / total if total > 0 else float("nan")
        precision = TP / (TP + FP) if (TP + FP) > 0 else float("nan")
        recall = TP / (TP + FN) if (TP + FN) > 0 else float("nan")
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else float("nan")

        correct_na = (df_detailed['real'].isna()).sum()
        correct_not_na = (df_detailed['real'].notna()).sum()

        # print("🔹 Métricas de NA")
        # print(f"Correct:     {correct}/{total}")
        # print(f"Accuracy:  {accuracy:.2%}")
        # print(f"Precision: {precision:.2%}")
        # print(f"Recall:    {recall:.2%}")
        # print(f"F1 Score:  {f1:.2%}")
        # print(f"TP: {TP}/{correct_na}, FP: {FP}, FN: {FN}, TN: {TN}/{correct_not_na}")

        df_detailed.to_json(output_detailed, orient="records")

        metrics = []
        metrics.append({
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
                "TP": f"{int(TP)}",
                "FP": int(FP),
                "FN": int(FN),
                "TN": f"{int(TN)}",
                "correct": f"{correct}/{total}",
                "total": int(total)
            }
        )
        df_metrics = pd.DataFrame(metrics)
        df_metrics.to_json(output_metrics, orient="records")


    def compare_practice(self, file1, file2, output_file, output_json_geral_detailed, output_classe0_metrics, output_classe1_metrics):
        
        df_output = pd.read_excel(file1)
        df_real = pd.read_excel(file2)

        # Garantir colunas como string
        df_real.columns = df_real.columns.map(str)
        df_output.columns = df_output.columns.map(str)

        # id_cols = ['Parent File', 'FileName', 'Method']
        practice_cols = [col for col in df_real.columns if col.isdigit()]

        detailed = []

        for idx, row_real in df_real.iterrows():
            mask = (
                (df_output['Parent File'] == row_real['Parent File']) &
                (df_output['FileName'] == row_real['FileName']) &
                (df_output['Method'] == row_real['Method'])
            )
            row_output = df_output[mask]
            if row_output.empty:
                continue

            row_output = row_output.iloc[0]

            for p in practice_cols:
                real = row_real[p]
                expected = row_output[p]

                # Caso especial: ambos NaN → correto
                if pd.isna(real) and pd.isna(expected):
                    correct = 1
                # Se real for 0 e expected também for 0 → correto
                elif not pd.isna(real) and float(real) == 0.0 and not pd.isna(expected) and float(expected) == 0.0:
                    correct = 1
                elif not pd.isna(real) and float(real) == 1.0 and not pd.isna(expected) and float(expected) == 1.0:
                    correct = 1
                # Todos os outros casos → erro
                else:
                    correct = 0

                
                detailed.append({
                    'Parent File': row_real['Parent File'],
                    'FileName': row_real['FileName'],
                    'Method': row_real['Method'],
                    'practice': p,
                    'real': real,
                    'expected': expected,
                    'correct': correct
                })

        df_detailed = pd.DataFrame(detailed)
        df_detailed.to_excel(output_file, index=False)

        # Métricas globais

        # Filtrar apenas linhas válidas (onde real é 0 ou 1)
        valid = df_detailed

        
        TP_1 = ((valid["real"] == 1) & (valid["expected"] == 1)).sum()
        FP_1 = ((valid["real"] != 1) & (valid["expected"] == 1)).sum()
        FN_1 = ((valid["real"] == 1) & (valid["expected"] != 1)).sum()
        TN_1 = ((valid["real"] != 1) & (valid["expected"] != 1)).sum()

        # Para 0

        TP_0 = ((valid["real"] == 0) & (valid["expected"] == 0)).sum()
        FP_0 = ((valid["real"] != 0) & (valid["expected"] == 0)).sum()
        FN_0 = ((valid["real"] == 0) & (valid["expected"] != 0)).sum()
        TN_0 = ((valid["real"] != 0) & (valid["expected"] != 0)).sum()

        # Classe 0
        acc_0, prec_0, rec_0, f1_0, total_0, correct_0 = self.compute_metrics(TP_0, TN_0, FP_0, FN_0)

        # Classe 1
        acc_1, prec_1, rec_1, f1_1, total_1, correct_1 = self.compute_metrics(TP_1, TN_1, FP_1, FN_1)

        # Mostrar resultados
        # total_real_0 = (df_detailed["real"] == 0).sum()
        # total_expected_0 = (df_detailed["expected"] == 0).sum()
        # acc_0 = total_expected_0 / total_real_0 if total_real_0 > 0 else float("nan")

        correct_0_total = (df_detailed['real'] == 0).sum()
        correct_1_total = (df_detailed['real'] == 1).sum()
        correct_total_dif_1 = (df_detailed['real'] != 1).sum()
        correct_total_dif_0 = (df_detailed['real'] != 0).sum()

        # print("🔹 Classe 0 (prática não seguida)")
        # print(f"Correct:     {correct_0}/{total_0}")
        # print(f"Accuracy:  {acc_0:.2%}")
        # print(f"Precision: {prec_0:.2%}")
        # print(f"Recall:    {rec_0:.2%}")
        # print(f"F1 Score:  {f1_0:.2%}")
        # print(f"TP: {TP_0}/{correct_0_total}, FP: {FP_0}, FN: {FN_0}, TN: {TN_0}/{correct_total_dif_0}")

        # print("\n🔹 Classe 1 (prática seguida)")
        # print(f"Correct:     {correct_1}/{total_1}")
        # print(f"Accuracy:  {acc_1:.2%}")
        # print(f"Precision: {prec_1:.2%}")
        # print(f"Recall:    {rec_1:.2%}")
        # print(f"F1 Score:  {f1_1:.2%}")
        # print(f"TP: {TP_1}/{correct_1_total}, FP: {FP_1}, FN: {FN_1}, TN: {TN_1}/{correct_total_dif_1}")


        df_detailed.to_json(output_json_geral_detailed, orient="records")
        
        metrics_0 = []

        metrics_0.append({
                "accuracy": round(acc_0, 4),
                "precision": round(prec_0, 4),
                "recall": round(rec_0, 4),
                "f1_score": round(f1_0, 4),
                "TP": f"{int(TP_0)}",
                "FP": int(FP_0),
                "FN": int(FN_0),
                "TN": f"{int(TN_0)}",
                "correct": f"{correct_0}/{total_0}",
                "total": int(total_0)
            }
        )

        metrics_1 = []

        metrics_1.append({
                "accuracy": round(acc_1, 4),
                "precision": round(prec_1, 4),
                "recall": round(rec_1, 4),
                "f1_score": round(f1_1, 4),
                "TP": f"{int(TP_1)}",
                "FP": int(FP_1),
                "FN": int(FN_1),
                "TN": f"{int(TN_1)}",
                "correct": f"{correct_1}/{total_1}",
                "total": int(total_1)
            }
        )

        df_metrics_0 = pd.DataFrame(metrics_0)
        df_metrics_0.to_json(output_classe0_metrics, orient="records")

        df_metrics_1 = pd.DataFrame(metrics_1)
        df_metrics_1.to_json(output_classe1_metrics, orient="records")


    def individual_practices_nan_only(self, file1, output):

        df_detailed = pd.read_excel(file1)

        practice_metrics_na = []


        fn_lista_na = []
        fp_lista_na = []

        for p in sorted(df_detailed['practice'].unique(), key=lambda x: int(x)):
            subset = df_detailed[df_detailed['practice'] == p]

            fn_rows_na = subset[(subset["expected"] == 0) & (subset["real"].isna())][["Parent File", "FileName", "Method", "real", "expected"]]
            fp_rows_na = subset[(subset["expected"] == 1) & (subset["real"].notna())][["Parent File", "FileName", "Method", "real", "expected"]]

            fp_rows_na = fp_rows_na.copy()
            fn_rows_na = fn_rows_na.copy()
            fp_rows_na["practice"] = p
            fn_rows_na["practice"] = p

            # Converter em dicts e adicionar à lista
            fp_lista_na.extend(fp_rows_na.to_dict(orient='records'))
            fn_lista_na.extend(fn_rows_na.to_dict(orient='records'))

            # Métricas para classe NA
            TP = (subset["real"].isna() & subset["expected"] == 1).sum()       # NA == NA
            FN = (subset["real"].isna() & (subset["expected"] == 0)).sum()       # NA != NA (esperava NA, veio 0)
            FP = ((subset["real"].notna()) & subset["expected"] == 1).sum()       # 0 == NA (esperava 0, veio NA)
            TN = ((subset["real"].notna()) & (subset["expected"] == 0)).sum()       # 0 == 0

            acc, prec, rec, f1, total, correct = self.compute_metrics(TP, TN, FP, FN)

            real = (subset["real"].isna()).sum()
            correct = (subset["expected"] == 1).sum()
            practice_metrics_na.append({
                "practice": p,
                "total": total,
                "correct": correct,
                "real": real,
                "accuracy": round(acc, 4),
                "precision": round(prec, 4) if prec != 0 else "-",
                "recall": round(rec, 4) if rec != 0 else "-",
                "f1_score": round(f1, 4) if f1 != 0 else "-",
                "TP": TP, "FP": FP, "FN": FN, "TN": TN
            })

        df_metrics_na = pd.DataFrame(practice_metrics_na)

        # Mostrar resultados
        # print("Métricas da Classe NA (para NaN e 0):")
        # print(df_metrics_na.to_string(index=False))

        df_metrics_na.to_json(output, orient="records")

        df_fp_na = pd.DataFrame(fp_lista_na)
        df_fn_na = pd.DataFrame(fn_lista_na)

        # df_fp_na.to_excel(f"tool/src/dashboard_llms/output/{exp}_fp_individual_NA_3.xlsx", index=False)
        # df_fn_na.to_excel(f"tool/src/dashboard_llms/output/{exp}_fn_individual_NA_3.xlsx", index=False)


    def individual_practices(self, file1, output_classe0_individual_metrics, output_classe1_individual_metrics, output_geral_individual_metrics, output_practiceMetrics, output_matrix):

        df_detailed = pd.read_excel(file1)

        practice_metrics_0 = []
        practice_metrics_1 = []
        practice_geral = []
        practiceMetrics = []
        practice_matrix = []

        fn_lista_0 = []
        fp_lista_0 = []
        fn_lista_1 = []
        fp_lista_1 = []

        for p in sorted(df_detailed['practice'].unique(), key=lambda x: int(x)):
            subset = df_detailed[df_detailed['practice'] == p]

            # subset_0 = subset[subset["real"] == 0]
            TP_0 = ((subset["expected"] == 0) & (subset["real"] == 0)).sum()
            FP_0 = ((subset["expected"] == 0) & (subset["real"] != 0)).sum()
            FN_0 = ((subset["expected"] != 0) & (subset["real"] == 0)).sum()
            TN_0 = ((subset["expected"] != 0) & (subset["real"] != 0)).sum()
            
            fn_rows_0 = subset[(subset["expected"] != 0) & (subset["real"] == 0)][["Parent File", "FileName", "Method", "real", "expected"]]
            fp_rows_0 = subset[(subset["expected"] == 0) & (subset["real"] != 0)][["Parent File", "FileName", "Method", "real", "expected"]]

            fp_rows_0 = fp_rows_0.copy()
            fn_rows_0 = fn_rows_0.copy()
            fp_rows_0["practice"] = p
            fn_rows_0["practice"] = p

            # Converter em dicts e adicionar à lista
            fp_lista_0.extend(fp_rows_0.to_dict(orient='records'))
            fn_lista_0.extend(fn_rows_0.to_dict(orient='records'))

            acc_0, prec_0, rec_0, f1_0, total_0, correct_0 = self.compute_metrics(TP_0, TN_0, FP_0, FN_0)
            
            total_real_0 = (subset["real"] == 0).sum() 
            expected_0 = (subset["expected"] == 0).sum()

            practice_metrics_0.append({
                "practice": p,
                "total": total_0,
                "llm identify": expected_0,
                "correct": correct_0,
                "real": total_real_0,
                "accuracy": round(acc_0, 4),
                "precision": round(prec_0, 4) if prec_0 != 0 else "-",
                "recall": round(rec_0, 4) if rec_0 != 0 else "-",
                "f1_score": round(f1_0, 4) if f1_0 != 0 else "-",
                "TP": TP_0, "FP": FP_0, "FN": FN_0, "TN": TN_0,
            })

            # Classe 1
            # subset_1 = subset[subset["real"] == 1]
            TP_1 = ((subset["expected"] == 1) & (subset["real"] == 1)).sum()
            FP_1 = ((subset["expected"] == 1) & (subset["real"] != 1)).sum()
            FN_1 = ((subset["expected"] != 1) & (subset["real"] == 1)).sum()
            TN_1 = ((subset["expected"] != 1) & (subset["real"] != 1)).sum()

            fn_rows_1 = subset[(subset["expected"] != 1) & (subset["real"] == 1)][["Parent File", "FileName", "Method", "real", "expected"]]
            fp_rows_1 = subset[(subset["expected"] == 1) & (subset["real"] != 1)][["Parent File", "FileName", "Method", "real", "expected"]]

            fp_rows_1 = fp_rows_1.copy()
            fn_rows_1 = fn_rows_1.copy()
            fp_rows_1["practice"] = p
            fn_rows_1["practice"] = p

            fp_lista_1.extend(fp_rows_1.to_dict(orient='records'))
            fn_lista_1.extend(fn_rows_1.to_dict(orient='records'))

            acc_1, prec_1, rec_1, f1_1, total_1, correct_1 = self.compute_metrics(TP_1, TN_1, FP_1, FN_1)

            total_real_1 = (subset["real"] == 1).sum()
            expected_1 = (subset["expected"] == 1).sum()

            practice_metrics_1.append({
                "practice": p,
                "total": total_1,
                "llm identify": expected_1,
                "correct": correct_1,
                "real": total_real_1,
                "accuracy": round(acc_1, 4),
                "precision": round(prec_1, 4) if prec_1 != 0 else "-",
                "recall": round(rec_1, 4) if rec_1 != 0 else "-",
                "f1_score": round(f1_1, 4) if f1_1 != 0 else "-",
                "TP": TP_1, "FP": FP_1, "FN": FN_1, "TN": TN_1
            })

            # Métricas gerais
            TP = ((subset["expected"] == 1) & (subset["real"] == 1)).sum()
            FP = ((subset["expected"] == 1) & (subset["real"] != 1)).sum()
            FN = ((subset["expected"] != 1) & (subset["real"] == 1)).sum()
            TN = ((subset["expected"] != 1) & (subset["real"] != 1)).sum()

            acc, prec, rec, f1, total, correct = self.compute_metrics(TP, TN, FP, FN)

            total_real_na = (subset["real"].isna()).sum()
            expected_na = (subset["expected"].isna()).sum()

            correct_na = ((subset["real"].isna()) & (subset["expected"].isna())).sum()  # NA == 1

            # subset_na = subset[subset["real"].isna()]
            TP_na = ((subset["expected"].isna()) & (subset["real"].isna())).sum()
            FP_na = ((subset["expected"].isna()) & (subset["real"].notna())).sum()
            FN_na = ((subset["expected"].notna()) & (subset["real"].isna())).sum()
            TN_na = ((subset["expected"].notna()) & (subset["real"].notna())).sum()

            # # Métricas para classe NA
            # TP_na = (subset["real"].isna() & subset["expected"].isna()).sum()       # NA == NA
            # FN_na = (subset["real"].isna() & (subset["expected"].notna())).sum()       # NA != NA (esperava NA, veio 0)
            # FP_na = ((subset["real"].notna()) & subset["expected"].isna()).sum()       # 0 == NA (esperava 0, veio NA)
            # TN_na = ((subset["real"].notna()) & (subset["expected"].notna())).sum()       # 0 == 0

            # acc_na, prec_na, rec_na, f1_na, total_na, correct_na = self.compute_metrics(TP_na, TN_na, FP_na, FN_na)

            # if p == 9:
            #     print(subset_na)
            #     print("practice:", p)
            #     print("FP_na: ", FP_na)
            #     print("FN_na: ", FN_na)

            practice_geral.append({
                "practice": p,
                "correct_na": TP_na,
                "incorrect_na": FP_na + FN_na,
                "real_na" : total_real_na,
                "correct_0": TP_0,
                "incorrect_0": FP_0 + FN_0,
                "real_0" : total_real_0,
                "correct_1": TP_1,
                "incorrect_1": FP_1 + FN_1,
                "real_1" : total_real_1,
            })

            practice_matrix.append({
                "practice": p,
                "TP_na": TP_na,
                "FP_na": FP_na,
                "FN_na": FN_na,
                "TN_na": TN_na,
                "real_na" : total_real_na,
                "TP_0": TP_0,
                "FP_0": FP_0,
                "FN_0": FN_0,
                "TN_0": TN_0,
                "real_0" : total_real_0,
                "TP_1": TP_1,
                "FP_1": FP_1,
                "FN_1": FN_1,
                "TN_1": TN_1,
                "real_1" : total_real_1,
            })

            practiceMetrics.append({
                "practice": p,
                "total": total,
                "correct": correct,
                "accuracy": round(acc, 4),
                "precision": round(prec, 4) if prec != 0 else "-",
                "recall": round(rec, 4) if rec != 0 else "-",
                "f1_score": round(f1, 4) if f1 != 0 else "-",
                "TP": TP, "FP": FP, "FN": FN, "TN": TN
            })

        df_metrics_0 = pd.DataFrame(practice_metrics_0)
        df_metrics_1 = pd.DataFrame(practice_metrics_1)
        df_metrics_geral = pd.DataFrame(practice_geral)
        df_practiceMetrics = pd.DataFrame(practiceMetrics)
        df_practiceMatrix = pd.DataFrame(practice_matrix)

        # Mostrar resultados
        # print("Métricas da Classe 0:")
        # print(df_metrics_0.to_string(index=False))
        # print("Métricas da Classe 1:")
        # print(df_metrics_1.to_string(index=False))
        # print("Métricas Gerais:")
        # print(df_metrics_geral.to_string(index=False))

        # print(len(fp_lista_0))
        # print(len(fn_lista_0))
        # print(len(fp_lista_1))
        # print(len(fn_lista_1))


        # df_fp_0 = pd.DataFrame(fp_lista_0)
        # df_fn_0 = pd.DataFrame(fn_lista_0)
        # df_fp_1 = pd.DataFrame(fp_lista_1)
        # df_fn_1 = pd.DataFrame(fn_lista_1)

        # print("\nFalse Positives (Classe 0):")
        # print(df_fp_0.to_string(index=False))

        # print("\nFalse Negatives (Classe 0):")
        # print(df_fn_0.to_string(index=False))

        # print("\nFalse Positives (Classe 1):")
        # print(df_fp_1.to_string(index=False))

        # print("\nFalse Negatives (Classe 1):")
        # print(df_fn_1.to_string(index=False))

        # Exportar resultados para JSON
        df_metrics_0.to_json(output_classe0_individual_metrics, orient="records")
        df_metrics_1.to_json(output_classe1_individual_metrics, orient="records")
        df_metrics_geral.to_json(output_geral_individual_metrics, orient="records")
        df_practiceMetrics.to_json(output_practiceMetrics, orient="records")
        df_practiceMatrix.to_json(output_matrix, orient="records")


        # df_fp_0.to_excel(f"tool/src/dashboard_llms/output/{exp}_fp_individual_0_3.xlsx", index=False)
        # df_fn_0.to_excel(f"tool/src/dashboard_llms/output/{exp}_fn_individual_0_3.xlsx", index=False)
        # df_fp_1.to_excel(f"tool/src/dashboard_llms/output/{exp}_fp_individual_1_3.xlsx", index=False)
        # df_fn_1.to_excel(f"tool/src/dashboard_llms/output/{exp}_fn_individual_1_3.xlsx", index=False)

        # df_detailed.to_json(f"tool/src/dashboard_llms/output/{exp}{version}_detailed_individual.json", orient="records")
        # df_metrics.to_json(f"tool/src/dashboard_llms/output/{exp}{version}_metrics_individual.json", orient="records")


    def category_metrics(self, file1, file2, weights_json_path, output_category_classe1, output_category_classe0, output_category_classe_na, output_category_detailed, output_category_detailed_excel):

        # Carregar dataframes
        df_output = pd.read_excel(file1)
        df_real = pd.read_excel(file2)

        df_real.columns = df_real.columns.map(str)
        df_output.columns = df_output.columns.map(str)

        # id_cols = ['Parent File', 'FileName', 'Method']
        practice_cols = [col for col in df_real.columns if col.isdigit()]

        # Carregar JSON de pesos
        with open(weights_json_path, 'r') as f:
            weights = json.load(f)

        # Mapear práticas para subcategorias
        subcategory_mapping = {}
        main_category = weights["Input Validation"]["children"]
        for subcat_name, subcat_data in main_category.items():
            for practice, _ in subcat_data["children"].items():
                subcategory_mapping[practice] = subcat_name

        detailed = []
        for _, row_real in df_real.iterrows():
            mask = (
                (df_output['Parent File'] == row_real['Parent File']) &
                (df_output['FileName'] == row_real['FileName']) &
                (df_output['Method'] == row_real['Method'])
            )
            row_output = df_output[mask]
            if row_output.empty:
                continue
            row_output = row_output.iloc[0]

            for p in practice_cols:
                subcat = subcategory_mapping.get(p)
                if not subcat:
                    continue

                real = row_real[p]
                expected = row_output[p]

                if pd.isna(real) and pd.isna(expected):
                    correct = 1
                elif not pd.isna(real) and float(real) == 0.0 and not pd.isna(expected) and float(expected) == 0.0:
                    correct = 1
                elif not pd.isna(real) and float(real) == 1.0 and pd.isna(expected):
                    correct = 1
                else:
                    correct = 0

                detailed.append({
                    'subcategory': subcat,
                    'practice': p,
                    'real': real,
                    'expected': expected,
                    'correct': correct
                })

        df_detailed = pd.DataFrame(detailed)
        df_detailed.to_excel(output_category_detailed_excel, index=False)
        df_detailed.to_json(output_category_detailed, orient="records")

        # ============================
        # ✅ MÉTRICAS POR SUBCATEGORIA
        # ============================

        subcat_metrics_1 = []
        subcat_metrics_0 = []
        subcat_metrics_na = []

        for subcat in sorted(df_detailed['subcategory'].unique()):
            subset = df_detailed[df_detailed['subcategory'] == subcat]

            # Classe 1
            # subset_1 = subset[subset["expected"] == 1]
            # subset_1 = subset

            TP_1 = ((subset["expected"] == 1) & (subset["real"] == 1)).sum()
            FP_1 = ((subset["expected"] == 1) & (subset["real"] != 1)).sum()
            FN_1 = ((subset["expected"] != 1) & (subset["real"] == 1)).sum()
            TN_1 = ((subset["expected"] != 1) & (subset["real"] != 1)).sum()

            accuracy_1, precision_1, recall_1, f1_1, total_1, correct_1 = self.compute_metrics(TP_1, TN_1, FP_1, FN_1)

            practices = sorted(subset["practice"].unique().tolist())

            subcat_metrics_1.append({
                "subcategory": subcat,
                "practices": ", ".join(map(str, practices)) if practices else "-",
                "total": total_1,
                "correct": correct_1,
                "incorrect": total_1 - correct_1,
                "accuracy": round(accuracy_1, 4),
                "precision": round(precision_1, 4) if precision_1 else "-",
                "recall": round(recall_1, 4) if recall_1 else "-",
                "f1_score": round(f1_1, 4) if f1_1 else "-",
                # "TP": TP_1,
                # "FP": FP_1,
                # "FN": FN_1,
                # "TN": TN_1
            })

            # print(subcat_metrics_1)

            # Classe 0

            # subset_0 = subset[subset["expected"] == 0]
            # subset_0 = subset
            TP_0 = ((subset["expected"] == 0) & (subset["real"] == 0)).sum()
            FP_0 = ((subset["expected"] == 0) & (subset["real"] != 0)).sum()
            FN_0 = ((subset["expected"] != 0) & (subset["real"] == 0)).sum()
            TN_0 = ((subset["expected"] != 0) & (subset["real"] != 0)).sum()

            accuracy_0, precision_0, recall_0, f1_0, total_0, correct_0 = self.compute_metrics(TP_0, TN_0, FP_0, FN_0)

            subcat_metrics_0.append({
                "subcategory": subcat,
                "practices": ", ".join(map(str, practices)) if practices else "-",
                "total": total_0,
                "correct": correct_0,
                "incorrect": total_0 - correct_0,
                "accuracy": round(accuracy_0, 4),
                "precision": round(precision_0, 4) if precision_0 else "-",
                "recall": round(recall_0, 4) if recall_0 else "-",
                "f1_score": round(f1_0, 4) if f1_0 else "-",
                # "TP": TP_0,
                # "FP": FP_0,
                # "FN": FN_0,
                # "TN": TN_0
            })

            # print(subcat_metrics_0)

            # Classe NA

            # subset_na = subset[subset["expected"].isna()]
            # subset_na = subset
            TP_na = ((subset["expected"].isna()) & (subset["real"].isna())).sum()
            FP_na = ((subset["expected"].isna()) & (subset["real"].notna())).sum()
            FN_na = ((subset["expected"].notna()) & (subset["real"].isna())).sum()
            TN_na = ((subset["expected"].notna()) & (subset["real"].notna())).sum()



            accuracy_na, precision_na, recall_na, f1_na, total_na, correct_na = self.compute_metrics(TP_na, TN_na, FP_na, FN_na)

            subcat_metrics_na.append({
                "subcategory": subcat,
                "practices": ", ".join(map(str, practices)) if practices else "-",
                "total": total_na,
                "correct": correct_na,
                "incorrect": total_na - correct_na,
                "accuracy": round(accuracy_na, 4),
                "precision": round(precision_na, 4) if precision_na else "-",
                "recall": round(recall_na, 4) if recall_na else "-",
                "f1_score": round(f1_na, 4) if f1_na else "-",
                # "TP": TP_na,
                # "FP": FP_na,
                # "FN": FN_na,
                # "TN": TN_na
            })

            # print(subcat_metrics_na)


        # print(subcat_metrics_1)
        df_metrics_1 = pd.DataFrame(subcat_metrics_1)
        # print(df_metrics_1.to_string(index=False))

        # print(subcat_metrics_0)
        df_metrics_0 = pd.DataFrame(subcat_metrics_0)
        # print(df_metrics_0.to_string(index=False))

        # print(subcat_metrics_na)
        df_metrics_na = pd.DataFrame(subcat_metrics_na)
        # print(df_metrics_na.to_string(index=False))

        df_metrics_0.to_json(output_category_classe0, orient="records")
        df_metrics_1.to_json(output_category_classe1, orient="records")
        df_metrics_na.to_json(output_category_classe_na, orient="records")

        # df_detailed.to_json(f"tool/src/dashboard_llms/output/{exp}{version}_detailed_categories.json", orient="records")
        # df_metrics.to_json(f"tool/src/dashboard_llms/output/{exp}{version}_metrics_categories.json", orient="records")


    def compute_metrics(self, tp, tn, fp, fn):
        total = tp + tn + fp + fn
        correct = tp + tn
        accuracy = (tp + tn) / total if total > 0 else float("nan")
        precision = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
        recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else float("nan")
        return accuracy, precision, recall, f1, total, correct
    
    
    def process_score_divide_na(self, weights_path, expected_excel, output_score, output_json):

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


    def process_score(self, weights_path, expected_excel, output_score, output_json):

        # Carregar dados
        df = pd.read_excel(expected_excel)

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
            for p in practices:
                val = row.get(p)
                if pd.isna(val) or val == "NA" or val == 1:
                    total_missing += weights.get(p, 0.0)
            
            return min(1.0, max(0.0, total_missing))  # Clamp entre 0 e 1

        df["score"] = df.apply(calc_score, axis=1)

        # Guardar Excel atualizado
        df.to_excel(output_score, index=False)
        # print(f"Exportado para {output_file}")
        # print(df)

        df.to_json(output_json, orient='records')


    def score_comparison_table(self, qm_score, paper_score_path, output_comparison, groundtruth_path, output_all, output_consolidated_json, gt_score_qm_path=None):
        df_qm = pd.read_excel(qm_score)

        with open(paper_score_path, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)

        paper_rows = []
        for main_key, versions in paper_data.items():
            for vx, methods in versions.items():
                for method, score in methods.items():
                    if method != "final":
                        filename = f"{main_key}_{vx}"
                        paper_rows.append({
                            "FileName": filename,
                            "Method": method,
                            "score_paper": score
                        })
        df_paper = pd.DataFrame(paper_rows)

        df_qm.columns = [str(c).strip() for c in df_qm.columns]

        if "score" in df_qm.columns:
            df_qm.rename(columns={"score": "score_qm"}, inplace=True)

        df_merged = df_qm

        if gt_score_qm_path:
            df_gt_qm = pd.read_excel(gt_score_qm_path)
            df_gt_qm.columns = [str(c).strip() for c in df_gt_qm.columns]

            if "score" in df_gt_qm.columns:
                df_gt_qm.rename(columns={"score": "score_groundtruth_qm"}, inplace=True)

            df_merged = pd.merge(
                df_merged,
                df_gt_qm[["Parent File", "FileName", "Method", "score_groundtruth_qm"]],
                on=["Parent File", "FileName", "Method"],
                how="left"
            )

        df_final = pd.merge(
            df_merged,
            df_paper,
            on=["FileName", "Method"],
            how="left"
        )

        df_final.to_json(output_all, orient="records")
        self.good_score_table(output_all, output_consolidated_json, groundtruth_path)

        cols_to_keep = [c for c in ["Parent File", "FileName", "Method", "score_qm", "score_paper", "score_groundtruth_qm"] if c in df_final.columns]
        df_final = df_final[cols_to_keep]

        df_final.to_excel(output_comparison, index=False)
        df_final.to_json(output_comparison.replace("xlsx", "json"), orient="records", indent=2)

    def good_score_table(self, output_all, output_consolidated_json, groundtruth_path):
        
        # --- Carregar ficheiros ---
        json_all = json.load(open(output_all, encoding="utf-8"))
        gt_data = json.load(open(groundtruth_path, encoding="utf-8"))

        consolidated = defaultdict(dict)

        # --- Converter groundtruth em estrutura rápida para lookup ---
        gt_lookup = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for row in gt_data:
            filename = row["FileName"]
            method = row["Method"]
            practice = int(row["practice"])
            gt_lookup[filename][method][f"Practice {practice}"] = row["real"]

        # --- Construir consolidado ---
        for row in json_all:
            filename_full = row["FileName"]  # ex: NewCustomer_Vx0
            if "_" in filename_full:
                base, version = filename_full.rsplit("_", 1)
            else:
                base, version = filename_full, "v0"

            score_qm = row.get("score_qm", None)
            score_paper = row.get("score_paper", None)
            score_groundtruth_qm = row.get("score_groundtruth_qm", None)

            practices_qm = {f"Practice {i}": row.get(str(i), None) for i in range(1, 17)}

            if version not in consolidated[base]:
                consolidated[base][version] = {
                    "score_qm": {},
                    "score_paper": {},
                    "score_groundtruth_qm": {},
                    "practices": {}
                }

            method = row["Method"]
            consolidated[base][version]["score_qm"][method] = score_qm
            consolidated[base][version]["score_paper"][method] = score_paper
            consolidated[base][version]["score_groundtruth_qm"][method] = score_groundtruth_qm

            gt_practices = gt_lookup.get(filename_full, {}).get(method, {})

            consolidated[base][version]["practices"][method] = {
                "qm": practices_qm,
                "groundtruth": gt_practices
            }

        # --- Guardar JSON consolidado ---
        with open(output_consolidated_json, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":

    prompt_choices = {
        1: "prompt_1",
        2: "prompt_2",
        3: "prompt_3",
        4: "prompt_4",
        5: "prompt_5",
        6: "universal"
        }

    version_following = {
        1: "a",
        2: "b"
    }

    version_applicability = {
        1: "a",
        2: "b"
    }

    llm_paths = {
        1: "gpt-3.5-turbo",
        2: "gpt-4o-mini",
        3: "gpt-4.1",
        4: "gpt-4.1-mini",
        5: "gemini-2.5-flash"
    }

    # parser = argparse.ArgumentParser(description="Run LLM Individual Practices Evaluation")
    # parser.add_argument("--llm", type=int, choices=llm_paths.keys(), required=True, help="LLM model to use")
    # parser.add_argument("--p", type=int, choices=prompt_choices.keys(), required=True, help="Prompt version")
    # parser.add_argument("--v1", type=int, choices=version_applicability.keys(), required=True, help="Prompt applicability version")
    # parser.add_argument("--v2", type=int, choices=version_following.keys(), required=True, help="Prompt sub-version")

    # args = parser.parse_args()

    processor = XLSXProcessor('tool/src/dashboard_llms/input')
    

    # GERAL Inputs and Outputs
    # GERAL Inputs
    real = "tool/src/dashboard_llms/input/Missing Practices in WsvdBench_GroundTruth_V3.xlsx"
    manual_weights = "tool/src/dashboard_llms/input/manual_weights.json"
    qm_weights = "tool/src/dashboard_llms/output_weights/qm_weights.json"
    paper_score = "tool/src/dashboard_llms/input/score_cristiano_paper.json"

    # --- Calculate Ground Truth Scores ---
    base_output = "tool/src/dashboard_llms/output"
    gt_score_path = f"{base_output}/groundtruth_scores"
    os.makedirs(gt_score_path, exist_ok=True)

    gt_score_qm_excel = f"{gt_score_path}/gt_score_qm.xlsx"
    gt_score_qm_json = f"{gt_score_path}/gt_score_qm.json"
    processor.process_score_divide_na(qm_weights, real, gt_score_qm_excel, gt_score_qm_json)

    # gt_score_manual_excel = f"{gt_score_path}/gt_score_manual.xlsx"
    # gt_score_manual_json = f"{gt_score_path}/gt_score_manual.json"
    # processor.process_score(manual_weights, real, gt_score_manual_excel, gt_score_manual_json)

    input_prompt_35_1 = [1, 1, "tool/src/test_results/individual_practices/gpt-3.5-turbo/prompt_1_a/scenario 1_3_5.json"]
    input_prompt_35_2 = [1, 2, "tool/src/test_results/individual_practices/gpt-3.5-turbo/prompt_2_a/scenario 2_3_5.json"]
    input_prompt_35_4 = [1, 4, "tool/src/test_results/individual_practices/gpt-3.5-turbo/prompt_4_a/scenario 4_3_5.json"]
    input_prompt_35_5 = [1, 5, "tool/src/test_results/individual_practices/gpt-3.5-turbo/prompt_5_a/scenario 5_3_5.json"]
    input_prompt_35_6 = [1, 6, "tool/src/test_results/individual_practices/gpt-3.5-turbo/universal/scenario 6_3_5.json"]

    input_prompt_4o_1 = [2, 1, "tool/src/test_results/individual_practices/gpt-4o-mini/prompt_1_a/scenario 1_4o.json"]
    input_prompt_4o_2 = [2, 2, "tool/src/test_results/individual_practices/gpt-4o-mini/prompt_2_a/scenario 2_4o.json"]
    input_prompt_4o_4 = [2, 4, "tool/src/test_results/individual_practices/gpt-4o-mini/prompt_4_a/scenario 4_4o.json"]
    input_prompt_4o_5 = [2, 5, "tool/src/test_results/individual_practices/gpt-4o-mini/prompt_5_a/scenario 5_4o.json"]
    input_prompt_4o_6 = [2, 6, "tool/src/test_results/individual_practices/gpt-4o-mini/universal/scenario 6_4o.json"]

    input_prompt_41_1 = [3, 1, "tool/src/test_results/individual_practices/gpt-4.1/prompt_1_a/scenario 1_4_1.json"]
    input_prompt_41_2 = [3, 2, "tool/src/test_results/individual_practices/gpt-4.1/prompt_2_a/scenario 2_4_1.json"]
    input_prompt_41_4 = [3, 4, "tool/src/test_results/individual_practices/gpt-4.1/prompt_4_a/scenario 4_4_1.json"]
    input_prompt_41_5 = [3, 5, "tool/src/test_results/individual_practices/gpt-4.1/prompt_5_a/scenario 5_4_1.json"]
    input_prompt_41_6 = [3, 6, "tool/src/test_results/individual_practices/gpt-4.1/universal/scenario 6_4_1.json"]

    input_prompt_41_mini_1 = [4, 1, "tool/src/test_results/individual_practices/gpt-4.1-mini/prompt_1_a/scenario 1_4_1_mini.json"]
    input_prompt_41_mini_2 = [4, 2, "tool/src/test_results/individual_practices/gpt-4.1-mini/prompt_2_a/scenario 2_4_1_mini.json"]
    input_prompt_41_mini_4 = [4, 4, "tool/src/test_results/individual_practices/gpt-4.1-mini/prompt_4_a/scenario 4_4_1_mini.json"]
    input_prompt_41_mini_5 = [4, 5, "tool/src/test_results/individual_practices/gpt-4.1-mini/prompt_5_a/scenario 5_4_1_mini.json"]
    input_prompt_41_mini_6 = [4, 6, "tool/src/test_results/individual_practices/gpt-4.1-mini/universal/scenario 6_4_1_mini.json"]

    input_vertex_ai_1 = [5, 1, "tool/src/test_results/individual_practices/gemini-2.5-flash/prompt_1_a/scenario 1_2_5.json"]
    input_vertex_ai_2 = [5, 2, "tool/src/test_results/individual_practices/gemini-2.5-flash/prompt_2_a/scenario 2_2_5.json"]
    # input_vertex_ai_4 = [5, 4, "tool/src/test_results/individual_practices/gpt-4.1-mini/prompt_4_a/scenario 4_4_1_mini.json"]
    input_vertex_ai_5 = [5, 5, "tool/src/test_results/individual_practices/gemini-2.5-flash/prompt_5_a/scenario 5_2_5.json"]

    # lista = [input_prompt_35_6]

    lista = [input_prompt_35_1, input_prompt_35_2, input_prompt_35_4, input_prompt_35_5, input_prompt_35_6,
            input_prompt_4o_1, input_prompt_4o_2, input_prompt_4o_4, input_prompt_4o_5, input_prompt_4o_6,
            input_prompt_41_1, input_prompt_41_2, input_prompt_41_4, input_prompt_41_5, input_prompt_41_6,
            input_prompt_41_mini_1, input_prompt_41_mini_2, input_prompt_41_mini_4, input_prompt_41_mini_5, input_prompt_41_mini_6,
            input_vertex_ai_1, input_vertex_ai_2, input_vertex_ai_5]

    # lista = [input_vertex_ai_1, input_vertex_ai_2, input_vertex_ai_5]

    
    for i in lista:
        llm = i[0]
        prompt = i[1]
        input_prompt = i[2]
        version = 1   # Sempre a

        print(f"\n\n🚀 Processando LLM {llm_paths.get(llm)} com {prompt_choices.get(prompt)} versão {version_following.get(version)}\n")

        # Bases para não repetir
        base_output = "tool/src/dashboard_llms/output"
        base_excel = "tool/src/dashboard_llms/output_excels"

        llm = llm_paths.get(llm, "unknown")
        prompt = prompt_choices.get(prompt, "prompt_1")
        version = version_following.get(version, "a")

        prompt_tag = f"{prompt}_{version}_{llm.split('-')[1]}"   # → prompt_5_a_3.5
        base_prompt = f"{base_output}/{prompt}/{llm}"
        os.makedirs(base_prompt, exist_ok=True)

        # Outputs Excel principais
        output_prompt_excel = f"{base_excel}/{prompt}_{version}_{llm.split('-')[1]}.xlsx"
        output_prompt_excel_na = f"{base_excel}/{prompt}_{version}_{llm.split('-')[1]}_na.xlsx"

        # Classe NA
        output_excel_nan_detailed = f"{base_prompt}/classe NA/excel_na_detailed.xlsx"
        output_json_nan_detailed = f"{base_prompt}/classe NA/json_na_detailed.xlsx"
        output_json_nan_metrics = f"{base_prompt}/classe NA/json_na_metrics.json"
        output_json_nan_individual_metrics = f"{base_prompt}/classe NA/json_na_individual_metrics.json"

        # Geral
        output_geral_metrics = f"{base_prompt}/geral/geral_detailed.json"
        output_geral_individual_metrics = f"{base_prompt}/geral/geral_individual_metrics.json"
        output_geral_detailed = f"{base_prompt}/geral/geral_detailed.xlsx"
        output_practiceMetrics = f"{base_prompt}/geral/practice_metrics.json"

        output_matrix = f"{base_prompt}/geral/matrix.json"

        # Classe 0
        output_classe0_metrics = f"{base_prompt}/classe 0/classe0_metrics.json"
        output_classe0_individual_metrics = f"{base_prompt}/classe 0/classe0_individual_metrics.json"

        # Classe 1
        output_classe1_metrics = f"{base_prompt}/classe 1/classe1_metrics.json"
        output_classe1_individual_metrics = f"{base_prompt}/classe 1/classe1_individual_metrics.json"

        # Categoria
        output_category_metrics_classe1 = f"{base_prompt}/category/category_classe1.json"
        output_category_metrics_classe0 = f"{base_prompt}/category/category_classe0.json"
        output_category_metrics_classe_na = f"{base_prompt}/category/category_classe_na.json"
        output_category_detailed = f"{base_prompt}/category/category_detailed.json"
        output_category_detailed_excel = f"{base_prompt}/category/category_detailed.xlsx"

        # Score
        # output_score_qm_excel = f"{base_prompt}/score/qm_score.xlsx"
        # output_score_qm = f"{base_prompt}/score/qm_score.json"
        # output_manual_weights_excel = f"{base_prompt}/score/manual_weights.xlsx"
        # output_score_manual = f"{base_prompt}/score/manual_weights.json"
        # output_llm_score_excel = f"{base_prompt}/score/llm_score.xlsx"


        # New Score
        output_new_score_qm_excel = f"{base_prompt}/score/qm_new_score.xlsx"
        output_new_score_qm = f"{base_prompt}/score/qm_new_score.json"
        output_new_manual_weights_excel = f"{base_prompt}/score/manual_new_weights.xlsx"
        output_new_score_manual = f"{base_prompt}/score/manual_new_weights.json"
        output_new_llm_score_excel = f"{base_prompt}/score/llm_new_score.xlsx"

        # Score table comparison
        output_score_comparison = f"{base_prompt}/score/score_comparison.xlsx"
        output_new_score_comparison = f"{base_prompt}/score/new_score_comparison.xlsx"
    
        # GT SCORE

        output_gt_score_excel = f"{base_prompt}/score/gt_score.xlsx"
        output_gt_score_json = f"{base_prompt}/score/gt_score.json"

        # Score 
        

        processor.save_to_excel_individual_practice(input_prompt, output_prompt_excel, output_prompt_excel_na)

        processor.nan_compare(output_prompt_excel_na, real, output_excel_nan_detailed, output_json_nan_detailed, output_json_nan_metrics)

        processor.individual_practices_nan_only(output_excel_nan_detailed, output_json_nan_individual_metrics)

        processor.compare_practice(output_prompt_excel, real, output_geral_detailed, output_geral_metrics, output_classe0_metrics, output_classe1_metrics)
        
        processor.individual_practices(output_geral_detailed, output_classe0_individual_metrics, output_classe1_individual_metrics, output_geral_individual_metrics, output_practiceMetrics, output_matrix)

        processor.category_metrics(output_prompt_excel, real, manual_weights, output_category_metrics_classe1, output_category_metrics_classe0, output_category_metrics_classe_na, output_category_detailed, output_category_detailed_excel)

        # processor.process_score(qm_weights, output_prompt_excel, output_score_qm_excel, output_score_qm)
        # processor.process_score(manual_weights, output_prompt_excel, output_manual_weights_excel, output_score_manual)

        processor.process_score_divide_na(qm_weights, output_prompt_excel, output_new_score_qm_excel, output_new_score_qm)
        # processor.process_score_divide_na(manual_weights, output_prompt_excel, output_new_manual_weights_excel, output_new_score_manual)
        processor.process_score_divide_na(qm_weights, real, output_gt_score_excel, output_gt_score_json)

        # processor.process_score(llm_weights, output_prompt_excel, output_llm_score_excel)

        # processor.score_comparison_table(output_score_qm_excel, output_manual_weights_excel, paper_score, output_score_comparison, output_geral_metrics, output_all = f"{base_prompt}/score/score_comparison_all.json", output_consolidated_json = f"{base_prompt}/score/score_consolidated.json")
        
        processor.score_comparison_table(output_new_score_qm_excel, paper_score, output_new_score_comparison, output_geral_metrics, output_all = f"{base_prompt}/score/new_score_comparison_all.json", output_consolidated_json = f"{base_prompt}/score/new_score_consolidated.json", gt_score_qm_path=output_gt_score_excel)