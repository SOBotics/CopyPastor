import hmac
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from html import unescape
from flask import Flask, render_template, request, jsonify, g, redirect, url_for

app = Flask(__name__)
DATABASE = 'copypastorDB.db'


@app.errorhandler(404)
def page_not_found(error):
    print(error)
    return render_template('error.html',
                           message="Sorry, that page doesn't exist ...",
                           image="https://http.cat/404"), 404


@app.errorhandler(500)
def internal_server_error(error):
    print(error)
    return render_template('error.html',
                           message="Umph! Something bad happened, we'll look" +
                                   "into it. Thanks ...",
                           image="https://http.cat/500"), 500


@app.route("/")
def display_posts():
    counts = [len(i) for i in get_feedback_counts()]
    data = [i * 100.0 / sum(counts) for i in counts]
    return render_template("main_page.html",
                           data=zip(
                               data,
                               ["#8eef83", "#ef8282", "#82deef", "#010101"],
                               counts
                            ),
                           posts=get_latest_10_posts())


@app.route("/github", methods=['POST'])
def github_webhook():
    data = request.json
    signature = request.headers.get("X-Hub-Signature", None)
    if not signature:
        return jsonify({"status": "failure",
                        "message": "Error - Authentication Failure"}), 403
    calc_signature = "sha1=" + str(hmac.new(str.encode(get_github_creds()),
                                            msg=request.data,
                                            digestmod='sha1').hexdigest())
    if not hmac.compare_digest(calc_signature, signature):
        print("Request with an unknown signature - {}, expected signature - {}, payload - {}".format(
            signature, calc_signature, request.data), file=sys.stderr)
        return jsonify({"status": "failure",
                        "message": "Error - Authentication Failure"}), 403
    if "/develop" in data.get("ref"):
        subprocess.call("../update-develop.sh", stdout=open(os.devnull, 'w'),
                        stderr=subprocess.STDOUT)
    if "/master" in data.get("ref"):
        subprocess.call("../update.sh", stdout=open(os.devnull, 'w'),
                        stderr=subprocess.STDOUT)

    return data.get("ref")


@app.route("/posts/create", methods=['POST'])
def store_post():
    try:
        auth = request.form["key"]
        if not check_for_auth(auth):
            return jsonify({"status": "failure",
                            "message": "Error - Authentication Failure"}), 403
        date_one = request.form["date_one"]
        date_two = request.form["date_two"]
        if date_one < date_two:
            return jsonify({"status": "failure",
                            "message": "Error - Plagiarized post created earlier"}), 400

        if request.form.get('username_one', None) is not None:
            data = (request.form["url_one"], request.form["url_two"],
                    request.form["title_one"], request.form["title_two"],
                    date_one, date_two, request.form["body_one"],
                    request.form["body_two"], request.form["username_one"],
                    request.form["username_two"], request.form["user_url_one"],
                    request.form["user_url_two"], request.form["score"])
        else:
            data = (request.form["url_one"], request.form["url_two"],
                    request.form["title_one"], request.form["title_two"],
                    date_one, date_two, request.form["body_one"],
                    request.form["body_two"], request.form["score"])
        reasons = [i.split(':') for i in request.form["reasons"].split(",")]
        if any(len(i) != 2 for i in reasons):
            return jsonify({"status": "failure",
                            "message": "Error - Bad data {}".format(request.form["reasons"])}), 422
        post_id = save_data(data)
        for reason in reasons:
            msg, status = set_caught_for(post_id, retrieve_reason_id(reason[0]), reason[1])
            if status:
                return jsonify({"status": "failure",
                                "message": "Error - " + msg}), 400
        if post_id == -1:
            return jsonify({"status": "failure",
                            "message": "Error - Post already present"}), 400
    except KeyError as error:
        return jsonify({"status": "failure", "message":
                        "Error - Missing argument {}".format(error.args[0])}), 400
    return jsonify({"status": "success", "post_id": post_id})


