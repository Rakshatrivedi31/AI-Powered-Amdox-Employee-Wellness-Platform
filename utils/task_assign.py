import os
import random
from datetime import datetime

# ══════════════════════════════════════════════════════════
#  MOOD → EMOJI KEY  (for display)
# ══════════════════════════════════════════════════════════

MOOD_MAPPING = {
    "Happy":    "Happy 😊",
    "Calm":     "Calm 😌",
    "Neutral":  "Neutral 😐",
    "Tired":    "Tired 😴",
    "Stressed": "Stressed 😰",
    "Sad":      "Sad 😔",
    "Angry":    "Angry 😠",
    "Energetic":"Energetic ⚡",
}

# ══════════════════════════════════════════════════════════
#  RICH TASK DATABASE  (8 moods × 3 levels × 5 tasks)
# ══════════════════════════════════════════════════════════

TASK_DB = {
    "Happy": {
        "low": [
            {"task": "Creative Brainstorming",     "description": "Your positive energy is perfect for generating fresh ideas!", "icon": "🎨", "duration": 60,  "priority": "Medium", "category": "Creative"},
            {"task": "Mentor a Teammate",           "description": "Spread good energy — help a colleague learn something new.",    "icon": "🌟", "duration": 45,  "priority": "Low",    "category": "Mentoring"},
            {"task": "Write Blog / Documentation",  "description": "Great mood to write clearly and creatively.",                   "icon": "✍️", "duration": 50,  "priority": "Low",    "category": "Writing"},
            {"task": "Explore New Tools",           "description": "A happy mind is curious — try a new tool today.",               "icon": "🔭", "duration": 40,  "priority": "Low",    "category": "Learning"},
            {"task": "Design UI Mockup",            "description": "Creative juices flowing — sketch that feature idea!",           "icon": "🖌️", "duration": 55,  "priority": "Medium", "category": "Design"},
        ],
        "medium": [
            {"task": "Team Collaboration Session",  "description": "Best time to align with your team and build great things!",     "icon": "👥", "duration": 90,  "priority": "High",   "category": "Collaboration"},
            {"task": "Feature Development",         "description": "Channel happiness into building something meaningful.",          "icon": "🚀", "duration": 120, "priority": "High",   "category": "Development"},
            {"task": "Client Presentation Prep",    "description": "Confidence + energy = a presentation that shines!",             "icon": "📊", "duration": 75,  "priority": "High",   "category": "Presentation"},
            {"task": "Code New Feature",            "description": "Perfect mood for focused, productive dev work.",                "icon": "💻", "duration": 100, "priority": "High",   "category": "Development"},
            {"task": "Sprint Planning Session",     "description": "Your enthusiasm will energise the whole team's planning!",      "icon": "📋", "duration": 60,  "priority": "Medium", "category": "Planning"},
        ],
        "high": [
            {"task": "Lead a Workshop",             "description": "Your energy is infectious — inspire the whole team!",           "icon": "🎤", "duration": 120, "priority": "Critical","category": "Leadership"},
            {"task": "Strategic Roadmap Planning",  "description": "High energy + happy mood = perfect big-picture thinking.",      "icon": "🗺️", "duration": 150, "priority": "Critical","category": "Strategy"},
            {"task": "Stakeholder Meeting",         "description": "Represent the team with your best foot forward!",               "icon": "🤝", "duration": 90,  "priority": "Critical","category": "Communication"},
            {"task": "System Architecture Design",  "description": "Complex design decisions need exactly this positive focus.",    "icon": "🏗️", "duration": 180, "priority": "Critical","category": "Architecture"},
            {"task": "Release Deployment",          "description": "High focus + great mood = safe, successful deployment!",        "icon": "📦", "duration": 120, "priority": "Critical","category": "DevOps"},
        ],
    },
    "Calm": {
        "low": [
            {"task": "Deep Work Focus Session",     "description": "Calm state is ideal for deep, uninterrupted concentration.",    "icon": "🧠", "duration": 120, "priority": "High",   "category": "Deep Work"},
            {"task": "Technical Documentation",     "description": "Clear mind = clear writing. Perfect for technical docs.",       "icon": "📝", "duration": 60,  "priority": "Medium", "category": "Documentation"},
            {"task": "Code Refactoring",            "description": "Calm focus spots improvement opportunities others miss.",       "icon": "♻️", "duration": 90,  "priority": "Medium", "category": "Refactoring"},
            {"task": "Research & Analysis",         "description": "Deep dive into that topic you've been meaning to explore.",     "icon": "🔬", "duration": 80,  "priority": "Medium", "category": "Research"},
            {"task": "Online Learning",             "description": "Calm is the best state to absorb new knowledge.",               "icon": "📚", "duration": 60,  "priority": "Low",    "category": "Learning"},
        ],
        "medium": [
            {"task": "Code Review",                 "description": "Calm clarity is perfect for catching bugs and feedback.",       "icon": "💻", "duration": 60,  "priority": "High",   "category": "Review"},
            {"task": "Bug Investigation",           "description": "Methodical calm is ideal for tracking down tricky bugs.",       "icon": "🐛", "duration": 90,  "priority": "High",   "category": "Debugging"},
            {"task": "System Design Discussion",    "description": "Calm reasoning leads to solid, well-thought architectures.",    "icon": "📐", "duration": 75,  "priority": "High",   "category": "Design"},
            {"task": "Data Analysis & Reporting",   "description": "Numbers reveal themselves to a calm, focused mind.",            "icon": "📊", "duration": 100, "priority": "High",   "category": "Analysis"},
            {"task": "API Integration Work",        "description": "Detail-oriented calm is exactly what integrations need.",       "icon": "🔌", "duration": 80,  "priority": "Medium", "category": "Integration"},
        ],
        "high": [
            {"task": "Complex Problem Solving",     "description": "Tackle the hardest challenge with your calm superpower.",       "icon": "🔧", "duration": 150, "priority": "Critical","category": "Problem Solving"},
            {"task": "Performance Optimization",    "description": "Patient analysis will find every bottleneck.",                  "icon": "⚡", "duration": 120, "priority": "Critical","category": "Optimization"},
            {"task": "Security Audit",              "description": "Calm thoroughness is essential for a proper security review.",  "icon": "🔒", "duration": 180, "priority": "Critical","category": "Security"},
            {"task": "Database Optimization",       "description": "Complex queries need exactly this focused, calm mindset.",      "icon": "🗄️", "duration": 100, "priority": "Critical","category": "Database"},
            {"task": "Infrastructure Setup",        "description": "Careful, calm execution — perfect for critical infra work.",    "icon": "🖥️", "duration": 150, "priority": "Critical","category": "Infrastructure"},
        ],
    },
    "Neutral": {
        "low": [
            {"task": "Email & Inbox Cleanup",       "description": "A steady day to clear the clutter and get to inbox zero.",      "icon": "📧", "duration": 30,  "priority": "Low",    "category": "Admin"},
            {"task": "Task List Review",            "description": "Review and reprioritise your tasks for the week ahead.",        "icon": "✅", "duration": 25,  "priority": "Low",    "category": "Planning"},
            {"task": "Meeting Notes Update",        "description": "Update notes and action items from recent meetings.",           "icon": "🗒️", "duration": 30,  "priority": "Low",    "category": "Documentation"},
            {"task": "Reply to Messages",           "description": "Catch up on Slack messages you've been meaning to reply.",      "icon": "💬", "duration": 20,  "priority": "Low",    "category": "Communication"},
            {"task": "Calendar & Schedule Plan",    "description": "Organise your week and block time for priorities.",             "icon": "📅", "duration": 20,  "priority": "Low",    "category": "Planning"},
        ],
        "medium": [
            {"task": "Routine Development Tasks",   "description": "Steady state is great for consistent, reliable output.",        "icon": "⚙️", "duration": 90,  "priority": "Medium", "category": "Development"},
            {"task": "Testing & QA Execution",      "description": "Neutral mood is ideal for thorough test execution.",            "icon": "🧪", "duration": 60,  "priority": "Medium", "category": "Testing"},
            {"task": "Status Report Writing",       "description": "Clear, neutral tone is perfect for accurate status updates.",   "icon": "📄", "duration": 40,  "priority": "Medium", "category": "Reporting"},
            {"task": "Jira / Ticket Updates",       "description": "Keep the board clean and accurate.",                           "icon": "🎫", "duration": 30,  "priority": "Medium", "category": "Admin"},
            {"task": "Peer Code Review",            "description": "Balanced mindset gives fair, objective feedback.",              "icon": "👀", "duration": 50,  "priority": "Medium", "category": "Review"},
        ],
        "high": [
            {"task": "Sprint Execution",            "description": "Consistent execution is the key to sprint success.",            "icon": "🏃", "duration": 180, "priority": "High",   "category": "Execution"},
            {"task": "Product Demo Preparation",    "description": "Steady, organised preparation leads to a polished demo.",       "icon": "🎬", "duration": 120, "priority": "High",   "category": "Presentation"},
            {"task": "Cross-team Coordination",     "description": "Neutral and balanced — perfect for cross-team collab.",         "icon": "🤝", "duration": 90,  "priority": "High",   "category": "Collaboration"},
            {"task": "Legacy Code Migration",       "description": "Patient, steady work is what complex migrations require.",      "icon": "🔄", "duration": 150, "priority": "High",   "category": "Migration"},
            {"task": "Release Notes Writing",       "description": "Clear, neutral voice is ideal for user-facing release notes.",  "icon": "📋", "duration": 60,  "priority": "High",   "category": "Documentation"},
        ],
    },
    "Tired": {
        "low": [
            {"task": "Light Admin Only",            "description": "Simple tasks only — preserve your energy.",                     "icon": "📋", "duration": 25,  "priority": "Low",    "category": "Admin"},
            {"task": "Read & Review Docs",          "description": "Passive reading is manageable when energy is low.",             "icon": "📖", "duration": 30,  "priority": "Low",    "category": "Reading"},
            {"task": "Organise Files & Folders",    "description": "Low-effort cleanup that still feels productive.",               "icon": "🗂️", "duration": 20,  "priority": "Low",    "category": "Organisation"},
            {"task": "Watch a Learning Video",      "description": "Passive learning — easy on tired minds, still valuable.",       "icon": "🎥", "duration": 20,  "priority": "Low",    "category": "Learning"},
            {"task": "Power Nap (15 min)",          "description": "A short nap can restore 2 hours of productivity!",             "icon": "😴", "duration": 15,  "priority": "Low",    "category": "Rest"},
        ],
        "medium": [
            {"task": "Pomodoro Work Blocks",        "description": "Work 25 min, rest 5 min — paced approach for low energy.",      "icon": "⏱️", "duration": 30,  "priority": "Medium", "category": "Focused Work"},
            {"task": "Pair Programming",            "description": "Work with a colleague — shared energy helps when yours is low.","icon": "👨‍💻","duration": 60,  "priority": "Medium", "category": "Collaboration"},
            {"task": "Review Pull Requests",        "description": "Light review work that doesn't demand peak cognitive load.",    "icon": "🔍", "duration": 45,  "priority": "Medium", "category": "Review"},
            {"task": "Simple Bug Fixes",            "description": "Small, clear tasks are manageable even when tired.",            "icon": "🐛", "duration": 40,  "priority": "Medium", "category": "Debugging"},
            {"task": "Standup & Reassess",          "description": "Communicate your status, then reassess your load.",             "icon": "📢", "duration": 15,  "priority": "Low",    "category": "Communication"},
        ],
        "high": [
            {"task": "🚨 Delegate Tasks NOW",       "description": "High workload + low energy = burnout risk. Delegate urgently!", "icon": "⚠️", "duration": 20,  "priority": "Critical","category": "Management"},
            {"task": "Talk to Manager",             "description": "Communicate your capacity — good managers want to help.",       "icon": "🗣️", "duration": 15,  "priority": "Critical","category": "Communication"},
            {"task": "Focus on Top 1 Task Only",    "description": "Do only the single most critical item. Everything else waits.", "icon": "🎯", "duration": 60,  "priority": "Critical","category": "Focus"},
            {"task": "Request Deadline Extension",  "description": "Quality over speed — ask for more time.",                      "icon": "📅", "duration": 10,  "priority": "Critical","category": "Planning"},
            {"task": "Rest & Recovery",             "description": "Your health matters most. Take a recovery break.",              "icon": "🛌", "duration": 0,   "priority": "Critical","category": "Wellness"},
        ],
    },
    "Stressed": {
        "low": [
            {"task": "Box Breathing (5 min)",       "description": "4s in, 4s hold, 4s out, 4s hold — proven stress relief.",      "icon": "🧘", "duration": 5,   "priority": "Low",    "category": "Wellness"},
            {"task": "Walk Outside (10 min)",       "description": "Fresh air and movement are proven cortisol reducers.",          "icon": "🚶", "duration": 10,  "priority": "Low",    "category": "Wellness"},
            {"task": "Journaling",                  "description": "Externalising stress onto paper reduces its mental load.",      "icon": "📔", "duration": 10,  "priority": "Low",    "category": "Wellness"},
            {"task": "Listen to Calm Music",        "description": "Lo-fi or classical music lowers stress hormones.",              "icon": "🎵", "duration": 20,  "priority": "Low",    "category": "Wellness"},
            {"task": "Tidy Your Workspace",         "description": "A tidy desk = a less anxious mind. Start small.",              "icon": "🧹", "duration": 15,  "priority": "Low",    "category": "Organisation"},
        ],
        "medium": [
            {"task": "Break Tasks into Subtasks",   "description": "Big tasks overwhelm — break them into 15-min chunks.",         "icon": "📝", "duration": 20,  "priority": "Medium", "category": "Planning"},
            {"task": "Delegate 2 Tasks",            "description": "Identify what others can do and hand it off.",                  "icon": "🤝", "duration": 20,  "priority": "High",   "category": "Delegation"},
            {"task": "1-on-1 with Manager",         "description": "Share your stress — a good manager wants to help.",             "icon": "💬", "duration": 30,  "priority": "High",   "category": "Communication"},
            {"task": "Complete 1 Overdue Item",     "description": "Crossing off one pending item immediately reduces stress.",     "icon": "✅", "duration": 45,  "priority": "Medium", "category": "Execution"},
            {"task": "Reschedule Non-urgent Work",  "description": "Protect bandwidth by deferring what isn't truly urgent.",      "icon": "📅", "duration": 15,  "priority": "Medium", "category": "Planning"},
        ],
        "high": [
            {"task": "🚨 URGENT: Seek Support",     "description": "High stress + high workload is a danger zone. Escalate now!",  "icon": "🆘", "duration": 15,  "priority": "Critical","category": "Wellness"},
            {"task": "Emergency Task Triage",       "description": "Cancel, defer, or delegate everything non-critical.",          "icon": "🔴", "duration": 20,  "priority": "Critical","category": "Management"},
            {"task": "Call HR / EAP Helpline",      "description": "Employee Assistance Programs exist for exactly this.",         "icon": "📞", "duration": 30,  "priority": "Critical","category": "Support"},
            {"task": "Wellness / Medical Check",    "description": "Chronic high stress has physical effects. See a doctor.",      "icon": "🏥", "duration": 60,  "priority": "Critical","category": "Health"},
            {"task": "Take Emergency Leave",        "description": "Mental health days are real sick days. Wellbeing first.",      "icon": "🛑", "duration": 0,   "priority": "Critical","category": "Rest"},
        ],
    },
    "Sad": {
        "low": [
            {"task": "Gentle Admin Tasks",          "description": "Light, low-pressure tasks — be kind to yourself today.",       "icon": "🌱", "duration": 30,  "priority": "Low",    "category": "Admin"},
            {"task": "Connect with a Friend",       "description": "A quick chat with someone you trust can shift your mood.",     "icon": "💙", "duration": 15,  "priority": "Low",    "category": "Social"},
            {"task": "Gratitude List (3 items)",    "description": "Writing 3 things you're grateful for lifts mood.",             "icon": "🙏", "duration": 5,   "priority": "Low",    "category": "Wellness"},
            {"task": "Short Walk Outside",          "description": "Movement releases endorphins — even 10 minutes helps.",        "icon": "🚶", "duration": 10,  "priority": "Low",    "category": "Wellness"},
            {"task": "Watch Something Funny",       "description": "Laughter is medicine — permit yourself a short break.",        "icon": "😄", "duration": 15,  "priority": "Low",    "category": "Break"},
        ],
        "medium": [
            {"task": "Reach Out to Your Team",      "description": "You don't have to struggle alone — your team is there.",       "icon": "👫", "duration": 20,  "priority": "Medium", "category": "Social"},
            {"task": "Familiar / Easy Work",        "description": "Easy wins on known tasks builds confidence.",                  "icon": "🏠", "duration": 60,  "priority": "Medium", "category": "Work"},
            {"task": "Write Down What's Wrong",     "description": "Naming the problem gives you power over it.",                  "icon": "📓", "duration": 10,  "priority": "Low",    "category": "Journaling"},
            {"task": "Ask for Help Openly",         "description": "Asking for help is a sign of strength, not weakness.",         "icon": "🤲", "duration": 15,  "priority": "Medium", "category": "Communication"},
            {"task": "EAP / Counselling Session",   "description": "Professional support is available — please use it.",           "icon": "💚", "duration": 60,  "priority": "High",   "category": "Support"},
        ],
        "high": [
            {"task": "Reduce Workload Now",         "description": "Sadness + heavy load is unsustainable. Reduce today.",         "icon": "⬇️", "duration": 15,  "priority": "Critical","category": "Management"},
            {"task": "Talk to HR",                  "description": "HR exists to support you — this is the right time.",           "icon": "🗣️", "duration": 30,  "priority": "Critical","category": "Support"},
            {"task": "Request Flexible Work",       "description": "Request WFH or adjusted hours while you recover.",             "icon": "🏡", "duration": 20,  "priority": "Critical","category": "Work"},
            {"task": "Professional Mental Support", "description": "A therapist can provide tools you need right now.",            "icon": "🧠", "duration": 60,  "priority": "Critical","category": "Health"},
            {"task": "Self-Care Day",               "description": "Sometimes the most productive thing is to rest.",              "icon": "💆", "duration": 0,   "priority": "Critical","category": "Rest"},
        ],
    },
    "Angry": {
        "low": [
            {"task": "Physical Exercise (10 min)",  "description": "Channel that energy — run, push-ups, anything physical!",      "icon": "🏃", "duration": 10,  "priority": "Low",    "category": "Wellness"},
            {"task": "Write It Out, Don't Send",    "description": "Write the angry message — then delete it. You'll feel better.","icon": "🗑️", "duration": 5,   "priority": "Low",    "category": "Journaling"},
            {"task": "Cold Water / Fresh Air",      "description": "Physical reset helps emotional reset — step outside briefly.", "icon": "💨", "duration": 5,   "priority": "Low",    "category": "Wellness"},
            {"task": "5-4-3-2-1 Grounding",         "description": "Name 5 things you see, 4 hear, 3 touch — brings you to now.", "icon": "🌍", "duration": 5,   "priority": "Low",    "category": "Wellness"},
            {"task": "Listen to Music",             "description": "Match mood with music, then gradually go calmer.",             "icon": "🎵", "duration": 15,  "priority": "Low",    "category": "Break"},
        ],
        "medium": [
            {"task": "Constructive Writing Task",   "description": "Channel anger into powerful, focused writing or docs.",        "icon": "⚡", "duration": 45,  "priority": "Medium", "category": "Writing"},
            {"task": "Identify the Root Cause",     "description": "Write down what triggered you and why — clarity helps.",       "icon": "🔍", "duration": 15,  "priority": "Medium", "category": "Analysis"},
            {"task": "Delay Response by 1 Hour",    "description": "Never send angry messages immediately — wait and review.",     "icon": "⏳", "duration": 60,  "priority": "Medium", "category": "Management"},
            {"task": "Structured Problem Solving",  "description": "Convert anger into a problem statement, then solve calmly.",   "icon": "🧩", "duration": 50,  "priority": "Medium", "category": "Problem Solving"},
            {"task": "Organise / Physical Tasks",   "description": "Move things, organise — physical activity channels anger.",    "icon": "💪", "duration": 20,  "priority": "Low",    "category": "Organisation"},
        ],
        "high": [
            {"task": "🛑 Cool Down Period",         "description": "Decisions made in anger are almost always regretted.",         "icon": "🧊", "duration": 30,  "priority": "Critical","category": "Wellness"},
            {"task": "Postpone All Meetings",       "description": "Don't attend meetings while this angry — reschedule now.",     "icon": "📵", "duration": 10,  "priority": "Critical","category": "Management"},
            {"task": "Conflict Resolution Help",    "description": "If workplace issue — involve HR or a neutral mediator.",       "icon": "⚖️", "duration": 60,  "priority": "Critical","category": "Support"},
            {"task": "Escalate via Proper Channel", "description": "If something is wrong, report it through the right process.",  "icon": "📢", "duration": 30,  "priority": "Critical","category": "Communication"},
            {"task": "Take a Personal Day",         "description": "Sometimes stepping away completely is the wisest action.",     "icon": "🚪", "duration": 0,   "priority": "Critical","category": "Rest"},
        ],
    },
    "Energetic": {
        "low": [
            {"task": "Quick Win Tasks",             "description": "Use your energy to knock out small tasks fast!",               "icon": "⚡", "duration": 30,  "priority": "Medium", "category": "Execution"},
            {"task": "Team Motivation",             "description": "Share your positive energy with teammates who need it.",       "icon": "🔥", "duration": 20,  "priority": "Low",    "category": "Social"},
            {"task": "Learn Something New",         "description": "High energy is perfect for absorbing new information.",        "icon": "📚", "duration": 45,  "priority": "Medium", "category": "Learning"},
            {"task": "Brain Dump Ideas",            "description": "Capture all those ideas before they fade away!",               "icon": "💡", "duration": 25,  "priority": "Low",    "category": "Ideation"},
            {"task": "Optimise Workflow",           "description": "Find and fix inefficiencies with your energetic mindset.",     "icon": "⚙️", "duration": 40,  "priority": "Medium", "category": "Optimisation"},
        ],
        "medium": [
            {"task": "Complex Feature Development", "description": "Tackle that challenging feature with full energy!",            "icon": "🚀", "duration": 120, "priority": "High",   "category": "Development"},
            {"task": "Lead Team Meeting",           "description": "Your energy will make the meeting productive and engaging.",   "icon": "🎯", "duration": 60,  "priority": "High",   "category": "Leadership"},
            {"task": "Hackathon Project",           "description": "Perfect time to make progress on that innovative idea!",       "icon": "🏆", "duration": 180, "priority": "High",   "category": "Innovation"},
            {"task": "Mentor Junior Developers",    "description": "Share your knowledge and enthusiasm with others.",             "icon": "👨‍🏫","duration": 90,  "priority": "Medium", "category": "Mentoring"},
            {"task": "Performance Improvements",    "description": "High energy + focus = great optimisation work.",               "icon": "📈", "duration": 100, "priority": "High",   "category": "Optimisation"},
        ],
        "high": [
            {"task": "Architecture Redesign",       "description": "Big-picture thinking with high energy = great results!",       "icon": "🏛️", "duration": 180, "priority": "Critical","category": "Architecture"},
            {"task": "Critical Feature Delivery",   "description": "Push that important feature across the finish line!",          "icon": "🎯", "duration": 240, "priority": "Critical","category": "Delivery"},
            {"task": "Client Demo",                 "description": "Your enthusiasm will wow the clients!",                        "icon": "🤝", "duration": 90,  "priority": "Critical","category": "Presentation"},
            {"task": "Team Building Activity",      "description": "Lead a fun activity to boost team morale.",                    "icon": "🎉", "duration": 120, "priority": "High",   "category": "Team Building"},
            {"task": "Innovation Sprint",           "description": "Dedicate time to breakthrough ideas and prototypes.",          "icon": "💡", "duration": 180, "priority": "Critical","category": "Innovation"},
        ],
    },
}

