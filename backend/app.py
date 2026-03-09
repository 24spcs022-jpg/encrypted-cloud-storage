import os, json, base64, uuid, hashlib, time
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from crypto_utils import *
import re

app = Flask(__name__)
CORS(app)

BASE = os.path.dirname(__file__)
FRONTEND = os.path.join(BASE, "..", "frontend")
UPLOADS = os.path.join(BASE, "uploads")
DOWNLOADS = os.path.join(BASE, "downloads")
USERS = os.path.join(BASE, "users.json")

os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(DOWNLOADS, exist_ok=True)

if not os.path.exists(USERS):
    json.dump({}, open(USERS, "w"))

# ---------------- USERS ----------------

def load_users():
    return json.load(open(USERS))

def save_users(u):
    json.dump(u, open(USERS, "w"), indent=2)

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_token(u, t, users):
    return u in users and users[u].get("token") == t


# ---------------- FRONTEND ----------------

@app.get("/")
def home():
    return send_from_directory(FRONTEND, "index.html")

@app.get("/dashboard")
def dash():
    return send_from_directory(FRONTEND, "dashboard.html")

@app.get("/chat")
def chat_page():
    return send_from_directory(FRONTEND, "chat.html")

@app.get("/frontend/<path:p>")
def f(p):
    return send_from_directory(FRONTEND, p)


# ---------------- PASSWORD SECURITY ----------------

def is_strong_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
    return re.match(pattern, password)


# ---------------- AUTH ----------------

@app.post("/register")
def register():

    u = request.form.get("username")
    p = request.form.get("password")

    users = load_users()

    if u in users:
        return jsonify({"error": "User already exists"})

    # check strong password
    if not is_strong_password(p):
        return jsonify({
            "error": "Password must contain 8 characters, uppercase, lowercase, number and special symbol"
        })

    hashed = hash_pw(p)

    priv, pub = generate_rsa_keys()

    users[u] = {
        "password": hashed,
        "private": base64.b64encode(priv).decode(),
        "public": base64.b64encode(pub).decode(),
        "files": {},
        "token": None,
        "messages": []
    }

    save_users(users)

    return jsonify({"message": "Registered successfully"})

@app.post("/login")
def login():

    username = request.form.get("username")
    password = request.form.get("password")

    users = load_users()

    # check user exists
    if username not in users:
        return jsonify({"error":"Invalid username or password"})

    # check password
    stored = users[username]["password"]
    entered = hash_pw(password)

    if stored != entered:
        return jsonify({"error":"Invalid username or password"})

    token = str(uuid.uuid4())

    users[username]["token"] = token
    save_users(users)

    return jsonify({"token":token})

# ---------------- UPLOAD ----------------

@app.post("/upload")
def upload():

    u = request.form["username"]
    t = request.form["token"]
    expiry = request.form.get("expiry", "never")
    files = request.files.getlist("files")

    users = load_users()

    if not check_token(u, t, users):
        return jsonify({"error": "Session expired"}), 401

    now = int(time.time())
    uploaded = []

    for file in files:

        if expiry == "24h":
            exp = now + 86400
        elif expiry == "7d":
            exp = now + 604800
        else:
            exp = None

        data = file.read()

        aes, nonce, tag, enc = aes_encrypt(data)

        enc_key = rsa_encrypt(
            base64.b64decode(users[u]["public"]),
            aes
        )

        fid = str(uuid.uuid4())

        open(os.path.join(UPLOADS, fid), "wb").write(enc)

        json.dump({
            "name": file.filename,
            "nonce": base64.b64encode(nonce).decode(),
            "tag": base64.b64encode(tag).decode(),
            "key": base64.b64encode(enc_key).decode(),
            "expire": exp
        }, open(os.path.join(UPLOADS, fid + ".meta"), "w"))

        users[u]["files"][file.filename] = fid
        uploaded.append(file.filename)

    save_users(users)

    return jsonify({"uploaded": uploaded})


# ---------------- FILE LIST ----------------

@app.get("/my_files")
def my_files():

    u = request.args["username"]
    t = request.args["token"]

    users = load_users()

    if not check_token(u, t, users):
        return jsonify([])

    return jsonify(list(users[u]["files"].keys()))


# ---------------- DOWNLOAD ----------------

@app.get("/download")
def download():

    u = request.args["username"]
    t = request.args["token"]
    f = request.args["filename"]

    users = load_users()

    if not check_token(u, t, users):
        return "Expired", 401

    fid = users[u]["files"][f]

    meta = json.load(open(os.path.join(UPLOADS, fid + ".meta")))

    if meta["expire"] and int(time.time()) > meta["expire"]:
        return "File expired", 410

    enc = open(os.path.join(UPLOADS, fid), "rb").read()

    aes = rsa_decrypt(
        base64.b64decode(users[u]["private"]),
        base64.b64decode(meta["key"])
    )

    data = aes_decrypt(
        aes,
        base64.b64decode(meta["nonce"]),
        base64.b64decode(meta["tag"]),
        enc
    )

    out = os.path.join(DOWNLOADS, f)

    open(out, "wb").write(data)

    return send_file(out, as_attachment=True)


# ---------------- DELETE ----------------

@app.post("/delete_file")
def delete_file():

    u = request.form["username"]
    t = request.form["token"]
    fname = request.form["filename"]

    users = load_users()

    if not check_token(u, t, users):
        return jsonify({"error": "Expired"}), 401

    fid = users[u]["files"].get(fname)

    if not fid:
        return jsonify({"error": "Not found"})

    try:
        os.remove(os.path.join(UPLOADS, fid))
        os.remove(os.path.join(UPLOADS, fid + ".meta"))
    except:
        pass

    del users[u]["files"][fname]

    save_users(users)

    return jsonify({"message": "Deleted"})

#-----------------share----------------------

@app.post("/share_file")
def share_file():

    sender = request.form["sender"]
    receiver = request.form["receiver"]
    token = request.form["token"]
    filename = request.form["filename"]

    users = load_users()

    if not check_token(sender, token, users):
        return jsonify({"error": "Session expired"}), 401

    if receiver not in users:
        return jsonify({"error": "User not found"})

    fid = users[sender]["files"].get(filename)

    if not fid:
        return jsonify({"error": "File not found"})

    # give receiver access
    users[receiver]["files"][filename] = fid

    save_users(users)

    return jsonify({"message": "File shared"})


# ---------------- CHAT ----------------

@app.post("/send_message")
def send_message():

    s = request.form["sender"]
    r = request.form["receiver"]
    t = request.form["token"]
    txt = request.form["text"]
    reply = request.form.get("reply_to")

    users = load_users()

    if not check_token(s, t, users):
        return jsonify({"error": "Expired"})

    if r not in users:
        return jsonify({"error": "User not found"})

    users[r]["messages"].append({
        "id": str(uuid.uuid4()),
        "from": s,
        "text": txt,
        "reply_to": reply
    })

    save_users(users)

    return jsonify({"message": "Sent"})

@app.get("/inbox")
def inbox():

    u = request.args["username"]
    t = request.args["token"]

    users = load_users()

    if not check_token(u, t, users):
        return jsonify([])

    return jsonify(users[u]["messages"])


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)