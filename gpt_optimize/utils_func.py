def sanitize_code_blocks(file_content):
    lines = file_content.split("\n")

    in_code_block = False
    code_lines = []
    code_block_found = False

    for line in lines:
        if line.strip().startswith("```"):  # check if line starts with backticks
            in_code_block = not in_code_block
            code_block_found = True  # update flag
            continue  # skip the markdown syntax line itself
        elif in_code_block:
            code_lines.append(line)

    # If a code block was found, return the code lines, otherwise return original content
    return "\n".join(code_lines) if code_block_found else file_content
