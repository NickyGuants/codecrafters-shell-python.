import os
import sys


def main():
    valid_commands = ['exit', 'echo', 'type']
    path = os.environ.get("PATH")
    while True:
        sys.stdout.write("$ ")
        # Wait for user input
        user_input = input()
        # differentiate command from arguments
        command = user_input.split()[0]
        args = user_input.split()[1:]
        match command:
            case 'exit':
                exit_shell(args[0])
            case 'echo':
                print(f"{' '.join(args)}")
            case 'type':
                cmd = args[0]
                if cmd in valid_commands:
                    print(f"{cmd} is a shell builtin")
                else:
                    found = False
                    dirs = path.split(":")
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
            case _:
                print(f"{user_input}: command not found")


def exit_shell(arg):
    sys.exit(int(arg))


if __name__ == "__main__":
    main()
