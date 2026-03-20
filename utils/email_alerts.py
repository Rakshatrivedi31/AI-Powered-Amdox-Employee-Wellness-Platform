import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
#  EMAIL CONFIGURATION
# ══════════════════════════════════════════════════════════

EMAIL_CONFIG = {
    'enabled':         True,                          
    'smtp_server':     'smtp.gmail.com',
    'smtp_port':       587,
    'sender_email':    'rakshatrivedi00@gmail.com',   
    'sender_password': 'lmmj rrse gmbq xxnr',         
    'hr_email':        'rakshatrivedi00@gmail.com',   
}


# ══════════════════════════════════════════════════════════
#  MAIN FUNCTION — signature matches ALL callers
# ══════════════════════════════════════════════════════════

def send_stress_alert_email(
    employee: str,
    email:    str,
    stress:   float,
    emotion:  str,
    level:    str,
    workload: int,
) -> bool:
    """
    Send stress alert email to HR.

    Args:
        employee  (str):   Employee name
        email     (str):   Employee email (shown in report)
        stress    (float): Stress score 0–10
        emotion   (str):   Detected emotion
        level     (str):   "CRITICAL" or "WARNING"
        workload  (int):   Current workload 1–10

    Returns:
        bool: True if sent, False otherwise
    """

    # ── Guard: disabled ───────────────────────────────────
    if not EMAIL_CONFIG.get('enabled'):
        logger.info(f"📧 Email skipped (disabled) — {employee} [{level}]")
        print(f"📧 [Email disabled] Would send {level} alert for "
              f"{employee} (stress={stress}/10)")
        return False

    # ── Guard: no password ────────────────────────────────
    if not EMAIL_CONFIG.get('sender_password', '').strip():
        logger.warning("⚠️ sender_password not set in EMAIL_CONFIG")
        print("⚠️ Email not sent — set sender_password in email_alerts.py")
        return False

    try:
        # Level-specific styling
        if level == "CRITICAL":
            color         = "#dc3545"
            bg_color      = "#f8d7da"
            badge_text    = "🔴 CRITICAL — IMMEDIATE ACTION REQUIRED"
            priority_label= "URGENT"
        else:
            color         = "#ff9800"
            bg_color      = "#fff3cd"
            badge_text    = "⚠️ WARNING — Action Within 24 Hours"
            priority_label= "HIGH"

        filled     = int(round(stress))
        stress_bar = "█" * filled + "░" * (10 - filled)
        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str   = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<style>
  body{{margin:0;padding:0;font-family:Arial,sans-serif;background:#f0f2f5}}
  .wrap{{max-width:620px;margin:30px auto;background:#fff;border-radius:12px;
         overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.12)}}
  .hdr{{background:{color};padding:30px 24px;text-align:center;color:#fff}}
  .hdr h1{{margin:0 0 6px;font-size:26px}}
  .hdr p{{margin:0;font-size:14px;opacity:.9}}
  .badge{{display:inline-block;background:rgba(255,255,255,.25);padding:6px 18px;
          border-radius:20px;margin-top:12px;font-weight:700;font-size:13px}}
  .body{{padding:28px 24px}}
  .info{{background:{bg_color};border-left:5px solid {color};
         padding:16px 18px;border-radius:6px;margin-bottom:20px}}
  .info p{{margin:5px 0;font-size:14px;color:#333}}
  .metrics{{display:flex;gap:12px;margin-bottom:20px}}
  .metric{{flex:1;text-align:center;padding:18px 10px;border-radius:8px;
           background:#f8f9fa;border:1px solid #e0e0e0}}
  .val{{font-size:30px;font-weight:700;color:{color}}}
  .lbl{{font-size:11px;color:#888;text-transform:uppercase;margin-top:4px}}
  .sbar{{font-family:monospace;font-size:18px;color:{color};letter-spacing:2px}}
  .acts{{background:#f8f9fa;border-radius:8px;padding:18px 20px;margin-bottom:20px}}
  .acts h3{{margin:0 0 12px;font-size:15px;color:{color}}}
  .acts li{{font-size:14px;color:#444;margin-bottom:6px}}
  .footer{{background:#f8f9fa;padding:16px 24px;text-align:center;
           font-size:12px;color:#888;border-top:1px solid #e0e0e0}}
</style></head>
<body><div class="wrap">
  <div class="hdr">
    <h1>🚨 Employee Stress Alert</h1>
    <p>Amdox AI-Powered Wellness Monitoring System</p>
    <div class="badge">{badge_text}</div>
  </div>
  <div class="body">
    <div class="info">
      <p><strong>👤 Employee:</strong> {employee}</p>
      <p><strong>📧 Email:</strong> {email or '—'}</p>
      <p><strong>😊 Emotion:</strong> {emotion}</p>
      <p><strong>🏷️ Priority:</strong> {priority_label}</p>
      <p><strong>🕐 Detected At:</strong> {now_str}</p>
    </div>
    <div class="metrics">
      <div class="metric">
        <div class="val">{stress}/10</div>
        <div class="sbar">{stress_bar}</div>
        <div class="lbl">Stress Level</div>
      </div>
      <div class="metric">
        <div class="val">{workload}/10</div>
        <div class="lbl">Workload</div>
      </div>
    </div>
    <div class="acts">
      <h3>✅ Recommended HR Actions</h3>
      <ul>
        <li>📞 Contact <strong>{employee}</strong> for immediate check-in</li>
        <li>📅 Schedule urgent 1-on-1 today</li>
        <li>📉 Review and reduce current workload</li>
        <li>🧘 Offer EAP / counseling access</li>
        {"<li>🏖️ Consider authorising emergency time off</li>" if level == "CRITICAL" else ""}
        <li>📚 Share stress management resources</li>
      </ul>
    </div>
    <p style="font-size:13px;color:#666;border-top:1px solid #eee;padding-top:14px">
      Auto-generated when <strong>{employee}</strong>'s stress crossed
      <strong>{level}</strong> threshold ({stress}/10).
      Check the HR dashboard for full trend data.
    </p>
  </div>
  <div class="footer">
    <strong>🏢 Amdox Wellness Platform</strong><br>Report: {date_str}
  </div>
</div></body></html>"""

        msg = MIMEMultipart('alternative')
        msg['From']       = f"Amdox Wellness <{EMAIL_CONFIG['sender_email']}>"
        msg['To']         = EMAIL_CONFIG['hr_email']
        msg['Subject']    = f"🚨 [{level}] Stress Alert — {employee} ({stress}/10)"
        msg['X-Priority'] = '1' if level == "CRITICAL" else '2'
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'],
                          EMAIL_CONFIG['smtp_port'], timeout=10) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'],
                         EMAIL_CONFIG['sender_password'].replace(' ', ''))
            server.send_message(msg)

        logger.info(f"📧 ✅ Sent to HR for {employee} [{level}]")
        print(f"📧 ✅ Email sent → HR | {employee} | {level} | stress={stress}/10")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail auth failed — use App Password, not regular password.")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def test_email_config() -> bool:
    """Test Gmail login without sending."""
    if not EMAIL_CONFIG.get('enabled'):
        print("ℹ️ Email disabled."); return False
    try:
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'],
                          EMAIL_CONFIG['smtp_port'], timeout=8) as s:
            s.starttls()
            s.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'].replace(' ', ''))
        print("✅ Gmail login OK — ready to send!"); return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Auth failed — check App Password."); return False
    except Exception as e:
        print(f"❌ Connection error: {e}"); return False


if __name__ == "__main__":
    send_stress_alert_email("Raksha", "r@co.com", 8.5, "Stressed", "CRITICAL", 9)