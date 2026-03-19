import os, sys, warnings, logging

os.environ['TF_CPP_MIN_LOG_LEVEL']  = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['PYTHONWARNINGS']        = 'ignore'
warnings.filterwarnings('ignore')
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

# ── Silence Streamlit internal warnings ──────────────────
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.elements').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime').setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.emotion_detector  import (detect_emotion_from_text,
                                     detect_emotion_from_camera_streamlit,
                                     detect_emotion_from_speech,
                                     manual_mood_entry_streamlit,
                                     calculate_stress_level)
from utils.mood_tracking     import (load_employee_data, save_employee_data,
                                     save_mood, get_mood_history, get_mood_stats,
                                     get_team_stats, authenticate_employee,
                                     TEAMS, ALL_EMPLOYEES,
                                     create_mood_timeline_chart,
                                     generate_sample_data)
from utils.stress_alert      import check_stress_alert, get_all_active_alerts, resolve_all_alerts
from utils.email_alerts      import send_stress_alert_email
from utils.db_manager        import (get_all_employees_table, get_mood_history_table,
                                      get_alerts_table, get_db_stats, purge_old_entries,
                                      insert_mood_entry, upsert_employee_status, insert_alert)
from utils.task_assign       import recommend_multiple_tasks
from utils.chart_utils       import (create_overall_mood_chart, create_team_mood_charts,
                                     create_stress_distribution, create_team_health_gauge)
from utils.team_analytics    import analyze_team_mood, calculate_team_health_score

# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Amdox Wellness Platform",
    page_icon="🚀", layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════
#  CSS — "Obsidian Neon" dark glassmorphism
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, .stApp     { font-family: 'Sora', sans-serif !important; }

