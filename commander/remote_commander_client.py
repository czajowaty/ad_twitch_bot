import asyncio
import socket
import sys


async def main_loop(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        command = input("Enter command: ")
        if command.strip().lower() == 'exit':
            return
        s.sendto(command.encode(), ('127.0.0.1', port))
        print(f"Sent command: '{command}'.")


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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_loop(port))


if __name__ == '__main__':
    main()
