from flask import Flask, redirect, safe_join
from pymongo import MongoClient

db = MongoClient()["shrt"]

links = db["links"]
files = db["files"]
last_gen = db["last_gen"]

app = Flask(__name__)

LINK_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

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
        num = 0
        last_gen.insert_one({"obj": "link", "num": num})
    else:
        num = data["num"] + 1

    last_gen.update({"obj": "link"}, {"$set": {"num": num}})

    code_num = set_base(num, len(LINK_CHARS))
    code = ""
    for x in code_num:
        code += LINK_CHARS[x]
    return code

@app.route("/api/mk", methods=["POST"])
def mk_ln():
    pass

@app.route("/")
def home():
    return redirect("https://mita.me/")

@app.route("/<string:code>")
def link(code):
    return code

if __name__ == "__main__":
    app.run()
