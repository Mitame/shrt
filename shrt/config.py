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


from . import app

import json
from binascii import b2a_hex
from os import urandom

default_config = {
    "secret_key": b2a_hex(urandom(32)).decode("utf8"),
    "auth": {
        "anon_can_create_user": False,
        "user_can_create_user": True,
        "admin_can_create_user": True,

        "anon_can_shrt": True,
        "user_can_shrt": True,
        "admin_can_shrt": True,

        "anon_can_upload": False,
        "user_can_upload": True,
        "admin_can_upload": True,
    },

    "link_shortener": {
        "characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
        "min_length": 4,
        "randomise": False,
        "convert_punycode": True,
        "not_found_redirect": None
    },

    "uploads": {
        "drop_dir": "./drop",
        "default_max_file_size": 100*1024**2,  # 100MB
        "auto_deletion_timeout": -1,  # disabled
    }
}

def merge_dicts(a, b):
    """Use a as base, overwrite with items from b"""
    new_dict = a
    for key, value in b.items():
        if isinstance(value, dict):
            if key in a:
                merge_dicts(a[key], b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]

    return new_dict


try:
    loaded_config = json.load(open("config.json"))
    config = merge_dicts(default_config, loaded_config)
except IOError:
    print("Config file not found. Loading defaults...")
    print("You should probably edit the config file with your settings.")
    config = default_config

json.dump(
    config,
    open("config.json", "w"),
    sort_keys = True,
    indent = 2,
    separators = (',', ': ')
)

app.secret_key = config["secret_key"]

banned_words = []
