"""
Auto-generates individual-practice prompt files (followed + applicability)
for all practices in practices_data.json, following Oleksandr's prompt_1 format.

Each practice gets two files:
  prompts/GPT/individual_practices_prompts/prompt_1/followed/a/p{N}.txt
  prompts/GPT/individual_practices_prompts/prompt_1/applicability/a/p{N}.txt

where N is the global practice number (1-189).

Existing files are skipped by default (--skip-existing, which is the default).
Use --overwrite to replace them.

Usage:
    python generate_prompts.py
    python generate_prompts.py --practices-json ./src/dashboard_llms/input/practices_data.json
    python generate_prompts.py --overwrite
    python generate_prompts.py --only-category "Injection"
"""

import os
import json
import argparse

DEFAULT_PRACTICES_JSON = "./src/dashboard_llms/input/practices_data.json"
DEFAULT_PROMPTS_ROOT   = "./src/llms_and_prompts/prompts/GPT/global_practices_prompts"

FOLLOWED_TEMPLATE = """\
Given the following Java function:

{{content}}

Evaluate the function **only** according to the following OWASP secure coding practice of {practice_category}:

[1] {description}

Format your response like this:
1. Does the function FOLLOW OWASP Rule 1 of {practice_category}? Answer with "Yes" or "No" only.
- If yes, respond: "1. Yes;"
- If no, respond: "1. No;"

Only respond with the line shown above. **End your response with a semicolon (;)** and nothing else.\
"""

APPLICABILITY_TEMPLATE = """\
Given the following Java function:

{{content}}

Evaluate the function **only** according to the following OWASP secure coding practice of {practice_category}:

[1] {description}

Format your response like this:
1. Does the OWASP Rule 1 of {practice_category} practice is applicable? Answer with "Yes" or "No" only.
- If yes, respond: "1. Yes;"
- If no, respond: "1. No;"

Only respond with the line shown above. **End your response with a semicolon (;)** and nothing else.\
"""


def generate_prompts(practices_data: dict, prompts_root: str, overwrite: bool, only_category: str | None) -> None:
    practices = practices_data["practices"]
    created = 0
    skipped = 0

    for practice_id, info in practices.items():
        n = int(practice_id[1:])  # "P84" -> 84
        description     = info["description"]
        practice_category = info["practice_category"]

        if only_category and practice_category.lower() != only_category.lower():
            continue

        for prompt_version in ("prompt_1",):
            for kind, template in (
                ("followed",      FOLLOWED_TEMPLATE),
                ("applicability", APPLICABILITY_TEMPLATE),
            ):
                folder = os.path.join(prompts_root, prompt_version, kind, "a")
                os.makedirs(folder, exist_ok=True)
                filepath = os.path.join(folder, f"p{n}.txt")

                if os.path.exists(filepath) and not overwrite:
                    skipped += 1
                    continue

                content = template.format(
                    practice_category=practice_category,
                    description=description,
                )
                with open(filepath, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                created += 1

    print(f"Created : {created} files")
    print(f"Skipped : {skipped} files (already exist — use --overwrite to replace)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate individual-practice prompt files from practices_data.json."
    )
    parser.add_argument("--practices-json", default=DEFAULT_PRACTICES_JSON,
                        help=f"Path to practices_data.json (default: {DEFAULT_PRACTICES_JSON})")
    parser.add_argument("--prompts-root", default=DEFAULT_PROMPTS_ROOT,
                        help=f"Root folder for prompt files (default: {DEFAULT_PROMPTS_ROOT})")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing prompt files (default: skip)")
    parser.add_argument("--only-category", default=None,
                        help="Generate only for a specific practice_category (e.g. 'Injection')")
    args = parser.parse_args()

    with open(args.practices_json, "r", encoding="utf-8") as f:
        practices_data = json.load(f)

    generate_prompts(practices_data, args.prompts_root, args.overwrite, args.only_category)


if __name__ == "__main__":
    main()
