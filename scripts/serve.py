#!/usr/bin/env python3
"""
Simple HTTP server that serves the visualization and provides a JSON API
for querying the letters database.

Run: python3 scripts/serve.py
Open: http://localhost:8765
"""

import http.server
import json
import os
import sqlite3
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'roman_letters.db')
WEB_DIR = os.path.join(os.path.dirname(__file__), '..', 'web')
PORT = 8765


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class APIHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path.startswith('/api/'):
            self.handle_api(path, params)
        else:
            super().do_GET()

    def handle_api(self, path, params):
        conn = get_db()
        try:
            if path == '/api/stats':
                data = self.api_stats(conn)
            elif path == '/api/network':
                data = self.api_network(conn, params)
            elif path == '/api/authors':
                data = self.api_authors(conn, params)
            elif path == '/api/letters':
                data = self.api_letters(conn, params)
            elif path == '/api/letter':
                data = self.api_letter(conn, params)
            elif path == '/api/collections':
                data = self.api_collections(conn)
            elif path == '/api/timeline':
                data = self.api_timeline(conn, params)
            elif path == '/api/map_letters':
                data = self.api_map_letters(conn, params)
            else:
                self.send_error(404, 'Unknown API endpoint')
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        finally:
            conn.close()

    def api_stats(self, conn):
        c = conn.cursor()
        stats = {}
        c.execute('SELECT COUNT(*) FROM letters')
        stats['total_letters'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM letters WHERE english_text IS NOT NULL')
        stats['english_translated'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM letters WHERE latin_text IS NOT NULL')
        stats['latin_available'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM letters WHERE modern_english IS NOT NULL')
        stats['modern_english'] = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM authors')
        stats['total_people'] = c.fetchone()[0]
        c.execute('SELECT COUNT(DISTINCT collection) FROM letters')
        stats['collections_scraped'] = c.fetchone()[0]
        c.execute('''
            SELECT collection, COUNT(*) as cnt
            FROM letters GROUP BY collection ORDER BY cnt DESC
        ''')
        stats['by_collection'] = [{'collection': r[0], 'count': r[1]} for r in c.fetchall()]
        return stats

    def api_network(self, conn, params):
        """Return nodes and edges for the network graph."""
        c = conn.cursor()

        year_min = int(params.get('year_min', [300])[0])
        year_max = int(params.get('year_max', [650])[0])
        collection = params.get('collection', [None])[0]

        # Build query conditions
        conditions = []
        query_params = []
        if collection:
            conditions.append('l.collection = ?')
            query_params.append(collection)

        where = ''
        if conditions:
            where = 'WHERE ' + ' AND '.join(conditions)

        # Get edges (letter flows between people)
        c.execute(f'''
            SELECT
                l.sender_id, l.recipient_id,
                COUNT(*) as letter_count,
                s.name as sender_name, s.lat as s_lat, s.lon as s_lon, s.role as s_role,
                r.name as recipient_name, r.lat as r_lat, r.lon as r_lon, r.role as r_role,
                GROUP_CONCAT(DISTINCT l.collection) as collections
            FROM letters l
            JOIN authors s ON l.sender_id = s.id
            JOIN authors r ON l.recipient_id = r.id
            {where}
            GROUP BY l.sender_id, l.recipient_id
            ORDER BY letter_count DESC
        ''', query_params)

        edges = []
        node_ids = set()
        for row in c.fetchall():
            edges.append({
                'source': row[0],
                'target': row[1],
                'weight': row[2],
                'sender_name': row[3],
                'recipient_name': row[7],
                'collections': row[11],
            })
            node_ids.add(row[0])
            node_ids.add(row[1])

        # Get nodes
        nodes = []
        if node_ids:
            placeholders = ','.join('?' * len(node_ids))
            c.execute(f'''
                SELECT id, name, role, location, lat, lon, birth_year, death_year
                FROM authors WHERE id IN ({placeholders})
            ''', list(node_ids))
            for row in c.fetchall():
                # Count letters sent and received
                c2 = conn.cursor()
                c2.execute('SELECT COUNT(*) FROM letters WHERE sender_id = ?', (row[0],))
                sent = c2.fetchone()[0]
                c2.execute('SELECT COUNT(*) FROM letters WHERE recipient_id = ?', (row[0],))
                received = c2.fetchone()[0]

                nodes.append({
                    'id': row[0],
                    'name': row[1],
                    'role': row[2],
                    'location': row[3],
                    'lat': row[4],
                    'lon': row[5],
                    'birth_year': row[6],
                    'death_year': row[7],
                    'letters_sent': sent,
                    'letters_received': received,
                })

        return {'nodes': nodes, 'edges': edges}

    def api_authors(self, conn, params):
        c = conn.cursor()
        c.execute('''
            SELECT a.id, a.name, a.name_latin, a.role, a.location, a.lat, a.lon,
                   a.birth_year, a.death_year, a.bio,
                   (SELECT COUNT(*) FROM letters WHERE sender_id = a.id) as sent,
                   (SELECT COUNT(*) FROM letters WHERE recipient_id = a.id) as received
            FROM authors a
            ORDER BY sent + received DESC
        ''')
        return [dict(r) for r in c.fetchall()]

    def api_letters(self, conn, params):
        c = conn.cursor()
        collection = params.get('collection', [None])[0]
        author_id = params.get('author_id', [None])[0]
        limit = int(params.get('limit', [100])[0])
        offset = int(params.get('offset', [0])[0])

        conditions = []
        query_params = []
        if collection:
            conditions.append('l.collection = ?')
            query_params.append(collection)
        if author_id:
            conditions.append('(l.sender_id = ? OR l.recipient_id = ?)')
            query_params.extend([author_id, author_id])

        where = ''
        if conditions:
            where = 'WHERE ' + ' AND '.join(conditions)

        query_params.extend([limit, offset])
        c.execute(f'''
            SELECT l.id, l.collection, l.letter_number, l.ref_id,
                   s.name as sender, r.name as recipient,
                   l.year_approx, l.subject_summary,
                   CASE WHEN l.english_text IS NOT NULL THEN 1 ELSE 0 END as has_english,
                   CASE WHEN l.latin_text IS NOT NULL THEN 1 ELSE 0 END as has_latin,
                   l.source_url, l.quick_summary, l.interesting_note
            FROM letters l
            LEFT JOIN authors s ON l.sender_id = s.id
            LEFT JOIN authors r ON l.recipient_id = r.id
            {where}
            ORDER BY l.collection, l.letter_number
            LIMIT ? OFFSET ?
        ''', query_params)
        return [dict(r) for r in c.fetchall()]

    def api_letter(self, conn, params):
        """Get full letter text by ID."""
        letter_id = params.get('id', [None])[0]
        if not letter_id:
            return {'error': 'id required'}
        c = conn.cursor()
        c.execute('''
            SELECT l.*, s.name as sender_name, r.name as recipient_name
            FROM letters l
            LEFT JOIN authors s ON l.sender_id = s.id
            LEFT JOIN authors r ON l.recipient_id = r.id
            WHERE l.id = ?
        ''', (letter_id,))
        row = c.fetchone()
        if row:
            return dict(row)
        return {'error': 'not found'}

    def api_collections(self, conn):
        c = conn.cursor()
        # Include scan_url if column exists
        try:
            c.execute('SELECT *, scan_url FROM collections ORDER BY date_range')
        except Exception:
            c.execute('SELECT * FROM collections ORDER BY date_range')
        return [dict(r) for r in c.fetchall()]

    def api_map_letters(self, conn, params):
        """Return letters with sender/recipient coordinates for map timelapse."""
        c = conn.cursor()
        c.execute('''
            SELECT l.id, l.collection, l.letter_number, l.year_approx,
                   s.name as sender_name, s.lat as s_lat, s.lon as s_lon,
                   s.location as s_location,
                   r.name as recipient_name, r.lat as r_lat, r.lon as r_lon,
                   r.location as r_location,
                   l.quick_summary, l.interesting_note
            FROM letters l
            JOIN authors s ON l.sender_id = s.id
            JOIN authors r ON l.recipient_id = r.id
            WHERE s.lat IS NOT NULL AND r.lat IS NOT NULL
                  AND l.year_approx IS NOT NULL
            ORDER BY l.year_approx, l.collection, l.letter_number
        ''')
        return [dict(r) for r in c.fetchall()]

    def api_timeline(self, conn, params):
        """Return letter counts by decade for timeline visualization."""
        c = conn.cursor()
        c.execute('''
            SELECT
                (year_approx / 10) * 10 as decade,
                COUNT(*) as count,
                collection
            FROM letters
            WHERE year_approx IS NOT NULL
            GROUP BY decade, collection
            ORDER BY decade
        ''')
        return [dict(r) for r in c.fetchall()]

    def log_message(self, format, *args):
        # Quiet logging - only log API calls
        if '/api/' in str(args[0]):
            super().log_message(format, *args)


if __name__ == '__main__':
    print(f"Starting Roman Letters Network server on http://localhost:{PORT}")
    print(f"Database: {os.path.abspath(DB_PATH)}")
    server = http.server.HTTPServer(('', PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
