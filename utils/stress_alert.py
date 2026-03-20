from datetime import datetime

# Session-level in-memory dedup store
_alert_history: list = []


# ══════════════════════════════════════════════════════════
#  MAIN — check_stress_alert
# ══════════════════════════════════════════════════════════

def check_stress_alert(employee: str, stress_level: float, data: dict) -> dict | None:
    """
    Check stress level and generate alert if threshold crossed.
    Returns alert dict or None if stress is low (< 4).

    NOTE: Email is NOT sent here — handled by app.py _save_alert()
          only on CRITICAL (stress>=8) or Angry emotion.
    """
    # ── Determine level ───────────────────────────────────
    if stress_level >= 8.0:
        level = "CRITICAL"
        emoji = "🚨"
        color = "#ff4757"
        message = (f"🚨 CRITICAL: {employee}'s stress is at {stress_level}/10! "
                   "Immediate manager intervention required.")
        actions = [
            "🆘 IMMEDIATE manager intervention required",
            "🧘 Offer emergency counseling session",
            "📉 Reduce workload NOW",
            "🏖️ Consider emergency time off",
            "📞 Schedule urgent 1-on-1 within the hour",
        ]

    elif stress_level >= 6.0:
        level = "WARNING"
        emoji = "⚠️"
        color = "#ffa502"
        message = (f"⚠️ WARNING: {employee}'s stress is at {stress_level}/10. "
                   "Please check in within 24 hours.")
        actions = [
            "📅 Check-in with employee within 24 hours",
            "📊 Review and balance workload",
            "⏰ Offer flexible working schedule",
            "📚 Share stress management resources",
            "💬 Keep communication open",
        ]

    elif stress_level >= 4.0:
        level = "MONITOR"
        emoji = "👀"
        color = "#ffd93d"
        message = (f"👀 MONITOR: {employee}'s stress is increasing "
                   f"({stress_level}/10) — keep an eye on it.")
        actions = [
            "📈 Monitor stress trends over next 3 days",
            "☕ Encourage regular breaks",
            "🗣️ Keep communication channels open",
            "🎯 Ensure realistic deadlines",
            "🌟 Recognise and appreciate their work",
        ]

    else:
        return None   # Stress is healthy — no alert

    # ── Build alert dict ──────────────────────────────────
    alert = {
        "employee":     employee,
        "level":        level,
        "level_emoji":  emoji,
        "color":        color,
        "stress_level": stress_level,
        "message":      message,
        "actions":      actions,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resolved":     False,
    }

    # ── Persist into employee record ──────────────────────
    emp_record = data.get("employees", {}).get(employee)
    if emp_record is not None:
        emp_record.setdefault("alerts", [])
        existing = emp_record["alerts"]
        # Only append if level changed from the last stored alert
        if not existing or existing[-1].get("level") != level:
            emp_record["alerts"].append(alert)

    # ── Session dedup ─────────────────────────────────────
    if (not _alert_history
            or _alert_history[-1].get("employee") != employee
            or _alert_history[-1].get("level")    != level):
        _alert_history.append(alert)

    # ── EMAIL REMOVED FROM HERE ───────────────────────────
    # Email is sent by app.py _save_alert() only when:
    #   stress >= 8 (CRITICAL)  OR  emotion == 'Angry'
    # This prevents duplicate emails.

    return alert


# ══════════════════════════════════════════════════════════
#  GET ALL ACTIVE ALERTS  (for HR dashboard)
# ══════════════════════════════════════════════════════════

def get_all_active_alerts(data: dict) -> list:
    """
    Return all unresolved alerts.
    Merges session history + persistent employee data.
    Sorted CRITICAL → WARNING → MONITOR.
    """
    seen: set = set()
    all_alerts: list = []

    def _add(alert: dict):
        uid = (f"{alert.get('employee')}_{alert.get('timestamp')}"
               f"_{alert.get('level')}")
        if uid not in seen and not alert.get("resolved", False):
            seen.add(uid)
            all_alerts.append(alert)

    for a in _alert_history:
        _add(a)

    for emp_data in data.get("employees", {}).values():
        for a in emp_data.get("alerts", []):
            _add(a)

    order = {"CRITICAL": 0, "WARNING": 1, "MONITOR": 2}
    all_alerts.sort(key=lambda x: order.get(x.get("level", ""), 99))
    return all_alerts


# ══════════════════════════════════════════════════════════
#  SUMMARY  (for KPI card)
# ══════════════════════════════════════════════════════════

def get_alert_summary(data: dict) -> dict:
    """Count breakdown — used in HR KPI cards."""
    alerts = get_all_active_alerts(data)
    return {
        "total":    len(alerts),
        "critical": sum(1 for a in alerts if a.get("level") == "CRITICAL"),
        "warning":  sum(1 for a in alerts if a.get("level") == "WARNING"),
        "monitor":  sum(1 for a in alerts if a.get("level") == "MONITOR"),
    }


# ══════════════════════════════════════════════════════════
#  RESOLVE
# ══════════════════════════════════════════════════════════

def resolve_alert(employee: str, data: dict) -> bool:
    """Mark all alerts for one employee as resolved (session + persistent)."""
    for a in _alert_history:
        if a.get("employee") == employee:
            a["resolved"]    = True
            a["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    if employee in data.get("employees", {}):
        for a in data["employees"][employee].get("alerts", []):
            a["resolved"]    = True
            a["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    return True


def resolve_all_alerts(employee: str, data: dict) -> int:
    """
    Resolve all active alerts for an employee.
    Returns count of alerts resolved.
    Called from app.py HR dashboard Resolve button.
    """
    count = 0
    for a in _alert_history:
        if a.get("employee") == employee and not a.get("resolved", False):
            a["resolved"]    = True
            a["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            count += 1

    if employee in data.get("employees", {}):
        for a in data["employees"][employee].get("alerts", []):
            if not a.get("resolved", False):
                a["resolved"]    = True
                a["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                count += 1

    return count


def clear_employee_alerts(employee: str, data: dict) -> bool:
    """Fully remove all alerts for an employee (hard reset)."""
    global _alert_history
    _alert_history = [a for a in _alert_history if a.get("employee") != employee]

    if employee in data.get("employees", {}):
        data["employees"][employee]["alerts"] = []

    return True