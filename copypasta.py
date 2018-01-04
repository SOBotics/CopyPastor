import sqlite3
from html import unescape

from flask import Flask, render_template, request, jsonify, g
from datetime import datetime

app = Flask(__name__)
DATABASE = 'copypastorDB.db'


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
        post_id = save_data(data)
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/feedback/create", methods=['POST'])
def store_feedback():
    try:
        data = (request.form["post_id"], request.form["feedback_type"], request.form["username"], request.form["link"])
        if data[1] not in ("tp", "fp"):
            return jsonify({"status": "failure", "message": "Error - Unknown feedback type"}), 400
        ret_msg, feedback_id = save_feedback(data)
        if feedback_id:
            return jsonify({"status": "success", "message": ret_msg, "feedback_id": feedback_id})
        else:
            return jsonify({"status": "failure", "message": "Error - " + ret_msg}), 400
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400


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
                               body_one=get_body(data["body_one"]), body_two=get_body(data["body_two"]),
                               feedback=data["feedback"])
    except KeyError as e:
        print(e)
        return render_template('error.html', message="Sorry, the post has been deleted ..."), 410


def get_body(body):
    return unescape(body).split("\r\n")


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def init_db():
    db = get_db()
    cur = db.cursor()
    with app.open_resource('schema.sql', mode='r') as f:
        cur.executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')


@app.teardown_appcontext
def close_connection(exception):
    if exception:
        print(exception)
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def save_data(data):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO posts "
                    "(url_one, url_two, title_one, title_two, date_one, date_two, body_one, body_two) "
                    "VALUES (?,?,?,?,?,?,?,?);", data)
        cur.execute("SELECT last_insert_rowid();")
        post_id = cur.fetchone()[0]
        db.commit()
        return post_id


def save_feedback(data):
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT feedback_id, feedback_type FROM feedback WHERE post_id=? AND username=?;",
                    (data[0], data[2]))
        old_db = cur.fetchone()
        if old_db:
            if old_db[1] == data[1]:
                ret_msg = "user feedback already registered"
                feedback_id = old_db[0]
            else:
                cur.execute("UPDATE feedback SET feedback_type=?, link=? WHERE post_id=? AND username=?;",
                            (data[1], data[3], data[0], data[2]))
                ret_msg = "user feedback updated from {} to {}".format(old_db[1], data[1])
                feedback_id = old_db[0]
        else:
            try:
                cur.execute("PRAGMA foreign_keys = ON;")
                cur.execute("INSERT INTO feedback (post_id, feedback_type, username, link) VALUES (?,?,?,?);", data)
                cur.execute("SELECT last_insert_rowid();")
                feedback_id = cur.fetchone()[0]
                ret_msg = "user feedback registered successfully"
            except sqlite3.IntegrityError as e:
                print(e)
                return "Post ID is incorrect. Post is either deleted or not yet created", None
        db.commit()
        return ret_msg, feedback_id


def retrieve_data(post_id):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT url_one, url_two, title_one, title_two, date_one, date_two, body_one, body_two FROM posts "
                    "WHERE post_id=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute("SELECT feedback_type, username, link FROM feedback WHERE post_id=?;", (post_id,))
        feedbacks = cur.fetchall()
        data = {i: j for i, j in
                zip(('url_one', 'url_two', 'title_one', 'title_two', 'date_one', 'date_two', 'body_one',
                     'body_two', 'feedback'), list(row)+[feedbacks])}
        return data
