import os


class Config:
    APP_NAME = "MattGPT"
    APP_PORT = os.getenv("APP_PORT")
    # Cast bool from env var
    # https://stackoverflow.com/a/65407083
    DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "t")
    CONTENT_DIR = os.path.dirname(__file__) + "/content"

    CHROMA_HOSTNAME = os.getenv("CHROMA_HOSTNAME")
    CHROMA_PORT = os.getenv("CHROMA_PORT")

    INFINITY_INSTANCE_URL = os.getenv("INFINITY_INSTANCE_URL")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

    OLLAMA_INSTANCE_URL = os.getenv("OLLAMA_INSTANCE_URL")
    MODEL = os.getenv("MODEL")
