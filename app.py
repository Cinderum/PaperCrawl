from flask import Flask,render_template
from model.forms import SearchForm
from flask import request
import sqlite3
import process

app = Flask(__name__)
app.config["SECRET_KEY"] = "12345678"

# 首页 - 展示介绍页面
@app.route('/')
def index():
    return render_template("index.html")

# 信息抽取结果页面
@app.route('/results')
def results():
    search_list = process.main()
    return render_template("answers.html", news=search_list)

if __name__ == '__main__':
    app.run()