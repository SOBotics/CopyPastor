import sqlite3
from html import unescape

from flask import Flask, render_template, request, jsonify, g, redirect, url_for
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


@app.route("/")
def display_posts():
    return render_template("main_page.html")


@app.route("/posts/create", methods=['POST'])
def store_post():
    try:
        auth = request.form["key"]
        if not check_for_auth(auth):
            return jsonify({"status": "failure", "message": "Error - Authentication Failure"}), 403
        date_one = request.form["date_one"]
        date_two = request.form["date_two"]
        if date_one < date_two:
            return jsonify({"status": "failure", "message": "Error - Plagiarized post created earlier"}), 400
        data = (request.form["url_one"], request.form["url_two"], request.form["title_one"],
                request.form["title_two"], date_one, date_two, request.form["body_one"], request.form["body_two"],
                request.form["username_one"], request.form["username_two"], request.form["user_url_one"],
                request.form["user_url_two"])
        post_id = save_data(data)
        if post_id == -1:
            return jsonify({"status": "failure", "message": "Error - Post already present"}), 400
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/feedback/create", methods=['POST'])
def store_feedback():
    try:
        auth = request.form["key"]
        if not check_for_auth(auth):
            return jsonify({"status": "failure", "message": "Error - Authentication Failure"}), 403
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


@app.route("/posts/find", methods=['GET'])
def find_post_get():
    try:
        url_one, url_two = request.args["url_one"], request.args["url_two"]
    except KeyError as e:
        return render_template('error.html', message="Sorry, you're missing argument {} ...".format(e.args[0])), 400
    post_id = retrieve_post_id(url_one, url_two)
    if post_id is None:
        return render_template('error.html', message="Sorry, that page doesn't exist ..."), 404
    return redirect(url_for('get_post', post_id=post_id))


@app.route("/posts/find", methods=['POST'])
def find_post_post():
    try:
        url_one, url_two = request.form["url_one"], request.form["url_two"]
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    post_id = retrieve_post_id(url_one, url_two)
    if post_id is None:
        return jsonify({"status": "failure", "message": "Error - No such post found"}), 404
    return jsonify({"status": "success", "url": url_for('get_post', post_id=post_id), "post_id": post_id})


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
                               username_one=data["username_one"], username_two=data["username_two"],
                               user_url_one=data["user_url_one"], user_url_two=data["user_url_two"],
                               type="Reposted" if data["user_url_one"] == data["user_url_two"] else "Plagiarized",
                               feedback=data["feedback"])
    except KeyError as e:
        print(e)
        return render_template('error.html', message="Sorry, the post has been deleted ..."), 410


@app.route("/posts/pending", methods=['GET'])
def get_pending():
    posts = fetch_posts_without_feedback()
    return jsonify({"status": "success", "posts": posts})


@app.route("/posts/findTarget", methods=['GET'])
def get_target():
    try:
        url_one = request.args["url"]
    except KeyError as e:
        return jsonify({"status": "failure", "message": "Error - Missing argument {}".format(e.args[0])}), 400
    targets = retrieve_targets(url_one)
    posts = [{"post_id": i, "target_url": j} for i, j in targets]
    return jsonify({"status": "success", "posts": posts})


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
        cur.execute("SELECT  * FROM posts WHERE url_one=? AND url_two=?;", (data[0], data[1]))
        if cur.fetchone():
            return -1
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
                ret_msg = "User feedback already registered"
                feedback_id = old_db[0]
            else:
                cur.execute("UPDATE feedback SET feedback_type=?, link=? WHERE post_id=? AND username=?;",
                            (data[1], data[3], data[0], data[2]))
                ret_msg = "User feedback updated from {} to {}".format(old_db[1], data[1])
                feedback_id = old_db[0]
        else:
            try:
                cur.execute("PRAGMA foreign_keys = ON;")
                cur.execute("INSERT INTO feedback (post_id, feedback_type, username, link) VALUES (?,?,?,?);", data)
                cur.execute("SELECT last_insert_rowid();")
                feedback_id = cur.fetchone()[0]
                ret_msg = "User feedback registered successfully"
            except sqlite3.IntegrityError as e:
                print(e)
                return "Post ID is incorrect. Post is either deleted or not yet created", None
        db.commit()
        return ret_msg, feedback_id


def retrieve_data(post_id):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT url_one, url_two, title_one, title_two, date_one, date_two, body_one, body_two, "
                    "username_one, username_two, user_url_one, user_url_two FROM posts "
                    "WHERE post_id=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute("SELECT feedback_type, username, link FROM feedback WHERE post_id=?;", (post_id,))
        feedbacks = cur.fetchall()
        data = {i: j for i, j in
                zip(('url_one', 'url_two', 'title_one', 'title_two', 'date_one', 'date_two', 'body_one',
                     'body_two', 'username_one', 'username_two', 'user_url_one', 'user_url_two', 'feedback'),
                    list(row) + [feedbacks])}
        return data


def retrieve_post_id(url_one, url_two):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id FROM posts WHERE url_one=? AND url_two=?", (url_one, url_two))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


def check_for_auth(data):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT associated_user FROM auth WHERE auth_string=?", (data,))
        row = cur.fetchone()
        if row is None:
            return False
        return True


def fetch_posts_without_feedback():
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("select post_id from posts where post_id not in (select post_id from feedback);")
        posts = cur.fetchall()
        if posts:
            return [i[0] for i in posts]
        return posts


def retrieve_targets(url_one):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id, url_two FROM posts WHERE url_one=?", (url_one,))
        targets = cur.fetchall()
        return targets