@app.route("/feedback/create", methods=['POST'])
def store_feedback():
    try:
        auth = request.form["key"]
        if not check_for_auth(auth):
            return jsonify({"status": "failure",
                            "message": "Error - Authentication Failure"}), 403
        data = (request.form["post_id"], request.form["feedback_type"],
                request.form["username"], request.form["link"])
        if data[1] not in ("tp", "fp"):
            return jsonify({"status": "failure",
                            "message": "Error - Unknown feedback type"}), 400
        ret_msg, feedback_id = save_feedback(data)
        if feedback_id:
            return jsonify({"status": "success",
                            "message": ret_msg, "feedback_id": feedback_id})
        else:
            return jsonify({"status": "failure",
                            "message": "Error - " + ret_msg}), 400
    except KeyError as error:
        return jsonify({"status": "failure",
                        "message": "Error - Missing argument {}".format(error.args[0])}), 400


@app.route("/posts/find", methods=['GET'])
def find_post_get():
    try:
        url_one, url_two = request.args["url_one"], request.args["url_two"]
    except KeyError as error:
        return render_template('error.html',
                               message="Sorry, you're missing argument" +
                                       "{} ...".format(error.args[0]),
                               image="https://http.cat/400"), 400
    post_id = retrieve_post_id(url_one, url_two)
    if post_id is None:
        return render_template('error.html',
                               message="Sorry, that page doesn't exist ...",
                               image="https://http.cat/404"), 404
    return redirect(url_for('get_post', post_id=post_id))


@app.route("/posts/find", methods=['POST'])
def find_post_post():
    try:
        url_one, url_two = request.form["url_one"], request.form["url_two"]
    except KeyError as error:
        return jsonify({"status": "failure",
                        "message": "Error - Missing argument {}".format(error.args[0])}), 400
    post_id = retrieve_post_id(url_one, url_two)
    if post_id is None:
        return jsonify({"status": "failure",
                        "message": "Error - No such post found"}), 404
    return jsonify({"status": "success",
                    "url": url_for('get_post', post_id=post_id),
                    "post_id": post_id})


@app.route("/posts/<int:post_id>", methods=['GET'])
def get_post(post_id):
    data = retrieve_data(post_id)
    if data is None:
        return render_template('error.html',
                               message="Sorry, that page doesn't exist ...",
                               image="https://http.cat/404"), 404
    posts_type = "Reposted" if data["user_url_one"] == data["user_url_two"] else "Plagiarized"
    try:
        return render_template('render.html',
                               url_one=data["url_one"],
                               url_two=data["url_two"],
                               title_one=unescape(data["title_one"]),
                               title_two=unescape(data["title_two"]),
                               date_one=datetime.fromtimestamp(float(data["date_one"])),
                               date_two=datetime.fromtimestamp(float(data["date_two"])),
                               body_one=get_body(data["body_one"]),
                               body_two=get_body(data["body_two"]),
                               f_body_one=get_escaped_body(data["body_one"]),
                               f_body_two=get_escaped_body(data["body_two"]),
                               username_one=data["username_one"],
                               username_two=data["username_two"],
                               user_url_one=data["user_url_one"],
                               user_url_two=data["user_url_two"],
                               type=posts_type,
                               feedback=data["feedback"],
                               score=data["score"],
                               reasons=data["reasons"])
    except KeyError as error:
        print(error)
        return render_template('error.html',
                               message="Sorry, the post has been deleted ...",
                               image="https://http.cat/410"), 410


@app.route("/posts/pending", methods=['GET'])
def get_pending():
    type_of_post = request.args.get("reasons", False)
    if type_of_post == "true":
        posts = fetch_posts_without_feedback_with_details()
        items = [
            {i: j for i, j in zip(('post_id', 'url_one', 'url_two',
                                   'title_one', 'title_two', 'date_one',
                                   'date_two', 'username_one', 'username_two',
                                   'user_url_one', 'user_url_two', 'feedback'), post)}
            for post in posts]
        return jsonify({"status": "success", "posts": items})
    else:
        posts = fetch_posts_without_feedback()
        return jsonify({"status": "success", "posts": posts})


