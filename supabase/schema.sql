-- KLA Business Suite — skema Supabase
-- Jalankan di: dashboard.supabase.com -> project kamu -> SQL Editor -> New query -> Run
--
-- Semua akses aplikasi lewat SERVICE ROLE key (server side, di Python function),
-- yang otomatis bypass RLS. RLS tetap diaktifkan plus policy deny supaya anon key
-- tidak bisa membaca data. Token auth memakai HMAC stateless, jadi tabel sessions
-- tidak diperlukan.

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
  id            BIGSERIAL PRIMARY KEY,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name     TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('super_admin','area_manager','store_leader','sales')),
  branch        TEXT,
  area          TEXT,
  is_active     BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  last_login    TIMESTAMPTZ
);

-- 2. Audit log
CREATE TABLE IF NOT EXISTS audit_log (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT,
  username   TEXT,
  action     TEXT NOT NULL,
  detail     TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Analysis store metadata (satu baris, id = 1)
CREATE TABLE IF NOT EXISTS analysis_store (
  id           BIGINT PRIMARY KEY DEFAULT 1,
  filename     TEXT,
  uploaded_by  TEXT,
  sku_count    INTEGER DEFAULT 0,
  storage_path TEXT,
  uploaded_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 4. PC build history
CREATE TABLE IF NOT EXISTS build_history (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT,
  branch      TEXT,
  build_name  TEXT,
  build_type  TEXT,
  budget      NUMERIC,
  total_price NUMERIC,
  components  TEXT,
  ai_notes    TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: aktifkan di semua tabel, tambah policy deny untuk anon/authenticated.
-- Service role tetap bisa full akses (bypass RLS).
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log     ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE build_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS deny_public_users         ON users;
DROP POLICY IF EXISTS deny_public_audit_log     ON audit_log;
DROP POLICY IF EXISTS deny_public_analysis_store ON analysis_store;
DROP POLICY IF EXISTS deny_public_build_history ON build_history;

CREATE POLICY deny_public_users          ON users          FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
CREATE POLICY deny_public_audit_log      ON audit_log      FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
CREATE POLICY deny_public_analysis_store ON analysis_store FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
CREATE POLICY deny_public_build_history  ON build_history  FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);

-- Seed admin default (password: admin123). Ganti password setelah login pertama.
INSERT INTO users (username, password_hash, full_name, role, is_active)
VALUES (
  'admin',
  '87713280795750557dae5dce27b090dc28bb9b2324314ebb68fd0d4545ca9f73',
  'Super Admin KLA',
  'super_admin',
  true
)
ON CONFLICT (username) DO NOTHING;

-- 5. Storage bucket untuk file Excel dan hasil analisis (private).
INSERT INTO storage.buckets (id, name, public)
VALUES ('kla-inventory', 'kla-inventory', false)
ON CONFLICT (id) DO NOTHING;