# Fallback for unknown moods
TASK_DB["No Data"] = TASK_DB["Neutral"]
TASK_DB["—"]       = TASK_DB["Neutral"]


# ══════════════════════════════════════════════════════════
#  OPTIONAL ML MODEL
# ══════════════════════════════════════════════════════════

def _try_init_ml():
    """Try to load/train sklearn model. Returns model tuple or None."""
    try:
        import joblib
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import LabelEncoder

        mood_enc  = LabelEncoder()
        task_enc  = LabelEncoder()
        model_dir = "models"
        os.makedirs(model_dir, exist_ok=True)
        mp, mep, tep = (f"{model_dir}/task_model.pkl",
                        f"{model_dir}/mood_encoder.pkl",
                        f"{model_dir}/task_encoder.pkl")

        if all(os.path.exists(p) for p in [mp, mep, tep]):
            try:
                return (joblib.load(mp), joblib.load(mep), joblib.load(tep))
            except Exception:
                pass

        # Train fresh
        import pandas as pd
        train = {
            "mood":      ["Happy","Happy","Stressed","Stressed","Calm","Calm",
                          "Tired","Tired","Angry","Angry","Neutral","Neutral",
                          "Energetic","Energetic","Sad","Sad"],
            "workload":  [2,3,8,7,4,5,6,7,3,4,5,6,1,2,4,5],
            "task_type": ["Creative","Complex","Break","Simple","Planning",
                          "Review","Simple","Break","Solo","Break","Routine",
                          "Planning","Complex","Creative","Simple","Break"],
        }
        df = pd.DataFrame(train)
        df["me"] = mood_enc.fit_transform(df["mood"])
        df["te"] = task_enc.fit_transform(df["task_type"])
        model = DecisionTreeClassifier(max_depth=5, random_state=42)
        model.fit(df[["me","workload"]], df["te"])
        try:
            joblib.dump(model, mp); joblib.dump(mood_enc, mep); joblib.dump(task_enc, tep)
        except Exception:
            pass
        return (model, mood_enc, task_enc)

    except ImportError:
        return None


