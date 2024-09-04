from multiprocessing import Process

from .startup.bot import start_bot
from .startup.web import start_web


def main() -> None:
    # Initialize the database
    # TODO(es3n1n): figure why it produces an unclosed transaction in production
    # asyncio_run(db.init())  # noqa: ERA001

    # Start the web
    web_process = Process(target=start_web)
    web_process.start()

    # Start the telegram bot
    start_bot()


if __name__ == '__main__':
    main()
