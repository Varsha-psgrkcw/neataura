from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, jwt, bcrypt
from datetime import datetime, timedelta
from functools import wraps

# ─── Use PostgreSQL on Render, SQLite locally ─────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras
    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    def fetchall(cursor): return cursor.fetchall()
    def fetchone(cursor): return cursor.fetchone()
    PLACEHOLDER = "%s"
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), "../database/neataura.db")
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    PLACEHOLDER = "?"

app = Flask(__name__, static_folder="../frontend/static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

SECRET_KEY = os.environ.get("SECRET_KEY", "neataura-secret-key-change-in-production")

# ─── DB query helper ──────────────────────────────────────────
def db_query(sql, params=(), one=False, write=False):
    sql = sql.replace("?", PLACEHOLDER)
    conn = get_db()
    try:
        if DATABASE_URL:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = conn.cursor()
        cur.execute(sql, params)
        if write:
            conn.commit()
            return cur.lastrowid if not DATABASE_URL else cur.fetchone()
        result = cur.fetchone() if one else cur.fetchall()
        return result
    finally:
        conn.close()

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
    data     = request.json
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        db_query(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, pw_hash), write=True
        )
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Account created successfully"}), 201

@app.post("/api/login")
def login():
    data  = request.json
    email = data.get("email", "").strip().lower()
    pw    = data.get("password", "")

    user = db_query("SELECT * FROM users WHERE email=?", (email,), one=True)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    stored_hash = user["password_hash"] if isinstance(user, dict) else user[3]
    if not bcrypt.checkpw(pw.encode(), stored_hash.encode()):
        return jsonify({"error": "Invalid credentials"}), 401

    user_id   = user["id"] if isinstance(user, dict) else user[0]
    user_name = user["username"] if isinstance(user, dict) else user[1]

    token = jwt.encode(
        {"user_id": user_id, "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY, algorithm="HS256"
    )
    return jsonify({"token": token, "username": user_name})

# ─── Services ────────────────────────────────────────────────
@app.get("/api/services")
def get_services():
    rows = db_query("SELECT * FROM services ORDER BY category, name")
    return jsonify([dict(r) for r in rows])

@app.get("/api/services/<int:service_id>")
def get_service(service_id):
    row = db_query("SELECT * FROM services WHERE id=?", (service_id,), one=True)
    if not row:
        return jsonify({"error": "Service not found"}), 404
    return jsonify(dict(row))

# ─── Workers ─────────────────────────────────────────────────
@app.get("/api/workers")
def get_workers():
    service_id  = request.args.get("service_id")
    city        = request.args.get("city")
    gender_pref = request.args.get("gender")   # Male | Female | Any

    query  = "SELECT * FROM workers WHERE available=1"
    params = []

    if service_id:
        query += " AND id IN (SELECT worker_id FROM worker_services WHERE service_id=?)"
        params.append(service_id)
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    if gender_pref and gender_pref != "Any":
        query += " AND gender=?"
        params.append(gender_pref)

    rows = db_query(query, params)
    return jsonify([dict(r) for r in rows])

# ─── Bookings ────────────────────────────────────────────────
@app.post("/api/bookings")
@require_auth
def create_booking():
    data = request.json
    if DATABASE_URL:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO bookings
               (user_id, service_id, worker_id, city, booking_date, booking_time,
                num_workers, num_days, total_amount, status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (request.user_id, data["service_id"], data.get("worker_id"),
             data["city"], data["date"], data["time"],
             data.get("num_workers", 1), data.get("num_days", 1),
             data["total_amount"], "pending")
        )
        booking_id = cur.fetchone()["id"]
        conn.commit()
        conn.close()
    else:
        import sqlite3
        conn = get_db()
        cur  = conn.execute(
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
        conn.commit()
        conn.close()

    return jsonify({"booking_id": booking_id, "message": "Booking confirmed!"}), 201

@app.get("/api/bookings")
@require_auth
def get_bookings():
    rows = db_query(
        """SELECT b.*, s.name as service_name, w.name as worker_name
           FROM bookings b
           LEFT JOIN services s ON b.service_id = s.id
           LEFT JOIN workers  w ON b.worker_id  = w.id
           WHERE b.user_id=?
           ORDER BY b.created_at DESC""",
        (request.user_id,)
    )
    return jsonify([dict(r) for r in rows])

@app.put("/api/bookings/<int:booking_id>/cancel")
@require_auth
def cancel_booking(booking_id):
    row = db_query(
        "SELECT * FROM bookings WHERE id=? AND user_id=?",
        (booking_id, request.user_id), one=True
    )
    if not row:
        return jsonify({"error": "Booking not found"}), 404
    db_query("UPDATE bookings SET status='cancelled' WHERE id=?", (booking_id,), write=True)
    return jsonify({"message": "Booking cancelled"})

# ─── Profile ─────────────────────────────────────────────────
@app.get("/api/profile")
@require_auth
def get_profile():
    user = db_query(
        "SELECT id, username, email, city, phone, created_at FROM users WHERE id=?",
        (request.user_id,), one=True
    )
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user))

