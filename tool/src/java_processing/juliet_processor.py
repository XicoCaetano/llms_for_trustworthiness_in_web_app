import os
import javalang

# Methods to include in the analysis and their label
# bad()    -> vulnerable (equivalent to VxA in WSVD-bench)
# goodB2G()-> secure     (equivalent to Vx0  in WSVD-bench)
# Skipped: good() (just calls the others), goodG2B() (ambiguous), main() (test harness)
RELEVANT_METHODS = {"bad", "goodB2G"}


class JulietProcessor:
    """
    Walks the Juliet CWE89 directory tree and extracts the source code of
    relevant methods from each .java test-case file.

    Directory structure expected:
        <root>/
            s01/
                CWE89_SQL_Injection__*.java
            s02/
                ...

    Parameters
    ----------
    baseline_only : if True (default), only process *_01.java files.
        These are the "Flow Variant 01 – Baseline" files that contain both
        bad() and goodB2G() in the same class, making them directly
        comparable to the WSVD-bench Vx0/VxA pairs.
    """

    def __init__(self, root_folder: str, baseline_only: bool = True):
        self.root_folder = root_folder
        self.baseline_only = baseline_only

    # ------------------------------------------------------------------
    # Public API (mirrors what JavaProcessor + iterate_files_and_methods
    # provide for the WSVD-bench pipeline)
    # ------------------------------------------------------------------

    def iter_files_and_methods(self):
        """
        Yield (subfolder, filename, methods) for every relevant .java file.

        subfolder : e.g. "s01"
        filename  : e.g. "CWE89_SQL_Injection__Environment_executeBatch_01.java"
        methods   : list of (method_name, start_line, source_code)
        """
        for subfolder in sorted(os.listdir(self.root_folder)):
            subfolder_path = os.path.join(self.root_folder, subfolder)
            if not os.path.isdir(subfolder_path):
                continue

            for filename in sorted(os.listdir(subfolder_path)):
                if not filename.endswith(".java"):
                    continue
                if self.baseline_only and not filename.endswith("_01.java"):
                    continue

                filepath = os.path.join(subfolder_path, filename)
                methods = self.process_java_file(filepath)
                if methods:
                    yield subfolder, filename, methods

    def process_java_file(self, file_path: str):
        """
        Parse a Juliet .java file and return a list of
        (method_name, start_line, source_code) for relevant methods only.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
            tree = javalang.parse.parse(code)
        except Exception as e:
            print(f"[WARN] Could not parse {file_path}: {e}")
            return []

        methods = []
        for _, node in tree:
            if not isinstance(node, javalang.tree.MethodDeclaration):
                continue
            if node.name not in RELEVANT_METHODS:
                continue
            start = node.position.line if node.position else 0
            source = self._extract_source(code, node)
            methods.append((node.name, start, source))

        return methods

    @staticmethod
    def get_label(method_name: str) -> str:
        """Return 'bad' (vulnerable) or 'good' (secure) for a method name."""
        if method_name == "bad":
            return "bad"
        if method_name == "goodB2G":
            return "good"
        return "unknown"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_source(code: str, method_node) -> str:
        """Extract full method source by counting braces — same logic as JavaProcessor."""
        lines = code.splitlines()
        start_line = (method_node.position.line - 1) if method_node.position else 0

        i = start_line
        while i < len(lines) and "{" not in lines[i]:
            i += 1
        if i >= len(lines):
            return "\n".join(lines[start_line:start_line + 1])

        brace = 0
        started = False
        out = []
        for j in range(start_line, len(lines)):
            line = lines[j]
            out.append(line)
            if j >= i:
                brace += line.count("{")
                brace -= line.count("}")
                started = True
            if started and brace == 0:
                break

        return "\n".join(out)
