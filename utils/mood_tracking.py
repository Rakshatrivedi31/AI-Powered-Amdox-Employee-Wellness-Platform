import json
import logging
import os
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  FILE PATHS
# ══════════════════════════════════════════════════════════

DATA_FILE = "data/employee_data.json"
# ══════════════════════════════════════════════════════════
#  TEAM STRUCTURE
# ══════════════════════════════════════════════════════════

TEAMS = {
    "Team Alpha 🔵": {
        "members":    ["Raksha", "Sneha", "Smita", "Isha"],
        "lead":       "Raksha",
        "department": "Engineering",
        "color":      "#667eea",
        "icon":       "🔵",
    },
    "Team Beta 🟢": {
        "members":    ["Saniya", "Arjun", "Priya", "Kajal"],
        "lead":       "Saniya",
        "department": "Design",
        "color":      "#00e87a",
        "icon":       "🟢",
    },
    "Team Gamma 🔴": {
        "members":    ["Divya", "Rohit", "Anjali", "Vikram"],
        "lead":       "Divya",
        "department": "Marketing",
        "color":      "#ff4757",
        "icon":       "🔴",
    },
}

ALL_EMPLOYEES: list = [m for t in TEAMS.values() for m in t["members"]]

# ══════════════════════════════════════════════════════════
#  AUTHENTICATION
# ══════════════════════════════════════════════════════════

EMPLOYEE_CREDENTIALS: dict = {emp.lower(): f"{emp}@2026" for emp in ALL_EMPLOYEES}

HR_CREDENTIALS: dict = {
    "hr_admin": "admin@2026",
    "admin":    "admin@2026",
    "hr":       "hr@2026",
}


def authenticate_employee(username: str, password: str):
    """
    Returns (success, display_name, role)
    role is 'employee' or 'hr'
    """
    if not username or not password:
        return False, None, None

    uname = username.strip().lower()

    if uname in HR_CREDENTIALS:
        if HR_CREDENTIALS[uname] == password:
            return True, uname, "hr"

    if uname in EMPLOYEE_CREDENTIALS:
        if EMPLOYEE_CREDENTIALS[uname] == password:
            for emp in ALL_EMPLOYEES:
                if emp.lower() == uname:
                    return True, emp, "employee"

    return False, None, None

# ══════════════════════════════════════════════════════════
#  DEFAULT DATA STRUCTURE
# ══════════════════════════════════════════════════════════

def _default_data() -> dict:
    employees: dict = {}
    for team_name, team_info in TEAMS.items():
        for member in team_info["members"]:
            employees[member] = {
                "mood_history":  [],
                "tasks":         [],
                "alerts":        [],
                "team":          team_name,
                "email":         f"{member.lower()}@company.com",
                "employee_id":   member.lower(),
                "is_lead":       member == team_info["lead"],
                "last_emotion":  "Neutral",
                "last_workload": 5,
            }
    return {"employees": employees, "teams": {k: v for k, v in TEAMS.items()}}

# ══════════════════════════════════════════════════════════
#  LOAD / SAVE
# ══════════════════════════════════════════════════════════

def load_employee_data() -> dict:
    os.makedirs("data", exist_ok=True)
    default = _default_data()

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)

            for emp, info in default["employees"].items():
                stored.setdefault("employees", {})
                if emp not in stored["employees"]:
                    stored["employees"][emp] = info
                else:
                    for k, v in info.items():
                        stored["employees"][emp].setdefault(k, v)

            stored["teams"] = TEAMS
            return stored
        except Exception as e:
            logger.error(f"Load error: {e} — using defaults")

    return default


