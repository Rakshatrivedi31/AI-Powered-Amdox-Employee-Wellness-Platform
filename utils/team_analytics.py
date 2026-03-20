import pandas as pd
import plotly.graph_objects as go
from collections import Counter, defaultdict
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════
#  LAZY IMPORT — prevents circular imports
# ══════════════════════════════════════════════════════════

def _get_tracking():
    from utils.mood_tracking import TEAMS, get_mood_history
    return TEAMS, get_mood_history


# ══════════════════════════════════════════════════════════
#  CORE ANALYTICS
# ══════════════════════════════════════════════════════════

def analyze_team_mood(data: dict, team_name: str = None) -> dict:
    """
    Company-wide OR single-team mood analysis.
    app.py calls: analyze_team_mood(data)
    """
    TEAMS, get_mood_history = _get_tracking()

    employees = (TEAMS[team_name]["members"]
                 if team_name and team_name in TEAMS
                 else [m for t in TEAMS.values() for m in t["members"]])

    all_moods, all_stress, all_workload = [], [], []

    for emp in employees:
        history = get_mood_history(emp, data, 7)
        if history:
            latest = history[-1]
            all_moods.append(latest.get("emotion", "Neutral"))
            all_stress.append(latest.get("stress_level", 5))
            all_workload.append(latest.get("workload", 5))

    if not all_moods:
        return {
            "mood_distribution": {}, "average_stress": 0.0,
            "average_workload": 0.0, "total_employees": len(employees),
            "active_employees": 0,   "high_stress_count": 0,
            "dominant_mood": "—",    "team_health": 0,
        }

    mood_dist  = Counter(all_moods)
    avg_stress = round(sum(all_stress) / len(all_stress), 1)

    return {
        "mood_distribution":  dict(mood_dist),
        "average_stress":     avg_stress,
        "average_workload":   round(sum(all_workload) / len(all_workload), 1),
        "total_employees":    len(employees),
        "active_employees":   len(all_moods),
        "high_stress_count":  sum(1 for s in all_stress if s >= 7),
        "dominant_mood":      mood_dist.most_common(1)[0][0],
        "team_health":        max(0, round(100 - avg_stress * 10)),
    }


def calculate_team_health_score(data: dict, team_name: str = None) -> float:
    """
    Health score 0-100.
    Factors: Stress 40% + Workload balance 30% + Positive mood 30%

    app.py calls: calculate_team_health_score(team_name, data)
    This function handles BOTH call orders via type detection.
    """
    # Handle reversed args: calculate_team_health_score(team_name_str, data_dict)
    if isinstance(data, str) and isinstance(team_name, dict):
        data, team_name = team_name, data

    stats = analyze_team_mood(data, team_name)
    if not stats or stats["active_employees"] == 0:
        return 0.0

    stress_score   = max(0.0, 40.0 - stats["average_stress"] * 4)
    avg_wl         = stats["average_workload"]
    workload_score = 30.0 if 3 <= avg_wl <= 7 else max(0.0, 30.0 - abs(avg_wl - 5) * 5)
    pos_count      = sum(stats["mood_distribution"].get(m, 0)
                         for m in {"Happy", "Calm", "Energetic"})
    mood_score     = (pos_count / max(stats["active_employees"], 1)) * 30.0

    return round(stress_score + workload_score + mood_score, 1)


def get_at_risk_employees(data: dict, threshold: float = 7.0) -> list:
    """Employees with latest stress >= threshold, sorted desc."""
    TEAMS, get_mood_history = _get_tracking()

    at_risk = []
    for emp in data.get("employees", {}):
        history = get_mood_history(emp, data, 3)
        if history:
            latest = history[-1]
            stress = latest.get("stress_level", 0)
            if stress >= threshold:
                team = next((t for t, d in TEAMS.items() if emp in d["members"]), "Unknown")
                at_risk.append({
                    "name":    emp,
                    "team":    team,
                    "stress":  stress,
                    "emotion": latest.get("emotion", "Neutral"),
                    "date":    latest.get("date", "—"),
                    "status":  "🔴 CRITICAL" if stress >= 8 else "🟠 WARNING",
                })

    return sorted(at_risk, key=lambda x: x["stress"], reverse=True)


