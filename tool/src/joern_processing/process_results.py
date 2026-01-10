#!/usr/bin/env python3
import json, re, argparse
from pathlib import Path

# ruído a ignorar
DROP_RE = re.compile(r"^(<operator>\.|<unresolvedNamespace>|.*<init>:|ANY(\.|:|$))")

def simple_method_name(s: str) -> str:
    """
    'pt.uc....ChangePaymentMethod_Vx0.process:...' -> 'process'
    """
    if not s or s.startswith("<"):
        return ""
    left = s.split(":", 1)[0]            # corta assinatura
    parts = left.split(".")
    part1 = parts[-2]
    part2 = parts[-1]
    parts_all = part1 + "." + part2
    return parts_all if parts else ""

def uniq_preserve(seq):
    seen, out = set(), []
    for x in seq:
        if x and x not in seen:
            seen.add(x); out.append(x)
    return out

def main():
    ap = argparse.ArgumentParser(description="Extrai filename, main_method e called_methods do joern_results.json")
    ap.add_argument("--input", default="./tool/src/joern_processing/output_joern_vm/joern_results.json")
    ap.add_argument("--outdir", default="./tool/src/joern_processing/output_joern_process/summary.json")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.outdir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # ignorar a primeira key "" (pasta)
    if isinstance(data, dict) and "" in data and isinstance(data[""], dict):
        data = data[""]

    results = []
    # estrutura: { filename: { main_method: [callees...] } }
    for filename, methods in (data or {}).items():
        if not isinstance(methods, dict):
            continue

        for main_method, callees in methods.items():
            if not isinstance(callees, list):
                continue

            called = []
            for raw in callees:
                if not raw or DROP_RE.search(raw):
                    continue
                m = simple_method_name(raw)
                if m:
                    called.append(m)

            results.append({
                "filename": filename,
                "main_method": main_method,
                "called_methods": uniq_preserve(called)
            })

    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] {len(results)} entradas escritas em {out_path}")

if __name__ == "__main__":
    main()
