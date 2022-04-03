import sys

from .database import DB
from .bot import Bot


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "migrate":
        DB().create_migrations(
            sys.argv[2] == "--empty" if len(sys.argv) >= 3 else False
        )
    else:
        bot = Bot()
        bot.run()


if __name__ == "__main__":
    main()