_ML = _try_init_ml()   # None if sklearn not installed


# ══════════════════════════════════════════════════════════
#  CORE RECOMMENDATION FUNCTIONS
# ══════════════════════════════════════════════════════════

def _level(workload: int) -> str:
    if workload <= 3:  return "low"
    if workload <= 7:  return "medium"
    return "high"


def recommend_task(mood: str, workload: int = 5) -> dict:
    """Single task recommendation — used internally and for testing."""
    pool  = TASK_DB.get(mood, TASK_DB["Neutral"])[_level(workload)]
    selected = random.choice(pool)

    # Try ML hint if available
    if _ML:
        try:
            model, mood_enc, task_enc = _ML
            if mood in list(mood_enc.classes_):
                me   = mood_enc.transform([mood])[0]
                pred = task_enc.inverse_transform(model.predict([[me, workload]]))[0]
                match = [t for t in pool if t.get("category","").lower() == pred.lower()]
                if match:
                    selected = random.choice(match)
        except Exception:
            pass

    return {
        "task":        selected["task"],
        "description": selected["description"],
        "icon":        selected["icon"],
        "duration":    selected["duration"],
        "priority":    selected["priority"],
        "category":    selected.get("category", "General"),
        "mood":        mood,
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def recommend_multiple_tasks(mood: str, workload: int = 5, count: int = 3) -> list:
    """
    Return `count` unique tasks for the given mood + workload.
    This is the main function imported by app.py.
    """
    pool = TASK_DB.get(mood, TASK_DB["Neutral"])[_level(workload)]
    sample = random.sample(pool, min(count, len(pool)))
    return [
        {
            "task":        t["task"],
            "description": t["description"],
            "icon":        t["icon"],
            "duration":    t["duration"],
            "priority":    t["priority"],
            "category":    t.get("category", "General"),
        }
        for t in sample
    ]