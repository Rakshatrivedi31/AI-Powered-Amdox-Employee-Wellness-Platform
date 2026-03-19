
# 🚀 Amdox Employee Wellness Platform

**AI-Powered Employee Wellbeing — Real-time Emotion Detection, Stress Monitoring & HR Analytics**

## 📌 Overview

**Amdox Wellness Platform** is a full-stack AI-powered employee wellness monitoring system built with Python and Streamlit. It helps HR teams track employee stress and emotional wellbeing in real time across multiple teams — using emotion detection from text, camera, speech, and manual input.

Designed with a sleek **Obsidian Neon** dark glassmorphism UI, the platform gives employees a private space to log their mood and gives HR a live analytics command centre.

---

## ✨ Features

### 👤 Employee Dashboard
| Feature | Details |
|---|---|
| 😊 **Emotion Detection** | Text analysis, Camera (DeepFace AI), Speech Recognition, Manual picker |
| 📋 **AI Task Recommendations** | Mood-based personalised task suggestions using Decision Tree ML |
| 📊 **Mood History** | 30-day timeline charts, stress trends, mood distribution |
| 🚨 **Stress Monitor** | Real-time stress gauge with actionable wellness tips |
| 👥 **Team Analytics** | View your team's mood, health score, and member status |
| 🔐 **Privacy Controls** | Data encryption, anonymization, GDPR-compliant settings |

### 👥 HR Dashboard
| Feature | Details |
|---|---|
| 📊 **Overview** | Company-wide mood charts, stress distribution, team comparison |
| 👥 **Team Analytics** | Per-team health scores, member-level mood status |
| 🔔 **Alert Centre** | CRITICAL / WARNING / MONITOR alerts with resolve button |
| 📋 **Employee Detail** | Individual mood logs, trend charts, check-in history |
| 🗄️ **Database Viewer** | Live SQLite viewer — Employees, Mood History, Alerts |
| ⚙️ **Data Retention** | Configurable retention window (15 / 30 / 45 / 60 / 90 days) |

### 🤖 AI & Smart Features
- **DeepFace** real-time facial emotion recognition via webcam
- **TextBlob** NLP sentiment analysis on text input
- **Google Speech API** for voice-based mood logging
- **Decision Tree** ML model for task recommendations
- **Auto stress alerts** — email HR only on CRITICAL stress (≥8/10) or Angry emotion
- **SQLite** database with auto-sync from JSON

---

## 🏗️ Project Structure

```
amdox-wellness/
│
├── app.py                    # Main Streamlit app — all pages & routing
│
├── utils/
│   ├── mood_tracking.py      # Core data model, auth, team structure, charts
│   ├── emotion_detector.py   # Text / Camera / Speech / Manual detection
│   ├── stress_alert.py       # Alert levels (CRITICAL/WARNING/MONITOR)
│   ├── email_alerts.py       # Gmail SMTP — HR email notifications
│   ├── db_manager.py         # SQLite database — CRUD + migration
│   ├── task_assign.py        # ML-based task recommendation engine
│   ├── chart_utils.py        # Plotly charts for HR overview
│   ├── team_analytics.py     # Team-level mood aggregation & scoring
│   └── data_privacy.py       # Encryption, anonymization, GDPR controls
│
├── data/
│   ├── employee_data.json    # Primary employee data store
│   └── wellness.db           # SQLite database (auto-created)
│
├── .streamlit/
│   └── config.toml           # Streamlit logger config (suppresses warnings)
│
├── requirements.txt
└── README.md
```

---

## 👥 Teams & Employees

```
Team Alpha 🔵  (Engineering)   — Raksha, Sneha, Smita, Isha
Team Beta  🟢  (Design)        — Saniya, Arjun, Priya, Kajal
Team Gamma 🔴  (Marketing)     — Divya, Rohit, Anjali, Vikram
```

## 🔐 Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Employee | `<EmployeeName>` (e.g. `Raksha`) | `Raksha@2025` |
| HR Admin | `admin` | `admin@2025` |
| HR Admin | `hr_admin` | `admin@2025` |

> **Pattern:** Every employee's password is `Name@2025`

> ⚠️ **PyAudio** may need system-level install:
> - **Windows:** `pip install pyaudio` (usually works directly)
> - **Mac:** `brew install portaudio && pip install pyaudio`
> - **Linux:** `sudo apt-get install portaudio19-dev && pip install pyaudio`

### 4. Configure Email Alerts (Optional)
Open `utils/email_alerts.py` and update:
```python
EMAIL_CONFIG = {
    'enabled':       True,
    'smtp_server':   'smtp.gmail.com',
    'smtp_port':     587,
    'sender_email':  'your-email@gmail.com',
    'sender_password': 'your-gmail-app-password',  # Gmail App Password
    'hr_email':      'hr@yourcompany.com',
}
```
> Get a Gmail App Password from: **Google Account → Security → 2-Step Verification → App Passwords**

### 5. Run the App
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📧 Email Alert Logic

Emails are sent to HR **only** in these situations:

| Condition | Email? |
|---|---|
| Stress ≥ 8/10 (CRITICAL) | ✅ Yes |
| Emotion = Angry | ✅ Yes |
| Stress 6–7/10 (WARNING) | ❌ No — dashboard alert only |
| Stress 4–5/10 (MONITOR) | ❌ No |

---

## 🗄️ Database

The app uses **SQLite** (`data/wellness.db`) with 3 tables:

| Table | Contents |
|---|---|
| `employees` | Profile, last emotion, avg stress, check-in count |
| `mood_history` | Every mood entry with timestamp, emotion, stress, workload |
| `alerts` | All CRITICAL/WARNING/MONITOR alerts with level and message |

Data auto-syncs from `employee_data.json` to SQLite on every mood save and on Database page open.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit, Custom CSS (Glassmorphism) |
| Emotion Detection | DeepFace, TextBlob, SpeechRecognition, OpenCV |
| ML / AI | scikit-learn Decision Tree, TF-Keras |
| Database | SQLite3 (via Python stdlib) |
| Data Storage | JSON + SQLite dual store |
| Charts | Plotly |
| Email | Gmail SMTP (smtplib) |
| Security | Python `cryptography` library |

---

<div align="center">
  Made with ❤️ for employee wellbeing · Amdox Wellness Platform
</div>
