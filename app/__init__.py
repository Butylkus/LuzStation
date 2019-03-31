# -*- coding: utf-8 -*-

from flask import Flask
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

from flask_bootstrap import Bootstrap

Bootstrap(app)

from app import routes

if __name__ == "__main__":
    app.run()
