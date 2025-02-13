import os


class Config:
    APP_NAME = "MattGPT"
    APP_PORT = os.getenv("APP_PORT")
    # Cast bool from env var
    # https://stackoverflow.com/a/65407083
    DEBUG = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "t")
    CONTENT_DIR = os.path.dirname(__file__) + "/content"
    STATIC_FILES_DIR = "static"
    GENERATED_IMAGES_DIR = os.path.join(STATIC_FILES_DIR, "generated-images")

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
