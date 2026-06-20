from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, jwt, bcrypt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__, static_folder="../frontend/static")
CORS(app)

SECRET_KEY = "neataura-secret-key-change-in-production"
DB_PATH = os.path.join(os.path.dirname(__file__), "../database/neataura.db")

# ─── DB helper ───────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ─── JWT auth decorator ──────────────────────────────────────
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

# ─── Auth routes ─────────────────────────────────────────────
@app.post("/api/register")
def register():
    data = request.json
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
                (username, email, pw_hash)
            )
            db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409

    return jsonify({"message": "Account created successfully"}), 201

@app.post("/api/login")
def login():
    data  = request.json
    email = data.get("email", "").strip().lower()
    pw    = data.get("password", "")

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

    if not user or not bcrypt.checkpw(pw.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY, algorithm="HS256"
    )
    return jsonify({"token": token, "username": user["username"]})

# ─── Services ────────────────────────────────────────────────
@app.get("/api/services")
def get_services():
    with get_db() as db:
        rows = db.execute("SELECT * FROM services ORDER BY category, name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/services/<int:service_id>")
def get_service(service_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone()
    if not row:
        return jsonify({"error": "Service not found"}), 404
    return jsonify(dict(row))

# ─── Workers ─────────────────────────────────────────────────
@app.get("/api/workers")
def get_workers():
    service_id = request.args.get("service_id")
    city       = request.args.get("city")
    with get_db() as db:
        query = "SELECT * FROM workers WHERE available=1"
        params = []
        if service_id:
            query += " AND id IN (SELECT worker_id FROM worker_services WHERE service_id=?)"
            params.append(service_id)
        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
        rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

# ─── Bookings ────────────────────────────────────────────────
@app.post("/api/bookings")
@require_auth
def create_booking():
    data = request.json
    with get_db() as db:
        cur = db.execute(
            """INSERT INTO bookings
               (user_id, service_id, worker_id, city, booking_date, booking_time,
                num_workers, num_days, total_amount, status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (request.user_id, data["service_id"], data.get("worker_id"),
             data["city"], data["date"], data["time"],
             data.get("num_workers", 1), data.get("num_days", 1),
             data["total_amount"], "pending")
        )
        booking_id = cur.lastrowid
        db.commit()
    return jsonify({"booking_id": booking_id, "message": "Booking confirmed!"}), 201

@app.get("/api/bookings")
@require_auth
def get_bookings():
    with get_db() as db:
        rows = db.execute(
            """SELECT b.*, s.name as service_name, w.name as worker_name
               FROM bookings b
               LEFT JOIN services s ON b.service_id = s.id
               LEFT JOIN workers  w ON b.worker_id  = w.id
               WHERE b.user_id=?
               ORDER BY b.created_at DESC""",
            (request.user_id,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.put("/api/bookings/<int:booking_id>/cancel")
@require_auth
def cancel_booking(booking_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM bookings WHERE id=? AND user_id=?",
            (booking_id, request.user_id)
        ).fetchone()
        if not row:
            return jsonify({"error": "Booking not found"}), 404
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,))
        db.commit()
    return jsonify({"message": "Booking cancelled"})

# ─── User profile ────────────────────────────────────────────
@app.get("/api/profile")
@require_auth
def get_profile():
    with get_db() as db:
        user = db.execute(
            "SELECT id, username, email, city, phone, created_at FROM users WHERE id=?",
            (request.user_id,)
        ).fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))

@app.put("/api/profile")
@require_auth
def update_profile():
    data = request.json
    with get_db() as db:
        db.execute(
            "UPDATE users SET city=?, phone=? WHERE id=?",
            (data.get("city"), data.get("phone"), request.user_id)
        )
        db.commit()
    return jsonify({"message": "Profile updated"})

# ─── Serve frontend ──────────────────────────────────────────
@app.get("/")
def serve_frontend():
    return send_from_directory("../frontend/templates", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))