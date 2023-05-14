import json
from flask import Flask
from flask_cors import CORS

from pydantic import BaseModel

from typing import Union
import os
from dotenv import load_dotenv

load_dotenv('.env')

app = Flask(__name__)
CORS(app)


@app.route("/")
def helloWorld():
  return "Hello, cross-origin-world!"
