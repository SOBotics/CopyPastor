import json
import sqlite3
from html import unescape

from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template('error.html', message="Sorry, that page doesn't exist ..."), 404


@app.errorhandler(500)
def internal_server_error(error):
    print(error)
    return render_template('error.html', message="Umph! Something bad happened, we'll look into it. Thanks ..."), 500


@app.route("/posts/create", methods=['POST'])
def store_post():
    try:
        date_one = request.form["date_one"]
        date_two = request.form["date_two"]
        if date_one < date_two:
            return jsonify({"status": "failure", "message": "Error - Plagiarized post created earlier"}), 400
        data = (request.form["url_one"], request.form["url_two"], request.form["title_one"],
                request.form["title_two"], date_one, date_two, request.form["body_one"], request.form["body_two"])
        post_id = store_data(data)
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/posts/<int:post_id>", methods=['GET'])
def get_post(post_id):
    data = retrieve_data(post_id)
    if data is None:
        return render_template('error.html', message="Sorry, that page doesn't exist ..."), 404
    try:
        return render_template('render.html', url_one=data["url_one"], url_two=data["url_two"],
                               title_one=unescape(data["title_one"]), title_two=unescape(data["title_two"]),
                               date_one=datetime.fromtimestamp(float(data["date_one"])),
                               date_two=datetime.fromtimestamp(float(data["date_two"])),
                               body_one=get_body(data["body_one"]), body_two=get_body(data["body_two"]))
    except KeyError as e:
        print(e)
        return render_template('error.html', message="Sorry, the post has been deleted ..."), 410


def get_body(body):
    return unescape(body).split("\r\n")


def store_data(data):
    con = sqlite3.connect('copypastorDB.db')
    cur = con.cursor()
    cur.execute("INSERT INTO posts (url_one, url_two, title_one, title_two, date_one, date_two, body_one, body_two) "
                "VALUES (?,?,?,?,?,?,?,?);", data)
    cur.execute("SELECT last_insert_rowid();")
    post_id = cur.fetchone()[0]
    con.commit()
    con.close()
    return post_id


def retrieve_data(post_id):
    con = sqlite3.connect('copypastorDB.db')
    cur = con.cursor()
    cur.execute("SELECT url_one, url_two, title_one, title_two, date_one, date_two, body_one, body_two FROM posts "
                "WHERE post_id=?;", (post_id,))
    row = cur.fetchone()
    if row is None:
        return None
    data = {i: j for i, j in
            zip(('url_one', 'url_two', 'title_one', 'title_two', 'date_one', 'date_two', 'body_one', 'body_two'), row)}
    con.commit()
    con.close()
    return data

