import sys


def main():
    while True:
        sys.stdout.write("$ ")
        # Wait for user input
        user_input = input()
        match user_input:
            case 'exit 0':
                exit_shell()
            case _:
                print(f"{user_input}: command not found")


def exit_shell():
    sys.exit(0)


if __name__ == "__main__":
    main()
