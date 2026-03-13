CREATE TABLE IF NOT EXISTS papers (
  id VARCHAR(64) PRIMARY KEY,
  title VARCHAR(512) NOT NULL,
  authors JSONB NOT NULL DEFAULT '[]'::jsonb,
  abstract TEXT NOT NULL DEFAULT '',
  status VARCHAR(32) NOT NULL,
  progress_percent INTEGER NOT NULL DEFAULT 0,
  file_path VARCHAR(1024) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  job_id VARCHAR(64) PRIMARY KEY,
  paper_id VARCHAR(64) NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  status VARCHAR(32) NOT NULL,
  stage VARCHAR(64) NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_structures (
  paper_id VARCHAR(64) PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_overviews (
  paper_id VARCHAR(64) PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
  payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS reading_memories (
  paper_id VARCHAR(64) PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
  progress_status VARCHAR(32) NOT NULL DEFAULT 'new',
  progress_percent INTEGER NOT NULL DEFAULT 0,
  last_read_section VARCHAR(255) NOT NULL DEFAULT 'Introduction',
  stuck_points JSONB NOT NULL DEFAULT '[]'::jsonb,
  key_questions JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS chat_sessions (
  session_id VARCHAR(64) PRIMARY KEY,
  paper_id VARCHAR(64) NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
  message_id VARCHAR(64) PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
  role VARCHAR(32) NOT NULL,
  content_md TEXT NOT NULL,
  citations JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at VARCHAR(64) NOT NULL
);
