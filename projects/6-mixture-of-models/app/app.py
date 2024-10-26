import json
import os
import threading

from flask import Flask, current_app, g, jsonify, render_template, request, Response

from config import Config
from database import init_app, db
from models import User, Chat, ChatMessageRole

from services.app_logger import AppLogger
from services.chat_manager import ChatManager
from services.cli_commands import register_cli_commands
from services.image_gen import ImageGen
from services.app_llm import AppLlm
from services.llm_http_client import LlmHttpClient
from services.embedding_service import EmbeddingService
from services.content_store import ContentStore, OpenSearchConfig


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_app(app)

    with app.app_context():
        app_boot()

        chat_manager = get_chat_manager()
        logger = get_app_logger()
        # https://stackoverflow.com/a/76884963
        register_cli_commands(app, chat_manager, logger)

    @app.errorhandler(404)
    def not_found(e):
        user = get_user()

        return render_template(
            "404.html",
            title=current_app.config["APP_NAME"],
            model=current_app.config["MODEL"],
            user=user,
        )

    if not app.config["DEBUG"]:

        @app.errorhandler(Exception)
        def handle_error(e):
            user = get_user()

            return render_template(
                "error.html",
                title=current_app.config["APP_NAME"],
                model=current_app.config["MODEL"],
                user=user,
            )

    @app.route("/", methods=["GET"])
    def index():
        user = get_user()
        chat = get_chat()
        chat_json = json.dumps(chat.to_dict())

        return render_template(
            "index.html",
            title=current_app.config["APP_NAME"],
            model=current_app.config["MODEL"],
            user=user,
            chat=chat,
            chat_json=chat_json,
        )

    @app.route("/refresh", methods=["GET"])
    def refresh():
        user = get_user()

        content_store = get_content_store()
        content_store.refresh_index()

        return render_template(
            "page.html",
            title=current_app.config["APP_NAME"],
            model=current_app.config["MODEL"],
            user=user,
            message="Index Refreshed",
        )

    @app.route("/document", methods=["POST"])
    def add_document():
        title = request.json["title"]
        body = request.json["body"]

        content_store = get_content_store()
        content_store.add_document(title, body)

        return jsonify({}), 200

    @app.route("/document/find/<query>", methods=["GET"])
    def find_document(query: str):
        content_store = get_content_store()
        result = content_store.find_document(query)

        return jsonify(result), 200

    # # Deprecated
    # @app.route("/prompt", methods=["POST"])
    # def prompt():
    #     user_input = request.json["prompt"].strip()
    #     app_llm = get_app_llm()

    #     output = app_llm.get_llm_response(input=user_input)

    #     return jsonify({"output": output})

    @app.route("/prompt-stream", methods=["POST"])
    def prompt_stream():
        user_input = request.json["prompt"].strip()

        user = get_user()
        chat = get_chat()
        chat_manager = get_chat_manager()

        app_llm = get_app_llm()
        classification = app_llm.classify_message(user_input)

        if classification.is_image:
            image_gen_prompt = app_llm.get_diffusion_prompt_from_input(input=user_input)

            image_gen = get_image_gen()
            image_filename = image_gen.gen_image_from_prompt(prompt=image_gen_prompt)

            chat_message = chat_manager.get_generated_image_and_save_messages(
                image_filename=image_filename,
                image_dir_path=app.config["GENERATED_IMAGES_DIR"],
                prompt=user_input,
                assistantRole=ChatMessageRole.ASSISTANT,
                userRole=ChatMessageRole.USER,
                chat=chat,
                user=user,
            )

            return jsonify({"output": chat_message.body})
        else:
            chat_manager.create_chat_message(
                body=user_input, role=ChatMessageRole.USER, chat=chat, user=user
            )

            chat_summary = ""
            chat_summary_last_message_id = 0

            if chat.chat_summary and chat.chat_summary.body:
                chat_summary = chat.chat_summary.body
                chat_summary_last_message_id = chat.chat_summary.last_message_id

            return Response(
                chat_manager.get_llm_response_stream_and_save_messages(
                    assistantRole=ChatMessageRole.ASSISTANT,
                    chat=chat,
                    chat_messages=chat.chat_messages,
                    chat_summary=chat_summary,
                    chat_summary_last_message_id=chat_summary_last_message_id,
                ),
                mimetype="text/event-stream",
            )

    @app.route("/image-generate", methods=["POST"])
    def image_generate():
        user_input = request.json["prompt"].strip()

        user = get_user()
        chat = get_chat()
        chat_manager = get_chat_manager()

        image_gen = get_image_gen()
        image_filename = image_gen.gen_image_from_prompt(prompt=user_input)

        chat_message = chat_manager.get_generated_image_and_save_messages(
            image_filename=image_filename,
            image_dir_path=app.config["GENERATED_IMAGES_DIR"],
            prompt=user_input,
            assistantRole=ChatMessageRole.ASSISTANT,
            userRole=ChatMessageRole.USER,
            chat=chat,
            user=user,
        )

        return jsonify({"output": chat_message.body})

    # @app.route("/chats", methods=["GET"])
    # def chats():
    #     chats = db.session.execute(db.select(Chat)).scalars().all()
    #     chats = list(map(lambda chat: chat.to_dict(), chats))

    #     return jsonify(chats), 200

    # @app.route("/chats/<id>", methods=["GET"])
    # def chat(id: int):

    @app.route("/chats/<id>/chat-messages", methods=["DELETE"])
    def delete_chat_messages(id: int):
        user = get_user()
        chat = get_chat()
        chat_manager.delete_chat_messages_and_summary_for_chat(chat=chat, user=user)

        return jsonify(), 204

    return app


