import os


class Config:
    BOT_TOKEN: str
    DB_PATH: str

    def __init__(self) -> None:
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.DB_PATH = os.getenv("DB_PATH", "data/concrete.db")

        if not self.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN is required. Добавьте BOT_TOKEN в файл .env и перезапустите бота."
            )


config = Config()
