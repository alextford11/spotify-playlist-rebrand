from flask import Flask


def create_app():
    from app.views.index import index_blueprint

    app = Flask(__name__)
    app.register_blueprint(index_blueprint)
    return app
