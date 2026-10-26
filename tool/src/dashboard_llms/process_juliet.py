"""
Process Juliet CWE-89 LLM results into the JSON structure expected by index.html.

Generates all files under:
    src/dashboard_llms/output/juliet_<prompt>/<model>/

Run from the tool/ directory:
    python src/dashboard_llms/process_juliet_to_dashboard.py

Then open index.html and choose e.g. Prompt = "Juliet P1" from the dropdown.
"""

import os
import json
import glob
import math
from collections import defaultdict

import pandas as pd
import numpy as np

RESULTS_ROOT = "./src/test_results/juliet"
OUTPUT_BASE  = "./src/dashboard_llms/output"
WEIGHTS_JSON = "./src/dashboard_llms/input/manual_weights.json"

PRACTICES = [str(i) for i in range(1, 17)]


# ---------------------------------------------------------------------------
# Weights and subcategory helpers
# ---------------------------------------------------------------------------

def _load_weights():
    with open(WEIGHTS_JSON, "r", encoding="utf-8") as f:
        wj = json.load(f)

    weights = {}
    def _walk(d):
        if not isinstance(d, dict):
            return
        for k, v in d.items():
            if isinstance(v, dict):
                if "weight" in v and k.isdigit():
                    weights[k] = weights.get(k, 0.0) + v["weight"]
                _walk(v)
    _walk(wj)
    return weights, wj


def _subcategory_map(weights_json):
    mapping = {}
    main = weights_json["Input Validation"]["children"]
    for subcat, subcat_data in main.items():
        for practice in subcat_data["children"]:
            mapping[practice] = subcat
    return mapping


# ---------------------------------------------------------------------------
# Load Juliet results into DataFrames
# ---------------------------------------------------------------------------

def load_results():
    """
    Returns {model: {prompt: DataFrame}}.
    DataFrame columns: Parent File, FileName, Method, "1"…"16"
    (values: 0, 1, or NaN for N/A)
    """
    data: dict = {}
    pattern = os.path.join(RESULTS_ROOT, "*", "*", "template_practices_result_*.json")
    for path in sorted(glob.glob(pattern)):
        parts = path.replace("\\", "/").split("/")
        model  = parts[-3]
        prompt = parts[-2].replace("_a", "")

        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        rows = []
        for subfolder, files in raw.items():
            for filename, methods in files.items():
                for method_name, result in methods.items():
                    if result == "" or not isinstance(result, dict):
                        continue
                    res_list = result.get("results", [])
                    while len(res_list) < 16:
                        res_list.append(2)

                    row = {
                        "Parent File": subfolder,
                        "FileName": filename.replace(".java", ""),
                        "Method": method_name,
                    }
                    for i, val in enumerate(res_list[:16]):
                        row[str(i + 1)] = float("nan") if val == 2 else float(val)
                    rows.append(row)

        if not rows:
            continue

        df = pd.DataFrame(rows)
        data.setdefault(model, {})
        if prompt not in data[model]:
            data[model][prompt] = df
        else:
            data[model][prompt] = pd.concat([data[model][prompt], df], ignore_index=True)

    return data


# ---------------------------------------------------------------------------
# Synthetic ground truth
# ---------------------------------------------------------------------------

def make_ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    """
    bad()    → applicable (non-NaN) practices expected = 0
    goodB2G()→ applicable practices expected = 1
    NaN stays NaN (not applicable).
    """
    gt_rows = []
    for _, row in df.iterrows():
        gt = {"Parent File": row["Parent File"],
              "FileName": row["FileName"],
              "Method": row["Method"]}
        method = row["Method"]
        for p in PRACTICES:
            val = row[p]
            if pd.isna(val):
                gt[p] = float("nan")
            elif method == "bad":
                gt[p] = 0.0
            elif method == "goodB2G":
                gt[p] = 1.0
            else:
                gt[p] = float("nan")
        gt_rows.append(gt)
    return pd.DataFrame(gt_rows)


# ---------------------------------------------------------------------------
# Detailed comparison (LLM predictions vs ground truth)
# ---------------------------------------------------------------------------