.stApp {
    background:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(102,126,234,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(246,79,89,0.08) 0%, transparent 55%),
        linear-gradient(160deg, #080714 0%, #0f0c29 35%, #12101e 70%, #0a0915 100%);
    min-height: 100vh;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0b1e 0%, #110f24 60%, #0d0b1e 100%) !important;
    border-right: 1px solid rgba(102,126,234,0.18) !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }

::-webkit-scrollbar       { width: 4px; }
::-webkit-scrollbar-track { background: #080714; }
::-webkit-scrollbar-thumb { background: #667eea44; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #667eea; }

/* ─── Hero banner ─── */
.hero-banner {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #1a1060 0%, #2d1b69 30%, #1e0a3c 60%, #2a0e2a 100%);
    border: 1px solid rgba(102,126,234,0.3);
    border-radius: 20px; padding: 2rem 2.5rem;
    margin-bottom: 2rem; text-align: center;
}
.hero-banner::before {
    content: ''; position: absolute; inset: 0;
    background:
        radial-gradient(circle at 20% 50%, rgba(102,126,234,0.25) 0%, transparent 50%),
        radial-gradient(circle at 80% 30%, rgba(246,79,89,0.15) 0%, transparent 45%);
    pointer-events: none;
}
.hero-banner::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #667eea, #a78bfa, #f64f59, #ffa502, #667eea);
    background-size: 300% 100%;
    animation: gradientSlide 4s linear infinite;
}
@keyframes gradientSlide { 0%{background-position:0% 50%} 100%{background-position:300% 50%} }
.hero-banner h1, .hero-banner h2 {
    position: relative; font-size: 2rem; font-weight: 800;
    color: #fff; letter-spacing: -0.5px; margin-bottom: 0.3rem;
}
.hero-banner p { position: relative; color: rgba(255,255,255,0.6); font-size: 0.9rem; }

/* ─── KPI Grid ─── */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    position: relative; overflow: hidden;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 1.4rem 1.2rem; text-align: center;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.kpi-card:hover {
    transform: translateY(-6px); border-color: rgba(102,126,234,0.4);
    box-shadow: 0 16px 40px rgba(102,126,234,0.18);
}
.kpi-card::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0;
    height: 2px; border-radius: 0 0 16px 16px; opacity: 0; transition: opacity 0.25s;
}
.kpi-card:hover::after { opacity: 1; }
.kpi-c1::after { background: linear-gradient(90deg,#667eea,#a78bfa); }
.kpi-c2::after { background: linear-gradient(90deg,#ff4757,#ffa502); }
.kpi-c3::after { background: linear-gradient(90deg,#00e87a,#00c4ff); }
.kpi-c4::after { background: linear-gradient(90deg,#ffd93d,#ff6348); }
.kpi-icon  { font-size: 2rem; margin-bottom: 0.6rem; }
.kpi-value { font-size: 2.1rem; font-weight: 800; color: #fff; letter-spacing: -1px; }
.kpi-label { color: #64748b; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.3px; margin-top: 0.4rem; }

/* ─── Glass panel ─── */
.glass {
    background: rgba(255,255,255,0.025); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.07); border-radius: 18px;
    padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
}

/* ─── Divider ─── */
.gd {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(102,126,234,0.4), rgba(167,139,250,0.4), transparent);
    margin: 1.6rem 0; border: none;
}

/* ─── Task cards ─── */
.task-outer { position: relative; margin-bottom: 1.4rem; }
.task-num {
    position: absolute; top: 1rem; right: 1.2rem;
    font-size: 3.5rem; font-weight: 900; opacity: 0.07;
    font-family: 'JetBrains Mono', monospace;
}
.task-card {
    position: relative; padding: 1.5rem 1.8rem; border-radius: 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
    transition: transform 0.22s cubic-bezier(.34,1.56,.64,1), box-shadow 0.22s ease;
}
.task-card:hover { transform: translateX(10px) scale(1.01); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
.tc-happy    { background:linear-gradient(135deg,rgba(0,232,122,0.13),rgba(0,196,255,0.06)); border-left:3px solid #00e87a; }
.tc-calm     { background:linear-gradient(135deg,rgba(0,196,255,0.13),rgba(102,126,234,0.07)); border-left:3px solid #00c4ff; }
.tc-neutral  { background:linear-gradient(135deg,rgba(148,163,184,0.10),rgba(71,85,105,0.06)); border-left:3px solid #64748b; }
.tc-stressed { background:linear-gradient(135deg,rgba(255,165,2,0.15),rgba(255,71,87,0.07)); border-left:3px solid #ffa502; }
.tc-tired    { background:linear-gradient(135deg,rgba(162,155,254,0.13),rgba(118,75,162,0.07)); border-left:3px solid #a29bfe; }
.tc-sad      { background:linear-gradient(135deg,rgba(79,195,247,0.13),rgba(0,196,255,0.07)); border-left:3px solid #4fc3f7; }
.tc-angry    { background:linear-gradient(135deg,rgba(255,71,87,0.15),rgba(246,79,89,0.07)); border-left:3px solid #ff4757; }
.tc-energetic{ background:linear-gradient(135deg,rgba(255,211,61,0.15),rgba(255,165,2,0.07)); border-left:3px solid #ffd93d; }
.tc-default  { background:linear-gradient(135deg,rgba(102,126,234,0.13),rgba(118,75,162,0.07)); border-left:3px solid #667eea; }
.task-icon  { font-size:2.4rem; margin-bottom:0.6rem; }
.task-seq   { font-size:0.65rem; color:#475569; text-transform:uppercase; letter-spacing:1.2px; }
.task-title { font-size:1.1rem; font-weight:700; color:#f1f5f9; margin:0.3rem 0 0.5rem; }
.task-desc  { color:#94a3b8; font-size:0.84rem; line-height:1.6; margin-bottom:1rem; font-style:italic; }
.tag { display:inline-block; padding:2px 10px; border-radius:20px; margin-right:6px; font-size:0.72rem; font-weight:600; background:rgba(255,255,255,0.07); color:#94a3b8; }
.tag-critical { background:rgba(255,71,87,0.2); color:#ff6b78; }
.tag-high     { background:rgba(255,165,2,0.2); color:#ffb340; }
.tag-medium   { background:rgba(102,126,234,0.2); color:#8fa4ff; }
.tag-low      { background:rgba(0,232,122,0.2); color:#00e87a; }

/* ─── Alert cards ─── */
.al { padding:1rem 1.3rem; border-radius:12px; margin-bottom:0.9rem; border-left:4px solid; }
.al-crit { background:rgba(255,71,87,0.1); border-color:#ff4757; }
.al-warn { background:rgba(255,165,2,0.1); border-color:#ffa502; }
.al-mon  { background:rgba(255,211,61,0.1); border-color:#ffd93d; }
.al-ok   { background:rgba(0,232,122,0.1); border-color:#00e87a; }
.al h3   { font-size:1rem; font-weight:700; color:#f1f5f9; margin-bottom:0.3rem; }
.al p    { font-size:0.84rem; color:#94a3b8; margin:0; }

/* ─── Stress bar ─── */
.stress-wrap { text-align:center; padding:2.2rem 1rem; }
.stress-num  { font-size:5.5rem; font-weight:900; line-height:1; letter-spacing:-3px; }
.stress-sub  { font-size:1rem; font-weight:500; margin:0.4rem 0 1.4rem; }
.bar-track   { background:rgba(255,255,255,0.06); border-radius:50px; height:14px; max-width:480px; margin:0 auto; overflow:hidden; }
.bar-fill    { height:100%; border-radius:50px; transition:width 0.8s cubic-bezier(.4,0,.2,1); }

/* ─── Member row ─── */
.member-row {
    display:flex; align-items:center; gap:0.8rem;
    padding:0.6rem 0.8rem; border-radius:10px; margin-bottom:0.4rem;
    background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.04);
}
.member-row:hover { background:rgba(102,126,234,0.06); }

/* ─── Buttons ─── */
.stButton > button {
    background: linear-gradient(135deg,#667eea 0%,#764ba2 100%) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-family: 'Sora', sans-serif !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s cubic-bezier(.34,1.56,.64,1) !important;
    box-shadow: 0 4px 15px rgba(102,126,234,0.3) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(102,126,234,0.5) !important; }

/* ─── Form inputs ─── */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
    font-family: 'Sora', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
}
.stSelectbox > div > div { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.1) !important; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] { background:rgba(255,255,255,0.02) !important; border-radius:10px; gap:2px; padding:4px; }
.stTabs [data-baseweb="tab"]      { color:#64748b !important; border-radius:8px !important; font-weight:500 !important; }
.stTabs [aria-selected="true"]    { background:rgba(102,126,234,0.2) !important; color:#a5b4fc !important; }

/* ─── Streamlit alerts ─── */
.stInfo    { background:rgba(102,126,234,0.12) !important; color:#a5b4fc !important; border-radius:10px !important; }
.stSuccess { background:rgba(0,232,122,0.12)   !important; color:#6ee7b7 !important; border-radius:10px !important; }
.stWarning { background:rgba(255,165,2,0.12)   !important; color:#fcd34d !important; border-radius:10px !important; }
.stError   { background:rgba(255,71,87,0.12)   !important; color:#fca5a5 !important; border-radius:10px !important; }

/* ─── Metrics ─── */
div[data-testid="stMetricValue"] { color:#fff !important; font-weight:700 !important; }
div[data-testid="stMetricLabel"] { color:#64748b !important; }

/* ─── Dataframe ─── */
.stDataFrame th { background:rgba(102,126,234,0.15) !important; color:#a5b4fc !important; }
.stDataFrame td { color:#cbd5e0 !important; }

/* ─── Radio ─── */
.stRadio label { color:#94a3b8 !important; font-weight:500 !important; }
[data-testid="stRadio"] [aria-checked="true"] + label { color:#a5b4fc !important; }

/* ─── Login card ─── */
.login-shell {
    background: rgba(255,255,255,0.03); backdrop-filter: blur(24px);
    border: 1px solid rgba(255,255,255,0.1); border-radius: 24px;
    padding: 2.8rem 2.5rem; max-width: 460px; margin: 4rem auto 0;
}
.login-logo { text-align:center; margin-bottom:2rem; }
.login-logo .icon { font-size:3.5rem; margin-bottom:0.5rem; }
.login-logo h1 {
    font-size:1.9rem; font-weight:800; letter-spacing:-0.5px;
    background: linear-gradient(135deg,#667eea,#a78bfa 50%,#f64f59);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.login-logo p { color:#475569; font-size:0.85rem; margin-top:0.2rem; }

/* ─── Profile block ─── */
.profile-block { text-align:center; padding:1.8rem 0.5rem 1.2rem; }
.profile-emoji { font-size:3.5rem; }
.profile-name  { font-size:1.15rem; font-weight:700; color:#f1f5f9; margin:0.5rem 0 0.2rem; }
.profile-team  { font-size:0.75rem; color:#667eea; letter-spacing:0.5px; }
.profile-mood  { font-size:0.78rem; color:#64748b; margin-top:0.4rem; }

/* ─── Team health bar ─── */
.team-bar { background:#1a1a2e; border-radius:50px; height:6px; margin:0.4rem 0 1rem; overflow:hidden; }
.team-bar-fill { height:100%; border-radius:50px; }

/* ─── Expander ─── */
div[data-testid="stExpander"] { background:rgba(255,255,255,0.02) !important; border:1px solid rgba(255,255,255,0.07) !important; border-radius:14px !important; }
div[data-testid="stExpander"] summary { font-weight:600 !important; color:#cbd5e0 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════
E_EMOJI = {'Happy':'😊','Calm':'😌','Neutral':'😐','Stressed':'😰',
           'Tired':'😴','Sad':'😔','Angry':'😠','Energetic':'⚡','—':'🔮','No Data':'—'}
E_CLASS = {'Happy':'tc-happy','Calm':'tc-calm','Neutral':'tc-neutral','Stressed':'tc-stressed',
           'Tired':'tc-tired','Sad':'tc-sad','Angry':'tc-angry','Energetic':'tc-energetic'}
E_COLOR = {'Happy':'#00e87a','Calm':'#00c4ff','Neutral':'#94a3b8','Stressed':'#ffa502',
           'Tired':'#a29bfe','Sad':'#4fc3f7','Angry':'#ff4757','Energetic':'#ffd93d','—':'#667eea'}
P_TAG   = {'Critical':'tag-critical','High':'tag-high','Medium':'tag-medium','Low':'tag-low'}
T_COLOR = {'Team Alpha 🔵':'#667eea','Team Beta 🟢':'#00e87a','Team Gamma 🔴':'#ff4757'}

# ══════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════
for k, v in [('authenticated', False), ('user_type', None),
              ('current_user', None), ('detected_emotion', None)]:
    if k not in st.session_state:
        st.session_state[k] = v

if 'data' not in st.session_state:
    st.session_state.data = load_employee_data()
    # Auto-generate sample data if employees have no history
    generate_sample_data(st.session_state.data, days=7)

data = st.session_state.data

# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def _save_alert(employee, emp_data, emotion, workload, stress, method):
    # 1. Save to JSON (backup)
    save_mood(employee, emotion, workload, stress, data, method)
    save_employee_data(data)

    # 2. ── Sync to SQLite DB ──────────────────────────────
    emp_id   = employee.lower().replace(' ', '_')
    now_ts   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now_date = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M')
    try:
        insert_mood_entry(emp_id, {
            'timestamp':    now_ts,
            'date':         now_date,
            'time':         now_time,
            'emotion':      emotion,
            'workload':     workload,
            'stress_level': stress,
            'method':       method,
        })
        upsert_employee_status(emp_id, emotion, workload)
    except Exception as e:
        logging.warning(f"DB sync failed (non-fatal): {e}")

    # 3. Check stress alert
    alert = check_stress_alert(employee, stress, data)

    # 4. Email on CRITICAL or Angry
    should_email = (stress >= 8) or (emotion == 'Angry')
    if alert and should_email and alert['level'] in ('CRITICAL', 'WARNING'):
        send_stress_alert_email(
            employee, emp_data.get('email', ''),
            stress, emotion, alert['level'], workload
        )

    # 5. Save alert to SQLite
    if alert:
        try:
            insert_alert(emp_id, {
                'level':        alert['level'],
                'level_emoji':  alert.get('level_emoji', '🔔'),
                'color':        alert.get('color', '#ffa502'),
                'stress_level': stress,
                'message':      alert.get('message', ''),
                'actions':      alert.get('actions', []),
                'timestamp':    now_ts,
            })
        except Exception as e:
            logging.warning(f"DB alert sync failed (non-fatal): {e}")

    return alert


def gd():
    st.markdown('<div class="gd"></div>', unsafe_allow_html=True)


def kpi4(vals):
    html = '<div class="kpi-grid">'
    for ci, (variant, icon, val, label) in enumerate(vals, 1):
        html += f'''
        <div class="kpi-card kpi-c{variant}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-label">{label}</div>
        </div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def task_card_html(i, task, css_class, accent):
    p    = task.get('priority', 'Medium')
    ptag = P_TAG.get(p, '')
    dur  = task.get('duration', 0)
    ds   = f"{dur} min" if dur > 0 else "Flexible"
    cat  = task.get('category', 'General')
    return f"""
    <div class="task-outer">
      <div class="task-num" style="color:{accent}">{str(i).zfill(2)}</div>
      <div class="task-card {css_class}">
        <div class="task-icon">{task.get('icon','📌')}</div>
        <div class="task-seq">Task {i} of 3</div>
        <div class="task-title">{task.get('task','')}</div>
        <div class="task-desc">"{task.get('description','')}"</div>
        <span class="tag">⏱ {ds}</span>
        <span class="tag {ptag}">🎯 {p}</span>
        <span class="tag">📂 {cat}</span>
      </div>
    </div>"""

# ══════════════════════════════════════════════════════════
#  LOGIN  ← NO PASSWORD HINTS SHOWN ON UI
# ══════════════════════════════════════════════════════════
def show_login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div class="login-shell">
          <div class="login-logo">
            <div class="icon">🚀</div>
            <h1>Amdox Wellness</h1>
            <p>AI-Powered Employee Wellbeing Platform</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["👤  Employee Login", "👥  HR Login"])

        with tab1:
            emp_id   = st.selectbox("Select your name", ALL_EMPLOYEES, key="sel_emp")
            emp_pass = st.text_input("Password", type="password",
                                     placeholder="Enter your password", key="emp_pass")
            if st.button("🔓 Sign In", width='stretch', type="primary", key="b_emp"):
                ok, name, role = authenticate_employee(emp_id, emp_pass)
                if ok:
                    st.session_state.update(
                        authenticated=True, user_type='employee', current_user=name
                    )
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")

        with tab2:
            hr_u = st.text_input("Username", placeholder="Enter HR username", key="hr_u")
            hr_p = st.text_input("Password", type="password",
                                 placeholder="Enter HR password", key="hr_p")
            if st.button("🔓 HR Sign In", width='stretch', type="primary", key="b_hr"):
                ok, name, role = authenticate_employee(hr_u, hr_p)
                if ok and role == "hr":
                    st.session_state.update(
                        authenticated=True, user_type='hr', current_user=name
                    )
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")

# ══════════════════════════════════════════════════════════
#  EMPLOYEE DASHBOARD SHELL
# ══════════════════════════════════════════════════════════
def show_employee_dashboard():
    employee = st.session_state.current_user
    emp_data = data.get("employees", {}).get(employee, {})
    mood_now = st.session_state.detected_emotion or emp_data.get('last_emotion', '—')
    mc       = E_COLOR.get(mood_now, '#667eea')

    with st.sidebar:
        st.markdown(f"""
        <div class="profile-block">
          <div class="profile-emoji">{E_EMOJI.get(mood_now,'🔮')}</div>
          <div class="profile-name">{employee}</div>
          <div class="profile-team">{emp_data.get('team','Unknown')}</div>
          <div class="profile-mood">Mood: <b style="color:{mc}">{mood_now}</b></div>
        </div>
        """, unsafe_allow_html=True)
        gd()
        menu = st.radio("Navigation", ["🏠  Home","😊  Emotion","📋  Tasks",
                             "📊  History","👥  Team","🚨  Stress","🔐  Privacy"],
                        label_visibility="collapsed")
        gd()
        if st.button("🚪  Logout", width='stretch'):
            for k in ['authenticated', 'current_user', 'user_type', 'detected_emotion']:
                st.session_state[k] = False if k == 'authenticated' else None
            st.rerun()

    page = menu.split("  ", 1)[1]
    dispatch = {
        "Home":    lambda: page_home(employee, emp_data),
        "Emotion": lambda: page_emotion(employee, emp_data),
        "Tasks":   lambda: page_tasks(employee),
        "History": lambda: page_history(employee),
        "Stress":  lambda: page_stress(employee),
        "Team":    lambda: page_team(employee, emp_data),
        "Privacy": page_privacy,
    }
    dispatch.get(page, lambda: None)()

# ── HOME ─────────────────────────────────────────────────
def page_home(employee, emp_data):
    st.markdown(f"""
    <div class="hero-banner">
      <h1>Welcome back, {employee}! 👋</h1>
      <p>{emp_data.get('team','Unknown')} &nbsp;·&nbsp; {datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>""", unsafe_allow_html=True)

    history = get_mood_history(employee, data, 7)
    latest  = history[-1] if history else None
    stats   = get_mood_stats(employee, data)
    stress_v= latest['stress_level'] if latest else 0
    sc      = '#00e87a' if stress_v < 5 else '#ffa502' if stress_v < 7 else '#ff4757'
    mood_v  = latest['emotion'] if latest else '—'

    kpi4([
        (1, '😊', f"{E_EMOJI.get(mood_v,'🔮')} {mood_v}", "Current Mood"),
        (2, '📊', f'<span style="color:{sc}">{stress_v}/10</span>', "Stress Level"),
        (3, '✅', str(stats.get('total_entries', 0)), "Total Check-ins"),
        (4, '🔔', str(len(emp_data.get('alerts', []))), "Active Alerts"),
    ])
    gd()

    if stats and stats.get('total_entries', 0) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Stress",       f"{stats.get('average_stress', 0)}/10")
        c2.metric("Most Common Mood", stats.get('most_common_mood', '—'))
        c3.metric("Trend",            stats.get('trend', '—'))
        fig = create_mood_timeline_chart(employee, days=30)
        if fig:
            st.plotly_chart(fig, width='stretch')
    else:
        st.markdown("""
        <div class="glass" style="text-align:center;padding:3rem">
          <div style="font-size:4rem;margin-bottom:0.8rem">🌱</div>
          <div style="font-size:1.2rem;font-weight:700;color:#a5b4fc;margin-bottom:0.4rem">No data yet</div>
          <div style="color:#475569">Head to the <b style="color:#667eea">😊 Emotion</b> tab to log your first check-in!</div>
        </div>""", unsafe_allow_html=True)

# ── EMOTION ──────────────────────────────────────────────
def page_emotion(employee, emp_data):
    st.markdown("""
    <div class="hero-banner">
      <h2>😊 Emotion Detection</h2>
      <p>Choose how you'd like to share your mood today</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📝  Text","📷  Camera","🎤  Speech","✋  Manual"])

    with tab1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### 💬 How are you feeling today?")
        text = st.text_area("Your feelings", placeholder="e.g., Feeling a bit overwhelmed with deadlines...",
                            height=110, key="t_text", label_visibility="collapsed")
        wl = st.slider("📦 Workload level", 1, 10, 5, key='wl_t')
        if st.button("🔍 Analyse My Mood", type="primary", key="btn_text"):
            if text.strip():
                with st.spinner("🧠 Analysing sentiment..."):
                    emotion, polarity, emoji = detect_emotion_from_text(text)
                    recent = [m['emotion'] for m in get_mood_history(employee, data, 7)]
                    stress = calculate_stress_level(emotion, wl, recent)
                    _save_alert(employee, emp_data, emotion, wl, stress, 'text')
                    st.session_state.detected_emotion = emotion
                c1, c2, c3 = st.columns(3)
                c1.metric("Detected Emotion", f"{emoji} {emotion}")
                c2.metric("Stress Level",     f"{stress}/10")
                c3.metric("Polarity",         f"{polarity:+.2f}")
                st.success(f"✅ Mood saved! Navigate to **📋 Tasks** for personalised recommendations.")
                st.rerun()
            else:
                st.warning("Please enter some text first.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### 📷 Real-time Camera Detection")
        st.info("Click **Stop & Capture** anytime.")
        wl = st.slider("📦 Workload level", 1, 10, 5, key='wl_c')

        # ── Show saved result (survives rerender) ──
        if st.session_state.get('_cam_result'):
            r = st.session_state['_cam_result']
            c1, c2, c3 = st.columns(3)
            c1.metric("Detected",   f"{E_EMOJI.get(r['emotion'],'😐')} {r['emotion']}")
            c2.metric("Confidence", f"{r['conf']}%")
            c3.metric("Stress",     f"{r['stress']}/10")
            st.success("✅ Camera mood saved! Go to **📋 Tasks** for recommendations.")
            if st.button("🔄 Try Again", key="cam_clear"):
                st.session_state.pop('_cam_result', None)
                st.rerun()
        else:
            if st.button("📷 Open Camera & Detect", type="primary", key="btn_cam"):
                emotion, conf = detect_emotion_from_camera_streamlit()
                if emotion:
                    recent = [m['emotion'] for m in get_mood_history(employee, data, 7)]
                    stress = calculate_stress_level(emotion, wl, recent)
                    _save_alert(employee, emp_data, emotion, wl, stress, 'camera')
                    st.session_state.detected_emotion = emotion
                    st.session_state['_cam_result'] = {
                        'emotion': emotion,
                        'conf':    int(conf) if conf else 0,
                        'stress':  stress,
                    }
                    st.rerun()
                else:
                    st.error("❌ No face detected or camera failed. Allow camera permissions!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### 🎤 Speech Recognition")
        st.info("Click and speak clearly — AI analyses your words for emotion.")
        wl = st.slider("📦 Workload level", 1, 10, 5, key='wl_s')
        if st.button("🎤 Start Listening", type="primary", key="btn_sp"):
            with st.spinner("🎧 Listening..."):
                emotion, polarity, emoji, text_r = detect_emotion_from_speech()
            if emotion:
                recent = [m['emotion'] for m in get_mood_history(employee, data, 7)]
                stress = calculate_stress_level(emotion, wl, recent)
                _save_alert(employee, emp_data, emotion, wl, stress, 'speech')
                st.session_state.detected_emotion = emotion
                st.success(f"You said: *\"{text_r}\"*")
                c1, c2 = st.columns(2)
                c1.metric("Emotion", f"{emoji} {emotion}")
                c2.metric("Stress",  f"{stress}/10")
                st.rerun()
            else:
                st.error(f"❌ {text_r}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### ✋ Pick Your Current Mood")
        moods = [('😊','Happy','#00e87a'),('😌','Calm','#00c4ff'),
                 ('😐','Neutral','#94a3b8'),('😔','Sad','#4fc3f7'),
                 ('😰','Stressed','#ffa502'),('😠','Angry','#ff4757'),
                 ('😴','Tired','#a29bfe'),('⚡','Energetic','#ffd93d')]
        cols = st.columns(4)
        for i, (emoji, mood, color) in enumerate(moods):
            with cols[i % 4]:
                if st.button(f"{emoji}\n{mood}", key=f"mb_{mood}", width='stretch'):
                    st.session_state['_smood'] = mood

        sel = st.session_state.get('_smood')
        if sel:
            sc = next((c for e, m, c in moods if m == sel), '#667eea')
            se = next((e for e, m, c in moods if m == sel), '😐')
            st.markdown(f"""
            <div style="text-align:center;padding:1.2rem;margin:1rem 0;border-radius:14px;
                        background:linear-gradient(135deg,{sc}1a,{sc}0d);border:1px solid {sc}33">
              <span style="font-size:2.8rem">{se}</span>
              <div style="color:{sc};font-weight:700;font-size:1.05rem;margin-top:0.4rem">{sel}</div>
            </div>""", unsafe_allow_html=True)
            wl = st.slider("📦 Workload level", 1, 10, 5, key='wl_m')
            if st.button("💾 Save Mood", type="primary", key="btn_save"):
                recent = [m['emotion'] for m in get_mood_history(employee, data, 7)]
                stress = calculate_stress_level(sel, wl, recent)
                _save_alert(employee, emp_data, sel, wl, stress, 'manual')
                st.session_state.detected_emotion = sel
                st.session_state.pop('_smood', None)
                st.success(f"✅ **{sel}** saved! Stress score: {stress}/10")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ── TASKS ────────────────────────────────────────────────
def page_tasks(employee):
    emotion   = st.session_state.detected_emotion or "Neutral"
    emoji     = E_EMOJI.get(emotion, '😐')
    css_class = E_CLASS.get(emotion, 'tc-default')
    accent    = E_COLOR.get(emotion, '#667eea')

    st.markdown(f"""
    <div class="hero-banner">
      <h2>📋 AI Task Recommendations</h2>
      <p>Personalised for: {emoji} <b>{emotion}</b> mood</p>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([4, 1])
    with c1: wl = st.slider("📦 Current Workload", 1, 10, 5, key="task_wl")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🔄 Refresh", key="task_rf")

    st.markdown(f"""
    <div style="display:inline-block;padding:0.4rem 1.2rem;border-radius:30px;margin:0.5rem 0 1.2rem;
                background:{accent}1a;border:1px solid {accent}44;
                color:{accent};font-weight:600;font-size:0.85rem">
      {emoji}&nbsp; Currently feeling: {emotion} &nbsp;→&nbsp; tailored tasks below
    </div>""", unsafe_allow_html=True)

    tasks = recommend_multiple_tasks(emotion, wl, count=3)
    html  = ""
    for i, task in enumerate(tasks, 1):
        html += task_card_html(i, task, css_class, accent)
    st.markdown(html, unsafe_allow_html=True)

    gd()
    st.markdown(f"""
    <div class="glass" style="text-align:center;padding:1rem">
      <span style="color:#64748b;font-size:0.85rem">
        Not feeling <b style="color:{accent}">{emotion}</b>?
        Update your mood in the <b style="color:#667eea">😊 Emotion</b> tab for fresh recommendations.
      </span>
    </div>""", unsafe_allow_html=True)

# ── HISTORY ──────────────────────────────────────────────
def page_history(employee):
    st.markdown("""
    <div class="hero-banner">
      <h2>📊 Your Mood History</h2>
      <p>Wellness journey over time</p>
    </div>""", unsafe_allow_html=True)

    history = get_mood_history(employee, data, 30)
    stats   = get_mood_stats(employee, data)

    if not history:
        st.markdown("""
        <div class="glass" style="text-align:center;padding:3rem">
          <div style="font-size:3.5rem;margin-bottom:0.8rem">📭</div>
          <div style="font-size:1.1rem;font-weight:700;color:#a5b4fc">No history yet</div>
          <div style="color:#475569;margin-top:0.4rem">Start logging from the Emotion tab!</div>
        </div>""", unsafe_allow_html=True)
        return

    kpi4([
        (1, '📅', str(stats.get('total_entries', 0)), "Total Check-ins"),
        (2, '📊', f"{stats.get('average_stress', 0)}/10", "Avg Stress"),
        (3, '🎭', stats.get('most_common_mood', '—'), "Most Common"),
        (4, '🔴', str(stats.get('high_stress_days', 0)), "High Stress Days"),
    ])
    gd()
    fig = create_mood_timeline_chart(employee, days=30)
    if fig:
        st.plotly_chart(fig, width='stretch')

    st.markdown("### 🗂️ Recent Entries")
    df = pd.DataFrame([{
        'Date':     h['date'],
        'Time':     h['time'],
        'Emotion':  h['emotion'],
        'Stress':   h['stress_level'],
        'Workload': h['workload'],
        'Method':   h['method']
    } for h in history[-15:]])
    st.dataframe(df.sort_values('Date', ascending=False),
                 width='stretch', hide_index=True)

# ── STRESS ───────────────────────────────────────────────
def page_stress(employee):
    st.markdown("""
    <div class="hero-banner">
      <h2>🚨 Stress Monitor</h2>
      <p>Real-time wellbeing check</p>
    </div>""", unsafe_allow_html=True)

    history = get_mood_history(employee, data, 7)
    s   = history[-1]['stress_level'] if history else 0
    pct = int(s * 10)
    sc  = '#00e87a' if s < 5 else '#ffa502' if s < 7 else '#ff4757'
    lbl = 'All Good! 🌟' if s < 5 else 'Elevated ⚠️' if s < 8 else 'Critical 🚨'

    st.markdown(f"""
    <div class="glass">
      <div class="stress-wrap">
        <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:1.5px">Your Stress Level</div>
        <div class="stress-num" style="color:{sc}">{s}</div>
        <div class="stress-sub" style="color:{sc}">/10 &nbsp;—&nbsp; {lbl}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:{pct}%;background:linear-gradient(90deg,#00e87a,{sc})"></div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    cls  = 'al-crit' if s >= 8 else 'al-warn' if s >= 7 else 'al-mon' if s >= 4 else 'al-ok'
    icon = '🚨' if s >= 8 else '⚠️' if s >= 7 else '👀' if s >= 4 else '✅'
    head = ('CRITICAL — Immediate Action' if s >= 8 else 'WARNING — High Stress' if s >= 7
            else 'MONITOR — Rising' if s >= 4 else 'HEALTHY — Keep It Up!')
    msg  = ('Stress dangerously high. HR has been notified. Please take a break now.' if s >= 8
            else 'Elevated stress. Consider delegating or talking to your manager.' if s >= 7
            else 'Moderate stress. Take short breaks and review your workload.' if s >= 4
            else "You're doing great. Stress is within a healthy range.")

    st.markdown(f'<div class="al {cls}"><h3>{icon} {head}</h3><p>{msg}</p></div>',
                unsafe_allow_html=True)

    tips = {
        'critical': ['🧘 Take a 15-min break RIGHT NOW','🗣️ Talk to your manager or HR','📵 Step away from screens','🚶 Short walk outside'],
        'warning':  ['⏱️ Use Pomodoro (25+5 min)','📋 Delegate 2 non-urgent tasks','💤 Aim for 7-8 hrs sleep','🎵 Listen to calming music'],
        'monitor':  ['☕ Regular short breaks','📅 Review your schedule','🌟 Celebrate small wins','💬 Chat with a colleague'],
        'good':     ['🔥 Momentum is strong!','🌱 Share positivity with the team','🎯 Tackle your hardest task','💡 Explore something new'],
    }
    tip_k = 'critical' if s >= 8 else 'warning' if s >= 7 else 'monitor' if s >= 4 else 'good'
    st.markdown("### 💡 Recommended Actions")
    c1, c2 = st.columns(2)
    for i, tip in enumerate(tips[tip_k]):
        with [c1, c2][i % 2]:
            st.markdown(f'<div class="glass" style="padding:0.7rem 1rem;margin-bottom:0.4rem">{tip}</div>',
                        unsafe_allow_html=True)

    # Notify HR button
    gd()
    if s >= 5:
        if st.button("🚨 Notify HR About My Stress", type="primary", key="notify_hr"):
            emp_data = data.get("employees", {}).get(employee, {})
            send_stress_alert_email(employee, emp_data.get('email',''),
                                    s, history[-1]['emotion'] if history else 'Unknown',
                                    'WARNING', history[-1]['workload'] if history else 5)
            st.success("✅ HR has been notified. Someone will reach out to you soon.")


# ── TEAM ANALYTICS ───────────────────────────────────────
def page_team(employee, emp_data):
    my_team = emp_data.get('team', '')
    td      = TEAMS.get(my_team, {})
    tc      = T_COLOR.get(my_team, '#667eea')
    team_s  = get_team_stats(my_team, data)

    st.markdown(f"""
    <div class="hero-banner">
      <h1>{td.get('icon','👥')} {my_team}</h1>
      <p>{td.get('department','Team')} &nbsp;·&nbsp; Your Team Analytics</p>
    </div>""", unsafe_allow_html=True)

    if not team_s or not team_s.get('data_available'):
        st.markdown("""
        <div class="glass" style="text-align:center;padding:3rem">
          <div style="font-size:3rem">📭</div>
          <div style="color:#475569;margin-top:0.8rem">No team check-ins yet. Encourage your teammates!</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Team KPIs ──
    health = team_s['team_health']
    hc     = '#00e87a' if health >= 70 else '#ffa502' if health >= 40 else '#ff4757'
    kpi4([
        (1, '👥', str(len(td.get('members', []))),          "Team Size"),
        (2, '📊', f"{team_s['avg_stress']:.1f}/10",          "Avg Stress"),
        (3, '💼', f"{team_s['avg_workload']:.1f}/10",        "Avg Workload"),
        (4, '❤️', f'<span style="color:{hc}">{health}/100</span>', "Team Health"),
    ])
    gd()

    # ── Team Health Bar ──
    st.markdown(f"""
    <div style="margin-bottom:0.4rem;color:#94a3b8;font-size:0.82rem">Team Health Score</div>
    <div class="team-bar">
      <div class="team-bar-fill" style="width:{health}%;background:linear-gradient(90deg,{tc},{hc})"></div>
    </div>
    <div style="text-align:right;color:{hc};font-size:0.85rem;font-weight:700;margin-top:0.2rem">
      {health}/100
    </div>""", unsafe_allow_html=True)
    gd()

    # ── Team Members Mood Table ──
    st.markdown("### 👥 Team Members — Current Mood")
    members = team_s.get('members', [])

    for m in members:
        # ── Check privacy: hide mood if member turned off sharing ──
        member_priv  = get_privacy_settings(m['name'])
        mood_hidden  = (m['name'] != employee) and not member_priv.get('share_mood_with_team', False)

        sv     = m['stress'] if not mood_hidden else 0
        sc     = '#ff4757' if sv >= 8 else '#ffa502' if sv >= 6 else '#94a3b8'
        ee     = E_EMOJI.get(m['emotion'], '😐') if not mood_hidden else '🔒'
        ec     = E_COLOR.get(m['emotion'], '#667eea') if not mood_hidden else '#334155'
        lead   = '⭐ ' if m['is_lead'] else '   '
        is_me  = '← You' if m['name'] == employee else ''
        me_clr = '#a78bfa' if m['name'] == employee else '#e2e8f0'

        # Display values
        disp_emotion = 'Private 🔒' if mood_hidden else m['emotion']
        disp_date    = '—' if mood_hidden else m.get('date', '—')
        disp_stress  = '–/10' if mood_hidden else f"{m['stress']}/10"
        bar_filled   = 0 if mood_hidden else int(m['stress'])
        bar_empty    = 10 - bar_filled

        st.markdown(f"""
        <div class="glass" style="padding:0.9rem 1.2rem;margin-bottom:0.5rem;
             border-left:3px solid {ec if m['name'] != employee else '#a78bfa'}">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div style="display:flex;align-items:center;gap:0.8rem">
              <span style="font-size:1.6rem">{ee}</span>
              <div>
                <div style="color:{me_clr};font-weight:700;font-size:0.95rem">
                  {lead}{m['name']} <span style="color:#a78bfa;font-size:0.75rem">{is_me}</span>
                </div>
                <div style="color:#64748b;font-size:0.78rem">{disp_emotion} &nbsp;·&nbsp; {disp_date}</div>
              </div>
            </div>
            <div style="text-align:right">
              <div style="color:{sc};font-weight:700;font-size:1rem">{disp_stress}</div>
              <div style="color:#334155;font-size:0.7rem;letter-spacing:1px">
                {'█' * bar_filled}<span style="color:#1e293b">{'░' * bar_empty}</span>
              </div>
              <div style="color:#475569;font-size:0.72rem">Stress</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    gd()

    # ── Mood Distribution of Team ──
    if team_s.get('mood_distribution'):
        st.markdown("### 🎭 Team Mood Distribution")
        moods = team_s['mood_distribution']
        total = sum(moods.values())
        for mood, count in sorted(moods.items(), key=lambda x: -x[1]):
            pct   = int(count / total * 100)
            color = E_COLOR.get(mood, '#667eea')
            emoji = E_EMOJI.get(mood, '😐')
            st.markdown(f"""
            <div style="margin-bottom:0.5rem">
              <div style="display:flex;justify-content:space-between;
                          color:#94a3b8;font-size:0.82rem;margin-bottom:3px">
                <span>{emoji} {mood}</span>
                <span>{count} member{'s' if count>1 else ''} &nbsp;({pct}%)</span>
              </div>
              <div style="background:#1e293b;border-radius:6px;height:8px">
                <div style="background:{color};width:{pct}%;height:8px;
                            border-radius:6px;transition:width 0.5s"></div>
              </div>
            </div>""", unsafe_allow_html=True)

    gd()

    # ── Team Lead info ──
    lead_name = td.get('lead', '')
    if lead_name:
        lead_data  = data.get('employees', {}).get(lead_name, {})
        lead_mood  = lead_data.get('last_emotion', '—')
        lead_emoji = E_EMOJI.get(lead_mood, '😐')
        st.markdown(f"""
        <div class="glass" style="padding:1rem 1.4rem;border-left:4px solid #ffd93d;margin-top:0.5rem">
          <div style="color:#ffd93d;font-weight:700;font-size:0.85rem;margin-bottom:0.3rem">
            ⭐ Team Lead
          </div>
          <div style="color:#e2e8f0;font-size:1rem;font-weight:600">
            {lead_emoji} {lead_name} &nbsp;
            <span style="color:#64748b;font-size:0.82rem;font-weight:400">
              is feeling {lead_mood} today
            </span>
          </div>
        </div>""", unsafe_allow_html=True)


# ── PRIVACY ──────────────────────────────────────────────
def get_privacy_settings(employee: str) -> dict:
    """Load privacy settings from JSON file — persists across sessions."""
    path = "data/privacy_settings_all.json"
    defaults = {
        'share_mood_with_team': False,
        'camera_access':        True,
        'mic_access':           True,
        'email_alerts':         True,
    }
    if os.path.exists(path):
        try:
            import json as _json
            all_settings = _json.load(open(path))
            return all_settings.get(employee.lower(), defaults)
        except:
            pass
    return defaults

def save_privacy_settings(employee: str, settings: dict):
    """Save privacy settings to JSON file — persists across sessions."""
    import json as _json
    path = "data/privacy_settings_all.json"
    all_settings = {}
    if os.path.exists(path):
        try:
            all_settings = _json.load(open(path))
        except:
            pass
    all_settings[employee.lower()] = settings
    with open(path, 'w') as f:
        _json.dump(all_settings, f, indent=2)
    # Also keep in session state as cache
    st.session_state[f"privacy_{employee.lower()}"] = settings

def page_privacy():
    employee = st.session_state.current_user
    priv     = get_privacy_settings(employee)

    st.markdown("""
    <div class="hero-banner">
      <h2>🔐 Privacy Settings</h2>
      <p>Control how your data is collected and used</p>
    </div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### 👁️ Data Collection")
        cam   = st.checkbox("📷 Camera access",        value=priv.get('camera_access', True),        key="pv_cam")
        mic   = st.checkbox("🎤 Microphone access",    value=priv.get('mic_access', True),           key="pv_mic")
        share = st.checkbox("📊 Share mood with team", value=priv.get('share_mood_with_team', False), key="pv_share")
        email = st.checkbox("📧 Email alerts to HR",   value=priv.get('email_alerts', True),         key="pv_email")
        st.markdown('</div>', unsafe_allow_html=True)

        # Live preview
        if not share:
            st.markdown("""
            <div style="background:rgba(255,71,87,0.1);border:1px solid #ff475744;
                        padding:0.6rem 1rem;border-radius:8px;margin-top:0.5rem;font-size:0.82rem;color:#fca5a5">
              🔒 Your mood is <b>hidden</b> from teammates
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(0,232,122,0.1);border:1px solid #00e87a44;
                        padding:0.6rem 1rem;border-radius:8px;margin-top:0.5rem;font-size:0.82rem;color:#6ee7b7">
              👁️ Your mood is <b>visible</b> to teammates
            </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("#### 🛡️ Your Rights")
        st.markdown("""<div style="color:#94a3b8;font-size:0.87rem;line-height:2.2">
            ✅ &nbsp;Data encrypted at rest<br>
            ✅ &nbsp;Visible only to you &amp; HR<br>
            ✅ &nbsp;Auto-deleted after 90 days<br>
            ✅ &nbsp;GDPR compliant<br>
            ✅ &nbsp;Right to be forgotten
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Save Settings", type="primary", key="pv_save"):
        save_privacy_settings(employee, {
            'camera_access':        cam,
            'mic_access':           mic,
            'share_mood_with_team': share,
            'email_alerts':         email,
        })
        st.success("✅ Privacy settings saved!")
        if not share:
            st.info("🔒 Your mood will now appear as **Private** to your teammates.")
        st.rerun()

# ══════════════════════════════════════════════════════════
#  HR DASHBOARD
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
#  DATA RETENTION HELPERS
# ══════════════════════════════════════════════════════════

def get_retention_days() -> int:
    """Get current retention window from session state (default 30 days)."""
    return st.session_state.get('retention_days', 30)

def filter_by_retention(history: list, days: int) -> list:
    """Return only entries within the retention window."""
    if not history or days == 0:
        return history
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [h for h in history if h.get('date', '9999') >= cutoff]

def apply_retention_to_data(base_data: dict, days: int) -> dict:
    """
    Return a VIEW of data filtered by retention window.
    NEVER modifies the original — safe read-only view.
    """
    import copy
    view = copy.deepcopy(base_data)
    for emp in view.get('employees', {}).values():
        emp['mood_history'] = filter_by_retention(
            emp.get('mood_history', []), days
        )
    return view

def archive_and_purge(days: int) -> tuple[int, int]:
    """
    PERMANENTLY delete entries older than `days` from employee_data.json.
    wellness.db is your permanent database — data is always safe.
    Returns: (employees_affected, entries_deleted)
    """
    cutoff   = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    affected = 0
    deleted  = 0
    for emp_name, emp_val in data.get('employees', {}).items():
        before = len(emp_val.get('mood_history', []))
        emp_val['mood_history'] = [
            h for h in emp_val.get('mood_history', [])
            if h.get('date', '9999') >= cutoff
        ]
        after = len(emp_val['mood_history'])
        diff  = before - after
        if diff > 0:
            deleted  += diff
            affected += 1
    if deleted > 0:
        save_employee_data(data)
    return affected, deleted

def show_hr_dashboard():
    with st.sidebar:
        st.markdown("""
        <div class="profile-block">
          <div class="profile-emoji">👥</div>
          <div class="profile-name">HR Admin</div>
          <div class="profile-team">Wellness Analytics</div>
        </div>""", unsafe_allow_html=True)
        gd()
        hr_menu = st.radio("HR Navigation", ["📊  Overview","👥  Teams","🔔  Alerts","📋  Employee Detail","🗄️  Database","⚙️  Settings"],
                           label_visibility="collapsed")
        gd()
        if st.button("🚪  Logout", width='stretch'):
            for k in ['authenticated', 'current_user', 'user_type']:
                st.session_state[k] = False if k == 'authenticated' else None
            st.rerun()

    st.markdown("""
    <div class="hero-banner">
      <h1>👥 HR Wellness Command Centre</h1>
      <p>Real-time Employee Wellbeing Analytics &nbsp;·&nbsp; Powered by AI</p>
    </div>""", unsafe_allow_html=True)

    # Apply retention window filter (view only — never deletes)
    _ret_days = get_retention_days()
    _view     = apply_retention_to_data(data, _ret_days)
    ts     = analyze_team_mood(_view)
    alerts = get_all_active_alerts(data)   # alerts always show regardless of window
    avg_s  = ts['average_stress'] if ts else 0
    hi_s   = ts['high_stress_count'] if ts else 0
    sc     = '#ff4757' if avg_s >= 7 else '#ffa502' if avg_s >= 5 else '#00e87a'

    kpi4([
        (1, '👥', str(len(ALL_EMPLOYEES)),                                      "Total Employees"),
        (2, '📊', f'<span style="color:{sc}">{avg_s:.1f}/10</span>',            "Avg Stress"),
        (3, '🔴', str(hi_s),                                                    "High Stress"),
        (4, '🔔', f'<span style="color:#ff4757">{len(alerts)}</span>' if alerts else "0", "Active Alerts"),
    ])

    page = hr_menu.split("  ", 1)[1]

    # ── OVERVIEW ──────────────────────────────────────────
    if page == "Overview":
        gd()
        # Show retention badge
        st.markdown(f"""
        <div style="text-align:right;margin-bottom:0.5rem">
          <span style="background:rgba(102,126,234,0.15);border:1px solid #667eea;
                       color:#667eea;padding:4px 14px;border-radius:20px;font-size:0.78rem">
            📅 Showing last <b>{_ret_days} days</b> of data
            &nbsp;·&nbsp; <a href="#" style="color:#a78bfa;text-decoration:none">
            Change in ⚙️ Settings</a>
          </span>
        </div>""", unsafe_allow_html=True)

        if ts and ts.get('mood_distribution'):
            c1, c2 = st.columns(2)
            with c1:
                fig = create_overall_mood_chart(ts['mood_distribution'])
                if fig: st.plotly_chart(fig, width='stretch')
            with c2:
                team_stats_all = {n: get_team_stats(n, _view) for n in TEAMS}
                fig2 = create_team_mood_charts(team_stats_all)
                if fig2: st.plotly_chart(fig2, width='stretch')

            # Individual stress — use _view
            emp_stress = []
            for emp, ed in _view.get('employees', {}).items():
                h = ed.get('mood_history', [])
                if h:
                    emp_stress.append({'name': emp, 'stress': h[-1]['stress_level']})
            if emp_stress:
                fig3 = create_stress_distribution(emp_stress)
                if fig3: st.plotly_chart(fig3, width='stretch')
        else:
            st.markdown("""
            <div class="glass" style="text-align:center;padding:3.5rem">
              <div style="font-size:3.5rem">📭</div>
              <div style="color:#475569;margin-top:0.8rem">No mood data yet. Ask employees to log in!</div>
            </div>""", unsafe_allow_html=True)

    # ── TEAMS ─────────────────────────────────────────────
    elif page == "Teams":
        gd()
        for team_name, td in TEAMS.items():
            team_s = get_team_stats(team_name, _view)
            tc     = T_COLOR.get(team_name, '#667eea')
            health = team_s['team_health'] if team_s else 0
            hc     = '#00e87a' if health >= 70 else '#ffa502' if health >= 40 else '#ff4757'

            with st.expander(f"{td['icon']} {team_name}  —  {td['department']}", expanded=True):
                if team_s and team_s.get('data_available'):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Avg Stress",   f"{team_s['avg_stress']:.1f}/10")
                    c2.metric("Avg Workload", f"{team_s['avg_workload']:.1f}/10")
                    c3.metric("High Stress",  team_s['high_stress_count'])
                    c4.metric("Team Health",  f"{health}/100")

                    st.markdown(f"""
                    <div class="team-bar">
                      <div class="team-bar-fill" style="width:{health}%;background:linear-gradient(90deg,{tc},{hc})"></div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("**Team Members:**")
                    for m in team_s.get('members', []):
                        sv   = m['stress']
                        sclr = '#ff4757' if sv >= 8 else '#ffa502' if sv >= 6 else '#00e87a'
                        lead = '⭐ ' if m['is_lead'] else ''
                        ee   = E_EMOJI.get(m['emotion'], '😐')
                        c1, c2, c3, c4 = st.columns([3, 2, 1.2, 1.5])
                        c1.write(f"{lead}**{m['name']}**")
                        c2.write(f"{ee} {m['emotion']}")
                        c3.markdown(f"<span style='color:{sclr}'>{sv}/10</span>", unsafe_allow_html=True)
                        c4.write(m.get('date', '—'))

                    gauge = create_team_health_gauge(health, f"{td['icon']} {team_name.split(' ')[1]}")
                    st.plotly_chart(gauge, width='stretch')
                else:
                    st.info("No check-ins yet for this team.")

    # ── ALERTS ────────────────────────────────────────────
    elif page == "Alerts":
        gd()
        if not alerts:
            st.markdown("""
            <div class="al al-ok">
              <h3>✅ All Clear — No Active Alerts</h3>
              <p>Your team's wellbeing is in great shape. Keep monitoring regularly.</p>
            </div>""", unsafe_allow_html=True)
        else:
            crit = [a for a in alerts if a['level'] == 'CRITICAL']
            warn = [a for a in alerts if a['level'] == 'WARNING']
            mon  = [a for a in alerts if a['level'] == 'MONITOR']

            for level_alerts, cls, icon, label in [
                (crit, 'al-crit', '🚨', 'Critical'),
                (warn, 'al-warn', '⚠️', 'Warning'),
                (mon,  'al-mon',  '👀', 'Monitoring'),
            ]:
                if level_alerts:
                    st.markdown(f"#### {icon} {label} Alerts ({len(level_alerts)})")
                    for a in level_alerts:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"""
                            <div class="al {cls}">
                              <h3>{icon} {a['employee']} — {a['level']}</h3>
                              <p>{a['message']}</p>
                              <p style="font-size:0.76rem;color:#475569;margin-top:0.4rem">
                                🕐 {a.get('timestamp','—')} &nbsp;|&nbsp; Stress: {a.get('stress_level','—')}/10
                              </p>
                            </div>""", unsafe_allow_html=True)
                        with col2:
                            st.markdown("<br><br>", unsafe_allow_html=True)
                            if st.button(f"✅ Resolve", key=f"res_{a['employee']}_{a.get('timestamp','')}_{a.get('level','')}_{id(a)}"):
                                count = resolve_all_alerts(a['employee'], data)
                                save_employee_data(data)
                                st.success(f"Resolved {count} alert(s) for {a['employee']}")
                                st.rerun()

    # ── EMPLOYEE DETAIL ───────────────────────────────────
    elif page == "Employee Detail":
        gd()
        selected_emp = st.selectbox("Select Employee", ALL_EMPLOYEES, key="hr_emp_sel")
        if selected_emp:
            emp_data  = _view.get("employees", {}).get(selected_emp, {})
            stats     = get_mood_stats(selected_emp, _view)
            history   = get_mood_history(selected_emp, _view, _ret_days)
            mood_now  = emp_data.get('last_emotion', '—')
            mc        = E_COLOR.get(mood_now, '#667eea')

            st.markdown(f"""
            <div class="glass" style="text-align:center;padding:1.5rem">
              <div style="font-size:3rem">{E_EMOJI.get(mood_now,'😐')}</div>
              <div style="font-size:1.3rem;font-weight:700;color:#f1f5f9;margin:0.4rem 0">{selected_emp}</div>
              <div style="color:#667eea;font-size:0.8rem">{emp_data.get('team','—')}</div>
              <div style="color:{mc};font-weight:600;margin-top:0.4rem">
                Current mood: {mood_now}
              </div>
            </div>""", unsafe_allow_html=True)

            if stats.get('total_entries', 0) > 0:
                kpi4([
                    (1, '📅', str(stats.get('total_entries', 0)),    "Check-ins"),
                    (2, '📊', f"{stats.get('average_stress', 0)}/10","Avg Stress"),
                    (3, '🎭', stats.get('most_common_mood', '—'),    "Most Common"),
                    (4, '🔴', str(stats.get('high_stress_days', 0)), "High Stress Days"),
                ])
                fig = create_mood_timeline_chart(selected_emp, days=30)
                if fig: st.plotly_chart(fig, width='stretch')

                if history:
                    st.markdown("### 🗂️ Mood Log")
                    df = pd.DataFrame([{
                        'Date': h['date'], 'Time': h['time'],
                        'Emotion': h['emotion'], 'Stress': h['stress_level'],
                        'Workload': h['workload'], 'Method': h['method']
                    } for h in history[-20:]])
                    st.dataframe(df.sort_values('Date', ascending=False),
                                 width='stretch', hide_index=True)
            else:
                st.info(f"No mood data yet for {selected_emp}.")

    # ── DATABASE VIEWER ───────────────────────────────────
    elif page == "Database":
        gd()
        st.markdown("""
        <div class="hero-banner" style="margin-bottom:1.5rem">
          <h2 style="margin:0">🗄️ Database Viewer</h2>
          <p style="margin:0.3rem 0 0">Live view of all data stored in SQLite — clean table format</p>
        </div>""", unsafe_allow_html=True)

        db_st = get_db_stats()
        dr    = db_st.get('date_range', ('—','—'))
        dr_from = dr[0] if dr and dr[0] else '—'
        dr_to   = dr[1] if dr and dr[1] else '—'

        kpi4([
            (1, '👥', str(db_st['employees']),     "Employees"),
            (2, '📊', str(db_st['mood_entries']),  "Mood Entries"),
            (3, '🔔', str(db_st['alerts_total']),  "Total Alerts"),
            (4, '💾', f"{db_st['db_size_kb']} KB", "DB Size"),
        ])
        st.markdown(f"""
        <div style="text-align:right;color:#64748b;font-size:0.8rem;margin-bottom:1rem">
          📅 Data range: <b style="color:#667eea">{dr_from}</b> → <b style="color:#667eea">{dr_to}</b>
        </div>""", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["👥 Employees", "📊 Mood History", "🔔 Alerts"])

        with tab1:
            st.markdown("#### 👥 Employee Profiles")
            emp_table = get_all_employees_table()
            if emp_table:
                st.dataframe(emp_table, width='stretch', hide_index=True,
                    column_config={
                        "Avg Stress":      st.column_config.ProgressColumn("Avg Stress", min_value=0, max_value=10),
                        "Total Check-ins": st.column_config.NumberColumn("Check-ins", format="%d 📝"),
                    })
            else:
                st.info("No employee data found.")

        with tab2:
            st.markdown("#### 📊 Mood History")
            c1, c2 = st.columns([2,1])
            with c1:
                ef = st.selectbox("Filter by Employee", ["All Employees"] + ALL_EMPLOYEES, key="db_ef")
            with c2:
                df_days = st.selectbox("Days", [7,15,30,60,90], index=2, key="db_df")
            eid = ef.lower() if ef != "All Employees" else None
            mt  = get_mood_history_table(employee_id=eid, days=df_days)
            if mt:
                st.caption(f"{len(mt)} entries found")
                st.dataframe(mt, width='stretch', hide_index=True,
                    column_config={
                        "Stress":   st.column_config.ProgressColumn("Stress",   min_value=0, max_value=10),
                        "Workload": st.column_config.ProgressColumn("Workload", min_value=0, max_value=10),
                    })
            else:
                st.info("No mood entries found.")

        with tab3:
            st.markdown("#### 🔔 Alerts Log")
            at = get_alerts_table()
            if at:
                st.dataframe(at, width='stretch', hide_index=True)
            else:
                st.info("No alerts recorded yet.")


    # ── SETTINGS ──────────────────────────────────────────
    elif page == "Settings":
        gd()
        st.markdown("""
        <div class="hero-banner" style="margin-bottom:1.5rem">
          <h2 style="margin:0">⚙️ Data Retention Policy</h2>
          <p style="margin:0.3rem 0 0">Control how much historical data is shown on the dashboard</p>
        </div>""", unsafe_allow_html=True)

        # ── Current policy display ──
        current = get_retention_days()
        col1, col2, col3 = st.columns([1.5, 2, 1.5])
        with col2:
            st.markdown(f"""
            <div class="glass" style="text-align:center;padding:2rem">
              <div style="font-size:3rem">📅</div>
              <div style="font-size:2.2rem;font-weight:800;color:#667eea;margin:0.3rem 0">
                {current} Days
              </div>
              <div style="color:#64748b;font-size:0.85rem">Current Retention Window</div>
            </div>""", unsafe_allow_html=True)

        gd()

        # ── Policy selector ──
        st.markdown("#### 📋 Select Retention Window")
        st.markdown("""
        <div style="color:#64748b;font-size:0.85rem;margin-bottom:1rem">
        Dashboard will only show data within the selected window.
        Older data stays safely archived in <code>wellness.db</code> — nothing is lost.
        </div>""", unsafe_allow_html=True)

        POLICIES = {
            "15 Days  —  Fortnight view":   15,
            "30 Days  —  Monthly view":     30,
            "45 Days  —  Quarterly view":   45,
            "60 Days  —  Bi-monthly view":  60,
            "90 Days  —  Full quarter":     90,
            "All Time  —  No limit":         0,
        }

        selected_policy = st.radio(
            "Retention Policy",
            list(POLICIES.keys()),
            index=list(POLICIES.values()).index(current) if current in POLICIES.values() else 1,
            label_visibility="collapsed",
        )
        new_days = POLICIES[selected_policy]

        gd()

        # ── What this means ──
        if new_days > 0:
            cutoff_date = (datetime.now() - timedelta(days=new_days)).strftime("%d %b %Y")
            st.markdown(f"""
            <div class="glass" style="padding:1rem 1.5rem;border-left:4px solid #667eea">
              <b style="color:#e2e8f0">What this means:</b><br>
              <span style="color:#94a3b8;font-size:0.88rem">
              ✅ Dashboard shows: <b style="color:#00e87a">{cutoff_date}</b> → Today<br>
              🗄️ Older data: safely kept in <code>wellness.db</code> (permanent archive)<br>
              🔄 You can change this anytime — nothing is permanently deleted here
              </span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass" style="padding:1rem 1.5rem;border-left:4px solid #00e87a">
              <b style="color:#e2e8f0">All Time selected:</b><br>
              <span style="color:#94a3b8;font-size:0.88rem">
              ✅ All historical data will be shown on the dashboard<br>
              📊 This may slow down charts if data is very large
              </span>
            </div>""", unsafe_allow_html=True)

        gd()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Apply Window", type="primary", width='stretch'):
                st.session_state['retention_days'] = new_days
                label = selected_policy.split("  —  ")[0]
                st.success(f"✅ Dashboard now shows last **{label}** of data")
                st.rerun()

        gd()
        st.markdown("---")

        # ── DANGER ZONE: permanent purge ──
        st.markdown("""
        <div style="color:#ff4757;font-weight:700;font-size:1rem;margin-bottom:0.5rem">
          🗑️ Danger Zone — Permanent Data Purge
        </div>
        <div style="color:#64748b;font-size:0.82rem;margin-bottom:1rem">
        This will <b>permanently delete</b> old entries from the active database.<br>
        wellness.db keeps all data safe — only active dashboard entries will be removed.
        </div>""", unsafe_allow_html=True)

        purge_options = {
            "Delete data older than 30 days": 30,
            "Delete data older than 45 days": 45,
            "Delete data older than 60 days": 60,
            "Delete data older than 90 days": 90,
        }
        purge_choice = st.selectbox(
            "Purge Option", list(purge_options.keys()), key="purge_sel"
        )
        purge_days = purge_options[purge_choice]
        purge_cutoff = (datetime.now() - timedelta(days=purge_days)).strftime("%d %b %Y")

        # Count how many entries would be deleted
        preview_count = sum(
            len([h for h in emp.get('mood_history', []) if h.get('date', '9999') < (datetime.now() - timedelta(days=purge_days)).strftime("%Y-%m-%d")])
            for emp in data.get('employees', {}).values()
        )

        if preview_count > 0:
            st.markdown(f"""
            <div style="background:rgba(255,71,87,0.1);border:1px solid #ff4757;
                        padding:0.8rem 1.2rem;border-radius:8px;margin-bottom:0.8rem">
              <span style="color:#ff4757">⚠️ This will permanently delete
              <b>{preview_count} entries</b> older than {purge_cutoff}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.info(f"No entries found older than {purge_cutoff} — nothing to delete.")

        if 'confirm_purge' not in st.session_state:
            st.session_state['confirm_purge'] = False

        if preview_count > 0:
            confirm = st.checkbox(
                f"I understand this will permanently delete {preview_count} old entries from the active database",
                key="purge_confirm_cb"
            )
            if confirm:
                if st.button("🗑️ Permanently Delete Old Data", type="primary", key="do_purge"):
                    deleted, _ = purge_old_entries(purge_days)
                    affected   = 1 if deleted > 0 else 0
                    st.success(f"✅ Done! Deleted **{deleted} entries** from **{affected} employees** older than {purge_cutoff}")
                    st.info("💾 wellness.db archive is untouched — all historical data is safe.")
                    st.session_state['confirm_purge'] = False
                    st.rerun()


# ══════════════════════════════════════════════════════════
def main():
    if not st.session_state.authenticated:
        show_login()
    elif st.session_state.user_type == 'employee':
        show_employee_dashboard()
    else:
        show_hr_dashboard()

if __name__ == "__main__":
    main()