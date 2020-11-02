import asyncio
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RemoteCommanderServer:
    class Protocol:
        def __init__(self, command_handler):
            self._command_handler = command_handler

        @property
        def _name(self) -> str:
            return 'Commander server'

        def connection_made(self, transport):
            logger.info(f"{self._name} - connection established.")

        def connection_lost(self, exc):
            logger.info(f"{self._name} - connection lost.")

        def datagram_received(self, data, sender_address):
            command = data.decode()
            logger.info(f"{self._name} - Received '{command}' from {sender_address}.")
            self._command_handler(command)

    def __init__(self, port: int, command_handler: Callable[[str], None]):
        self._port = port
        self._command_handler = command_handler

    async def start(self):
        logger.info(f"Starting Command server on port {self._port}.")
        event_loop = asyncio.get_running_loop()
        await event_loop.create_datagram_endpoint(
            lambda: self.Protocol(self._command_handler),
            local_addr=('127.0.0.1', self._port))
