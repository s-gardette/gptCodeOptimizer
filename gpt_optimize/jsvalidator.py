import subprocess
import logging


class JsValidator:
    def __init__(self, file_path, error_file_path="errors.txt"):
        self.file_path = file_path
        self.error_file_path = error_file_path

    def install_prettier(self):
        try:
            subprocess.run(
                ["npm", "install", "--global", "prettier"],
                check=True,
                text=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            logging.warning(f"Could not install Prettier. Error: {str(e)}")
            logging.info(e.stdout)
            return False
        return True

    def format(self):
        # Attempt to format the file
        try:
            result = subprocess.run(
                ["prettier", "--write", "--parser", "babel", self.file_path],
                check=True,
                text=True,
                capture_output=True,
            )
            logging.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            # If Prettier is not found, try to install it
            if "command not found" in str(e):
                if self.install_prettier():
                    return self.format()
            logging.warning(
                f"Prettier found issues in {self.file_path}. Error: {str(e)}"
            )
            logging.warning(e.stderr)  # log the actual prettier error
            return e.stderr
