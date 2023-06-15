from gpt_optimize.gpt_optimize import CodeProcessor
import argparse
import logging
import os
from dotenv import load_dotenv


def parse_args():
    load_dotenv()  # Load .env variables

    parser = argparse.ArgumentParser(description="Your Script Description.")
    parser.add_argument(
        "--input", default=os.getenv("INPUT", "input"), help="Path to the input folder."
    )
    parser.add_argument(
        "--output",
        default=os.getenv("OUTPUT", "output"),
        help="Path to the output folder.",
    )
    parser.add_argument(
        "--codebase_path",
        default=os.getenv("CODEBASE_PATH", False),
        action="store_true",
        help="Path to your project codebase.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
        default=os.getenv("DEBUG", False),
    )

    parser.add_argument(
        "--extensions",
        action="store_true",
        help="Add comma separated list of allowed extensions",
        default=os.getenv("ALLOWED_EXTENSIONS", False),
    )

    parser.add_argument(
        "--tests",
        action="store_true",
        help="Generate tests for the code",
    )

    return parser.parse_args()


def main(args):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug(f'Debug mode is {"on" if args.debug else "off"}')

    print("Input path:", args.input)
    print("Output path:", args.output)
    print("Codebase path:", args.codebase_path)
    print("Allowed extensions:", args.extensions)

    processor = CodeProcessor(
        logger=logging, model="gpt-3.5-turbo-0613", tests=args.tests
    )
    processor.process_directory(
        args.input,
        args.output,
        code_base_path=args.codebase_path,
        allowed_extensions=args.extensions.split(",") if args.extensions else None,
    )


if __name__ == "__main__":
    args = parse_args()
    main(args)
