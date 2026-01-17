CREATE TABLE IF NOT EXISTS fitness_events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  activity TEXT NOT NULL CHECK (activity IN ('sleep','rest','walk','run','bike','strength')),
  steps INT NOT NULL CHECK (steps >= 0),
  heart_rate INT NOT NULL CHECK (heart_rate BETWEEN 30 AND 220),
  calories NUMERIC(8,2) NOT NULL CHECK (calories >= 0)
);

CREATE INDEX IF NOT EXISTS idx_fitness_events_ts ON fitness_events(ts);