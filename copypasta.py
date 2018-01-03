import json
from html import unescape

from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', message="Sorry, that page doesn't exist ..."), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', message="Umph! Something bad happened, we'll look into it. Thanks ..."), 500

@app.route("/posts/create", methods=['POST'])
def store_post():
    try:
        date_one = request.form["date_one"]
        date_two = request.form["date_two"]
        if date_one < date_two:
            return jsonify({"status": "failure", "message": "Error - Plagiarized post created earlier"}), 400
        data = {"url_one": request.form["url_one"], "url_two": request.form["url_two"],
                "title_one": request.form["title_one"], "title_two": request.form["title_two"],
                "date_one": date_one, "date_two": date_two,
                "body_one": request.form["body_one"], "body_two": request.form["body_two"]}
        post_id = store_data(data)
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/posts/<int:post_id>", methods=['GET'])
def get_post(post_id):
    with open("storage/data.txt", "r") as fp:
        for ind, data_string in enumerate(fp, start=1):
            if ind == post_id:
                data = json.loads(data_string)
                try:
                    return render_template('render.html', url_one=data["url_one"], url_two=data["url_two"],
                                           title_one=unescape(data["title_one"]), title_two=unescape(data["title_two"]),
                                           date_one=datetime.fromtimestamp(float(data["date_one"])),
                                           date_two=datetime.fromtimestamp(float(data["date_two"])),
                                           body_one=get_body(data["body_one"]), body_two=get_body(data["body_two"]))
                except KeyError as e:
                    return render_template('error.html', message="Sorry, the post has been deleted ..."), 410
        return render_template('error.html', message="Sorry, that page doesn't exist ..."), 404


def get_body(body):
    return unescape(body).split("\r\n")


def store_data(data):
    post_id = 1
    with open("storage/data.txt", "r") as fp:
        for _ in fp:
            post_id += 1
    with open("storage/data.txt", "a") as fp:
        json.dump(data, fp)
        fp.write("\n")
    return post_id