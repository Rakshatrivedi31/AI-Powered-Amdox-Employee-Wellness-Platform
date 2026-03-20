import sqlite3
import json
import os
import logging
from datetime import datetime

logger  = logging.getLogger(__name__)
DB_PATH = "data/wellness.db"


def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Disable foreign key enforcement so entries never silently rejected
    conn.execute("PRAGMA foreign_keys = OFF")
    return conn


def init_db():
    conn = get_conn()
    c    = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id   TEXT PRIMARY KEY,
        name          TEXT NOT NULL,
        team          TEXT,
        email         TEXT,
        is_lead       INTEGER DEFAULT 0,
        last_emotion  TEXT,
        last_workload INTEGER DEFAULT 5,
        created_at    TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS mood_history (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id  TEXT NOT NULL,
        timestamp    TEXT NOT NULL,
        date         TEXT NOT NULL,
        time         TEXT,
        emotion      TEXT,
        workload     INTEGER,
        stress_level REAL,
        method       TEXT
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id  TEXT NOT NULL,
        level        TEXT,
        level_emoji  TEXT,
        color        TEXT,
        stress_level REAL,
        message      TEXT,
        actions_json TEXT,
        timestamp    TEXT,
        resolved     INTEGER DEFAULT 0,
        resolved_at  TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_mood_emp   ON mood_history(employee_id);
    CREATE INDEX IF NOT EXISTS idx_mood_date  ON mood_history(date);
    CREATE INDEX IF NOT EXISTS idx_alert_emp  ON alerts(employee_id);
    """)
    conn.commit()
    conn.close()
    logger.info("✅ SQLite DB initialized")


def migrate_from_json(json_path: str = "data/employee_data.json") -> bool:
    if not os.path.exists(json_path):
        return False
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            jdata = json.load(f)
    except Exception as e:
        logger.error(f"Migration JSON read error: {e}")
        return False

    conn = get_conn()
    c    = conn.cursor()

    for name, emp in jdata.get("employees", {}).items():
        emp_id = emp.get("employee_id", name.lower().replace(" ", "_"))

        c.execute("""
            INSERT OR REPLACE INTO employees
            (employee_id, name, team, email, is_lead, last_emotion, last_workload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            emp_id, name,
            emp.get("team", ""),
            emp.get("email", ""),
            int(emp.get("is_lead", False)),
            emp.get("last_emotion", "Neutral"),
            emp.get("last_workload", 5),
        ))

        for h in emp.get("mood_history", []):
            ts = h.get("timestamp", "")
            if not ts:
                continue
            exists = c.execute(
                "SELECT 1 FROM mood_history WHERE employee_id=? AND timestamp=?",
                (emp_id, ts)
            ).fetchone()
            if not exists:
                c.execute("""
                    INSERT INTO mood_history
                    (employee_id, timestamp, date, time, emotion, workload, stress_level, method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_id, ts,
                    h.get("date", ""), h.get("time", ""),
                    h.get("emotion", ""), h.get("workload", 5),
                    h.get("stress_level", 0.0), h.get("method", ""),
                ))

        for a in emp.get("alerts", []):
            ts = a.get("timestamp", "")
            if not ts:
                continue
            exists = c.execute(
                "SELECT 1 FROM alerts WHERE employee_id=? AND timestamp=?",
                (emp_id, ts)
            ).fetchone()
            if not exists:
                c.execute("""
                    INSERT INTO alerts
                    (employee_id, level, level_emoji, color, stress_level,
                     message, actions_json, timestamp, resolved, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_id,
                    a.get("level", ""), a.get("level_emoji", ""),
                    a.get("color", ""), a.get("stress_level", 0.0),
                    a.get("message", ""),
                    json.dumps(a.get("actions", [])),
                    ts,
                    int(a.get("resolved", False)),
                    a.get("resolved_at", None),
                ))

    conn.commit()
    conn.close()
    logger.info(f"✅ Migrated from {json_path}")
    return True


# ══════════════════════════════════════════════════════════
#  READ HELPERS
# ══════════════════════════════════════════════════════════

