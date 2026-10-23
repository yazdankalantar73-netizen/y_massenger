import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# Y MESSENGER SERVER
# VERSION 1.26.1.7
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, "ymessenger.db")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
THEME_DIR = os.path.join(UPLOAD_DIR, "themes")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THEME_DIR, exist_ok=True)


app = Flask(__name__)

VERSION = "1.26.1.7"

# توکن‌های ورود
TOKENS = {}


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db


def init_db():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            user_id INTEGER PRIMARY KEY,
            main_color TEXT DEFAULT '#2196F3',
            background TEXT DEFAULT '',
            darkness REAL DEFAULT 0
        )
    """)

    db.commit()
    db.close()


init_db()


# =========================================================
# HELPERS
# =========================================================

def response_ok(**data):
    result = {
        "ok": True
    }
    result.update(data)
    return jsonify(result)


def response_error(message, code=400):
    return jsonify({
        "ok": False,
        "error": message
    }), code


def current_user():

    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return None

    token = auth[7:].strip()

    if not token:
        return None

    user_id = TOKENS.get(token)

    if not user_id:
        return None

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    db.close()

    return user


def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        user = current_user()

        if user is None:
            return response_error(
                "نیاز به ورود دارید.",
                401
            )

        return func(user, *args, **kwargs)

    return wrapper


def user_json(user):

    if not user:
        return None

    return {
        "id": user["id"],
        "username": user["username"],
        "bio": user["bio"] or "",
        "avatar": user["avatar"] or "",
        "created_at": user["created_at"]
    }


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "ok": True,
        "name": "Y MESSENGER",
        "version": VERSION,
        "server": "online"
    })


# =========================================================
# WEB APP
# =========================================================

@app.route("/app", methods=["GET"])
def app_page():

    path = os.path.join(
        BASE_DIR,
        "client.html"
    )

    if not os.path.exists(path):
        return "client.html not found", 404

    return send_from_directory(
        BASE_DIR,
        "client.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    bio = str(
        data.get("bio", "")
    ).strip()

    if len(username) < 3:
        return response_error(
            "نام کاربری باید حداقل ۳ کاراکتر باشد."
        )

    if len(password) < 4:
        return response_error(
            "رمز عبور باید حداقل ۴ کاراکتر باشد."
        )

    db = get_db()

    exists = db.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if exists:
        db.close()

        return response_error(
            "این نام کاربری قبلاً استفاده شده."
        )

    created_at = datetime.now().isoformat()

    password_hash = generate_password_hash(
        password
    )

    cursor = db.execute(
        """
        INSERT INTO users
        (username, password, bio, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            password_hash,
            bio,
            created_at
        )
    )

    user_id = cursor.lastrowid

    db.execute(
        """
        INSERT INTO themes
        (user_id, main_color, background, darkness)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            "#2196F3",
            "",
            0
        )
    )

    db.commit()

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    db.close()

    return response_ok(
        message="ثبت‌نام با موفقیت انجام شد.",
        user=user_json(user)
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    db = get_db()

    user = db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    db.close()

    if not user:
        return response_error(
            "نام کاربری یا رمز عبور اشتباه است.",
            401
        )

    if not check_password_hash(
        user["password"],
        password
    ):
        return response_error(
            "نام کاربری یا رمز عبور اشتباه است.",
            401
        )

    token = secrets.token_urlsafe(32)

    TOKENS[token] = user["id"]

    return response_ok(
        token=token,
        user=user_json(user)
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
@login_required
def logout(user):

    auth = request.headers.get(
        "Authorization",
        ""
    )

    token = auth[7:].strip()

    if token:
        TOKENS.pop(token, None)

    return response_ok(
        message="با موفقیت خارج شدید."
    )


# =========================================================
# ME
# =========================================================

@app.route("/api/me", methods=["GET"])
@login_required
def me(user):

    return response_ok(
        user=user_json(user)
    )


# =========================================================
# USERS
# =========================================================

@app.route("/api/users", methods=["GET"])
@login_required
def users(user):

    db = get_db()

    rows = db.execute(
        """
        SELECT id, username, bio, avatar, created_at
        FROM users
        WHERE id != ?
        ORDER BY username COLLATE NOCASE
        """,
        (user["id"],)
    ).fetchall()

    db.close()

    return response_ok(
        users=[
            user_json(row)
            for row in rows
        ]
    )


# =========================================================
# SEARCH USERS
# =========================================================

@app.route("/api/users/search", methods=["GET"])
@login_required
def search_users(user):

    query = request.args.get(
        "q",
        ""
    ).strip()

    db = get_db()

    rows = db.execute(
        """
        SELECT id, username, bio, avatar, created_at
        FROM users
        WHERE id != ?
        AND username LIKE ?
        ORDER BY username COLLATE NOCASE
        """,
        (
            user["id"],
            "%" + query + "%"
        )
    ).fetchall()

    db.close()

    return response_ok(
        users=[
            user_json(row)
            for row in rows
        ]
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/api/profile", methods=["GET"])
@login_required
def profile_get(user):

    return response_ok(
        user=user_json(user)
    )


@app.route("/api/profile", methods=["POST"])
@login_required
def profile_update(user):

    data = request.get_json(silent=True) or {}

    bio = str(
        data.get("bio", "")
    ).strip()

    db = get_db()

    db.execute(
        """
        UPDATE users
        SET bio = ?
        WHERE id = ?
        """,
        (
            bio,
            user["id"]
        )
    )

    db.commit()

    updated = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (user["id"],)
    ).fetchone()

    db.close()

    return response_ok(
        user=user_json(updated)
    )


# =========================================================
# THEME GET
# =========================================================

@app.route("/api/theme", methods=["GET"])
@login_required
def theme_get(user):

    db = get_db()

    theme = db.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = ?
        """,
        (user["id"],)
    ).fetchone()

    if not theme:

        db.execute(
            """
            INSERT INTO themes
            (user_id, main_color, background, darkness)
            VALUES (?, ?, ?, ?)
            """,
            (
                user["id"],
                "#2196F3",
                "",
                0
            )
        )

        db.commit()

        theme = db.execute(
            """
            SELECT *
            FROM themes
            WHERE user_id = ?
            """,
            (user["id"],)
        ).fetchone()

    db.close()

    return response_ok(
        theme={
            "main_color": theme["main_color"],
            "background": theme["background"],
            "darkness": theme["darkness"]
        }
    )


