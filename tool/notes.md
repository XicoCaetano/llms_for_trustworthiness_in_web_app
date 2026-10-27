# Notes — Ficheiros Importantes e Como Correr a Pipeline

## Ficheiros importantes para mostrar ao orientador

### Criados por mim (trabalho novo)

| Ficheiro | O que é |
|---|---|
| `src/dashboard_llms/input/practices_data.json` | Base de dados central: 189 práticas (P1–P189) mapeadas para OWASP Top 10 2025 e para cada CWE |
| `generate_prompts.py` | Script que auto-gera os 378 ficheiros de prompt a partir do JSON |
| `extract_vulnerability_lines.py` | Script que extrai linhas de vulnerabilidade dos ficheiros Juliet e gera o ground truth CSV |
| `src/llms_and_prompts/prompts/GPT/global_practices_prompts/` | 378 prompts gerados (189 práticas × followed + applicability) |
| `vulnerability_lines.csv` | Ground truth gerado para CWE-89 (120 linhas, colunas P84 e P86) |
| `main_juliet.py` | Pipeline principal para correr os LLMs no dataset Juliet |
| `src/java_processing/juliet_processor.py` | Extrai os métodos `bad()` e `goodB2G()` dos ficheiros `_01.java` |
| `src/dashboard_llms/process_juliet.py` | Converte resultados LLM do Juliet para formato compatível com a dashboard |

### Do Oleksandr (referência para comparação)

| Ficheiro | O que é |
|---|---|
| `main2.py` | Pipeline original para WSVD-Bench |
| `src/llms_and_prompts/prompts/GPT/individual_practices_prompts/` | Prompts originais (P1–P16, Input Validation, numeração local) |
| `src/dashboard_llms/input/WsvdBench_GroundTruth_V3.xlsx` | Ground truth manual do WSVD-Bench |

---

## Como correr

### Para tudo (todas as categorias OWASP, todos os modelos)

```bash
cd tool

# 1. Gerar todos os prompts (só precisas correr uma vez)
python generate_prompts.py

# 2. Gerar o ground truth CSV para um CWE específico
python extract_vulnerability_lines.py --root ./Dataset/Java/src/testcases/CWE89_SQL_Injection

# 3. Correr a pipeline LLM no Juliet (todos os modelos × prompts)
python main_juliet.py
```

### Para apenas um caso (ex: CWE-89, só Injection, só prompt_1, só gpt-3.5-turbo)

```bash
cd tool

# Gerar só os prompts de Injection
python generate_prompts.py --only-category "Injection"

# Ground truth apenas para CWE-89
python extract_vulnerability_lines.py

# Correr a pipeline — edita main_juliet.py para limitar modelos/prompts antes de correr
python main_juliet.py
```

---

## O que tens de ter em atenção

1. **A chave da API** — o ficheiro `.env` ou variável `OPENAI_API_KEY` tem de estar configurado antes de correr `main_juliet.py`. Cada chamada ao LLM tem custo.

2. **Os prompts gerados são genéricos** — os ficheiros em `global_practices_prompts` usam o template mais simples (prompt_1 sem exemplos de código mau). Para as categorias mais complexas podes querer adicionar exemplos manualmente depois.

3. **O ground truth do Juliet é derivado** — `bad()` → P=0, `goodB2G()` → P=1. Isso é automático pelo nome do método, não é uma anotação humana como no WSVD. Deves deixar isso claro ao orientador.

4. **Só CWE-89 tem dados no dataset** — o `Dataset/Java/` actualmente só tem `CWE89_SQL_Injection`. Se quiseres outras categorias, precisas de descarregar mais do Juliet Test Suite.

5. **As práticas P84 e P86 são as mapeadas para CWE-89** — P84 = parameterized queries, P86 = ORM/query builders. Se o orientador perguntar porque só 2 colunas, é porque só essas 2 práticas estão associadas ao CWE-89 no `practices_data.json`.
