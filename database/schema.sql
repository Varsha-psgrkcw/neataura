-- ============================================================
-- NeatAura Database Schema
-- Run: python database/init_db.py
-- ============================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    phone         TEXT,
    city          TEXT    DEFAULT 'Pollachi',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Service categories (Home / Technical)
CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,       -- e.g. 'Home', 'Technical'
    icon TEXT
);

-- Services
CREATE TABLE IF NOT EXISTS services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT    NOT NULL,   -- 'home' | 'technical'
    name        TEXT    NOT NULL,
    icon        TEXT,
    description TEXT,
    base_price  REAL    NOT NULL,
    duration    TEXT    DEFAULT '2-3 hrs'
);

-- Workers
CREATE TABLE IF NOT EXISTS workers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    avatar_bg  TEXT    DEFAULT '#6C3CE1',
    rating     REAL    DEFAULT 4.5,
    experience TEXT,
    city       TEXT,
    languages  TEXT,           -- comma-separated
    available  INTEGER DEFAULT 1,
    trust_badge TEXT   DEFAULT '✓ Background Verified'
);

-- Worker ↔ Service mapping
CREATE TABLE IF NOT EXISTS worker_services (
    worker_id  INTEGER REFERENCES workers(id),
    service_id INTEGER REFERENCES services(id),
    PRIMARY KEY (worker_id, service_id)
);

-- Bookings
CREATE TABLE IF NOT EXISTS bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    service_id    INTEGER NOT NULL REFERENCES services(id),
    worker_id     INTEGER REFERENCES workers(id),
    city          TEXT,
    booking_date  DATE    NOT NULL,
    booking_time  TIME    NOT NULL,
    num_workers   INTEGER DEFAULT 1,
    num_days      INTEGER DEFAULT 1,
    total_amount  REAL    NOT NULL,
    status        TEXT    DEFAULT 'pending',  -- pending | active | completed | cancelled
    payment_method TEXT,
    notes         TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Seed Data ──────────────────────────────────────────────

-- Home Services
INSERT OR IGNORE INTO services (category, name, icon, description, base_price, duration) VALUES
  ('home', 'Home Cleaning',    '🧹', 'Complete home deep cleaning',         499,  '3-4 hrs'),
  ('home', 'Kitchen Cleaning', '🍳', 'Kitchen and appliance cleaning',       349,  '2-3 hrs'),
  ('home', 'Bathroom Cleaning','🚿', 'Bathroom & toilet sanitisation',       249,  '1-2 hrs'),
  ('home', 'Sofa Cleaning',    '🛋️', 'Sofa & upholstery deep clean',         599,  '2-3 hrs'),
  ('home', 'Pest Control',     '🐛', 'Pest & insect treatment',             799,  '1-2 hrs'),
  ('home', 'Laundry & Ironing','👕', 'Washing and ironing service',          299,  '2-3 hrs');

-- Technical Services
INSERT OR IGNORE INTO services (category, name, icon, description, base_price, duration) VALUES
  ('technical', 'AC Repair',        '❄️', 'AC service, gas refill & repair',     699,  '1-2 hrs'),
  ('technical', 'Plumbing',         '🔧', 'Pipe fitting, leakage, blockage',      399,  '1-2 hrs'),
  ('technical', 'Electrician',      '⚡', 'Wiring, switches, fan installation',   349,  '1-2 hrs'),
  ('technical', 'CCTV & Security',  '📷', 'Camera installation & setup',          999,  '2-3 hrs'),
  ('technical', 'Laptop/PC Repair', '💻', 'Hardware & software troubleshooting',  499,  '1-3 hrs'),
  ('technical', 'TV Repair',        '📺', 'LED, LCD, Smart TV repair',            599,  '1-2 hrs');

-- Workers
INSERT OR IGNORE INTO workers (name, avatar_bg, rating, experience, city, languages) VALUES
  ('Ravi Kumar',  '#6C3CE1', 4.9, '6 yrs exp', 'Pollachi',  'Tamil, English'),
  ('Meena Devi',  '#10B981', 4.8, '4 yrs exp', 'Coimbatore','Tamil, Telugu'),
  ('Arjun Raj',   '#2563EB', 4.7, '5 yrs exp', 'Erode',     'Tamil'),
  ('Priya Singh', '#F59E0B', 4.6, '3 yrs exp', 'Tiruppur',  'Tamil, Hindi'),
  ('Kumar S.',    '#EF4444', 4.8, '7 yrs exp', 'Salem',     'Tamil, English');

-- Link workers to services (all workers handle all services for demo)
INSERT OR IGNORE INTO worker_services (worker_id, service_id)
  SELECT w.id, s.id FROM workers w, services s;