# =========================================================
# THEME UPDATE
# =========================================================

@app.route("/api/theme", methods=["POST"])
@login_required
def theme_update(user):

    data = request.get_json(silent=True) or {}

    main_color = data.get("main_color")
    darkness = data.get("darkness")

    db = get_db()

    current = db.execute(
        """
        SELECT *
        FROM themes
        WHERE user_id = ?
        """,
        (user["id"],)
    ).fetchone()

    if not current:

        db.execute(
            """
            INSERT INTO themes
            (user_id, main_color, background, darkness)
            VALUES (?, ?, ?, ?)
            """,
            (
                user["id"],
                main_color or "#2196F3",
                "",
                float(darkness or 0)
            )
        )

    else:

        new_color = (
            main_color
            if main_color is not None
            else current["main_color"]
        )

        new_darkness = (
            float(darkness)
            if darkness is not None
            else current["darkness"]
        )

        db.execute(
            """
            UPDATE themes
            SET main_color = ?,
                darkness = ?
            WHERE user_id = ?
            """,
            (
                new_color,
                new_darkness,
                user["id"]
            )
        )

    db.commit()
    db.close()

    return response_ok(
        message="تنظیمات ذخیره شد."
    )


# =========================================================
# BACKGROUND UPLOAD
# =========================================================

@app.route(
    "/api/theme/background",
    methods=["POST"]
)
@login_required
def background_upload(user):

    if "background" not in request.files:
        return response_error(
            "فایل تصویر ارسال نشده."
        )

    file = request.files["background"]

    if not file.filename:
        return response_error(
            "فایل انتخاب نشده."
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    allowed = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]

    if extension not in allowed:
        return response_error(
            "فرمت تصویر مجاز نیست."
        )

    filename = (
        str(user["id"])
        + "_"
        + secrets.token_hex(8)
        + extension
    )

    filepath = os.path.join(
        THEME_DIR,
        filename
    )

    file.save(filepath)

    background_url = (
        "/uploads/themes/"
        + filename
    )

    db = get_db()

    old = db.execute(
        """
        SELECT background
        FROM themes
        WHERE user_id = ?
        """,
        (user["id"],)
    ).fetchone()

    if old and old["background"]:

        old_name = os.path.basename(
            old["background"]
        )

        old_path = os.path.join(
            THEME_DIR,
            old_name
        )

        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass

    db.execute(
        """
        INSERT INTO themes
        (user_id, main_color, background, darkness)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET background = excluded.background
        """,
        (
            user["id"],
            "#2196F3",
            background_url,
            0
        )
    )

    db.commit()
    db.close()

    return response_ok(
        background=background_url
    )


