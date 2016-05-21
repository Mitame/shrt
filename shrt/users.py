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

from flask import request
from pymongo.errors import DuplicateKeyError

from . import db, app, config

users = db["users"]
users.create_index("username", unique=True)

useradd_tokens = db["useradd_tokens"]
users.create_index("token", unique=True)


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
    if username:
        creator = get_user(username)["_id"]
    else:
        creator = None

    token = util.get_code(do_random=True)
    useradd_tokens.insert_one({
        "token": token,
        "creator": creator,
        "used": False
    })

    return


@app.route("/api/useradd", methods=["POST"])
def site_create_user():
    username = request.form["username"]
    password = request.form["password"]
    if not config["auth"]["anon_can_create_user"]:
        code = request.form.get("code")
        if code is None:
            return jsonify({
                "ok": False,
                "reason": "This site is configured as invite only."
            })


if users.count() == 0:
    password = "aaaa"
    create_user("root", password)
    print("Root user created: %s:%s" % ("root", password))
