from flask import Flask
from dotenv import dotenv_values
import json


app = Flask(__name__)


@app.route("/")
def hello_world():
    config = dotenv_values('.env')
    json_str = json.dumps(config)
    return f"<p>Hello, World and Earth!<br/><br/>Configuration is {json_str}</p>"
    # return f"<p>Hello, World and Earth! password={config['PASSWORD']}</p>"
