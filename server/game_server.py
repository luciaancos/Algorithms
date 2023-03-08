import socketserver
import logging
import threading

import packet
from packet import Message
from game_manager import GameManager

logger = logging.getLogger(__name__)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    game_manager = GameManager()

    def handle_message(self, msg: Message):
        pass

    def handle(self):
        while True:
            msg = packet.recv_from_socket(self.request)
            if msg is None:
                break
            logger.debug(
                f"Received {msg} from {self.request.getpeername()} on thread {threading.current_thread().name}")
            self.handle_message(msg)