@app.put("/api/profile")
@require_auth
def update_profile():
    data = request.json
    db_query(
        "UPDATE users SET city=?, phone=?, username=? WHERE id=?",
        (data.get("city"), data.get("phone"), data.get("username"), request.user_id),
        write=True
    )
    return jsonify({"message": "Profile updated"})

# ─── SMS Notifications (Fast2SMS) ───────────────────────────
import urllib.request, urllib.parse, json as _json

FAST2SMS_KEY  = os.environ.get("FAST2SMS_KEY", "")   # set in Render env vars
ADMIN_PHONE   = os.environ.get("ADMIN_PHONE", "")    # your 10-digit mobile number

def send_sms(phone, message):
    """Send SMS via Fast2SMS DLT-free route."""
    if not FAST2SMS_KEY or not phone:
        return False
    try:
        payload = urllib.parse.urlencode({
            "route": "q",          # quick / transactional route
            "message": message,
            "language": "english",
            "flash": 0,
            "numbers": phone,
        }).encode()
        req = urllib.request.Request(
            "https://www.fast2sms.com/dev/bulkV2",
            data=payload,
            headers={
                "authorization": FAST2SMS_KEY,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception as e:
        print("SMS error:", e)
        return False

@app.post("/api/notify/booking")
@require_auth
def notify_booking():
    """Called by frontend right after a booking is confirmed."""
    d = request.json or {}
    msg = (
        f"NeatAura Booking Confirmed!\n"
        f"Booking ID  : {d.get('bookingId','—')}\n"
        f"Service     : {d.get('service','—')}\n"
        f"Worker      : {d.get('worker','—')}\n"
        f"Customer    : {d.get('customerName','—')}\n"
        f"Phone       : {d.get('customerPhone','—')}\n"
        f"City        : {d.get('city','—')}\n"
        f"Date & Time : {d.get('date','—')} at {d.get('time','—')}\n"
        f"Payment     : {d.get('paymentMethod','—')}\n"
        f"Amount      : {d.get('amount','—')}"
    )
    ok = send_sms(ADMIN_PHONE, msg)
    return jsonify({"sent": ok})

@app.post("/api/notify/sos")
@require_auth
def notify_sos():
    """Called by frontend when customer triggers SOS."""
    d = request.json or {}
    msg = (
        f"🆘 SOS EMERGENCY — NeatAura\n"
        f"Customer : {d.get('customerName','—')}\n"
        f"Phone    : {d.get('customerPhone','—')}\n"
        f"Address  : {d.get('address','—')}\n"
        f"Booking  : {d.get('bookingId','—')}\n"
        f"Reason   : {d.get('reason','—')}\n"
        f"PLEASE RESPOND IMMEDIATELY!"
    )
    ok = send_sms(ADMIN_PHONE, msg)
    return jsonify({"sent": ok})

# ─── Serve frontend ──────────────────────────────────────────
@app.get("/")
def serve_frontend():
    return send_from_directory("../frontend/templates", "index.html")

@app.get("/static/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("../frontend/static/js", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)