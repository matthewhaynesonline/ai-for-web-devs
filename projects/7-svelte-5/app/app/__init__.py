import json
import os
import threading

from flask import Flask, current_app, g, jsonify, render_template, request, Response
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.database import db_init_app, db
from app.models import User, Chat

from app.services.app_logger import AppLogger
from app.services.chat_manager import ChatManager
from app.services.cli_commands import register_cli_commands
from app.services.image_gen import ImageGen, ImageGenStub
from app.services.app_llm import AppLlm
from app.services.llm_http_client import LlmHttpClient
from app.services.embedding_service import EmbeddingService
from app.services.content_store import ContentStore, OpenSearchConfig


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["APP_SECRET_KEY"]
    db_init_app(app)

    with app.app_context():
        attach_services(app)
        register_cli_commands(app)
        app_boot(app)

    @app.errorhandler(404)
    def not_found(e):
        user = get_user()

        return render_template(
            "404.html",
            title=app.config["APP_NAME"],
            model=app.config["MODEL"],
            user=user,
        ), 404

    if not app.config["DEBUG"]:

        @app.errorhandler(Exception)
        def handle_error(e):
            user = get_user()
            status_code = e.code if isinstance(e, HTTPException) else 500

            return render_template(
                "error.html",
                title=app.config["APP_NAME"],
                model=app.config["MODEL"],
                user=user,
            ), status_code

    @app.route("/", methods=["GET"])
    def index() -> str:
        user = get_user()
        chat = get_chat()
        chat_json = json.dumps(chat.to_dict())

        return render_template(
            "index.html",
            title=app.config["APP_NAME"],
            model=app.config["MODEL"],
            user=user,
            chat=chat,
            chat_json=chat_json,
        )

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

        classification = app.app_llm.classify_message(user_input)

        if classification.is_image:
            image_gen_prompt = app.app_llm.get_diffusion_prompt_from_input(
                input=user_input
            )

            image_filename = app.image_gen.gen_image_from_prompt(
                prompt=image_gen_prompt
            )

            chat_message = app.chat_manager.get_generated_image_and_save_messages(
                image_filename=image_filename,
                prompt=user_input,
                chat=chat,
                user=user,
            )

            return jsonify({"output": chat_message.content})
        else:
            app.chat_manager.create_chat_message(
                content=user_input, chat=chat, user=user
            )

            return Response(
                app.chat_manager.get_llm_response_stream_and_save_messages(chat=chat),
                mimetype="text/event-stream",
            )

    @app.route("/image-generate", methods=["POST"])
    def image_generate():
        user_input = request.json["prompt"].strip()

        user = get_user()
        chat = get_chat()

        image_filename = app.image_gen.gen_image_from_prompt(prompt=user_input)

        chat_message = app.chat_manager.get_generated_image_and_save_messages(
            image_filename=image_filename,
            prompt=user_input,
            chat=chat,
            user=user,
        )

        return jsonify({"output": chat_message.content})

    # @app.route("/chats", methods=["GET"])
    # def chats():
    #     chats = db.session.execute(db.select(Chat)).scalars().all()
    #     chats = list(map(lambda chat: chat.to_dict(), chats))

    #     return jsonify(chats), 200

    # @app.route("/chats/<id>", methods=["GET"])
    # def chat(id: int):

    @app.route("/chats/<id>/chat-messages", methods=["DELETE"])
    def delete_chat_messages(id: int):
        chat = get_chat()
        app.chat_manager.delete_chat_content(chat=chat)

        return jsonify(), 204

    @app.route("/refresh", methods=["GET"])
    def refresh() -> str:
        user = get_user()

        app.content_store.refresh_index()

        return render_template(
            "page.html",
            title=app.config["APP_NAME"],
            model=app.config["MODEL"],
            user=user,
            message="Index Refreshed",
        )

    @app.route("/document", methods=["POST"])
    def add_document():
        title = request.json["title"]
        body = request.json["body"]

        app.content_store.add_document(title, body)

        return jsonify({}), 200

    @app.route("/document/find/<query>", methods=["GET"])
    def find_document(query: str):
        result = app.content_store.find_document(query)

        return jsonify(result), 200

    return app


def attach_services(app: Flask) -> None:
    app.logger_service = AppLogger(
        log_dir=app.config["LOGS_DIR"], log_file=app.config["LOG_FILE"]
    )

    app.llm_http_client = LlmHttpClient(
        inference_api_url=current_app.config["INFERENCE_API_URL"]
    )

    app.embedding_service = EmbeddingService(
        inference_api_url=current_app.config["INFINITY_INSTANCE_URL"],
        model=current_app.config["EMBEDDING_MODEL"],
    )

    search_config = OpenSearchConfig(
        hostname=current_app.config["SEARCH_HOSTNAME"],
        port=current_app.config["SEARCH_PORT"],
        auth=(
            current_app.config["SEARCH_USER"],
            current_app.config["SEARCH_PASSWORD"],
        ),
    )

    app.content_store = ContentStore(
        search_config=search_config,
        content_dir=current_app.config["CONTENT_DIR"],
        embedding_service=app.embedding_service,
    )

    app.app_llm = AppLlm(
        content_store=app.content_store,
        inference_small_api_url=app.config["INFERENCE_SMALL_API_URL"],
        llm_http_client=app.llm_http_client,
        logger=app.logger_service,
        debug=app.config["DEBUG"],
    )

    generated_images_dir = app.config["GENERATED_IMAGES_DIR"]
    os.makedirs(generated_images_dir, exist_ok=True)

    if app.config["FAKE_GENERATION"]:
        app.image_gen = ImageGenStub()
    else:
        app.image_gen = ImageGen(images_dir=generated_images_dir)

    app.chat_manager = ChatManager(
        db_uri=current_app.config["SQLALCHEMY_DATABASE_URI"],
        app_llm=app.app_llm,
        image_gen=app.image_gen,
        images_dir_url_path=app.config["GENERATED_IMAGES_DIR_URL_PATH"],
    )


def app_boot(app: Flask) -> None:
    # Eagerly load the LLM
    # Use thread to not block render
    # https://github.com/ollama/ollama/blob/main/docs/faq.md#how-can-i-preload-a-model-into-ollama-to-get-faster-response-times
    thread = threading.Thread(
        target=app.app_llm.get_llm_response_for_single_message, args=("")
    )
    thread.start()


def get_user() -> User:
    if "user" not in g:
        g.user = db.session.execute(db.select(User).limit(1)).scalar_one()

    return g.user


def get_chat() -> Chat:
    if "chat" not in g:
        g.chat = db.session.execute(db.select(Chat).limit(1)).scalar_one()

    return g.chat
