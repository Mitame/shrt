#!/usr/bin/env python3
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

from flask import Flask, redirect, safe_join, request, url_for, jsonify
from pymongo import MongoClient
import time

db = MongoClient()["shrt"]

links = db["links"]
last_gen = db["last_gen"]

app = Flask(__name__)

LINK_CHARS = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
LINK_MIN_LENGTH = 4

def set_base(num, base):
    units = [1]
    while max(units) < num:
        units.append(base**len(units))

    units.reverse()

    out = []
    for n in units:
        div = num // n
        out.append(div)
        num %= n

    # out.reverse()
    if len(out) > 1 and out[0] == 0:
        return out[1:]
    else:
        return out

def get_code():
    data = last_gen.find_one({"obj": "link"})
    if data is None:
        num = len(LINK_CHARS) ** (LINK_MIN_LENGTH - 1)
        last_gen.insert_one({"obj": "link", "num": num})
    else:
        num = max((data["num"] + 1, len(LINK_CHARS) ** (LINK_MIN_LENGTH-1)))

    last_gen.update({"obj": "link"}, {"$set": {"num": num}})

    code_num = set_base(num, len(LINK_CHARS))
    code = ""
    for x in code_num:
        code += LINK_CHARS[x]
    return code

def get_id(code):
    code = str(code)[::-1]
    num = 0
    for c in range(len(code)):
        num += LINK_CHARS.index(code[c])**(c+1)

    return num



@app.route("/api/mk", methods=["POST"])
def mk_ln():
    url = request.form["url"]
    code = get_code()
    data = {
        "type": "url",
        "code": code,
        "url": url,
        "ts": str(time.time()),
        "clicked": 0
    }

    links.insert_one(data)
    return jsonify({
        "ok": True,
        "url": url_for("home", _external=True, _scheme="https") + code,
    })


@app.route("/")
def home():
    return redirect("https://mita.me/")


@app.route("/new")
def new():
    return get_code()


@app.route("/<string:code>")
def link(code):
    data = links.find_one({"code": code})
    if data is not None:
        links.update(
            {
                "_id": data["_id"]
            },
            {"$inc":
                {"clicked": 1}
            }
        )
        return redirect(data["url"])
    else:
        return home()


if __name__ == "__main__":
    app.run(debug=True)