# =========================================================
# DELETE BACKGROUND
# =========================================================

@app.route(
    "/api/theme/background",
    methods=["DELETE"]
)
@login_required
def background_delete(user):

    db = get_db()

    row = db.execute(
        """
        SELECT background
        FROM themes
        WHERE user_id = ?
        """,
        (user["id"],)
    ).fetchone()

    if row and row["background"]:

        filename = os.path.basename(
            row["background"]
        )

        filepath = os.path.join(
            THEME_DIR,
            filename
        )

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass

    db.execute(
        """
        UPDATE themes
        SET background = ''
        WHERE user_id = ?
        """,
        (user["id"],)
    )

    db.commit()
    db.close()

    return response_ok(
        message="پس‌زمینه حذف شد."
    )


# =========================================================
# UPLOADS
# =========================================================

@app.route(
    "/uploads/<path:filename>",
    methods=["GET"]
)
def uploads(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# =========================================================
# SEND MESSAGE
# =========================================================

@app.route("/api/send", methods=["POST"])
@login_required
def send_message(user):

    data = request.get_json(silent=True) or {}

    receiver_username = str(
        data.get("username", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    if not receiver_username:
        return response_error(
            "گیرنده مشخص نشده."
        )

    if not message:
        return response_error(
            "پیام خالی است."
        )

    if len(message) > 5000:
        return response_error(
            "پیام بیش از حد طولانی است."
        )

    db = get_db()

    receiver = db.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (receiver_username,)
    ).fetchone()

    if not receiver:
        db.close()

        return response_error(
            "کاربر پیدا نشد."
        )

    created_at = datetime.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO messages
        (sender_id, receiver_id, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            user["id"],
            receiver["id"],
            message,
            created_at
        )
    )

    message_id = cursor.lastrowid

    db.commit()

    row = db.execute(
        """
        SELECT *
        FROM messages
        WHERE id = ?
        """,
        (message_id,)
    ).fetchone()

    db.close()

    return response_ok(
        message={
            "id": row["id"],
            "sender": user["username"],
            "receiver": receiver_username,
            "message": row["message"],
            "created_at": row["created_at"]
        }
    )


# =========================================================
# GET MESSAGES
# =========================================================

@app.route("/api/messages", methods=["GET"])
@login_required
def get_messages(user):

    username = request.args.get(
        "username",
        ""
    ).strip()

    if not username:
        return response_error(
            "کاربر مشخص نشده."
        )

    db = get_db()

    other = db.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    if not other:
        db.close()

        return response_error(
            "کاربر پیدا نشد."
        )

    rows = db.execute(
        """
        SELECT
            messages.id,
            sender.username AS sender,
            receiver.username AS receiver,
            messages.message,
            messages.created_at
        FROM messages

        JOIN users AS sender
        ON messages.sender_id = sender.id

        JOIN users AS receiver
        ON messages.receiver_id = receiver.id

        WHERE
        (
            messages.sender_id = ?
            AND messages.receiver_id = ?
        )
        OR
        (
            messages.sender_id = ?
            AND messages.receiver_id = ?
        )

        ORDER BY messages.id ASC
        """,
        (
            user["id"],
            other["id"],
            other["id"],
            user["id"]
        )
    ).fetchall()

    db.close()

    return response_ok(
        messages=[
            {
                "id": row["id"],
                "sender": row["sender"],
                "receiver": row["receiver"],
                "message": row["message"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("Y MESSENGER SERVER")
    print("Version:", VERSION)
    print("SERVER ONLINE")
    print("=" * 50)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )