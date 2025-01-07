import os
import re
import subprocess
import sys

noclobber = False


def main():
    global noclobber
    builtin_commands = ['exit', 'echo', 'type', 'pwd', 'cd', 'set']

    while True:
        try:
            sys.stdout.write("$ ")
            user_input = input().strip()
        except EOFError:
            print()
            break  # Exit on Ctrl+D
        except KeyboardInterrupt:
            print()  # Handle Ctrl+C gracefully
            continue

        if not user_input:
            continue  # Ignore empty input

        # Tokenize input
        parts = tokenize(user_input)
        if not parts:
            continue

        # Parse command and redirections
        command_parts, redirections = parse_command(parts)
        if not command_parts:
            continue  # Nothing to execute

        # Extract command and arguments
        command = command_parts[0]
        args = command_parts[1:]

        # Handle built-in commands or external commands
        if command in builtin_commands:
            handle_builtin(command, args, redirections)
        else:
            execute_external(command, args, redirections)


def tokenize(input_line):
    NORMAL, IN_SINGLE_QUOTE, IN_DOUBLE_QUOTE, ESCAPE = 0, 1, 2, 3
    tokens = []
    current_token = []
    state = NORMAL

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
                    if next_char in ['\\', '"', '$', '`']:
                        current_token.append(next_char)
                    else:
                        current_token.append('\\')
                        current_token.append(next_char)
                else:
                    current_token.append('\\')
            elif char == '"':
                state = NORMAL
            else:
                current_token.append(char)

        i += 1

    if state in [IN_SINGLE_QUOTE, IN_DOUBLE_QUOTE]:
        print("Error: unmatched quote detected")
        return []

    if current_token:
        tokens.append(''.join(current_token))

    return tokens


def parse_command(parts):
    command_parts = []
    redirections = []  # List of tuples: (fd, mode, filename)
    i = 0
    while i < len(parts):
        token = parts[i]
        # Match redirection operators with optional file descriptors
        redir_match = re.match(r'^(\d+)?(>|>\|)$', token)
        if redir_match:
            fd = int(redir_match.group(1)) if redir_match.group(1) else 1  # Default to stdout
            operator = redir_match.group(2)
            mode = 'w'  # Overwrite by default
            if operator == '>|':
                mode = 'w'  # Force overwrite, ignoring noclobber

            # Next token should be the filename
            if i + 1 < len(parts):
                filename = parts[i + 1]
                i += 1
            else:
                print("Syntax error: no file specified for redirection")
                return ([], [])

            # Handle noclobber
            if operator == '>' and noclobber and os.path.exists(filename):
                print(f"Error: {filename} already exists. Use '>|' to overwrite.")
                redirections = []  # Clear redirections
                break

            # Append redirection details
            redirections.append((fd, mode, filename))
        else:
            command_parts.append(token)
        i += 1

    return command_parts, redirections


def handle_builtin(command, args, redirections):
    match command:
        case 'exit':
            exit_shell(args)
        case 'echo':
            handle_echo(args, redirections)
        case 'type':
            handle_type(args)
        case 'pwd':
            handle_pwd(redirections)
        case 'cd':
            handle_cd(args)
        case 'set':
            handle_set(args)
        case _:
            print(f"Unknown builtin command: {command}")


def exit_shell(args):
    if not args:
        status = 0
    else:
        try:
            status = int(args[0])
        except ValueError:
            print("exit: numeric argument required")
            status = 1
    sys.exit(status)


def handle_echo(args, redirections):
    output = ' '.join(args)
    if redirections:
        for redir in redirections:
            fd, mode, filename = redir
            if fd == 1:
                try:
                    with open(filename, mode) as f:
                        f.write(output + '\n')
                except IOError as e:
                    print(f"Redirection error: {e}", file=sys.stderr)
            elif fd == 2:
                # For simplicity, only handle stdout (fd=1) and stderr (fd=2)
                print(f"echo: Unsupported file descriptor {fd}", file=sys.stderr)
            else:
                print(f"echo: Unsupported file descriptor {fd}", file=sys.stderr)
    else:
        print(output)


def handle_pwd(redirections):
    output = os.getcwd()
    if redirections:
        for redir in redirections:
            fd, mode, filename = redir
            if fd == 1:
                try:
                    with open(filename, mode) as f:
                        f.write(output + '\n')
                except IOError as e:
                    print(f"Redirection error: {e}", file=sys.stderr)
            elif fd == 2:
                print(f"pwd: Unsupported file descriptor {fd}", file=sys.stderr)
            else:
                print(f"pwd: Unsupported file descriptor {fd}", file=sys.stderr)
    else:
        print(output)


def handle_type(args):
    if not args:
        print("type: missing arguments")
        return
    path = os.environ.get("PATH", "")
    dirs = path.split(":")
    for cmd in args:
        if cmd in ['exit', 'echo', 'type', 'pwd', 'cd', 'set']:
            print(f"{cmd} is a shell builtin")
            continue
        found = False
        for directory in dirs:
            if not directory:
                continue
            cmd_path = os.path.join(directory, cmd)
            if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
                print(f"{cmd} is {cmd_path}")
                found = True
                break
        if not found:
            print(f"{cmd}: not found")


def handle_cd(args):
    if len(args) > 1:
        print("cd: too many arguments")
    else:
        new_dir = os.path.expanduser(args[0]) if args else os.environ.get("HOME")
        new_dir = os.path.expandvars(new_dir)
        try:
            os.chdir(new_dir)
        except FileNotFoundError:
            print(f"cd: {new_dir}: No such file or directory")
        except NotADirectoryError:
            print(f"cd: {new_dir}: Not a directory")
        except PermissionError:
            print(f"cd: {new_dir}: Permission denied")


def handle_set(args):
    global noclobber
    if not args:
        print("set: missing arguments")
        return
    if args[0] == '-o' and len(args) >= 2:
        option = args[1]
        if option == 'noclobber':
            noclobber = True
            print("noclobber option enabled")
        else:
            print(f"set: unknown option {option}")
    elif args[0] == '+o' and len(args) >= 2:
        option = args[1]
        if option == 'noclobber':
            noclobber = False
            print("noclobber option disabled")
        else:
            print(f"set: unknown option {option}")
    else:
        print("set: invalid syntax")


def execute_external(command, args, redirections):
    # Retrieve current PATH
    path = os.environ.get("PATH", "")
    dirs = path.split(":")
    program_path = None
    for directory in dirs:
        if not directory:
            continue
        potential_path = os.path.join(directory, command)
        if os.path.isfile(potential_path) and os.access(potential_path, os.X_OK):
            program_path = potential_path
            break
    if not program_path:
        print(f"{command}: command not found")
        return

    # Prepare subprocess arguments
    full_command = [program_path] + args

    # Set up redirection if needed
    stdout = None
    stderr = None
    for redir in redirections:
        fd, mode, filename = redir
        try:
            if fd == 1:
                stdout = open(filename, mode)
            elif fd == 2:
                stderr = open(filename, mode)
            else:
                print(f"Error: Unsupported file descriptor {fd}", file=sys.stderr)
                return
        except IOError as e:
            print(f"Redirection error: {e}", file=sys.stderr)
            return

    # Execute the command
    try:
        result = subprocess.run(
            full_command,
            text=True,
            stdout=stdout if stdout else None,
            stderr=stderr if stderr else None
        )
    finally:
        if stdout:
            stdout.close()
        if stderr:
            stderr.close()


def handle_external_output(command, result, redirections):
    # This function is no longer needed as redirection is handled via subprocess.run
    pass


if __name__ == "__main__":
    main()
