import os
import re
import subprocess
import sys


def main():
    builtin_commands = ['exit', 'echo', 'type', 'pwd', 'cd']
    path = os.environ.get("PATH")
    dirs = path.split(":")
    while True:
        sys.stdout.write("$ ")
        # Wait for user input
        user_input = input().strip()
        found = False
        # differentiate command from arguments
        parts = tokenize(user_input)
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        match command:
            case 'exit':
                exit_shell(args[0])
            case 'echo':
                print(f"{' '.join(args)}")
            case 'type':
                cmd = args[0]
                if cmd in builtin_commands:
                    print(f"{cmd} is a shell builtin")
                else:
                    found = False
                    for directory in dirs:
                        if not directory:
                            continue
                        cmd_path = os.path.join(directory, cmd)
                        if os.path.isfile(cmd_path):
                            found = True
                            print(f"{cmd} is {cmd_path}")
                            break
                    if not found:
                        print(f"{cmd}: not found")
            case 'pwd':
                print(os.getcwd())
            case 'cd':
                new_dir = ''.join(args)
                if new_dir == '~':
                    os.chdir(os.environ.get("HOME"))
                else:
                    if not os.path.isdir(new_dir):
                        print(f"cd: {new_dir}: No such file or directory")
                    else:
                        os.chdir(new_dir)
            case _:
                for directory in dirs:
                    if not directory:
                        continue
                    program_path = os.path.join(directory, command)
                    if os.path.isfile(program_path):
                        found = True
                        full_command = [program_path] + args
                        result = subprocess.run(
                            full_command,
                            text=True,  # Treat input/output as text
                            capture_output=True  # Capture stdout/stderr
                        )
                        if result.stdout:
                            print(result.stdout, end='')
                        if result.stderr:
                            print(result.stderr, end='', file=sys.stderr)
                        break
                if not found:
                    print(f"{user_input}: command not found")


def exit_shell(arg):
    sys.exit(int(arg))


def tokenize(input_line):
    NORMAL = 0
    IN_SINGLE_QUOTE = 1
    IN_DOUBLE_QUOTE = 2
    ESCAPE = 3

    tokens = []
    current_token = []
    state = NORMAL
    escape_char = False

    i = 0
    while i < len(input_line):
        char = input_line[i]

        if state == NORMAL:
            if char == '\\':
                state = ESCAPE
            elif char == "'":
                state = IN_SINGLE_QUOTE
            elif char == '"':
                state = IN_DOUBLE_QUOTE
            elif char.isspace():
                if current_token:
                    tokens.append(''.join(current_token))
                    current_token = []
            else:
                current_token.append(char)

        elif state == ESCAPE:
            current_token.append(char)
            state = NORMAL

        elif state == IN_SINGLE_QUOTE:
            if char == "'":
                state = NORMAL
            else:
                current_token.append(char)

        elif state == IN_DOUBLE_QUOTE:
            if char == '\\':
                i += 1
                if i < len(input_line):
                    next_char = input_line[i]
                    # In double quotes, only certain characters can be escaped
                    if next_char in ['\\', '"', '$', '`']:
                        current_token.append(next_char)
                    else:
                        # Backslash remains
                        current_token.append('\\')
                        current_token.append(next_char)
                else:
                    # Backslash at end of string; treat as literal
                    current_token.append('\\')
            elif char == '"':
                state = NORMAL
            else:
                current_token.append(char)

        i += 1

    # Append the last token if any
    if current_token:
        tokens.append(''.join(current_token))

    return tokens


if __name__ == "__main__":
    main()
