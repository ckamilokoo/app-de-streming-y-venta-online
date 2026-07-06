CREATE TABLE users (
  id TEXT PRIMARY KEY,              -- clerk user id (o dev id en mock)
  role TEXT NOT NULL DEFAULT 'buyer' CHECK (role IN ('buyer','streamer','admin')),
  display_name TEXT NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE streams (
  id TEXT PRIMARY KEY,              -- uuid propio
  streamer_id TEXT NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'scheduled'
    CHECK (status IN ('scheduled','live','ended')),
  ingest_type TEXT NOT NULL DEFAULT 'whip' CHECK (ingest_type IN ('whip','rtmp')),
  cf_live_input_uid TEXT NOT NULL,
  whip_url TEXT NOT NULL,
  whep_url TEXT NOT NULL,
  scheduled_at INTEGER,
  started_at INTEGER,
  ended_at INTEGER
);

CREATE TABLE products (
  id TEXT PRIMARY KEY,
  streamer_id TEXT NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  price_clp INTEGER NOT NULL,       -- CLP sin decimales
  stock INTEGER NOT NULL DEFAULT 0,
  image_key TEXT                    -- key en storage (local dev / R2 prod)
);

CREATE TABLE stream_products (
  stream_id TEXT NOT NULL REFERENCES streams(id),
  product_id TEXT NOT NULL REFERENCES products(id),
  PRIMARY KEY (stream_id, product_id)
);

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  stream_id TEXT NOT NULL REFERENCES streams(id),
  product_id TEXT NOT NULL REFERENCES products(id),
  buyer_id TEXT NOT NULL REFERENCES users(id),
  qty INTEGER NOT NULL DEFAULT 1,
  amount_clp INTEGER NOT NULL,
  payment_status TEXT NOT NULL DEFAULT 'mock_paid'
    CHECK (payment_status IN ('pending','mock_paid','paid','failed')),
  mp_preference_id TEXT,            -- fase 2 MercadoPago
  created_at INTEGER NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX idx_orders_stream ON orders(stream_id);
