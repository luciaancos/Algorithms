import socketserver
import logging
import threading

from packet import Message, MessageSocket
from game_manager import GameManager

logger = logging.getLogger(__name__)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    game_manager = GameManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.msg_socket = MessageSocket(self.request)

    def handle_message(self, msg: Message):
        pass

    def handle(self):
        while True:
            msg = self.msg_socket.recv()
            if msg is None:
                break
            logger.debug(
                f"Received {msg} from {self.request.getpeername()} on thread {threading.current_thread().name}")
            self.handle_message(msg)
