import os, json, uuid, hashlib, re
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE = os.path.dirname(__file__)
FRONTEND = os.path.join(BASE, "..", "frontend")
UPLOADS = os.path.join(BASE, "uploads")
USERS = os.path.join(BASE, "users.json")

os.makedirs(UPLOADS, exist_ok=True)

if not os.path.exists(USERS):
    json.dump({}, open(USERS, "w"))

def load_users():
    return json.load(open(USERS))

def save_users(u):
    json.dump(u, open(USERS, "w"), indent=2)

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def check_token(u,t,users):
    return u in users and users[u].get("token")==t

def strong_password(p):
    pattern=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
    return re.match(pattern,p)

# ---------- FRONTEND ----------
@app.get("/")
def home():
    return send_from_directory(FRONTEND,"index.html")

@app.get("/dashboard")
def dash():
    return send_from_directory(FRONTEND,"dashboard.html")

@app.get("/chat")
def chat():
    return send_from_directory(FRONTEND,"chat.html")

# ---------- REGISTER ----------
@app.post("/register")
def register():
    u=request.form.get("username")
    p=request.form.get("password")
    users=load_users()

    if u in users:
        return jsonify({"error":"User exists"})

    if not strong_password(p):
        return jsonify({"error":"Weak password"})

    users[u]={
        "password":hash_pw(p),
        "files":{},
        "messages":[],
        "token":None
    }

    save_users(users)
    return jsonify({"message":"Registered"})

# ---------- LOGIN ----------
@app.post("/login")
def login():

    u = request.form.get("username")
    p = request.form.get("password")  # optional

    users = load_users()

    if u not in users:
        return jsonify({"error":"User not found"})

    # ✅ Password login
    if p:
        if users[u]["password"] != hash_pw(p):
            return jsonify({"error":"Wrong password"})

    # ✅ OTP login (no password check)

    token = str(uuid.uuid4())
    users[u]["token"] = token

    save_users(users)

    return jsonify({"token":token})

# ---------- UPLOAD ----------
@app.post("/upload")
def upload():
    u=request.form["username"]
    t=request.form["token"]
    users=load_users()

    if not check_token(u,t,users):
        return jsonify({"error":"Session expired"})

    f=request.files["file"]
    fid=str(uuid.uuid4())
    path=os.path.join(UPLOADS,fid)
    f.save(path)

    users[u]["files"][f.filename]=fid
    save_users(users)

    return jsonify({"message":"Uploaded"})

# ---------- FILE LIST ----------
@app.get("/my_files")
def my_files():
    u=request.args["username"]
    t=request.args["token"]
    users=load_users()

    if not check_token(u,t,users):
        return jsonify([])

    return jsonify(list(users[u]["files"].keys()))

# ---------- DOWNLOAD ----------
@app.get("/download")
def download():
    u=request.args["username"]
    t=request.args["token"]
    f=request.args["filename"]
    users=load_users()

    if not check_token(u,t,users):
        return "Expired",401

    fid=users[u]["files"][f]
    return send_file(os.path.join(UPLOADS,fid),as_attachment=True)

# ---------- SHARE ----------
@app.post("/share_file")
def share_file():
    sender=request.form["sender"]
    receiver=request.form["receiver"]
    filename=request.form["filename"]

    users=load_users()

    if receiver not in users:
        return jsonify({"error":"User not found"})

    if filename not in users[sender]["files"]:
        return jsonify({"error":"File not found"})

    fid=users[sender]["files"][filename]
    users[receiver]["files"][filename]=fid

    save_users(users)
    return jsonify({"message":"File shared"})

# ---------- CHAT ----------
@app.post("/send_message")
def send_message():
    s=request.form["sender"]
    r=request.form["receiver"]
    txt=request.form["text"]

    users=load_users()

    if r not in users:
        return jsonify({"error":"User not found"})

    users[r]["messages"].append({
        "from":s,
        "text":txt
    })

    save_users(users)
    return jsonify({"message":"sent"})

@app.get("/inbox")
def inbox():
    u=request.args["username"]
    users=load_users()
    return jsonify(users[u]["messages"])

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
