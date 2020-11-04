import asyncio
import socket
import sys


def send_command(port: int, command: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(command.encode(), ('127.0.0.1', port))
    print(f"Sent command: '{command}'.")


async def main_loop(port):
    while True:
        command = input("Enter command: ")
        if command.strip().lower() == 'exit':
            return
        send_command(port, command)


def main():
    args = sys.argv
    if len(args) < 2:
        print("Provide receiver port.")
        return
    try:
        port = int(args[1])
    except ValueError as exc:
        print(f"Invalid port - {exc}.")
        return
    if len(args) == 2:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_loop(port))
    else:
        send_command(port, ' '.join(args[2:]))


if __name__ == '__main__':
    main()