def get_employee_comparison(data: dict) -> list:
    """All employees comparison table, sorted by stress desc."""
    TEAMS, get_mood_history = _get_tracking()

    comparison = []
    for emp in data.get("employees", {}):
        history = get_mood_history(emp, data, 7)
        if history:
            latest = history[-1]
            stress = latest.get("stress_level", 0)
            team   = next((t for t, d in TEAMS.items() if emp in d["members"]), "Unknown")
            status = ("🔴 Critical" if stress >= 8 else "🟠 Warning"
                      if stress >= 6 else "🟡 Monitor" if stress >= 4 else "🟢 Good")
            comparison.append({
                "Employee": emp,    "Team":     team,
                "Emotion":  latest.get("emotion", "Neutral"),
                "Stress":   stress, "Workload": latest.get("workload", 5),
                "Status":   status,
            })

    return sorted(comparison, key=lambda x: x["Stress"], reverse=True)


def get_team_stats_all(data: dict) -> dict:
    """Stats dict for all 3 teams."""
    TEAMS, _ = _get_tracking()
    results = {}
    for team_name in TEAMS:
        stats  = analyze_team_mood(data, team_name)
        health = calculate_team_health_score(data, team_name)
        results[team_name] = {
            **stats,
            "health_score": health,
            "status": ("Excellent" if health >= 80 else "Good"     if health >= 60 else
                       "Fair"      if health >= 40 else "Poor"     if health >= 20 else "Critical"),
        }
    return results


def get_company_trends(data: dict, days: int = 7) -> dict:
    """Daily average stress across the company."""
    TEAMS, get_mood_history = _get_tracking()
    all_employees = [m for t in TEAMS.values() for m in t["members"]]
    daily: dict = defaultdict(list)

    for emp in all_employees:
        for entry in get_mood_history(emp, data, days):
            daily[entry["date"]].append(entry["stress_level"])

    result = [
        {"date": d, "avg_stress": round(sum(v) / len(v), 1), "count": len(v)}
        for d, v in sorted(daily.items())
    ]
    return {"daily": result, "total_days": days}


# ══════════════════════════════════════════════════════════
#  RECOMMENDATIONS ENGINE
# ══════════════════════════════════════════════════════════

def get_team_recommendations(data: dict, team_name: str = None) -> list:
    """Actionable HR recommendations based on team stats."""
    stats  = analyze_team_mood(data, team_name)
    health = calculate_team_health_score(data, team_name)
    if not stats or stats["active_employees"] == 0:
        return []

    recs = []

    # Health score recommendation
    if health >= 80:   action = "Great job! Maintain current practices."
    elif health >= 60: action = "Good — continue monitoring stress levels."
    elif health >= 40: action = "Fair — implement wellness programs."
    elif health >= 20: action = "Poor — urgent intervention required."
    else:              action = "Critical — immediate action needed!"

    recs.append({
        "type": "info" if health >= 60 else "warning" if health >= 40 else "urgent",
        "icon": "🌟"   if health >= 80 else "😊"      if health >= 60 else
                "😐"   if health >= 40 else "🚨",
        "title":    f"Team Health: {health}/100",
        "message":  action,
        "priority": "HIGH" if health < 40 else "MEDIUM",
    })

    avg_s = stats["average_stress"]
    if avg_s >= 7:
        recs.append({
            "type": "urgent", "icon": "🚨", "priority": "HIGH",
            "title": "Critical Stress Levels",
            "message": f"Average stress: {avg_s}/10",
            "action": "Schedule mandatory wellness day and counseling",
        })
    elif avg_s >= 5:
        recs.append({
            "type": "warning", "icon": "⚠️", "priority": "MEDIUM",
            "title": "Moderate Stress",
            "message": f"Team stress at {avg_s}/10",
            "action": "Implement stress management workshop",
        })

    hi    = stats["high_stress_count"]
    total = max(stats["active_employees"], 1)
    if hi > 0 and round(hi / total * 100, 1) > 30:
        recs.append({
            "type": "urgent", "icon": "🔥", "priority": "HIGH",
            "title": f"{round(hi/total*100,1)}% High Stress",
            "message": f"{hi} employees affected",
            "action": "Conduct 1:1 check-ins immediately",
        })

    if stats.get("dominant_mood") in {"Stressed", "Angry", "Sad", "Tired"}:
        recs.append({
            "type": "warning", "icon": "😰", "priority": "MEDIUM",
            "title": "Negative Mood Dominant",
            "message": f"Most common: {stats['dominant_mood']}",
            "action": "Address underlying issues and provide support",
        })

    return recs


