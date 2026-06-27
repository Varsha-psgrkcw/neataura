-- NeatAura Database Schema (SQLite + PostgreSQL compatible)

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    phone         TEXT,
    city          TEXT    DEFAULT 'Pollachi',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    id          SERIAL PRIMARY KEY,
    category    TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    icon        TEXT,
    description TEXT,
    base_price  REAL    NOT NULL,
    duration    TEXT    DEFAULT '2-3 hrs'
);

CREATE TABLE IF NOT EXISTS workers (
    id          SERIAL PRIMARY KEY,
    name        TEXT    NOT NULL,
    gender      TEXT    NOT NULL DEFAULT 'Male',
    avatar_bg   TEXT    DEFAULT '#6C3CE1',
    initials    TEXT,
    rating      REAL    DEFAULT 4.5,
    trust_score TEXT    DEFAULT '96%',
    experience  TEXT,
    city        TEXT,
    languages   TEXT,
    available   INTEGER DEFAULT 1,
    trust_badge TEXT    DEFAULT 'Background Verified'
);

CREATE TABLE IF NOT EXISTS worker_services (
    worker_id  INTEGER REFERENCES workers(id),
    service_id INTEGER REFERENCES services(id),
    PRIMARY KEY (worker_id, service_id)
);

CREATE TABLE IF NOT EXISTS bookings (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    service_id     INTEGER NOT NULL REFERENCES services(id),
    worker_id      INTEGER REFERENCES workers(id),
    city           TEXT,
    booking_date   DATE    NOT NULL,
    booking_time   TIME    NOT NULL,
    num_workers    INTEGER DEFAULT 1,
    num_days       INTEGER DEFAULT 1,
    total_amount   REAL    NOT NULL,
    status         TEXT    DEFAULT 'pending',
    notes          TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Seed Services ──────────────────────────────────────────
INSERT INTO services (category, name, icon, description, base_price, duration) VALUES
  ('home', 'Home Cleaning',     '🧹', 'Complete home deep cleaning',           499, '3-4 hrs'),
  ('home', 'Kitchen Cleaning',  '🍳', 'Kitchen and appliance cleaning',         349, '2-3 hrs'),
  ('home', 'Bathroom Cleaning', '🚿', 'Bathroom & toilet sanitisation',         249, '1-2 hrs'),
  ('home', 'Sofa Cleaning',     '🛋', 'Sofa & upholstery deep clean',           599, '2-3 hrs'),
  ('home', 'Pest Control',      '🐛', 'Pest & insect treatment',               799, '1-2 hrs'),
  ('home', 'Laundry & Ironing', '👕', 'Washing and ironing service',            299, '2-3 hrs'),
  ('technical', 'AC Repair',        '❄', 'AC service, gas refill & repair',     699, '1-2 hrs'),
  ('technical', 'Plumbing',         '🔧', 'Pipe fitting, leakage, blockage',    399, '1-2 hrs'),
  ('technical', 'Electrician',      '⚡', 'Wiring, switches, fan installation', 349, '1-2 hrs'),
  ('technical', 'CCTV & Security',  '📷', 'Camera installation & setup',        999, '2-3 hrs'),
  ('technical', 'Laptop/PC Repair', '💻', 'Hardware & software troubleshooting',499, '1-3 hrs'),
  ('technical', 'TV Repair',        '📺', 'LED, LCD, Smart TV repair',          599, '1-2 hrs')
ON CONFLICT DO NOTHING;

-- ─── Seed Workers (with gender) ─────────────────────────────
INSERT INTO workers (name, gender, initials, avatar_bg, rating, trust_score, experience, city, languages) VALUES
  ('Ravi Kumar',  'Male',   'RK', '#6C3CE1', 4.9, '98%', '6 yrs exp', 'Pollachi',   'Tamil, English'),
  ('Meena Devi',  'Female', 'MD', '#E85D9A', 4.8, '96%', '4 yrs exp', 'Coimbatore', 'Tamil, Hindi'),
  ('Arjun Raj',   'Male',   'AR', '#2563EB', 4.7, '97%', '5 yrs exp', 'Erode',      'Tamil, English'),
  ('Priya Singh', 'Female', 'PS', '#10B981', 4.6, '94%', '3 yrs exp', 'Tiruppur',   'Tamil, Hindi'),
  ('Kumar S.',    'Male',   'KS', '#F59E0B', 4.8, '95%', '7 yrs exp', 'Salem',      'Tamil, English'),
  ('Lakshmi N.',  'Female', 'LN', '#EF4444', 4.7, '93%', '2 yrs exp', 'Pollachi',   'Tamil')
ON CONFLICT DO NOTHING;

-- Link all workers to all services
INSERT INTO worker_services (worker_id, service_id)
  SELECT w.id, s.id FROM workers w, services s
ON CONFLICT DO NOTHING;