import os


class Config:
    APP_NAME = "MattGPT"
    APP_PORT = os.getenv("APP_PORT")
    # Cast bool from env var
    # https://stackoverflow.com/a/65407083
    DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "t")

    OLLAMA_INSTANCE_URL = os.getenv("OLLAMA_INSTANCE_URL")
    MODEL = os.getenv("MODEL")
