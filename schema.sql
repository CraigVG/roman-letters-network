-- Roman Letters Network Database Schema
-- Tracking ~3000+ late antique letters (300-600 AD)

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_latin TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    role TEXT,           -- e.g. 'bishop', 'pope', 'senator', 'emperor'
    location TEXT,       -- primary location
    lat REAL,
    lon REAL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS letters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection TEXT NOT NULL,       -- e.g. 'sidonius_apollinaris', 'gregory_great'
    book INTEGER,                   -- book number within collection
    letter_number INTEGER,          -- letter number within book
    ref_id TEXT UNIQUE,             -- canonical reference e.g. 'sidonius.ep.1.1'
    sender_id INTEGER REFERENCES authors(id),
    recipient_id INTEGER REFERENCES authors(id),
    year_approx INTEGER,            -- approximate year written
    year_min INTEGER,               -- earliest possible year
    year_max INTEGER,               -- latest possible year
    origin_place TEXT,              -- where sent from
    origin_lat REAL,
    origin_lon REAL,
    dest_place TEXT,                -- where sent to
    dest_lat REAL,
    dest_lon REAL,
    subject_summary TEXT,           -- brief summary of contents
    latin_text TEXT,                -- original Latin
    english_text TEXT,              -- English translation
    translation_source TEXT,        -- 'existing' or 'ai_translated'
    source_url TEXT,                -- where we got the Latin text
    translation_url TEXT,           -- where we got the English (if existing)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS people_mentioned (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    letter_id INTEGER REFERENCES letters(id),
    person_id INTEGER REFERENCES authors(id),
    role_in_letter TEXT             -- 'mentioned', 'courier', 'subject', etc.
);

CREATE TABLE IF NOT EXISTS places_mentioned (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    letter_id INTEGER REFERENCES letters(id),
    place_name TEXT,
    lat REAL,
    lon REAL,
    context TEXT                    -- how it's referenced in the letter
);

-- Collections metadata
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    author_name TEXT NOT NULL,
    title TEXT,
    letter_count INTEGER,
    date_range TEXT,
    latin_source_url TEXT,
    english_source_url TEXT,
    scrape_status TEXT DEFAULT 'pending',  -- pending, in_progress, complete, failed
    notes TEXT
);

-- Indexes for visualization queries
CREATE INDEX IF NOT EXISTS idx_letters_sender ON letters(sender_id);
CREATE INDEX IF NOT EXISTS idx_letters_recipient ON letters(recipient_id);
CREATE INDEX IF NOT EXISTS idx_letters_year ON letters(year_approx);
CREATE INDEX IF NOT EXISTS idx_letters_collection ON letters(collection);
CREATE INDEX IF NOT EXISTS idx_people_mentioned_letter ON people_mentioned(letter_id);
CREATE INDEX IF NOT EXISTS idx_people_mentioned_person ON people_mentioned(person_id);
