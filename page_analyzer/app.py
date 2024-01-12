from flask import Flask, render_template
from dotenv import load_dotenv
import os

# from dotenv import dotenv_values
# import json

load_dotenv()

app = Flask(__name__)


@app.route("/")
def hello_world():
    # config = dotenv_values('.env')
    # json_str = json.dumps(config)
    port = os.getenv("TCP_PORT")
    # return f"<p>Hello, World and Earth!<br/><br/>Configuration is {json_str}</p>"
    # return f"<p>Hello, World and Earth!<br/><br/>TCP_PORT = {port}</p>"
    return render_template("index.html", port=port)
