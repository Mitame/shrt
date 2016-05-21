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

from flask import redirect, safe_join, request, url_for, jsonify, abort
import time
import idna
from urllib.parse import urlparse, urlunparse

from . import app, db, config, util, users


lcfg = config["link_shortener"]  # I got tired of typing it all the time

links = db["links"]
links.create_index("code")


def get_id(code):
    code = str(code)[::-1]
    num = 0
    for c in range(len(code)):
        num += config["link_shortener"]["characters"].index(code[c])**(c+1)

    return num


def shorten(target, code=None, hidden=None, item_type="link", internal=False):
    target_parse = urlparse(target)

    if target_parse.netloc in (urlparse(request.base_url).netloc, "") and not internal:
        return None

    target = urlunparse(target_parse)

    if code is None:
        code = util.get_code(item_type, do_random=hidden)
        is_custom_code = True
    else:
        is_custom_code = False

    data = {
        "type": "url",
        "code": code,
        "url": target,
        "ts": str(time.time()),
        "clicked": 0
    }

    retries = 0
    while retries < 5:
        try:
            links.insert_one(data)
            break
        except DuplicateKeyError:
            if is_custom_code:
                return None
            else:
                retries += 1

    parsed = urlparse(url_for("link", _external=True, code=code))

    if config["link_shortener"]["convert_punycode"]:
        try:
            new_host = idna.decode(parsed.hostname)
            parsed._replace(hostname=new_host)
        except ValueError:
            pass
    url = urlunparse(parsed)

    return url


@app.route("/api/mk", methods=["POST"])
def mk_ln():
    if not config["auth"]["anon_can_shrt"] and (config["auth"]["user_can_shrt"] or config["auth"]["admin_can_shrt"]):
        user = users.get_user()
        if user is None:
            return jsonify({
                "ok": False,
                "reason": "Requires HTTP Basic auth"
            })
        if user is False:
            return jsonify({
                "ok": False,
                "reason": "Login failed"
            })

        if not config["auth"]["user_can_shrt"] and config["auth"]["admin_can_shrt"]:
            if not user["is_admin"]:
                return jsonify({
                    "ok": False,
                    "reason": "Requires admin priviledges"
                })
            if not config["auth"]["admin_can_shrt"]:
                return jsonify({
                    "ok": False,
                    "reason": "shrt not permitted"
                })

    target = request.form["url"]

    url = shorten(
        target,
        code=request.form.get("code"),
        hidden=request.form.get("hidden")
    )
    if url is None:
        return jsonify({
            "ok": False,
            "reason": "Unknown",
        })

    return jsonify({
        "ok": True,
        "url": url,
    })


@app.route("/")
def home():
    if config["link_shortener"]["not_found_redirect"] is not None:
        return redirect(config["link_shortener"]["not_found_redirect"])
    else:
        abort(404)



@app.route("/<string:code>")
def link(code):
    data = links.find_and_modify({"code": code}, {"$inc":{"clicked": 1}})
    if data is not None:
        return redirect(data["url"])
    else:
        return home()
