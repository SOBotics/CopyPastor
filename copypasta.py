import json
from html import unescape

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route("/posts/create", methods=['POST'])
def store_post():
    post_id = 1
    with open("storage/data.txt", "r") as fp:
        for _ in fp:
            post_id += 1
    with open("storage/data.txt", "a") as fp:
        data = {"url_one": request.form.get("url_one"), "url_two": request.form.get("url_two"),
                "title_one": request.form.get("title_one"), "title_two": request.form.get("title_two"),
                "body_one": request.form.get("body_one"), "body_two": request.form.get("body_two")}
        json.dump(data,fp)
        fp.write("\n")
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/posts/<int:post_id>", methods=['GET'])
def get_post(post_id):
    with open("storage/data.txt", "r") as fp:
        for ind, data_string in enumerate(fp, start=1):
            if ind == post_id:
                data = json.loads(data_string)
                try:
                    return render_template('render.html', url_one=data["url_one"], url_two=data["url_two"],
                                           title_one=data["title_one"], title_two=data["title_two"],
                                           body_one=get_body(data["body_one"]), body_two=get_body(data["body_two"]))
                except KeyError as e:
                    print(e)
                    return render_template('error.html', message="Sorry, the post has been deleted...")
        return render_template('error.html', message="Sorry, that page doesn't exist ...")


def get_body(body):
    return unescape(body).split("\r\n")
