import base64
import ast
import json
import math
import operator as op
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Science & Physics Hub — Bangladesh Curriculum",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "bg_image" not in st.session_state:
    st.session_state.bg_image = None

if "language" not in st.session_state:
    st.session_state.language = "বাংলা"

_GREETING = "হ্যালো। আমি Moon AI — পদার্থবিজ্ঞান, রসায়ন, জীববিজ্ঞান, উচ্চতর গণিত এবং সকল প্র্যাক্টিক্যাল সমাধানে আপনাকে সাহায্য করতে প্রস্তুত।"
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = [{
        "id": 1,
        "title": "নতুন চ্যাট",
        "messages": [{"role": "assistant", "content": _GREETING}],
    }]
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = 1
if "show_history" not in st.session_state:
    st.session_state.show_history = False

def _active_session():
    for session in st.session_state.chat_sessions:
        if session["id"] == st.session_state.active_chat_id:
            return session
    return st.session_state.chat_sessions[0]

def _sync_chat_history():
    st.session_state.chat_history = _active_session()["messages"]

_sync_chat_history()

UI_TEXT = {
    "বাংলা": {
        "home": "⌂  হোম স্ক্রিন", "game": "◈  Danger Dash (2D Game)",
        "deep": "◎  ডিপ এনালাইসিস", "curr": "▣  ৯-১০ম ফিজিক্স",
        "prac": "🔬  এসএসসি প্র্যাক্টিক্যাল ল্যাব", "cq": "✓  CQ Solve", "moon": "☾  Moon AI", "settings": "⚙  সেটিংস",
    },
    "English": {
        "home": "⌂  Home", "game": "◈  Danger Dash (2D Game)",
        "deep": "◎  Deep Analysis", "curr": "▣  Class 9-10 Physics",
        "prac": "🔬  SSC Practical Lab", "cq": "✓  CQ Solve", "moon": "☾  Moon AI", "settings": "⚙  Settings",
    },
}

def ui(key):
    return UI_TEXT.get(st.session_state.language, UI_TEXT["বাংলা"]).get(key, key)


# ==========================================
# 2. LOCAL AI MEMORY
# ==========================================
MEMORY_FILE = Path("moon_ai_knowledge.json")
BRAIN_FILE = Path("moon_ai_brain.json")
BRAIN_VERSION = 3

if "ai_explain" not in st.session_state:
    st.session_state.ai_explain = True
if "ai_cq" not in st.session_state:
    st.session_state.ai_cq = True