def save_employee_data(data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

# ══════════════════════════════════════════════════════════
#  CSV HELPER — REMOVED (wellness.db use ho raha hai)
# _CSV_FIELDS, _export_to_csv(), load_csv_history() — sab hata diye
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
#  SAVE MOOD
# ══════════════════════════════════════════════════════════

def save_mood(employee: str, emotion: str, workload: int,
              stress: float, data: dict, method: str = "text") -> dict:
    if employee not in data.get("employees", {}):
        team = get_employee_team(employee)
        data.setdefault("employees", {})[employee] = {
            "mood_history": [], "tasks": [], "alerts": [],
            "team": team,
            "email": f"{employee.lower()}@company.com",
            "employee_id": employee.lower(),
            "is_lead": False,
            "last_emotion": "Neutral",
            "last_workload": 5,
        }

    now = datetime.now()
    entry = {
        "timestamp":   now.isoformat(),
        "date":        now.strftime("%Y-%m-%d"),
        "time":        now.strftime("%H:%M"),
        "emotion":     emotion,
        "workload":    int(max(1, min(10, workload))),
        "stress_level": round(float(min(max(stress, 0), 10)), 1),
        "method":      method,
    }

    data["employees"][employee]["mood_history"].append(entry)
    data["employees"][employee]["last_emotion"]  = emotion
    data["employees"][employee]["last_workload"] = entry["workload"]

    save_employee_data(data)
    return entry

# ══════════════════════════════════════════════════════════
#  MOOD HISTORY & STATS
# ══════════════════════════════════════════════════════════

def get_mood_history(employee: str, data: dict, days: int = 30) -> list:
    history = (data.get("employees", {})
                   .get(employee, {})
                   .get("mood_history", []))

    if not days:
        return history

    cutoff = datetime.now() - timedelta(days=days)
    result = []
    for entry in history:
        try:
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff:
                result.append(entry)
        except (KeyError, ValueError):
            pass
    return result


def get_mood_stats(employee: str, data: dict) -> dict:
    history = get_mood_history(employee, data, 30)

    empty = {
        "total_entries": 0, "average_stress": 0, "average_workload": 0,
        "most_common_mood": "No Data", "high_stress_days": 0,
        "mood_distribution": {}, "trend": "no data",
    }

    if not history:
        return empty

    emotions  = [e["emotion"] for e in history]
    stresses  = [e["stress_level"] for e in history]
    workloads = [e["workload"] for e in history]

    mid = len(stresses) // 2
    if len(stresses) > 1 and mid > 0:
        first_half  = sum(stresses[:mid]) / mid
        second_half = sum(stresses[mid:]) / (len(stresses) - mid)
        if second_half < first_half - 0.5:
            trend = "improving 📈"
        elif second_half > first_half + 0.5:
            trend = "worsening 📉"
        else:
            trend = "stable ➡️"
    else:
        trend = "insufficient data"

    return {
        "total_entries":     len(history),
        "mood_distribution": dict(Counter(emotions)),
        "average_stress":    round(sum(stresses)  / len(stresses),  1),
        "average_workload":  round(sum(workloads) / len(workloads), 1),
        "most_common_mood":  Counter(emotions).most_common(1)[0][0],
        "high_stress_days":  sum(1 for s in stresses if s >= 7),
        "trend":             trend,
    }

# ══════════════════════════════════════════════════════════
#  TEAM HELPERS
# ══════════════════════════════════════════════════════════

def get_employee_team(employee: str) -> str:
    for team_name, td in TEAMS.items():
        if employee in td["members"]:
            return team_name
    return "Unknown"


def get_team_stats(team_name: str, data: dict):
    td = TEAMS.get(team_name)
    if not td:
        return None

    members = td["members"]
    all_emotions, all_stress, all_workload, member_status = [], [], [], []

    for emp in members:
        history = get_mood_history(emp, data, 7)
        if history:
            latest = history[-1]
            all_emotions.append(latest["emotion"])
            all_stress.append(latest["stress_level"])
            all_workload.append(latest["workload"])
            member_status.append({
                "name":     emp,
                "emotion":  latest["emotion"],
                "stress":   latest["stress_level"],
                "workload": latest["workload"],
                "is_lead":  emp == td["lead"],
                "date":     latest["date"],
            })
        else:
            member_status.append({
                "name": emp, "emotion": "No Data",
                "stress": 0, "workload": 0,
                "is_lead": emp == td["lead"], "date": "—",
            })

    avg_stress = round(sum(all_stress) / len(all_stress), 1) if all_stress else 0.0

    return {
        "team_name":        team_name,
        "members":          member_status,
        "avg_stress":       avg_stress,
        "avg_workload":     round(sum(all_workload) / len(all_workload), 1) if all_workload else 0.0,
        "mood_distribution": dict(Counter(all_emotions)) if all_emotions else {},
        "high_stress_count": sum(1 for s in all_stress if s >= 7),
        "team_health":      max(0, round(100 - avg_stress * 10, 0)),
        "lead":             td["lead"],
        "department":       td["department"],
        "color":            td["color"],
        "icon":             td["icon"],
        "data_available":   len(all_stress) > 0,
    }


def get_all_teams_stats(data: dict) -> dict:
    return {name: get_team_stats(name, data) for name in TEAMS}

# ══════════════════════════════════════════════════════════
#  TREND DATA — JSON se (CSV removed)
# ══════════════════════════════════════════════════════════

def get_employee_trend_data(employee: str, days: int = 30, data: dict = None) -> pd.DataFrame:
    """CSV hata diya — ab JSON se directly padhta hai."""
    if data is None:
        data = load_employee_data()
    history = get_mood_history(employee, data, days)
    if not history:
        return pd.DataFrame()
    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["date"]      = pd.to_datetime(df["date"],      errors="coerce")
    return df.sort_values("timestamp")

# ══════════════════════════════════════════════════════════
#  PLOTLY CHARTS
# ══════════════════════════════════════════════════════════

def create_mood_timeline_chart(employee: str, days: int = 30, data: dict = None):
    """Returns plotly Figure or None if no data."""
    df = get_employee_trend_data(employee, days, data)
    if df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["stress_level"],
        mode="lines+markers", name="Stress",
        line=dict(color="#ff4757", width=3),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["workload"],
        mode="lines+markers", name="Workload",
        line=dict(color="#00c4ff", width=2, dash="dot"),
        marker=dict(size=6),
    ))
    fig.add_hline(
        y=7, line_dash="dash", line_color="#ffa502",
        annotation_text="⚠️ High Stress",
        annotation_position="top right",
    )
    fig.update_layout(
        title=f"📈 {employee} — Mood Timeline ({days} days)",
        xaxis_title="Date",
        yaxis=dict(title="Level (0-10)", range=[0, 10]),
        hovermode="x unified",
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def create_mood_distribution_chart(employee: str, days: int = 30, data: dict = None):
    """Returns plotly Figure or None if no data."""
    df = get_employee_trend_data(employee, days, data)
    if df.empty:
        return None

    mood_counts = df["emotion"].value_counts()
    color_map = {
        "Happy": "#00e87a", "Calm": "#00c4ff", "Neutral": "#888888",
        "Sad": "#4fc3f7",   "Stressed": "#ffa502", "Angry": "#ff4757",
        "Tired": "#a29bfe", "Energetic": "#ffd93d",
    }
    colors = [color_map.get(m, "#888888") for m in mood_counts.index]

    fig = go.Figure(data=[go.Pie(
        labels=mood_counts.index,
        values=mood_counts.values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo="label+percent",
        textposition="auto",
    )])
    fig.update_layout(
        title=f"🎭 {employee} — Mood Distribution",
        height=300,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
    )
    return fig


def create_team_health_gauge(health_score: float, team_label: str):
    """Gauge chart for team health score (0-100)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health_score,
        title={"text": f"{team_label} Health", "font": {"color": "#94a3b8"}},
        number={"suffix": "/100", "font": {"size": 24, "color": "#fff"}},
        gauge={
            "axis":  {"range": [0, 100], "tickcolor": "#475569"},
            "bar":   {"color": "#667eea"},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0,  40], "color": "rgba(255,71,87,0.2)"},
                {"range": [40, 70], "color": "rgba(255,165,2,0.2)"},
                {"range": [70,100], "color": "rgba(0,232,122,0.2)"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75, "value": 40,
            },
        },
    ))
    fig.update_layout(
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig

# ══════════════════════════════════════════════════════════
#  SAMPLE DATA GENERATOR
# ══════════════════════════════════════════════════════════

def generate_sample_data(data: dict, days: int = 7) -> None:
    import random
    emotions = ["Happy", "Calm", "Neutral", "Sad", "Stressed", "Angry", "Tired", "Energetic"]
    methods  = ["text", "camera", "speech", "manual"]

    for employee in ALL_EMPLOYEES:
        if data["employees"][employee].get("mood_history"):
            continue

        for day_offset in range(days, 0, -1):
            date = datetime.now() - timedelta(days=day_offset)

            if day_offset <= 2:
                emotion  = random.choice(["Stressed", "Tired", "Neutral", "Angry"])
                workload = random.randint(6, 10)
                stress   = random.uniform(6, 9)
            elif day_offset <= 4:
                emotion  = random.choice(["Neutral", "Calm", "Stressed", "Happy"])
                workload = random.randint(4, 8)
                stress   = random.uniform(4, 7)
            else:
                emotion  = random.choice(["Happy", "Calm", "Energetic", "Neutral"])
                workload = random.randint(3, 6)
                stress   = random.uniform(2, 5)

            entry = {
                "timestamp":   date.isoformat(),
                "date":        date.strftime("%Y-%m-%d"),
                "time":        date.strftime("%H:%M"),
                "emotion":     emotion,
                "workload":    workload,
                "stress_level": round(stress, 1),
                "method":      random.choice(methods),
            }
            data["employees"][employee]["mood_history"].append(entry)
            

    save_employee_data(data)