# ══════════════════════════════════════════════════════════
#  VISUALIZATIONS
# ══════════════════════════════════════════════════════════

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Sora, sans-serif"),
    margin=dict(l=20, r=20, t=50, b=20),
)


def create_team_health_gauge_viz(data: dict, team_name: str = None):
    score = calculate_team_health_score(data, team_name)
    if score >= 80:   status, color = "Excellent 🌟", "#00e87a"
    elif score >= 60: status, color = "Good 😊",      "#00c4ff"
    elif score >= 40: status, color = "Fair 😐",       "#ffd93d"
    elif score >= 20: status, color = "Poor 😟",       "#ffa502"
    else:             status, color = "Critical 🚨",   "#ff4757"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": f"Team Health<br><span style='font-size:0.8em;color:{color}'>{status}</span>",
               "font": {"color": "#94a3b8"}},
        delta={"reference": 50, "valueformat": ".1f"},
        number={"suffix": "/100", "font": {"size": 24, "color": "#fff"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#475569"},
            "bar":  {"color": color},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0,  20], "color": "rgba(255,71,87,0.15)"},
                {"range": [20, 40], "color": "rgba(255,165,2,0.12)"},
                {"range": [40, 60], "color": "rgba(255,211,61,0.12)"},
                {"range": [60, 80], "color": "rgba(0,196,255,0.12)"},
                {"range": [80,100], "color": "rgba(0,232,122,0.12)"},
            ],
            "threshold": {"line": {"color": "#ff4757", "width": 3},
                          "thickness": 0.75, "value": 40},
        },
    ))
    fig.update_layout(height=280, **_LAYOUT)
    return fig


def create_stress_comparison_chart(data: dict):
    TEAMS, _ = _get_tracking()
    rows = []
    for tn in TEAMS:
        s = analyze_team_mood(data, tn)
        if s and s["active_employees"] > 0:
            rows.append({
                "Team":   tn.split(" ")[1],
                "Stress": s["average_stress"],
                "Color":  "#ff4757" if s["average_stress"] >= 7 else
                          "#ffa502" if s["average_stress"] >= 5 else "#00e87a",
            })
    if not rows:
        return None

    df = pd.DataFrame(rows)
    fig = go.Figure(data=[go.Bar(
        x=df["Team"], y=df["Stress"],
        marker=dict(color=df["Color"].tolist(),
                    line=dict(color="rgba(0,0,0,0.3)", width=1)),
        text=[f"{s}/10" for s in df["Stress"]],
        textposition="outside",
        textfont=dict(color="#fff", size=13),
    )])
    fig.add_hline(y=7, line_dash="dash", line_color="#ff4757",
                  annotation_text="🚨 High Risk", annotation_position="top right")
    fig.update_layout(
        title="📊 Team Stress Comparison",
        xaxis_title="Team", yaxis=dict(title="Avg Stress (0-10)", range=[0, 10.5]),
        height=350, **_LAYOUT,
    )
    return fig


def create_mood_heatmap(data: dict):
    TEAMS, get_mood_history = _get_tracking()
    rows = []
    for tn, ti in TEAMS.items():
        for member in ti["members"]:
            h = get_mood_history(member, data, 7)
            if h:
                rows.append({
                    "Employee": member,
                    "Team":     tn.split(" ")[1],
                    "Stress":   h[-1].get("stress_level", 0),
                })
    if not rows:
        return None

    df    = pd.DataFrame(rows)
    pivot = df.pivot_table(values="Stress", index="Employee",
                           columns="Team", aggfunc="first").fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
        colorscale="RdYlGn_r",
        text=pivot.values, texttemplate="%{text:.1f}",
        textfont={"size": 12, "color": "white"},
        colorbar=dict(title="Stress"), zmin=0, zmax=10,
    ))
    fig.update_layout(
        title="🔥 Employee Stress Heatmap",
        xaxis=dict(title="Team", side="top"), yaxis_title="Employee",
        height=480, **_LAYOUT,
    )
    return fig