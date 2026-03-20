#!/usr/bin/env node
/**
 * generate-hub-cities.js
 *
 * Pre-computes hub city profiles from the SQLite database and writes
 * public/data/hub-cities.json.
 *
 * For each city it computes:
 *   - Letters sent per decade (outgoing_by_decade)
 *   - Letters received per decade (incoming_by_decade)
 *   - Top correspondent cities (top_correspondents)
 *   - Connectivity score per decade (unique cities communicated with)
 *
 * Usage: node scripts/generate-hub-cities.js
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.resolve(__dirname, '../../data/roman_letters.db');
const OUT_FILE = path.resolve(__dirname, '../public/data/hub-cities.json');

const HUB_CITIES = [
  { name: 'Rome',           lat: 41.8967, lon: 12.4822 },
  { name: 'Constantinople', lat: 41.0082, lon: 28.9784 },
  { name: 'Arles',          lat: 43.6767, lon: 4.6278  },
  { name: 'Marseille',      lat: 43.2965, lon: 5.3813  },
  { name: 'Ravenna',        lat: 44.4184, lon: 12.2035 },
  { name: 'Carthage',       lat: 36.8065, lon: 10.1815 },
  { name: 'Milan',          lat: 45.4642, lon: 9.19    },
  { name: 'Clermont',       lat: 45.7772, lon: 3.087   },
  { name: 'Lyon',           lat: 45.7484, lon: 4.8467  },
  { name: 'Vienne',         lat: 45.524,  lon: 4.874   },
  { name: 'Antioch',        lat: 36.2021, lon: 36.1601 },
  { name: 'Alexandria',     lat: 31.2001, lon: 29.9187 },
  { name: 'Hippo Regius',   lat: 36.8833, lon: 7.75    },
  { name: 'Caesarea',       lat: 38.7312, lon: 35.4787 },
  { name: 'Jerusalem',      lat: 31.7054, lon: 35.2024 },
];

const MATCH_THRESHOLD = 1.0; // degrees — max distance to match a city

function coordDist(lat1, lon1, lat2, lon2) {
  return Math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2);
}

function findCity(lat, lon) {
  if (lat == null || lon == null) return null;
  let best = null;
  let bestDist = MATCH_THRESHOLD;
  for (const c of HUB_CITIES) {
    const d = coordDist(lat, lon, c.lat, c.lon);
    if (d < bestDist) { bestDist = d; best = c.name; }
  }
  return best;
}

// ── Load letters from DB ──────────────────────────────────────────────────────

const db = new Database(DB_PATH, { readonly: true });

const rows = db.prepare(`
  SELECT
    l.year_approx,
    COALESCE(l.origin_lat, sp.lat) AS s_lat,
    COALESCE(l.origin_lon, sp.lon) AS s_lon,
    COALESCE(l.dest_lat, rp.lat)   AS r_lat,
    COALESCE(l.dest_lon, rp.lon)   AS r_lon
  FROM letters l
  LEFT JOIN authors sp ON l.sender_id    = sp.id
  LEFT JOIN authors rp ON l.recipient_id = rp.id
  WHERE l.year_approx IS NOT NULL
`).all();

db.close();

// ── Aggregate ─────────────────────────────────────────────────────────────────

const cityIndex = {};
for (const c of HUB_CITIES) {
  cityIndex[c.name] = {
    name: c.name, lat: c.lat, lon: c.lon,
    outgoing: {}, incoming: {},
    sentTo: {}, recvFrom: {},
    partnersByDecade: {},
  };
}

for (const row of rows) {
  const decade = String(Math.floor(row.year_approx / 10) * 10);
  const sc = findCity(row.s_lat, row.s_lon);
  const rc = findCity(row.r_lat, row.r_lon);

  if (sc && cityIndex[sc]) {
    const ci = cityIndex[sc];
    ci.outgoing[decade] = (ci.outgoing[decade] || 0) + 1;
    if (rc && rc !== sc) {
      ci.sentTo[rc] = (ci.sentTo[rc] || 0) + 1;
      if (!ci.partnersByDecade[decade]) ci.partnersByDecade[decade] = new Set();
      ci.partnersByDecade[decade].add(rc);
    }
  }

  if (rc && cityIndex[rc]) {
    const ci = cityIndex[rc];
    ci.incoming[decade] = (ci.incoming[decade] || 0) + 1;
    if (sc && sc !== rc) {
      ci.recvFrom[sc] = (ci.recvFrom[sc] || 0) + 1;
      if (!ci.partnersByDecade[decade]) ci.partnersByDecade[decade] = new Set();
      ci.partnersByDecade[decade].add(sc);
    }
  }
}

// ── Build output array ────────────────────────────────────────────────────────

const hubList = HUB_CITIES.map(({ name }) => {
  const ci = cityIndex[name];

  const combined = {};
  for (const [c, cnt] of Object.entries(ci.sentTo))   combined[c] = (combined[c] || 0) + cnt;
  for (const [c, cnt] of Object.entries(ci.recvFrom))  combined[c] = (combined[c] || 0) + cnt;
  const topCorrespondents = Object.entries(combined)
    .sort((a, b) => b[1] - a[1]).slice(0, 10)
    .map(([city, count]) => ({ city, count }));

  const connectivityByDecade = {};
  for (const [decade, partners] of Object.entries(ci.partnersByDecade)) {
    connectivityByDecade[decade] = partners.size;
  }

  return {
    name,
    lat: ci.lat,
    lon: ci.lon,
    total_sent:              Object.values(ci.outgoing).reduce((a, b) => a + b, 0),
    total_received:          Object.values(ci.incoming).reduce((a, b) => a + b, 0),
    outgoing_by_decade:      ci.outgoing,
    incoming_by_decade:      ci.incoming,
    connectivity_by_decade:  connectivityByDecade,
    top_correspondents:      topCorrespondents,
  };
});

// ── Write JSON ────────────────────────────────────────────────────────────────

fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
fs.writeFileSync(OUT_FILE, JSON.stringify(hubList, null, 2));
console.log(`Written ${hubList.length} hub cities to ${OUT_FILE}`);
