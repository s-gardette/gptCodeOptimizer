# gpt-optimize

`gpt-optimize` is a Python library designed to process and optimize a given set of code files using OpenAI's `gpt-3.5-turbo-0613` model. It also takes care of logging, error handling, and supports both single files and entire directories.

## Features

- **Code Optimization**: Optimizes JavaScript and TypeScript files using AI.
- **Debugging Support**: Includes a debug mode for detailed logging.
- **Directory Processing**: Can process entire directories of code files.
- **File Saving**: Saves the optimized code to a specified location.
- **Missing Import Handling**: Track missing imports for a given codebase.
- **Test File Generation**: Automatically generates test files for the processed code. (in progress)

## Installation

To install all the dependencies, you can use pip:

```sh
pip install -r requirements.txt
```

## How to use

```sh
python main.py --input <input_folder> --output <output_folder> --debug
```

- `<input_folder>` is the directory path of your input files.
- `<output_folder>` is the directory path where you want your output files to be saved.
- `--debug` is an optional argument that enables debugging mode.

You can also specify a path to your project's codebase with `--codebase_path`.

## Classes

### 1. `CodeProcessor`

- Initializes with a logger and a model (default is `"gpt-3.5-turbo-0613"`).
- Includes methods to process code, save it, and create test files.

### 2. `OpenAiHelper`

- Helps with processing code by calling the OpenAI API.

### 3. `MissingImport`

- Handles missing imports in a given codebase.

### 4. `OpenAiApi`

- A wrapper around the OpenAI API.

### 5. `ErrorHandler`

- Handles errors occurring during the OpenAI API calls.

## Dependencies

- Python 3.7 or newer.
- OpenAI API Key.
- Dotenv Python library for loading environment variables.
- Other dependencies as mentioned in the `requirements.txt`.

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

## License

Please refer to the included `LICENSE` file for rights and limitations under the terms of the license.
