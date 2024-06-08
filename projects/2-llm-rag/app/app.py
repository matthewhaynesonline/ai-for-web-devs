import threading

from flask import Flask, current_app, g, jsonify, render_template, request, Response

from config import Config

from services.llm_client import LlmClient


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        app_boot()

    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "404.html",
            title=current_app.config["APP_NAME"],
            model=current_app.config["MODEL"],
        )

    if not app.config["DEBUG"]:

        @app.errorhandler(Exception)
        def handle_error(e):
            return render_template(
                "error.html",
                title=current_app.config["APP_NAME"],
                model=current_app.config["MODEL"],
            )

    @app.route("/", methods=["GET"])
    def index():
        return render_template(
            "index.html",
            title=current_app.config["APP_NAME"],
            model=current_app.config["MODEL"],
        )

    @app.route("/prompt", methods=["POST"])
    def prompt():
        user_input = request.json["prompt"].strip()
        llm_client = get_llm_client()

        output = llm_client.get_llm_response(input=user_input)

        return jsonify({"output": output})

    @app.route("/prompt-stream", methods=["POST"])
    def prompt_stream():
        user_input = request.json["prompt"].strip()
        llm_client = get_llm_client()

        return Response(
            llm_client.get_llm_response_stream(input=user_input),
            mimetype="text/event-stream",
        )

    return app


def app_boot():
    llm_client = get_llm_client()

    # Eagerly load the LLM
    # Use thread to not block render
    # TODO: not sure if this does anything
    thread = threading.Thread(target=llm_client.get_llm_response)
    thread.start()


def get_llm_client():
    if "llm_client" not in g:
        g.llm_client = LlmClient(
            ollama_instance_url=current_app.config["OLLAMA_INSTANCE_URL"],
            model=current_app.config["MODEL"],
        )

    return g.llm_client


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=app.config["APP_PORT"], debug=app.config["DEBUG"])
