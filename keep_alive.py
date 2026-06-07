from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "บอทออนไลน์อยู่ครับ 🟢"

def run():
    app.run(host="0.0.0.0", port=8081)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