def build_detailed(df_llm: pd.DataFrame, df_gt: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row_gt in df_gt.iterrows():
        mask = (
            (df_llm["Parent File"] == row_gt["Parent File"]) &
            (df_llm["FileName"]    == row_gt["FileName"]) &
            (df_llm["Method"]      == row_gt["Method"])
        )
        matches = df_llm[mask]
        if matches.empty:
            continue
        row_llm = matches.iloc[0]

        for p in PRACTICES:
            real     = row_gt[p]    # ground truth
            expected = row_llm[p]   # LLM prediction

            both_na = pd.isna(real) and pd.isna(expected)
            both_eq = (not pd.isna(real) and not pd.isna(expected)
                       and float(real) == float(expected))
            correct = 1 if (both_na or both_eq) else 0

            rows.append({
                "Parent File": row_gt["Parent File"],
                "FileName":    row_gt["FileName"],
                "Method":      row_gt["Method"],
                "practice":    p,
                "real":        real,
                "expected":    expected,
                "correct":     correct,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _metrics(tp, tn, fp, fn):
    total   = tp + tn + fp + fn
    correct = tp + tn
    acc  = (tp + tn) / total if total > 0 else float("nan")
    prec = tp / (tp + fp)  if (tp + fp) > 0 else float("nan")
    rec  = tp / (tp + fn)  if (tp + fn) > 0 else float("nan")
    f1   = 2*prec*rec / (prec+rec) if (prec+rec) > 0 else float("nan")
    return acc, prec, rec, f1, total, correct


def _r(v):
    """Round or None for NaN."""
    return None if (isinstance(v, float) and math.isnan(v)) else round(v, 4)


def _class_summary(df, class_val):
    """Overall metrics for class_val (0 or 1) or None for NA."""
    if class_val is None:
        tp = int(( df["real"].isna() &  df["expected"].isna()).sum())
        fp = int(( df["real"].isna() &  df["expected"].notna()).sum())
        fn = int(( df["real"].notna() & df["expected"].isna()).sum())
        tn = int(( df["real"].notna() & df["expected"].notna()).sum())
    else:
        tp = int(((df["real"] == class_val) & (df["expected"] == class_val)).sum())
        fp = int(((df["real"] != class_val) & (df["expected"] == class_val)).sum())
        fn = int(((df["real"] == class_val) & (df["expected"] != class_val)).sum())
        tn = int(((df["real"] != class_val) & (df["expected"] != class_val)).sum())
    acc, prec, rec, f1, total, correct = _metrics(tp, tn, fp, fn)
    return [{"accuracy": _r(acc), "precision": _r(prec), "recall": _r(rec),
             "f1_score": _r(f1), "TP": str(tp), "FP": fp, "FN": fn, "TN": str(tn),
             "correct": f"{int(correct)}/{int(total)}", "total": int(total)}]


def _per_practice_metrics(df_detailed):
    """Returns m0, m1, m_na, m_geral, m_matrix, m_practice (lists of dicts)."""
    m0, m1, m_na, m_geral, m_matrix, m_practice = [], [], [], [], [], []

    for p in sorted(df_detailed["practice"].unique(), key=int):
        sub = df_detailed[df_detailed["practice"] == p]

        # class 0
        tp0 = int(((sub["expected"]==0)&(sub["real"]==0)).sum())
        fp0 = int(((sub["expected"]==0)&(sub["real"]!=0)).sum())
        fn0 = int(((sub["expected"]!=0)&(sub["real"]==0)).sum())
        tn0 = int(((sub["expected"]!=0)&(sub["real"]!=0)).sum())
        a0,p0,r0,f0,tot0,cor0 = _metrics(tp0,tn0,fp0,fn0)
        real0 = int((sub["real"]==0).sum())
        exp0  = int((sub["expected"]==0).sum())
        m0.append({"practice":p,"total":int(tot0),"llm identify":exp0,"correct":int(cor0),
                   "real":real0,"accuracy":_r(a0),"precision":_r(p0) or "-",
                   "recall":_r(r0) or "-","f1_score":_r(f0) or "-",
                   "TP":tp0,"FP":fp0,"FN":fn0,"TN":tn0})

        # class 1
        tp1 = int(((sub["expected"]==1)&(sub["real"]==1)).sum())
        fp1 = int(((sub["expected"]==1)&(sub["real"]!=1)).sum())
        fn1 = int(((sub["expected"]!=1)&(sub["real"]==1)).sum())
        tn1 = int(((sub["expected"]!=1)&(sub["real"]!=1)).sum())
        a1,p1,r1,f1v,tot1,cor1 = _metrics(tp1,tn1,fp1,fn1)
        real1 = int((sub["real"]==1).sum())
        exp1  = int((sub["expected"]==1).sum())
        m1.append({"practice":p,"total":int(tot1),"llm identify":exp1,"correct":int(cor1),
                   "real":real1,"accuracy":_r(a1),"precision":_r(p1) or "-",
                   "recall":_r(r1) or "-","f1_score":_r(f1v) or "-",
                   "TP":tp1,"FP":fp1,"FN":fn1,"TN":tn1})

        # class NA
        tpn = int(( sub["expected"].isna() &  sub["real"].isna()).sum())
        fpn = int(( sub["expected"].isna() &  sub["real"].notna()).sum())
        fnn = int(( sub["expected"].notna() & sub["real"].isna()).sum())
        tnn = int(( sub["expected"].notna() & sub["real"].notna()).sum())
        an,pn,rn,fn_v,totn,corn = _metrics(tpn,tnn,fpn,fnn)
        realn = int(sub["real"].isna().sum())
        m_na.append({"practice":p,"total":int(totn),"correct":int(corn),"real":realn,
                     "accuracy":_r(an),"precision":_r(pn) or "-",
                     "recall":_r(rn) or "-","f1_score":_r(fn_v) or "-",
                     "TP":tpn,"FP":fpn,"FN":fnn,"TN":tnn})

        # geral summary
        m_geral.append({
            "practice":p,
            "correct_na":tpn,"incorrect_na":fpn+fnn,"real_na":realn,
            "correct_0":tp0,"incorrect_0":fp0+fn0,"real_0":real0,
            "correct_1":tp1,"incorrect_1":fp1+fn1,"real_1":real1,
        })

        # matrix
        m_matrix.append({
            "practice":p,
            "TP_na":tpn,"FP_na":fpn,"FN_na":fnn,"TN_na":tnn,"real_na":realn,
            "TP_0":tp0,"FP_0":fp0,"FN_0":fn0,"TN_0":tn0,"real_0":real0,
            "TP_1":tp1,"FP_1":fp1,"FN_1":fn1,"TN_1":tn1,"real_1":real1,
        })

        # practice-level (class-1 based)
        a,pv,rv,f,tot,cor = _metrics(tp1,tn1,fp1,fn1)
        m_practice.append({"practice":p,"total":int(tot),"correct":int(cor),
                           "accuracy":_r(a),"precision":_r(pv) or "-",
                           "recall":_r(rv) or "-","f1_score":_r(f) or "-",
                           "TP":tp1,"FP":fp1,"FN":fn1,"TN":tn1})

    return m0, m1, m_na, m_geral, m_matrix, m_practice


def _category_metrics(df_detailed, subcat_map):
    rows = []
    for _, row in df_detailed.iterrows():
        sc = subcat_map.get(row["practice"])
        if sc:
            rows.append({"subcategory": sc, "practice": row["practice"],
                         "real": row["real"], "expected": row["expected"],
                         "correct": row["correct"]})
    df = pd.DataFrame(rows)
    if df.empty:
        return [], [], []

    cat1, cat0, cat_na = [], [], []
    for sc in sorted(df["subcategory"].unique()):
        sub = df[df["subcategory"] == sc]
        practices_in_cat = sorted(sub["practice"].unique().tolist(), key=int)

        for class_val, lst in [(1, cat1), (0, cat0)]:
            tp = int(((sub["expected"]==class_val)&(sub["real"]==class_val)).sum())
            fp = int(((sub["expected"]==class_val)&(sub["real"]!=class_val)).sum())
            fn = int(((sub["expected"]!=class_val)&(sub["real"]==class_val)).sum())
            tn = int(((sub["expected"]!=class_val)&(sub["real"]!=class_val)).sum())
            a,p,r,f,tot,cor = _metrics(tp,tn,fp,fn)
            lst.append({"subcategory":sc,"practices":", ".join(practices_in_cat),
                        "total":int(tot),"correct":int(cor),"incorrect":int(tot-cor),
                        "accuracy":_r(a),"precision":_r(p) or "-",
                        "recall":_r(r) or "-","f1_score":_r(f) or "-"})

        tpn = int((sub["expected"].isna()  & sub["real"].isna()).sum())
        fpn = int((sub["expected"].isna()  & sub["real"].notna()).sum())
        fnn = int((sub["expected"].notna() & sub["real"].isna()).sum())
        tnn = int((sub["expected"].notna() & sub["real"].notna()).sum())
        a,p,r,f,tot,cor = _metrics(tpn,tnn,fpn,fnn)
        cat_na.append({"subcategory":sc,"practices":", ".join(practices_in_cat),
                       "total":int(tot),"correct":int(cor),"incorrect":int(tot-cor),
                       "accuracy":_r(a),"precision":_r(p) or "-",
                       "recall":_r(r) or "-","f1_score":_r(f) or "-"})

    return cat1, cat0, cat_na


# ---------------------------------------------------------------------------
# Score calculation (mirrors process_score_divide_na)
# ---------------------------------------------------------------------------

def _calc_score(row_dict, weights):
    total_na_w = 0.0
    rated = {}
    for p in PRACTICES:
        val = row_dict.get(p)
        w   = weights.get(p, 0.0)
        if val is None or (isinstance(val, float) and math.isnan(val)):
            total_na_w += w
        else:
            rated[p] = w

    sum_rated = sum(rated.values())
    if total_na_w > 0 and sum_rated > 0:
        for p in list(rated):
            rated[p] += (rated[p] / sum_rated) * total_na_w

    score = 0.0
    for p in PRACTICES:
        val = row_dict.get(p)
        if val == 1.0 or val == 1:
            score += rated.get(p, weights.get(p, 0.0))

    return min(1.0, max(0.0, round(score, 10)))


def _build_consolidated(df_llm: pd.DataFrame, df_gt: pd.DataFrame, weights: dict) -> dict:
    consolidated = defaultdict(dict)

    for _, row_llm in df_llm.iterrows():
        fname  = row_llm["FileName"]
        method = row_llm["Method"]

        score_qm = _calc_score(row_llm.to_dict(), weights)

        gt_mask = (df_gt["FileName"] == fname) & (df_gt["Method"] == method)
        gt_match = df_gt[gt_mask]
        score_gt = _calc_score(gt_match.iloc[0].to_dict(), weights) if not gt_match.empty else None

        practices_qm = {f"Practice {i}": (None if pd.isna(row_llm[str(i)]) else row_llm[str(i)])
                        for i in range(1, 17)}

        version = method  # "bad" or "goodB2G" acts as the version axis

        if version not in consolidated[fname]:
            consolidated[fname][version] = {
                "score_qm":             {},
                "score_paper":          {},
                "score_groundtruth_qm": {},
                "practices":            {},
            }

        consolidated[fname][version]["score_qm"][method]             = score_qm
        consolidated[fname][version]["score_paper"][method]           = None
        consolidated[fname][version]["score_groundtruth_qm"][method]  = score_gt
        consolidated[fname][version]["practices"][method] = {
            "qm":          practices_qm,
            "groundtruth": {},
        }

    return dict(consolidated)


# ---------------------------------------------------------------------------
# JSON serialisation helper (NaN → null)
# ---------------------------------------------------------------------------

class _NanEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float) and math.isnan(obj):
            return None
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)

    def iterencode(self, o, _one_shot=False):
        # Replace Python NaN/Inf with null at encoding time
        if isinstance(o, float):
            if math.isnan(o) or math.isinf(o):
                return iter(["null"])
        return super().iterencode(o, _one_shot)


def _save(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=_NanEncoder, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main processing loop
# ---------------------------------------------------------------------------

def process_one(model: str, prompt: str, df_llm: pd.DataFrame):
    out = f"{OUTPUT_BASE}/juliet_{prompt}/{model}"
    print(f"  > {model} / {prompt}")

    weights, weights_json = _load_weights()
    subcat_map = _subcategory_map(weights_json)

    df_gt       = make_ground_truth(df_llm)
    df_detailed = build_detailed(df_llm, df_gt)

    na_metrics = _class_summary(df_detailed, None)
    c0_metrics = _class_summary(df_detailed, 0)
    c1_metrics = _class_summary(df_detailed, 1)

    m0, m1, m_na, m_geral, m_matrix, m_practice = _per_practice_metrics(df_detailed)
    cat1, cat0, cat_na = _category_metrics(df_detailed, subcat_map)

    consolidated = _build_consolidated(df_llm, df_gt, weights)

    _save(m_matrix,   f"{out}/geral/matrix.json")
    _save(m_practice, f"{out}/geral/practice_metrics.json")
    _save(m_geral,    f"{out}/geral/geral_individual_metrics.json")

    _save(c0_metrics, f"{out}/classe 0/classe0_metrics.json")
    _save(m0,         f"{out}/classe 0/classe0_individual_metrics.json")

    _save(c1_metrics, f"{out}/classe 1/classe1_metrics.json")
    _save(m1,         f"{out}/classe 1/classe1_individual_metrics.json")

    _save(na_metrics, f"{out}/classe NA/json_na_metrics.json")
    _save(m_na,       f"{out}/classe NA/json_na_individual_metrics.json")

    _save(cat0,    f"{out}/category/category_classe0.json")
    _save(cat1,    f"{out}/category/category_classe1.json")
    _save(cat_na,  f"{out}/category/category_classe_na.json")

    _save(consolidated, f"{out}/score/new_score_consolidated.json")

    print(f"     [OK] {len(df_llm)} rows written to {out}")


def main():
    print("[*] Loading Juliet results …")
    data = load_results()
    if not data:
        print("[!] No results found in", RESULTS_ROOT)
        return

    total = sum(len(ps) for ps in data.values())
    print(f"[*] Found {len(data)} model(s), {total} model×prompt combination(s)")

    for model, prompts in sorted(data.items()):
        for prompt, df in sorted(prompts.items()):
            process_one(model, prompt, df)

    print("\n[OK] Done.")
    print("     Open index.html and select the 'Juliet P1/P2/P4' prompt entries.")


if __name__ == "__main__":
    main()