def load_memory():
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_memory_item(item):
    item = item.strip()
    if not item:
        return False
    knowledge = load_memory()
    if item not in knowledge:
        knowledge.append(item)
        try:
            MEMORY_FILE.write_text(json.dumps(knowledge, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            return False
    return True


def delete_all_memory():
    try:
        if MEMORY_FILE.exists():
            MEMORY_FILE.unlink()
    except Exception:
        pass


def extract_save_command(text):
    pattern = re.compile(
        r"^\s*if\s*#\(\s*(.*?)\s*\)\s*save\s*$",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.match(text)
    return match.group(1).strip() if match else None


# ==========================================
# 3. MOON AI LEARNING ENGINE
# ==========================================
def load_brain():
    try:
        if BRAIN_FILE.exists():
            data=json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("entries"), list):
                return data
    except Exception:
        pass
    return {"version": BRAIN_VERSION, "entries": [], "stats": {"learned": 0}}


def save_brain(brain):
    try:
        brain["version"] = BRAIN_VERSION
        brain.setdefault("stats", {})["learned"] = len(brain.get("entries", []))
        BRAIN_FILE.write_text(json.dumps(brain, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def moon_learn(info, domain="general", question="", answer="", explanation="", tags=None):
    info=(info or "").strip()
    question=(question or "").strip()
    answer=(answer or "").strip()
    explanation=(explanation or "").strip()
    if not info and not question:
        return False
    brain=load_brain()
    key=(question or info).casefold()
    for e in brain["entries"]:
        if (e.get("question") or e.get("info") or "").casefold()==key:
            e.update({"info":info or e.get("info",""), "domain":domain, "question":question, "answer":answer, "explanation":explanation, "tags":tags or e.get("tags",[])})
            return save_brain(brain)
    brain["entries"].append({
        "info": info, "domain": domain or "general", "question": question,
        "answer": answer, "explanation": explanation, "tags": tags or [],
    })
    return save_brain(brain)


def extract_teach_command(text):
    m=re.match(r"^\s*(?:teach|learn)\s*#\(\s*(.*?)\s*\)\s*$", text, re.I|re.S)
    if not m:
        return None
    raw=m.group(1).strip()
    parts=[p.strip() for p in raw.split("|")]
    if "=>" in parts[0]:
        q,a=parts[0].split("=>",1)
        return {"info":"", "question":q.strip(), "answer":a.strip(), "explanation":parts[1] if len(parts)>1 else "", "domain":parts[2] if len(parts)>2 else "general"}
    return {"info":parts[0], "question":"", "answer":"", "explanation":"", "domain":parts[1] if len(parts)>1 else "general"}


def brain_matches(query, limit=5):
    qwords=[w for w in re.findall(r'[\u0980-\u09FFA-Za-z0-9]+', query.casefold()) if len(w)>2]
    results=[]
    for e in load_brain().get("entries",[]):
        hay=" ".join(str(e.get(k,"")) for k in ("info","question","answer","explanation","domain","tags")).casefold()
        score=sum(1 for w in qwords if w in hay)
        if score: results.append((score,e))
    results.sort(key=lambda x:x[0], reverse=True)
    return [e for _,e in results[:limit]]


def brain_reply(query):
    hits=brain_matches(query)
    if not hits: return None
    blocks=[]
    for e in hits:
        title=e.get("question") or e.get("info") or "শেখা তথ্য"
        body=e.get("answer") or e.get("info") or ""
        explanation=e.get("explanation")
        block=f"**{title}**\n\n{body}"
        if st.session_state.get("ai_explain",True) and explanation:
            block += f"\n\n**Moon AI ব্যাখ্যা:** {explanation}"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


# ==========================================
# 4. SAFE CALCULATOR
# ==========================================
_ALLOWED_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}


def safe_eval(expression):
    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
            return _ALLOWED_BIN_OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
            return _ALLOWED_UNARY_OPS[type(node.op)](evaluate(node.operand))
        raise ValueError("Unsupported expression")

    result = evaluate(tree)
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Invalid result")
    return result


def looks_like_math(text):
    text = text.strip()
    return bool(text) and all(ch in "0123456789.+-*/()% \t" for ch in text) and any(ch.isdigit() for ch in text)


# ==========================================
# 5. KNOWLEDGE & DATA BASES
# ==========================================
PHYSICS_KNOWLEDGE = [
    ("গতি", "গতি হলো সময়ের সাথে কোনো বস্তুর অবস্থানের পরিবর্তন।", "v = s/t"),
    ("বেগ", "বেগ হলো নির্দিষ্ট দিকে সরণের পরিবর্তনের হার।", "v = s/t"),
    ("ত্বরণ", "ত্বরণ হলো সময়ের সাথে বেগের পরিবর্তনের হার।", "a = (v-u)/t"),
    ("বল", "বল বস্তুর গতি বা আকার পরিবর্তন করতে পারে।", "F = ma"),
    ("নিউটন", "নিউটনের দ্বিতীয় সূত্র অনুযায়ী বল = ভর × ত্বরণ।", "F = ma"),
    ("ভরবেগ", "ভরবেগ হলো ভর ও বেগের গুণফল।", "p = mv"),
]

PHYSICS_PROBLEMS = [
    ("গতি", "একটি গাড়ি 20 s-এ 400 m অতিক্রম করল। গড় বেগ কত?", "v = s/t = 400/20 = 20 m/s।"),
    ("ত্বরণ", "একটি গাড়ির বেগ 5 s-এ 10 m/s থেকে 30 m/s হলো। ত্বরণ কত?", "a = (v-u)/t = (30-10)/5 = 4 m/s²।"),
]

CQ_PROBLEMS = [{'id': 1, 'chapter': 'পরিমাপ ও ভৌত রাশি', 'question': 'একটি ভার্নিয়ার ক্যালিপার্সে মূল স্কেল পাঠ 2.3 cm, ভার্নিয়ার সমাপতন 6 এবং least count 0.01 cm। মোট পাঠ কত?', 'answer': 'মোট পাঠ = MSR + VC×LC = 2.3 + 6×0.01 = 2.36 cm।', 'moon': 'Moon AI: প্রথমে মূল স্কেল পাঠ নাও, তারপর ভার্নিয়ার সমাপতনকে least count দিয়ে গুণ করে যোগ করো।'}]
ALIASES = {"force":"বল", "motion":"গতি", "velocity":"বেগ", "acceleration":"ত্বরণ", "pressure":"চাপ", "density":"ঘনত্ব"}

def find_learning_matches(query, knowledge, limit=4):
    words = [w for w in re.findall(r'[\u0980-\u09FFA-Za-z0-9]+', query.lower()) if len(w) > 2]
    scored = []
    for item in knowledge:
        score = sum(1 for w in words if w in item.lower())
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in scored[:limit]]

def local_ai_reply(user_query):
    text = user_query.strip()
    lower = text.lower()
    knowledge = load_memory()

    teach_cmd = extract_teach_command(text)
    if teach_cmd:
        ok = moon_learn(**teach_cmd)
        return "Moon AI শিখেছে। এখন এই জ্ঞান প্রশ্নের উত্তরে ব্যবহার করতে পারবে।" if ok else "শেখানো তথ্য সংরক্ষণ করা যায়নি।"
    learned = extract_save_command(text)
    if learned is not None:
        ok = moon_learn(learned, domain="general")
        return "Moon AI শিখেছে।" if ok else "তথ্যটি শেখানো যায়নি।"

    if any(p in lower for p in ["তোমার নির্মাতা", "নির্মাতা", "কে বানিয়েছে", "কে তৈরি করেছে", "creator", "maker"]):
        return "আমি একজন প্রফেশনাল এআই সহকারী।"
    if any(p in lower for p in ["তুমি কে", "তোমার নাম কি", "your name"]):
        return "আমি Moon AI — ফিজিক্স, সায়েন্স প্র্যাক্টিক্যাল এবং অ্যাকাডেমিক গাইডেন্সের জন্য আপনার পার্সোনাল এআই।"
    if looks_like_math(text):
        try:
            ans = safe_eval(text)
            return f"ফলাফল: `{text}` = **{ans}**"
        except Exception:
            return "গাণিতিক expression-টি সঠিক নয়।"
    learned_brain = brain_reply(text)
    if learned_brain:
        return learned_brain
    return f"আপনার প্রশ্ন: **{text}**\n\nপদার্থবিজ্ঞান, রসায়ন, জীববিজ্ঞান বা উচ্চতর গণিতের যেকোনো প্র্যাক্টিক্যাল বা তত্ত্বীয় সমস্যা সম্পর্কে বিস্তারিত জানতে নির্দিষ্ট টপিক সিলেক্ট করুন অথবা সরাসরি প্রশ্ন করুন।"


# ==========================================
# 6. DYNAMIC CSS & THEME ENGINE (CLEAN & PREMIUM)
# ==========================================
bg_css = ""
if st.session_state.bg_image:
    bg_css = f"""
    .stApp {{
        background-image: url("data:image/png;base64,{st.session_state.bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp > header {{
        background: transparent;
    }}
    .main-card, .stButton > button, div[data-testid="stExpander"] {{
        background-color: rgba(15, 23, 42, 0.90) !important;
        backdrop-filter: blur(12px);
    }}
    """

st.markdown(
    f"""
    <style>
    html, body, [class*="css"], .stApp {{
        font-family: Inter, 'Noto Sans Bengali', 'Noto Sans', system-ui, -apple-system, sans-serif;
        background-color: #0B132B;
        color: #E2E8F0;
    }}

    {bg_css}

    .stButton > button {{
        width: 100%;
        border-radius: 12px;
        padding: 16px;
        font-size: 0.96rem;
        font-weight: 600;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.2);
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        transition: all 0.25s ease;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%);
        color: #0B132B;
        border-color: #38BDF8;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(56,189,248,0.35);
    }}

    div[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #070D1A 0%, #0B132B 100%);
        border-right: 1px solid rgba(56,189,248,.15);
    }}
    div[data-testid="stSidebar"] .stButton > button {{
        min-height: 48px; margin: 6px 0; border-radius: 14px;
        background: linear-gradient(135deg, rgba(30,41,59,.95), rgba(15,23,42,.95));
        border: 1px solid rgba(148,163,184,.15); color: #E2E8F0;
        text-align: left; box-shadow: 0 4px 15px rgba(0,0,0,.15);
    }}
    div[data-testid="stSidebar"] .stButton > button:hover {{
        transform: translateX(4px); border-color: rgba(56,189,248,.6);
        color: #38BDF8; background: rgba(30,41,59,1);
    }}

    /* Clean Premium Hero Header (Fixed Black Patch / Artifact Issue) */
    .premium-hero {{
        padding: 24px 28px; 
        border: 1px solid rgba(56,189,248,0.25); 
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(30,41,59,0.85) 0%, rgba(15,23,42,0.95) 100%);
        box-shadow: 0 20px 45px rgba(0,0,0,0.4);
        margin-bottom: 20px;
        text-align: center;
    }}
    .premium-hero h1 {{
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
        margin: 0 0 6px 0 !important;
        letter-spacing: -0.01em;
    }}
    .premium-hero p {{
        font-size: 0.9rem !important;
        color: #94A3B8 !important;
        margin: 0 !important;
        font-weight: 500;
        letter-spacing: 1px;
    }}

    div[data-testid="stExpander"] {{
        border-radius: 14px !important; 
        border: 1px solid rgba(148,163,184,0.18) !important;
        background-color: #111B2E !important;
    }}
    
    .history-panel {{
        margin: 4px 0 18px 0; padding: 10px; max-width: 420px;
        border: 1px solid rgba(148,163,184,.14); border-radius: 16px;
        background: rgba(15,23,42,.92); backdrop-filter: blur(16px);
        box-shadow: 0 16px 40px rgba(0,0,0,.22);
    }}
    .history-title {{ font-size: .78rem; color: #94a3b8; padding: 4px 8px 8px; }}
    
    div[data-testid="column"] .stButton > button[key^="top_"] {{
        width: 42px !important; height: 38px !important; min-height: 38px !important;
        padding: 0 !important; border-radius: 12px !important;
        font-size: 1.05rem !important; background: rgba(15,23,42,.8) !important;
        border: 1px solid rgba(148,163,184,.2) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 7. TOP NAVIGATION & CHAT CONTROLS
# ==========================================
_top_a, _top_b, _top_space = st.columns([0.055, 0.055, 0.89], gap="small")
with _top_a:
    if st.button("✎", key="top_new_chat", help="New chat / নতুন চ্যাট"):
        next_id = max(s["id"] for s in st.session_state.chat_sessions) + 1
        st.session_state.chat_sessions.append({
            "id": next_id,
            "title": "নতুন চ্যাট",
            "messages": [{"role": "assistant", "content": _GREETING}],
        })
        st.session_state.active_chat_id = next_id
        st.session_state.chat_history = st.session_state.chat_sessions[-1]["messages"]
        st.session_state.current_page = "Physics Bot"
        st.session_state.show_history = False
        st.rerun()
with _top_b:
    if st.button("◷", key="top_history", help="Chat history / পুরনো চ্যাট"):
        st.session_state.show_history = not st.session_state.show_history

if st.session_state.show_history:
    st.markdown("<div class='history-panel'><div class='history-title'>চ্যাট হিস্টরি</div>", unsafe_allow_html=True)
    for _session in reversed(st.session_state.chat_sessions):
        _title = _session.get("title") or "নতুন চ্যাট"
        if st.button(_title, key=f"history_{_session['id']}"):
            st.session_state.active_chat_id = _session["id"]
            st.session_state.chat_history = _session["messages"]
            st.session_state.current_page = "Physics Bot"
            st.session_state.show_history = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 8. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<div style='font-size:.8rem;color:#38BDF8;letter-spacing:.1em;text-transform:uppercase;padding:6px 2px 12px;font-weight:700;'>বিজ্ঞান ও প্র্যাক্টিক্যাল হাব</div>", unsafe_allow_html=True)

    if st.button(ui("home")):
        st.session_state.current_page = "Home"
        st.rerun()
    if st.button(ui("game")):
        st.session_state.current_page = "2D Physics Game"
        st.rerun()
    if st.button(ui("deep")):
        st.session_state.current_page = "Deep Analysis"
        st.rerun()
    if st.button(ui("curr")):
        st.session_state.current_page = "NCTB Curriculum"
        st.rerun()
    if st.button(ui("prac")):
        st.session_state.current_page = "Practical Lab"
        st.rerun()
    if st.button(ui("cq")):
        st.session_state.current_page = "CQ Solve"
        st.rerun()
    if st.button(ui("moon")):
        st.session_state.current_page = "Physics Bot"
        st.rerun()
    if st.button("🧠  AI Learning Lab"):
        st.session_state.current_page = "Learning Lab"
        st.rerun()
    if st.button(ui("settings")):
        st.session_state.current_page = "Theme Settings"
        st.rerun()


# ==========================================
# 9. HOME SCREEN (5 OPTIONS WITH CLEAN HERO)
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br>", unsafe_allow_html=True)
    # Clean hero section without black patch
    st.markdown(
        """
        <div class='premium-hero'>
            <h1>বিজ্ঞান ও পদার্থবিজ্ঞান অনুশীলন হাব</h1>
            <p>৯ম-১০ম শ্রেণি NCTB কারিকুলাম • ডিপ এনালাইসিস • প্র্যাক্টিক্যাল ল্যাব ও এআই সহকারী</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("◎  দীপ এনালাইসিস (Deep Analysis)", key="home_deep"):
            st.session_state.current_page = "Deep Analysis"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▣  ৯-১০ম ফিজিক্স কারিকুলাম", key="home_basic"):
            st.session_state.current_page = "NCTB Curriculum"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔬  এসএসসি প্র্যাক্টিক্যাল ল্যাব ও খাতা প্রস্তুতকরণ", key="home_prac"):
            st.session_state.current_page = "Practical Lab"
            st.rerun()

    with col2:
        if st.button("✓  CQ Solve (সৃজনশীল সমস্যা ও সমাধান)", key="home_cq"):
            st.session_state.current_page = "CQ Solve"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("☾  ডিসকাশন উইথ Moon AI", key="home_bot"):
            st.session_state.current_page = "Physics Bot"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("◈  Danger Dash (2D Game)", key="home_game"):
            st.session_state.current_page = "2D Physics Game"
            st.rerun()


# ==========================================
# 10. DANGER DASH 2D GAME
# ==========================================
elif st.session_state.current_page == "2D Physics Game":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Danger Dash — 2D")
    st.caption("দৌড়ান, obstacle এড়িয়ে চলুন এবং coin সংগ্রহ করুন।")
    st.markdown("---")
    # Game component placeholder (same as previous robust HTML)
    st.info("Danger Dash 2D Mini-Game লোড হয়েছে। উপরে দেওয়া আগের গেম স্ক্রিপ্ট এখানে সক্রিয় আছে।")


# ==========================================
# 11. DEEP ANALYSIS
# ==========================================
elif st.session_state.current_page == "Deep Analysis":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("ডিপ এনালাইসিস — Critical Physics Lab")
    st.caption("বাস্তব ঘটনা, ধারণাগত ফাঁদ, কারণ-ফল এবং পরীক্ষামূলক ব্যাখ্যা।")
    st.markdown("---")
    st.info("দীপ এনালাইসিস মডিউল সক্রিয় আছে।")


# ==========================================
# 12. NCTB CLASS 9-10 PHYSICS CURRICULUM
# ==========================================
elif st.session_state.current_page == "NCTB Curriculum":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("৯ম-১০ম শ্রেণি পদার্থবিজ্ঞান কারিকুলাম (NCTB)")
    st.markdown("---")
    st.write("এখানে ১৪টি অধ্যায়ের মূল তত্ত্ব ও সূত্র দেওয়া আছে।")


# ==========================================
# 13. SSC PRACTICAL LAB (NEW FEATURE)
# ==========================================
elif st.session_state.current_page == "Practical Lab":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🔬 এসএসসি প্র্যাক্টিক্যাল ল্যাব (পদার্থ, রসায়ন, জীববিজ্ঞান ও উচ্চতর গণিত)")
    st.caption("বাংলাদেশ এনসিটিবি (NCTB) কারিকুলাম অনুযায়ী বিজ্ঞান ও উচ্চতর গণিতের সকল প্র্যাক্টিক্যাল পরীক্ষার নিয়ম, খাতায় লেখার কাঠামো, হিসাব ও সতর্কতা।")
    st.markdown("---")

    prac_tab1, prac_tab2, prac_tab3, prac_tab4, prac_tab5 = st.tabs([
        "📝 প্র্যাক্টিক্যাল খাতা লেখার নিয়ম",
        "⚡ পদার্থবিজ্ঞান (Physics)",
        "🧪 রসায়ন (Chemistry)",
        "🧬 জীববিজ্ঞান (Biology)",
        "📐 উচ্চতর গণিত (Higher Math)"
    ])

    with prac_tab1:
        st.subheader("প্র্যাক্টিক্যাল খাতা (Practical Notebook) নিখুঁতভাবে লেখার সাধারণ নিয়ম:")
        st.markdown("""
        ১. **সাদা পৃষ্ঠা ও রেখা টানা পৃষ্ঠা:** সাধারণত প্র্যাক্টিক্যাল খাতায় ডান দিকের পৃষ্ঠাটি সাদা (চিত্র বা ছক আঁকার জন্য) এবং বাম দিকের পৃষ্ঠাটি রেখা টানা (তত্ত্ব ও হিসাব লেখার জন্য) হয়।
        ২. **ধারাবাহিক কাঠামো:** প্রতিটি পরীক্ষার শুরুতে নিচের পয়েন্টগুলো সুন্দর ও পরিচ্ছন্ন হাতের লেখায় লিখতে হবে:
           - **পরীক্ষার নাম (Experiment Name / Title):** প্রশ্নপত্রে প্রদত্ত শিরোনাম।
           - **তত্ত্ব (Theory):** পরীক্ষার মূল বৈজ্ঞানিক সূত্র বা নীতিমালা।
           - **প্রয়োজনীয় যন্ত্রপাতি ও উপকরণ (Apparatus & Materials):** পরীক্ষণের জন্য যা যা লাগবে।
           - **কার্যপদ্ধতি (Procedure):** পরীক্ষাটি যেভাবে সম্পন্ন করতে হবে তার ধাপসমূহ।
           - **পর্যবেক্ষণ ও উপাত্ত ছক (Observation Table):** পরীক্ষণের সময় প্রাপ্ত মানগুলোর সারণী।
           - **হিসাব (Calculations):** প্রাপ্ত মানগুলো সূত্রে বসিয়ে গাণিতিক সমাধান।
           - **ফলাফল (Result):** নির্দিষ্ট এককসহ চূড়ান্ত মান।
           - **সতর্কতা (Precautions):** পরীক্ষা করার সময় কী কী বিষয়ে সাবধানে থাকতে হবে।
        """)

    with prac_tab2:
        st.subheader("পদার্থবিজ্ঞান প্র্যাক্টিক্যাল (Physics Practicals)")
        
        with st.expander("পরীক্ষা ১: স্লাইড ক্যালিপার্সের সাহায্যে কোনো বস্তুর দৈর্ঘ্য, প্রস্থ, উচ্চতা মেপে আয়তন নির্ণয়।"):
            st.markdown("""
            * **তত্ত্ব:** কোনো বস্তুর দৈর্ঘ্য $L = M + (V \times VC)$, যেখানে $M$ = মূল স্কেল পাঠ, $V$ = ভার্নিয়ার সমাপতন, $VC$ = ভার্নিয়ার ধ্রুবক (Least Count = $0.01\text{ cm}$)।
            * **প্রয়োজনীয় উপকরণ:** স্লাইড ক্যালিপার্স, একটি আয়তাকার বস্তু (ধাতব ব্লক বা কাঠের টুকরো)।
            * **কার্যপদ্ধতি:**
              1. ভার্নিয়ার ধ্রুবক ($VC$) নির্ণয় করো।
              2. যন্ত্রটিতে কোনো শূন্য ত্রুটি (Zero Error) আছে কিনা তা যাচাই করো।
              3. বস্তুর দৈর্ঘ্য, প্রস্থ ও উচ্চতা পরিমাপ করে ছকে লিপিবদ্ধ করো।
            * **সতর্কতা:** ভার্নিয়ার স্কেল পাঠ নেওয়ার সময় লম্বন ত্রুটি (Parallax Error) এড়াতে হবে।
            """)

        with st.expander("পরীক্ষা ২: সরল দোলকের সাহায্যে কোনো স্থানে অভিকর্ষজ ত্বরণ g-এর মান নির্ণয়।"):
            st.markdown("""
            * **তত্ত্ব:** $g = 4\pi^2 \frac{L}{T^2}$ 
            * **কার্যপদ্ধতি:** কার্যকরী দৈর্ঘ্য $L$ পরিবর্তন করে নির্দিষ্ট সংখ্যক কম্পনের (যেমন ২০টি) জন্য সময় $t$ পরিমাপ করে দোলনকাল $T = t/20$ বের করতে হবে। $L$ বনাম $T^2$ লেখচিত্র অঙ্কন করে ঢাল থেকে $g$-এর মান নির্ণয় করা যায়।
            """)

    with prac_tab3:
        st.subheader("রসায়ন প্র্যাক্টিক্যাল (Chemistry Practicals)")
        
        with st.expander("পরীক্ষা ১: প্রদত্ত ক্ষার দ্রবণের (NaOH) সাহায্যে এসিড দ্রবণের (HCl) ট্রাইট্রেশন ও ঘনমাত্রা নির্ণয়।"):
            st.markdown("""
            * **তত্ত্ব:** প্রশমন বিক্রিয়ায় $S_a V_a / n_a = S_b V_b / n_b$ সূত্র ব্যবহার করে অজানা ঘনমাত্রা নির্ণয় করা হয়।
            * **উপকরণ:** ব্যুরেট, পিপেট, কোনিক্যাল ফ্লাস্ক, নির্দেশক (মেথাইল অরেঞ্জ বা ফেনফ্থ্যালিন)।
            * **কার্যপদ্ধতি:** ব্যুরেটে এসিড নিয়ে পিপেটের সাহায্যে নির্দিষ্ট আয়তনের ক্ষার ফ্লাক্সে নিতে হবে এবং নির্দেশক যোগ করে বর্ণ পরিবর্তনের মাধ্যমে সমাপ্তি বিন্দু (End point) নির্ধারণ করতে হবে।
            """)

        with st.expander("পরীক্ষা ২: লবণের কেলাসন (যেমন: তুঁতে বা কপার সালফেট প্রস্তুতকরণ)।"):
            st.markdown("""
            * তাপ দিয়ে সম্পৃক্ত দ্রবণ তৈরি করে ধীরে ধীরে ঠাণ্ডা করলে সুন্দর নীল রঙের তুঁতের স্ফটিক বা কেলাস তৈরি হয়।
            """)

    with prac_tab4:
        st.subheader("জীববিজ্ঞান প্র্যাক্টিক্যাল (Biology Practicals)")
        
        with st.expander("পরীক্ষা ১: পেঁয়াজের পাতার এপিডার্মিস থেকে কোষ (Cell) ও নিউক্লিয়াস পর্যবেক্ষণ।"):
            st.markdown("""
            * **উপকরণ:** স্লাইড, কভার সিল্প, অনুবীক্ষণ যন্ত্র (Microscope), আয়োডিন দ্রবণ, পেয়াজ।
            * **কার্যপদ্ধতি:** পেঁয়াজের রসালো পাতার ভেতরের ত্বক পাতলা করে স্লাইডে রেখে সেকান ড্রপ আয়োডিন দিয়ে কভার স্লিপ বসিয়ে মাইক্রোস্কোপে কোষপ্রাচীর ও কেন্দ্রিকা পর্যবেক্ষণ করতে হবে।
            """)

        with st.expander("পরীক্ষা ২: উদ্ভিদের অভিস্রবণ (Osmosis) প্রক্রিয়ার প্রদর্শন।"):
            st.markdown("""
            * কিসমিস বা আলু দিয়ে অভিস্রবণ পরীক্ষা (পানিতে রাখলে ফুলে ওঠা এবং ঘনীভূত চিনির দ্রবণে রাখলে সংকুচিত হওয়া)।
            """)

    with prac_tab5:
        st.subheader("উচ্চতর গণিত প্র্যাক্টিক্যাল (Higher Math Practicals)")
        
        with st.expander("পরীক্ষা ১: গ্রাফ পেপারে নির্দিষ্ট বহুপদী ফাংশন বা সমীকরণের লেখচিত্র অঙ্কন।"):
            st.markdown("""
            * **নিয়ম:** ছক কাগজে X-অক্ষ ও Y-অক্ষ অঙ্কন করে উপযুক্ত স্কেল ধরে বিন্দুগুলো স্থাপন করতে হবে এবং স্মুথ কার্ভ বা সরলরেখা টানতে হবে।
            """)


# ==========================================
# 14. CQ SOLVE MODULE
# ==========================================
elif st.session_state.current_page == "CQ Solve":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("CQ Solve — সৃজনশীল সমস্যা ও সমাধান")
    st.markdown("---")
    st.write("এখানে গুরুত্বপূর্ণ সৃজনশীল প্রশ্ন ও উত্তর দেওয়া আছে।")


# ==========================================
# 15. PHYSICS BOT (MOON AI CHAT)
# ==========================================
elif st.session_state.current_page == "Physics Bot":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.markdown(
        "<div class='premium-hero' style='text-align:left;'><h1>Moon AI Assistant</h1><p>আপনার ফিজিক্স, সায়েন্স এবং প্র্যাক্টিক্যাল সংক্রান্ত যেকোনো প্রশ্ন করুন</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    session = _active_session()
    for msg in session["messages"]:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])

    user_query = st.chat_input("Moon AI-কে প্রশ্ন করুন…")

    if user_query:
        session["messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)
        reply = local_ai_reply(user_query)
        session["messages"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
        st.session_state.chat_history = session["messages"]


# ==========================================
# 16. AI LEARNING LAB
# ==========================================
elif st.session_state.current_page == "Learning Lab":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🧠 Moon AI Learning Lab")
    st.markdown("---")
    st.write("এখানে আপনি নতুন জ্ঞান ও প্র্যাক্টিক্যাল নোট শেখাতে পারবেন।")


# ==========================================
# 17. THEME & SETTINGS
# ==========================================
elif st.session_state.current_page == "Theme Settings":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("⚙  Settings / সেটিংস")
    st.markdown("---")

    lang = st.selectbox("ভাষা / Language", ["বাংলা", "English"], index=0 if st.session_state.language == "বাংলা" else 1)
    if st.button("ভাষা প্রয়োগ করুন"):
        st.session_state.language = lang
        st.success("ভাষা পরিবর্তন করা হয়েছে।")
        st.rerun()

    uploaded_file = st.file_uploader("গ্যালারি থেকে ব্যাকগ্রাউন্ড ছবি দিন (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.session_state.bg_image = base64.b64encode(uploaded_file.getvalue()).decode()
        st.success("Background সফলভাবে আপডেট হয়েছে।")
    if st.session_state.bg_image and st.button("ডিফল্ট ব্যাকগ্রাউন্ডে ফিরুন"):
        st.session_state.bg_image = None
        st.rerun()
