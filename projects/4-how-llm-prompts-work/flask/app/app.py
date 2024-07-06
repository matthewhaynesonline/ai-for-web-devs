from flask import Flask, g

from config import Config
from hf_client import HfClient


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/", methods=["GET"])
    def index():
        hf_client = get_hf_client()
        result = hf_client.run()

        return f"<pre><code>{result}</code></pre>"

    return app


def get_hf_client():
    if "hf_client" not in g:
        g.hf_client = HfClient()

    return g.hf_client


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=app.config["APP_PORT"], debug=app.config["DEBUG"])