def app_boot():
    app_llm = get_app_llm()

    # Eagerly load the LLM
    # Use thread to not block render
    # https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-preload-a-model-into-ollama-to-get-faster-response-times
    thread = threading.Thread(target=app_llm.get_llm_response, args=("", False))
    thread.start()


def get_llm_http_client() -> LlmHttpClient:
    if "llm_http_client" not in g:
        g.llm_http_client = LlmHttpClient(
            inference_api_url=current_app.config["INFERENCE_API_URL"]
        )

    return g.llm_http_client


def get_app_llm() -> AppLlm:
    if "app_llm" not in g:
        llm_http_client = get_llm_http_client()
        content_store = get_content_store()
        logger = get_app_logger()

        g.app_llm = AppLlm(
            inference_small_api_url=current_app.config["INFERENCE_SMALL_API_URL"],
            llm_http_client=llm_http_client,
            content_store=content_store,
            logger=logger,
            debug=current_app.config["DEBUG"],
        )

    return g.app_llm


def get_embedding_service() -> EmbeddingService:
    if "embedding_service" not in g:
        g.embedding_service = EmbeddingService(
            inference_api_url=current_app.config["INFINITY_INSTANCE_URL"],
            model=current_app.config["EMBEDDING_MODEL"],
        )

    return g.embedding_service


def get_content_store() -> ContentStore:
    if "content_store" not in g:
        embedding_service = get_embedding_service()

        search_config = OpenSearchConfig(
            hostname=current_app.config["SEARCH_HOSTNAME"],
            port=current_app.config["SEARCH_PORT"],
            auth=(
                current_app.config["SEARCH_USER"],
                current_app.config["SEARCH_PASSWORD"],
            ),
        )

        g.content_store = ContentStore(
            search_config=search_config,
            content_dir=current_app.config["CONTENT_DIR"],
            embedding_service=embedding_service,
        )

    return g.content_store


def get_user() -> User:
    if "user" not in g:
        g.user = db.session.execute(db.select(User).limit(1)).scalar_one()

    return g.user


def get_chat() -> Chat:
    if "chat" not in g:
        g.chat = db.session.execute(db.select(Chat).limit(1)).scalar_one()

    return g.chat


def get_chat_manager() -> ChatManager:
    if "chat_manager" not in g:
        app_llm = get_app_llm()

        g.chat_manager = ChatManager(
            db_uri=current_app.config["SQLALCHEMY_DATABASE_URI"], app_llm=app_llm
        )

    return g.chat_manager


def get_image_gen() -> ImageGen:
    if "image_gen" not in g:
        generated_images_dir = current_app.config["GENERATED_IMAGES_DIR"]
        os.makedirs(generated_images_dir, exist_ok=True)

        g.image_gen = ImageGen(images_dir=generated_images_dir)

    return g.image_gen


def get_app_logger() -> AppLogger:
    if "app_logger" not in g:
        g.app_logger = AppLogger(log_dir="logs", log_file="app.log")

    return g.app_logger


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=app.config["APP_PORT"], debug=app.config["DEBUG"])
