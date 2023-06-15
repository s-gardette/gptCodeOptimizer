import os
import re
import logging
from pathlib import Path

# Define a logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class MissingImport:
    def __init__(self, logger=None):
        self.logger = logger if logger is not None else logging.getLogger(__name__)

    def detect_relative_imports(self, js_code):
        # Regular expression pattern to match relative import statements
        pattern = re.compile(r'import .* from [\'"](.*?)[\'"];', re.MULTILINE)

        matches = pattern.findall(js_code)

        # Filter and display only the relative import paths
        relative_imports = [
            m for m in matches if m.startswith("./") or m.startswith("../")
        ]
        return relative_imports

    def verify_relative_imports(self, input_path, relative_imports, code_base_path):
        # Remove 'input' from input_path
        self.logger.debug("input_path %s", input_path)
        abs_input_path = input_path.replace("input", code_base_path)

        # Test if file exists
        file = Path(abs_input_path)
        if not file.is_file():
            self.logger.warning("File does not exist: %s", abs_input_path)
            return

        # Now check relative imports
        for rel_path in relative_imports:
            self.logger.debug("rel_path %s", rel_path)
            dirname = os.path.dirname(abs_input_path)
            self.logger.debug("dirname %s", dirname)
            raw_path = os.path.join(dirname, rel_path)
            self.logger.debug("raw_path %s", raw_path)
            abs_path = os.path.normpath(
                raw_path
            )  # Generate absolute path based on the relative import

            import_file = self._get_first_matching_file(abs_path)
            if import_file:
                self.logger.info("File exists: %s", import_file)
            else:
                self.logger.error("File does not exist: %s", abs_path)
                self._write_to_missing_imports(abs_path)

    def _get_first_matching_file(self, abs_path):
        for ext in ["*", ".js", ".jsx", ".ts", ".tsx"]:
            matches = list(Path(abs_path).parent.glob(Path(abs_path).name + ext))
            if matches:
                return matches[0]

    def _write_to_missing_imports(self, abs_path):
        with open("missing_imports.txt", "a+", encoding="utf-8") as file:
            file.write(f"{abs_path} \n\n")

    def create(self, input_path, output_path, code_base_path, optimised_code):
        self.logger.debug("output_path %s", output_path)
        relative_imports = self.detect_relative_imports(optimised_code)
        self.logger.debug("relative_imports %s", relative_imports)
        self.verify_relative_imports(input_path, relative_imports, code_base_path)


if __name__ == "__main__":
    mi = MissingImport(logger)
    # Insert the appropriate values for the parameters in the create method.
    mi.create("input_path", "output_path", "code_base_path", "optimised_code")
