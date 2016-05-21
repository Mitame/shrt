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
import random

from . import config, db

last_gen = db["last_gen"]

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

def get_code(item_type, do_random=None):
    if (config["link_shortener"]["randomise"] and do_random is None) or do_random:
        num = random.randint(0, len(config["link_shortener"]["characters"])**64)
    else:
        data = last_gen.find_one({"obj": item_type})
        if data is None:
            num = 0
            last_gen.insert_one({"obj": item_type, "num": num})
        else:
            num = data["num"] + 1
            last_gen.update({"obj": item_type}, {"$set": {"num": num}})


    code_num = set_base(num, len(config["link_shortener"]["characters"]))
    code = ""
    for x in code_num:
        code += config["link_shortener"]["characters"][x]

    # pad the code with characters to make it the min length
    code = code.rjust(
        config["link_shortener"]["min_length"],
        config["link_shortener"]["characters"][0]
    )

    return code
