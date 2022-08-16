import os

import redis
from flask import Flask


def create_app():
    from app.views.index import index_blueprint

    app = Flask(__name__)
    app.register_blueprint(index_blueprint)
    return app


def get_redis_client():
    return redis.from_url(os.getenv('REDISCLOUD_URL', 'redis://localhost:6379'))
