import os


class Config:
    APP_NAME = "MattGPT"
    APP_PORT = os.getenv("APP_PORT")
    APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
    # Cast bool from env var
    # https://stackoverflow.com/a/65407083
    DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "t")

    APP_USE_FLASH_ATTENTION = os.getenv("APP_USE_FLASH_ATTENTION", "False").lower() in (
        "true",
        "1",
        "t",
    )

    FAKE_GENERATION = os.getenv("FAKE_GENERATION", "False").lower() in (
        "true",
        "1",
        "t",
    )

    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

    CONTENT_DIR_NAME = "content"
    CONTENT_DIR = os.path.join(PROJECT_DIR, CONTENT_DIR_NAME)

    LOGS_DIR = os.path.join(PROJECT_DIR, "logs")
    LOG_FILE = "app.log"

    STATIC_FILES_DIR_NAME = "static"
    STATIC_FILES_DIR = os.path.join(PROJECT_DIR, STATIC_FILES_DIR_NAME)

    GENERATED_IMAGES_DIR_NAME = "generated-images"
    GENERATED_IMAGES_DIR = os.path.join(STATIC_FILES_DIR, GENERATED_IMAGES_DIR_NAME)
    GENERATED_IMAGES_DIR_URL_PATH = (
        f"/{STATIC_FILES_DIR_NAME}/{GENERATED_IMAGES_DIR_NAME}"
    )

    DB_ADAPTER = os.getenv("DB_ADAPTER")
    DB_HOSTNAME = os.getenv("DB_HOSTNAME")
    DB_PORT = os.getenv("DB_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    # https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#dialect-postgresql-psycopg-connect
    SQLALCHEMY_DATABASE_URI = f"{DB_ADAPTER}+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{POSTGRES_DB}"

    INFERENCE_API_URL = os.getenv("INFERENCE_API_URL")
    MODEL = os.getenv("INFERENCE_MODEL_NAME")

    INFERENCE_SMALL_API_URL = os.getenv("INFERENCE_SMALL_API_URL")

    INFINITY_INSTANCE_URL = os.getenv("INFINITY_INSTANCE_URL")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

    SEARCH_HOSTNAME = os.getenv("OPENSEARCH_HOSTNAME")
    SEARCH_PORT = os.getenv("OPENSEARCH_REST_API_PORT_HOST")
    SEARCH_USER = os.getenv("OPENSEARCH_USER")
    SEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
