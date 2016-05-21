# shrt - A _really_ simple link shortener
# Copyright (C) 2015  Mitame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import hashlib
import os
import time

from flask import request, jsonify, url_for, render_template, render_template_string
from pymongo.errors import DuplicateKeyError

from . import db, app, config, shortener, util

users = db["users"]
users.create_index("username", unique=True)

useradd_tokens = db["useradd_tokens"]
useradd_tokens.create_index("token", unique=True)


def hash_password(password, salt=None):
    if not isinstance(password, bytes):
        password = password.encode("utf8")

    hasher = hashlib.sha512()
    hasher.update(password)
    res = hasher.digest()

    if salt is not None:
        res = hash_password(res + hash_password(salt))

    return res


def create_salt():
    return hash_password(os.urandom(128))


def create_user(username, password, email=None, is_admin=False):
    salt = create_salt()
    user_data = {
        "username": username.lower(),
        "passhash": hash_password(password, salt),
        "salt": salt,
        "email": email,

        "max_file_upload": config["uploads"]["default_max_file_size"],
        "is_admin": is_admin,
        "deleted": False,
        "creation_time": time.time()
    }

    try:
        auto_id = users.insert_one(user_data)
    except DuplicateKeyError:
        raise ValueError("Username '%s' in use." % username)

    return auto_id


def check_login(username, password):
    user_data = users.find_one({"username": username.lower()})
    if user_data is None:
        return False

    passhash = hash_password(password, user_data["salt"])
    if passhash == user_data["passhash"]:
        return user_data
    else:
        return False


def get_user(username=None):
    if username is None:
        if request.authorization:
            username = request.authorization.username
            password = request.authorization.password
            return check_login(username, password)

        return None
    else:
        user_data = users.find_one({"username": username.lower()})
        return user_data


def create_useradd_token(username=None):
    creator = None
    if username:
        user = get_user(username)
        if user:
            creator = user["username"]


    token = util.get_code("useradd_token", do_random=True)
    x = useradd_tokens.insert({
        "token": token,
        "creator": creator,
        "used": False
    })

    print(x)

    return token


def check_code(token):
    data = useradd_tokens.find_and_modify(
        {"token": token, "used": False},
        {"$set": {"used": True}}
    )

    return bool(data)


@app.route("/api/invite", methods=["POST", "GET"])
def site_gen_invite_link():
    if config["auth"]["anon_can_create_user"]:
        return jsonify({
            "ok": False,
            "reason": "Invites are disabled on this site."
        })
    user = get_user()
    if user is None:
        return jsonify({
            "ok": False,
            "reason": "Authentication required"
        })

    if not user["is_admin"] and not config["auth"]["user_can_create_user"]:
        return jsonify({
            "ok": False,
            "reason": "Users cannot invite others"
        })

    if not config["auth"]["admin_can_create_user"]:
        return jsonify({
            "ok": False,
            "reason": "admins cannot invite others"
        })

    token = create_useradd_token(user["username"])
    url = shortener.shorten(url_for("site_accept_invite", _external=True, code=token), hidden=True)

    return jsonify({
        "ok": True,
        "url": url
    })



@app.route("/api/accept_invite")
def site_accept_invite():
    return render_template_string("""
    <html>
    <body>
    <form action="/api/useradd" method="post">

    <input type="hidden" name="code" value="{{ code }}" />

    <label for="username">Username</label>
    <input id="username" type="text" name="username" value="{{ username }}" /> <br />

    <label for="password">Password</label>
    <input type="password" name="password" value="{{ password }}" /> <br />

    <input type="submit" value="Submit" />

    </form>
    </body>
    </html>
    """, code=request.args["code"])


@app.route("/api/useradd", methods=["POST"])
def site_create_user():
    username = request.form["username"]
    password = request.form["password"]
    is_admin = request.form.get("is_admin")
    if not config["auth"]["anon_can_create_user"]:
        code = request.form.get("code")
        user = get_user()
        if code is None and user is None:
            return jsonify({
                "ok": False,
                "reason": "This site is configured as invite only."
            })
            print(code)
        if code and not check_code(code):
            return jsonify({
                "ok": False,
                "reason": "Code is not valid."
            })

        if user and not user["is_admin"] and not config["auth"]["user_can_create_user"]:
            return jsonify({
                "ok": False,
                "reason": "Users are not allowed to create more users"
            })

        if user and not (user["is_admin"] and config["auth"]["admin_can_create_user"]):
            return jsonify({
                "ok": False,
                "reason": "Admins are not allowed to create users. Check your config."
            })

    try:
        if user:
            is_admin = int(is_admin) and user["is_admin"]
    except ValueError:
        is_admin = False

    try:
        uid = create_user(username, password, is_admin=is_admin)

    except IndexError:
        return jsonify({
            "ok": False,
            "reason": "Username in use"
        })

    return jsonify({
        "ok": True
    })


if users.count() == 0:
    password = "aaaa"
    create_user("root", password, is_admin=True)
    print("Root user created: %s:%s" % ("root", password))