@app.route("/posts/findTarget", methods=['GET'])
def get_target():
    try:
        url_one = request.args["url"]
    except KeyError as error:
        return jsonify({"status": "failure",
                        "message": "Error - Missing argument {}".format(error.args[0])}), 400
    targets = retrieve_targets(url_one)
    posts = [{"post_id": i, "target_url": j} for i, j in targets]
    return jsonify({"status": "success", "posts": posts})


@app.route("/feedback/stats")
def get_feedback_stats():
    tp_feedback, fp_feedback, conf_feedback, none_feedback = get_feedback_counts()
    return jsonify({"status": "success", "none": none_feedback, "tp": tp_feedback, "fp": fp_feedback,
                    "conf": conf_feedback})


def get_escaped_body(body):
    return unescape(body).replace("`", "\\`").replace("</script>", "<//script>").replace("${", "$\\{")


def get_body(body):
    return unescape(body).split("\r\n")


def get_db():
    database = getattr(g, '_database', None)
    if database is None:
        database = g._database = sqlite3.connect(DATABASE)
    return database


def init_db():
    database = get_db()
    cur = database.cursor()
    with app.open_resource('schema.sql', mode='r') as schema:
        cur.executescript(schema.read())
    database.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')


@app.teardown_appcontext
def close_connection(exception):
    if exception:
        print(exception)
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()


def save_data(data):
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        cur.execute("SELECT * FROM posts "
                    "WHERE url_one=? AND url_two=?;", (data[0], data[1]))
        if cur.fetchone():
            return -1

        if len(data) != 13:
            cur.execute("INSERT INTO posts "
                        "(url_one, url_two, title_one, title_two, "
                        "date_one, date_two, body_one, body_two, username_one, "
                        "username_two, user_url_one, user_url_two, score) "
                        "VALUES (?,?,?,?,?,?,?,?,'','','','',?);", data)
        else:
            cur.execute("INSERT INTO posts "
                        "(url_one, url_two, title_one, title_two, date_one, "
                        "date_two, body_one, body_two, username_one, "
                        "username_two, user_url_one, user_url_two, score) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);", data)

        cur.execute("SELECT last_insert_rowid();")
        post_id = cur.fetchone()[0]
        database.commit()
        return post_id


def save_feedback(data):
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        cur.execute("SELECT feedback_id, feedback_type FROM feedback "
                    "WHERE post_id=? AND username=?;", (data[0], data[2]))
        old_database = cur.fetchone()
        if old_database:
            if old_database[1] == data[1]:
                return_message = "User feedback already registered"
                feedback_id = old_database[0]
            else:
                cur.execute("UPDATE feedback SET feedback_type=?, link=? "
                            "WHERE post_id=? AND username=?;",
                            (data[1], data[3], data[0], data[2]))
                return_message = "User feedback updated from {} to {}".format(old_database[1], data[1])
                feedback_id = old_database[0]
        else:
            try:
                cur.execute("PRAGMA foreign_keys = ON;")
                cur.execute("INSERT INTO feedback (post_id, feedback_type, username, link) "
                            "VALUES (?,?,?,?);", data)
                cur.execute("SELECT last_insert_rowid();")
                feedback_id = cur.fetchone()[0]
                return_message = "User feedback registered successfully"
            except sqlite3.IntegrityError as error:
                print(error)
                return "Post ID is incorrect. Post is either deleted or not yet created", None
        database.commit()
        return return_message, feedback_id


def retrieve_data(post_id):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT url_one, url_two, title_one, title_two, "
                    "date_one, date_two, body_one, body_two, username_one, "
                    "username_two, user_url_one, user_url_two, score "
                    "FROM posts WHERE post_id=?;", (post_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cur.execute("SELECT reason FROM reasons "
                    "INNER JOIN caught_for ON reasons.reason_id = caught_for.reason_id "
                    "WHERE post_id=?;", (post_id,))
        reasons = cur.fetchall()
        cur.execute("SELECT feedback_type, username, link "
                    "FROM feedback WHERE post_id=?;", (post_id,))
        feedbacks = cur.fetchall()
        data = {i: j for i, j in
                zip(('url_one', 'url_two', 'title_one', 'title_two',
                     'date_one', 'date_two', 'body_one', 'body_two',
                     'username_one', 'username_two', 'user_url_one',
                     'user_url_two', 'score', 'feedback', 'reasons'),
                    list(row) + [feedbacks] + [[r[0] for r in reasons]])}
        return data


def retrieve_post_id(url_one, url_two):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id FROM posts "
                    "WHERE url_one=? AND url_two=?", (url_one, url_two))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


def check_for_auth(data):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT associated_user FROM auth "
                    "WHERE auth_string=?", (data,))
        row = cur.fetchone()
        if row is None:
            return False
        return True


def get_github_creds():
    with app.app_context():
        cur = get_db().cursor()
        cur.execute('SELECT auth_string FROM auth '
                    'WHERE associated_user="GHKey";')
        row = cur.fetchone()
        if row is None:
            return False
        return row[0]


def fetch_posts_without_feedback():
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id FROM posts "
                    "WHERE post_id NOT IN (SELECT post_id FROM feedback);")
        posts = cur.fetchall()
        if posts:
            return [i[0] for i in posts]
        return posts


def fetch_posts_without_feedback_with_details():
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id, url_one, url_two, "
                    "title_one, title_two, date_one, date_two,"
                    "username_one, username_two, user_url_one, "
                    "user_url_two, score FROM posts "
                    "WHERE post_id NOT IN (SELECT post_id FROM feedback);")
        return cur.fetchall()


def retrieve_targets(url_one):
    with app.app_context():
        cur = get_db().cursor()
        cur.execute("SELECT post_id, url_two FROM posts "
                    "WHERE url_one=?", (url_one,))
        targets = cur.fetchall()
        return targets


def retrieve_reason_id(reason_text):
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        cur.execute("SELECT reason_id FROM reasons "
                    "WHERE reason=?;", (reason_text,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO reasons (reason) "
                        "VALUES (?);", (reason_text,))
            cur.execute("SELECT last_insert_rowid();")
            reason_id = cur.fetchone()[0]
        else:
            reason_id = row[0]
        database.commit()
        return reason_id


def set_caught_for(post_id, reason_id, score):
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        try:
            cur.execute("PRAGMA foreign_keys = ON;")
            cur.execute("INSERT INTO caught_for (post_id, reason_id, score) "
                        "VALUES (?,?,?);", (post_id, reason_id, score))
            database.commit()
            return "Added reason successfully", False
        except sqlite3.IntegrityError as error:
            print(error)
            return "Post ID or Reason ID is incorrect", True


def get_feedback_counts():
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        cur.execute("SELECT DISTINCT feedback_type, post_id FROM feedback;")
        posts_with_feedback = cur.fetchall()
        cur.execute("SELECT DISTINCT post_id FROM posts;")
        all_posts = [i[0] for i in cur.fetchall()]
        none_feedback = [i for i in all_posts if i not in [j for _, j in posts_with_feedback]]
        tp_feedback = [j for i, j in posts_with_feedback if i == "tp" and ("fp", j) not in posts_with_feedback]
        fp_feedback = [j for i, j in posts_with_feedback if i == "fp" and ("tp", j) not in posts_with_feedback]
        conf_feedback = list(set(j for _, j in posts_with_feedback if j not in tp_feedback + fp_feedback))
        return tp_feedback, fp_feedback, conf_feedback, none_feedback


def get_latest_10_posts():
    with app.app_context():
        database = get_db()
        cur = database.cursor()
        cur.execute("SELECT post_id, title_one, title_two, url_one, url_two "
                    "FROM posts ORDER BY post_id DESC LIMIT 10;")
        return cur.fetchall()
