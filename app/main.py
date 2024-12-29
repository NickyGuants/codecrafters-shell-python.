import sys


def main():
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
            case _:
                print(f"{user_input}: command not found")


def exit_shell(arg):
    sys.exit(int(arg))


if __name__ == "__main__":
    main()
