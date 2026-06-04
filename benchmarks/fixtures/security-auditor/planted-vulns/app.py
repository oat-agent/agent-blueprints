"""Deliberately vulnerable sample service used by the security-auditor benchmark.

DO NOT copy this code. It plants three issues the agent is expected to find:
  1. SQL injection via string-formatted query (get_user).
  2. A hardcoded AWS secret access key.
  3. (See requirements.txt) a known-vulnerable dependency pin.
"""

import sqlite3

# Planted issue #2: hardcoded credential (fake but pattern-matching value).
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY00"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"


def get_user(conn: sqlite3.Connection, user_id: str):
    cur = conn.cursor()
    # Planted issue #1: SQL injection — user_id is interpolated into the query.
    cur.execute("SELECT * FROM users WHERE id = '%s'" % user_id)
    return cur.fetchone()


def healthcheck():
    return {"status": "ok"}
