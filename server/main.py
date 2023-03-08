import logging
import threading
import sys

from game_server import ThreadedTCPServer, ThreadedTCPRequestHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        # Choose an available port
        port = 0

    # Note: some people think that listening on all interfaces is a bad practice
    server = ThreadedTCPServer(("", port), ThreadedTCPRequestHandler)

    with server:
        ip, port = server.server_address
        logger.info(f"Server running on {ip}:{port}")

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()
