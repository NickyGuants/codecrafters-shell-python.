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
        parts = parse_input(user_input)
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


def parse_input(user_input):
    pattern = r'\'[^\']*\'|\S+'
    matches = re.findall(pattern, user_input)
    return [arg.strip("'") for arg in matches]


if __name__ == "__main__":
    main()
