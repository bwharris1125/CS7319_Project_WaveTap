# import libraries
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Return a friendly HTTP greeting."""
    return "Hello, World!"


@app.route("/welcome")
def welcome():
    """Return a welcome message."""
    return "Welcome to CS 7319!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
