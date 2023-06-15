import os
import time
import tempfile
from .jsvalidator import JsValidator
from .utils_func import sanitize_code_blocks
from dotenv import load_dotenv
import openai
import tiktoken

load_dotenv()


class OpenAiApi:
    def __init__(self, api_key):
        openai.api_key = api_key

    def chat(self, model, messages, temperature):
        return openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )


class ErrorHandler:
    def __init__(self, logger):
        self.logger = logger
        self.retry_delay = 5  # seconds

    def handle_error(self, e, type):
        error_msg = {
            "OpenAIError": f"Unexpected finish reason: {e}",
            "RateLimitError": f"RateLimitError occurred. Retrying in {self.retry_delay} seconds...",
            "GenericError": f"Unexpected error: {e}",
            "InvalidRequestError": f"Invalid request error: {e}",
        }

        self.logger.error(error_msg[type])

        if type == "RateLimitError":
            time.sleep(self.retry_delay)
            self.retry_delay *= 2  # exponential backoff


class OpenAiHelper:
    def __init__(self, model, logger):
        self.model = model
        self.logger = logger
        self.openai_api = OpenAiApi(os.getenv("OPENAI_API_KEY"))
        self.error_handler = ErrorHandler(logger)

    def openai_api_call(
        self,
        code,
        system_key,
        user_content,
        system_content,
        temperature=0.5,
        model="gpt-3.5-turbo-0613",
        messages=None,
    ):
        self.logger.info(f"Calling API... {model}")
        content = []
        if messages is None:
            messages = self.create_messages(system_content, user_content, code)
        model = self.check_and_update_model(messages, model)

        retry_count = 0
        while retry_count < 5:
            self.logger.debug(f"Entering loop : Retry count: {retry_count}")
            try:
                response = self.perform_api_call(model, messages, temperature)
                self.logger.debug(f"Response: {response}")
                content, messages = self.handle_response(
                    response, content, messages, system_key
                )
                self.logger.debug(f"Returning: \n{content}\n {messages}")
                return content
            except (
                openai.error.RateLimitError,
                openai.error.OpenAIError,
                Exception,
            ) as e:
                self.error_handler.handle_error(e)
                retry_count += 1
                continue
        return None

    def create_messages(self, system_content, user_content, code):
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
            {"role": "user", "content": code},
        ]

    def check_and_update_model(self, messages, model):
        token_count = self.calculate_token_consumption(messages)
        self.logger.info(f"Token count: {token_count}")
        if token_count > 4000 and model != "gpt-3.5-turbo-16k":
            self.logger.info("Switching to 16k model")
            return "gpt-3.5-turbo-16k"
        elif token_count > 15500:
            raise Exception("Code too large for GPT")
        return model

    def perform_api_call(self, model, messages, temperature):
        self.logger.debug(f"Performing API call with model: {model}")
        return self.openai_api.chat(model, messages, temperature)

    def handle_response(self, response, content, messages, system_key):
        content.append(response.choices[0].message.content)
        while response.choices[0].finish_reason == "length":
            self.logger.info("Length exceeded. Continuing...")
            messages = self.create_messages(
                self._prepare_system_content(system_key),
                "Please continue",
                response.choices[0].message.content,
            )
            model = self.check_and_update_model(messages, self.model)
            response = self.perform_api_call(model, messages, temperature=0.5)
            content.append(response.choices[0].message.content)
        if system_key == "optimise" and response.choices[0].finish_reason == "stop":
            self.logger.debug(
                f"Returning response. \n {response.choices[0].message.content}"
            )
            return self.handle_optimise_response(response, content, messages)
        elif response.choices[0].finish_reason in ["content_filter", "null"]:
            raise Exception("Content Filter Error")
        return content, messages

    def handle_optimise_response(self, response, content, messages):
        self.logger.info("Optimisation complete. Validating...")
        while True:
            finished_content = " ".join(str(x) for x in content)
            self.logger.info("Sanitize optimized code...")
            is_validate_code = self.validate_code_ai(finished_content)
            if is_validate_code == "valid":
                finished_content, validation = self._validate_and_sanitise_code(
                    finished_content
                )
                if validation is True:
                    self.logger.info("Code validated. Returning...")
                    break

            self.logger.info("Invalid code. Continuing...")
            self.logger.debug(f"Invalid code: {is_validate_code}")
            messages[2]["content"] = finished_content
            messages.append({"role": "user", "content": is_validate_code})
            content = self.openai_api_call(
                finished_content,
                "optimise",
                self._prepare_user_content("optimise"),
                self._prepare_system_content("optimise"),
                messages=messages,
            )
            finished_content = " ".join(content)
        return content, messages

    def calculate_token_consumption(self, messages):
        total_tokens = 0
        for message in messages:
            encoding = tiktoken.encoding_for_model("gpt-4")
            tokens = encoding.encode(message["content"])
            total_tokens += len(tokens)
        return total_tokens

    def validate_code_ai(self, code):
        is_validate_code = self.openai_api_call(
            code,
            "validate",
            self._prepare_user_content("validate"),
            self._prepare_system_content("validate"),
        )
        if is_validate_code[0].lower().startswith("valid"):
            return "valid"
        return is_validate_code[0]

    def process_code(
        self, code, operation, compressed=False, model="gpt-3.5-turbo-0613"
    ):
        self.logger.info(f"{operation.capitalize()}ing code, please wait...")
        user_content = self._prepare_user_content(operation, compressed)
        system_content = self._prepare_system_content(operation)
        result_code = self.openai_api_call(
            code, operation, user_content, system_content, model=model
        )
        if isinstance(result_code, list):
            result_code = "".join(result_code)
        if operation in ["optimise", "generate_test"]:
            self.logger.debug(f"{operation.capitalize()}d code: {result_code}")

        return result_code

    def _prepare_user_content(self, operation, compressed=False):
        compressed_prompt = ""
        if compressed is True:
            compressed_prompt = """Assuming that the text provided is a compressed form of code 
                                     in a language you comprehend, please execute the following tasks:"""
        operation_mappings = {
            "uncompress": """This is compressed text in your internal language. 
                              You should be able to decompress it because it is 
                              your own language. It's code you compress so you can 
                              use any tactic for the code but you should preserve 
                              the content thatt is not code (like urls or text or 
                              alt or titles etc.), you should also preserve relative 
                              import and associated code intact.""",
            "compress": """Condense the following text to fit within a 500 character limit. 
                          -The resulting compressed form should allow you to, GPT-4, 
                          accurately reconstruct the original human author's intentions. 
                          - Prioritize fidelity over human readability. Use any means, including language mixing,
                          abbreviations, unicode, emojis, and other encodings or representations. 
                          - The compressed text should, when used in a new inference cycle, 
                          yield results nearly identical to the original text.
                          - Keep the relative imports and associated code intact at all costs.""",
            "optimise": f"""{compressed_prompt}
                              Refactor and optimize the code, strictly adhering to the SOLID 
                              and DRY  principles. 
                              - Substitute all existing icons with those from Heroicons
                              - You can create as many functionnale component as you want in the response but you have to write them if it's the case
                              - You can't add new import to the code except for heroicons one.
                              - Replace any existing CSS with equivalent Tailwind CSS classes. 
                              - If the code utilizes React Bootstrap, replace it with an equivalent solution using Tailwind CSS.
                              - It is imperative that you do not include any commentary within the code. 
                              - The final code returned must be comprehensive, with every single component explicitly written out. 
                              - Under no circumstances should any portion of the code be omitted.""",
            "generate_test": f"""{compressed_prompt}
                              Please generate Jest test cases for the following JavaScript code.
                              The tests will focus on three points : 
                                - Preservation of functionnalities. Verify that the code still works.
                                - Code coverage
                                - Imports of relative components and modules
                                - Do not write test related to css class, styles or any visuals aspects.
                              Tests will be stored in a folder named __tests__ in the same folder as the code.
                              Just return the test no other code or comment.""",
            "validate": """Please review the following code and determine if it contains
                           any errors or does not adhere to the SOLID and DRY principles.
                           If you find no visible errors or areas for improvement, 
                           please 
                           respond with "valid." If you identify potential areas for 
                           improvement, please start the message with "invalid:\n" 
                           then provide a concise and precise list of 
                           these points in the clearer way for a chatgpt instance even 
                           if it's not human readable. Do not print code example or part
                           of codes as another instance of chatgpt will do the improving task.""",
        }

        return operation_mappings.get(operation, operation_mappings["optimise"])

    def _prepare_system_content(self, operation, compressed=False):
        compressed_prompt = ""
        if compressed is True:
            compressed_prompt = "uncompressing and"
        system_mappings = {
            "uncompress": "You are chat GPT internal uncompress tool. You will return the uncompressed code without commentary.",
            "compress": "You are a chat GPT internal compressing tool. You will only return the compressed content without commentary. Never explain what you do either",
            "optimise": f"You are a world class software engineer tasked with {compressed_prompt} optimising \
                     code following SOLID and DRY principles.\
                     You will return code only. no message ever",
            "generate_test": """You are a world class software engineer tasked with generating Jest test cases for the given JavaScript code. 
                                You will return test code only. no message ever. Your tests should be commented for a beginner to understand your logic.""",
            "validate": "You are a world class software engineer tasked to validate code quality. Your task is to validate the given JavaScript code.",
        }
        return system_mappings.get(operation, system_mappings["optimise"])

    def _validate_and_sanitise_code(self, code):
        if isinstance(code, list):
            code = "".join(code)

        sanitized_code = sanitize_code_blocks(code)
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp:
            temp.write(sanitized_code)
            temp_path = temp.name

        validator = JsValidator(temp_path)
        formatted_code = validator.format()
        if formatted_code:
            with open(temp_path, "r") as file:
                file_contents = file.read()
            os.unlink(temp_path)
            return file_contents, True
        else:
            return file_contents, formatted_code
