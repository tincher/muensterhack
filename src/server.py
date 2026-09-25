from flask import Flask
from src.template_handler import TemplateHandler

app = Flask(__name__)
template_handler = TemplateHandler()


@app.route("/")
def index():
    return template_handler.get_example()
