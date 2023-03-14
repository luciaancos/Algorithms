import logging
import asyncio
import sys

from game_server import GameServer

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        # Choose an available port
        port = 0

    # Note: some people think that listening on all interfaces is a bad practice
    server = GameServer()
    await server.start_server("", port)


if __name__ == "__main__":
    # TODO: Do not show the whole traceback when pressing Ctrl+C
    asyncio.run(main())