def get_all_employees_table():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            e.name          AS "Employee",
            e.team          AS "Team",
            e.email         AS "Email",
            CASE e.is_lead WHEN 1 THEN '⭐ Yes' ELSE 'No' END AS "Team Lead",
            e.last_emotion  AS "Last Emotion",
            e.last_workload AS "Last Workload",
            COUNT(m.id)     AS "Total Check-ins",
            ROUND(AVG(m.stress_level), 1) AS "Avg Stress",
            MAX(m.date)     AS "Last Check-in"
        FROM employees e
        LEFT JOIN mood_history m ON e.employee_id = m.employee_id
        GROUP BY e.employee_id
        ORDER BY e.team, e.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mood_history_table(employee_id: str = None, days: int = 30):
    conn = get_conn()
    if employee_id:
        rows = conn.execute("""
            SELECT
                e.name         AS "Employee",
                m.date         AS "Date",
                m.time         AS "Time",
                m.emotion      AS "Emotion",
                m.stress_level AS "Stress",
                m.workload     AS "Workload",
                m.method       AS "Method"
            FROM mood_history m
            LEFT JOIN employees e ON m.employee_id = e.employee_id
            WHERE m.employee_id = ?
              AND m.date >= date('now', ?)
            ORDER BY m.timestamp DESC
        """, (employee_id, f'-{days} days')).fetchall()
    else:
        rows = conn.execute("""
            SELECT
                COALESCE(e.name, m.employee_id) AS "Employee",
                m.date         AS "Date",
                m.time         AS "Time",
                m.emotion      AS "Emotion",
                m.stress_level AS "Stress",
                m.workload     AS "Workload",
                m.method       AS "Method"
            FROM mood_history m
            LEFT JOIN employees e ON m.employee_id = e.employee_id
            WHERE m.date >= date('now', ?)
            ORDER BY m.timestamp DESC
        """, (f'-{days} days',)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_alerts_table():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            COALESCE(e.name, a.employee_id) AS "Employee",
            a.level        AS "Level",
            a.stress_level AS "Stress",
            a.message      AS "Message",
            a.timestamp    AS "Timestamp",
            CASE a.resolved WHEN 1 THEN '✅ Resolved' ELSE '🔴 Active' END AS "Status",
            a.resolved_at  AS "Resolved At"
        FROM alerts a
        LEFT JOIN employees e ON a.employee_id = e.employee_id
        ORDER BY a.timestamp DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_db_stats():
    conn  = get_conn()
    stats = {}
    stats['employees']     = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    stats['mood_entries']  = conn.execute("SELECT COUNT(*) FROM mood_history").fetchone()[0]
    stats['alerts_total']  = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    stats['alerts_active'] = conn.execute("SELECT COUNT(*) FROM alerts WHERE resolved=0").fetchone()[0]
    stats['date_range']    = conn.execute("SELECT MIN(date), MAX(date) FROM mood_history").fetchone()
    stats['db_size_kb']    = round(os.path.getsize(DB_PATH) / 1024, 1) if os.path.exists(DB_PATH) else 0
    conn.close()
    return stats


# ══════════════════════════════════════════════════════════
#  WRITE HELPERS
# ══════════════════════════════════════════════════════════

def upsert_employee_status(employee_id: str, last_emotion: str, last_workload: int):
    """Update last emotion/workload. Auto-inserts employee row if missing."""
    emp_id = employee_id.lower().strip()
    conn   = get_conn()
    # Ensure employee row exists (handles any missing employee gracefully)
    conn.execute("""
        INSERT OR IGNORE INTO employees (employee_id, name, team)
        VALUES (?, ?, 'Unknown')
    """, (emp_id, emp_id.capitalize()))
    conn.execute("""
        UPDATE employees SET last_emotion=?, last_workload=? WHERE employee_id=?
    """, (last_emotion, last_workload, emp_id))
    conn.commit()
    conn.close()


def insert_mood_entry(employee_id: str, entry: dict):
    """
    Insert one mood check-in.
    - Normalises employee_id to lowercase
    - Auto-creates employee row if missing (no silent failures)
    - Uses microsecond timestamp to avoid duplicate skips
    """
    emp_id = employee_id.lower().strip()
    now    = datetime.now()

    # Always generate a fresh unique timestamp to avoid duplicate-skip bug
    ts = entry.get("timestamp") or now.strftime('%Y-%m-%dT%H:%M:%S.%f')

    conn = get_conn()
    # Auto-insert employee if missing — prevents foreign key / silent reject
    conn.execute("""
        INSERT OR IGNORE INTO employees (employee_id, name, team)
        VALUES (?, ?, 'Unknown')
    """, (emp_id, emp_id.capitalize()))

    conn.execute("""
        INSERT INTO mood_history
        (employee_id, timestamp, date, time, emotion, workload, stress_level, method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        emp_id,
        ts,
        entry.get("date",         now.strftime('%Y-%m-%d')),
        entry.get("time",         now.strftime('%H:%M')),
        entry.get("emotion",      "Neutral"),
        entry.get("workload",     5),
        entry.get("stress_level", 0.0),
        entry.get("method",       "manual"),
    ))
    conn.commit()
    conn.close()
    logger.info(f"✅ Mood saved: {emp_id} | {entry.get('emotion')} | stress={entry.get('stress_level')}")


def insert_alert(employee_id: str, alert: dict):
    """Insert one alert. Normalises employee_id."""
    emp_id = employee_id.lower().strip()
    ts     = alert.get("timestamp") or datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO employees (employee_id, name, team)
        VALUES (?, ?, 'Unknown')
    """, (emp_id, emp_id.capitalize()))

    conn.execute("""
        INSERT INTO alerts
        (employee_id, level, level_emoji, color, stress_level,
         message, actions_json, timestamp, resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        emp_id,
        alert.get("level",        "MONITOR"),
        alert.get("level_emoji",  "🔔"),
        alert.get("color",        "#ffa502"),
        alert.get("stress_level", 0.0),
        alert.get("message",      ""),
        json.dumps(alert.get("actions", [])),
        ts,
    ))
    conn.commit()
    conn.close()


def purge_old_entries(days: int) -> tuple:
    conn    = get_conn()
    cutoff  = f'-{days} days'
    m_count = conn.execute(
        "SELECT COUNT(*) FROM mood_history WHERE date < date('now', ?)", (cutoff,)
    ).fetchone()[0]
    a_count = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE timestamp < datetime('now', ?)", (cutoff,)
    ).fetchone()[0]
    conn.execute("DELETE FROM mood_history WHERE date < date('now', ?)", (cutoff,))
    conn.execute("DELETE FROM alerts WHERE timestamp < datetime('now', ?)", (cutoff,))
    conn.commit()
    conn.close()
    return m_count, a_count


# ── Auto-init on import ───────────────────────────────────
init_db()
migrate_from_json()

if __name__ == "__main__":
    stats = get_db_stats()
    print(f"📊 DB Stats:")
    print(f"  Employees:    {stats['employees']}")
    print(f"  Mood entries: {stats['mood_entries']}")
    print(f"  Alerts:       {stats['alerts_total']}")
    print(f"  DB size:      {stats['db_size_kb']} KB")