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
# 2. LOCAL AI MEMORY & BRAIN
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


def load_brain():
    try:
        if BRAIN_FILE.exists():
            data = json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
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
    info = (info or "").strip()
    question = (question or "").strip()
    answer = (answer or "").strip()
    explanation = (explanation or "").strip()
    if not info and not question:
        return False
    brain = load_brain()
    key = (question or info).casefold()
    for e in brain["entries"]:
        if (e.get("question") or e.get("info") or "").casefold() == key:
            e.update({"info": info or e.get("info", ""), "domain": domain, "question": question, "answer": answer, "explanation": explanation, "tags": tags or e.get("tags", [])})
            return save_brain(brain)
    brain["entries"].append({
        "info": info, "domain": domain or "general", "question": question,
        "answer": answer, "explanation": explanation, "tags": tags or [],
    })
    return save_brain(brain)


def extract_teach_command(text):
    m = re.match(r"^\s*(?:teach|learn)\s*#\(\s*(.*?)\s*\)\s*$", text, re.I | re.S)
    if not m:
        return None
    raw = m.group(1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if "=>" in parts[0]:
        q, a = parts[0].split("=>", 1)
        return {"info": "", "question": q.strip(), "answer": a.strip(), "explanation": parts[1] if len(parts) > 1 else "", "domain": parts[2] if len(parts) > 2 else "general"}
    return {"info": parts[0], "question": "", "answer": "", "explanation": "", "domain": parts[1] if len(parts) > 1 else "general"}


def brain_matches(query, limit=5):
    qwords = [w for w in re.findall(r'[\u0980-\u09FFA-Za-z0-9]+', query.casefold()) if len(w) > 2]
    results = []
    for e in load_brain().get("entries", []):
        hay = " ".join(str(e.get(k, "")) for k in ("info", "question", "answer", "explanation", "domain", "tags")).casefold()
        score = sum(1 for w in qwords if w in hay)
        if score:
            results.append((score, e))
    results.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in results[:limit]]


def brain_reply(query):
    hits = brain_matches(query)
    if not hits:
        return None
    blocks = []
    for e in hits:
        title = e.get("question") or e.get("info") or "শেখা তথ্য"
        body = e.get("answer") or e.get("info") or ""
        explanation = e.get("explanation")
        block = f"**{title}**\n\n{body}"
        if st.session_state.get("ai_explain", True) and explanation:
            block += f"\n\n**Moon AI ব্যাখ্যা:** {explanation}"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


# ==========================================
# 3. SAFE MATH CALCULATOR
# ==========================================
_ALLOWED_BIN_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod, ast.FloorDiv: op.floordiv,
}
_ALLOWED_UNARY_OPS = {ast.UAdd: op.pos, ast.USub: op.neg}

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
# 4. KNOWLEDGE & DATA BASES (CQ & PHYSICS)
# ==========================================
PHYSICS_KNOWLEDGE = [
    ("গতি", "গতি হলো সময়ের সাথে কোনো বস্তুর অবস্থানের পরিবর্তন।", "v = s/t"),
    ("বেগ", "বেগ হলো নির্দিষ্ট দিকে সরণের পরিবর্তনের হার।", "v = s/t"),
    ("ত্বরণ", "ত্বরণ হলো সময়ের সাথে বেগের পরিবর্তনের হার।", "a = (v-u)/t"),
    ("বল", "বল বস্তুর গতি বা আকার পরিবর্তন করতে পারে।", "F = ma"),
    ("নিউটন", "নিউটনের দ্বিতীয় সূত্র অনুযায়ী বল = ভর × ত্বরণ।", "F = ma"),
    ("ভরবেগ", "ভরবেগ হলো ভর ও বেগের গুণফল।", "p = mv"),
    ("কাজ", "বল প্রয়োগে বলের দিকে সরণ হলে কাজ সম্পন্ন হয়।", "W = Fs"),
    ("ক্ষমতা", "কাজ করার হারকে ক্ষমতা বলে।", "P = W/t"),
    ("গতিশক্তি", "গতিশীল বস্তুর শক্তিকে গতিশক্তি বলে।", "Ek = 1/2 mv²"),
    ("বিভবশক্তি", "উচ্চতার কারণে সঞ্চিত শক্তিকে মহাকর্ষীয় বিভবশক্তি বলে।", "Ep = mgh"),
    ("মহাকর্ষ", "পৃথিবীর কাছে অভিকর্ষজ ত্বরণ প্রায় 9.8 m/s²।", "g ≈ 9.8 m/s²"),
    ("চাপ", "একক ক্ষেত্রফলে লম্বভাবে ক্রিয়াশীল বলকে চাপ বলে।", "P = F/A"),
    ("ঘনত্ব", "একক আয়তনে পদার্থের ভরকে ঘনত্ব বলে।", "ρ = m/V"),
    ("ওহম", "নির্দিষ্ট তাপমাত্রায় পরিবাহীর তড়িৎ প্রবাহ বিভব পার্থক্যের সমানুপাতিক।", "V = IR"),
]

PHYSICS_PROBLEMS = [
    ("গতি", "একটি গাড়ি 20 s-এ 400 m অতিক্রম করল। গড় বেগ কত?", "v = s/t = 400/20 = 20 m/s।"),
    ("ত্বরণ", "একটি গাড়ির বেগ 5 s-এ 10 m/s থেকে 30 m/s হলো। ত্বরণ কত?", "a = (v-u)/t = (30-10)/5 = 4 m/s²।"),
    ("বল", "5 kg ভরের বস্তুকে 3 m/s² ত্বরণ দিতে কত বল লাগবে?", "F = ma = 5×3 = 15 N।"),
    ("ওজন", "10 kg ভরের বস্তুর ওজন পৃথিবীতে কত? g=9.8 m/s² ধরো।", "W = mg = 10×9.8 = 98 N।"),
]

CQ_PROBLEMS = [
    {'id': 1, 'chapter': 'পরিমাপ ও ভৌত রাশি', 'question': 'একটি ভার্নিয়ার ক্যালিপার্সে মূল স্কেল পাঠ 2.3 cm, ভার্নিয়ার সমাপতন 6 এবং least count 0.01 cm। মোট পাঠ কত?', 'answer': 'মোট পাঠ = MSR + VC×LC = 2.3 + 6×0.01 = 2.36 cm।', 'moon': 'Moon AI: প্রথমে মূল স্কেল পাঠ নাও, তারপর ভার্নিয়ার সমাপতনকে least count দিয়ে গুণ করে যোগ করো।'},
    {'id': 2, 'chapter': 'গতি', 'question': 'একটি গাড়ি প্রথম 10 s-এ 100 m এবং পরের 10 s-এ 200 m অতিক্রম করল। গড় দ্রুতি কত?', 'answer': 'মোট দূরত্ব = 300 m, মোট সময় = 20 s; গড় দ্রুতি = 15 m/s।', 'moon': 'Moon AI: গড় দ্রুতি বের করতে মোট দূরত্বকে মোট সময় দিয়ে ভাগ করতে হয়।'},
    {'id': 3, 'chapter': 'গতি', 'question': 'একটি বস্তু u=5 m/s বেগে চলল এবং a=2 m/s²। 6 s পরে সরণ কত?', 'answer': 's=ut+½at² = 5×6 + ½×2×36 = 66 m।', 'moon': 'Moon AI: ধ্রুব ত্বরণের ক্ষেত্রে প্রথমে প্রাথমিক বেগের সরণ এবং ত্বরণের জন্য অতিরিক্ত সরণ আলাদা করে যোগ করা যায়।'},
    {'id': 4, 'chapter': 'বল', 'question': '8 kg ভরের ব্লকে 30 N প্রয়োগ বল এবং 6 N ঘর্ষণ বিপরীত দিকে। ত্বরণ কত?', 'answer': 'নিট বল = 30−6 = 24 N; a = 24/8 = 3 m/s²।', 'moon': 'Moon AI: ত্বরণ নির্ধারণে প্রয়োগ বল নয়, সব বলের ভেক্টর যোগফল বা net force ব্যবহার করতে হয়।'},
    {'id': 5, 'chapter': 'কাজ ও শক্তি', 'question': '50 N বল 30° কোণে প্রয়োগ করে বাক্সকে 8 m সরানো হলো। কাজ কত?', 'answer': 'W = Fs cos30° = 50×8×0.866 ≈ 346.4 J।', 'moon': 'Moon AI: শুধু সরণের দিকে থাকা বলের উপাংশ কাজ করে; তাই cosθ ব্যবহার করতে হয়।'},
    {'id': 6, 'chapter': 'চাপ ও তরল', 'question': 'একটি 200 N বল 0.04 m² এলাকায় কাজ করছে। চাপ কত?', 'answer': 'P = F/A = 200/0.04 = 5000 Pa।', 'moon': 'Moon AI: ক্ষেত্রফল ছোট হলে একই বলের জন্য চাপ বেশি হয়।'},
    {'id': 7, 'chapter': 'চল তড়িৎ', 'question': '6 Ω ও 3 Ω রোধ সমান্তরালে যুক্ত। সমতুল্য রোধ কত?', 'answer': '1/R = 1/6 + 1/3 = 1/2 ⇒ R = 2 Ω।', 'moon': 'Moon AI: parallel circuit-এ reciprocal যোগ হয় এবং সমতুল্য রোধ সবসময় ক্ষুদ্রতম রোধের চেয়েও কম।'},
]

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

    if any(p in lower for p in ["তুমি কে", "তোমার নাম কি", "your name", "who are you"]):
        return "আমি Moon AI — বিজ্ঞান, গণিত ও প্র্যাক্টিক্যাল শেখার পার্সোনাল এআই সহকারী।"
    if looks_like_math(text):
        try:
            ans = safe_eval(text)
            return f"গাণিতিক ফলাফল: `{text}` = **{ans}**"
        except Exception:
            return "গাণিতিক সমীকরণটি সঠিক নয়।"
    learned_brain = brain_reply(text)
    if learned_brain:
        return learned_brain
    return f"আপনার প্রশ্ন: **{text}**\n\nপদার্থবিজ্ঞান, রসায়ন, জীববিজ্ঞান বা উচ্চতর গণিতের যেকোনো প্র্যাক্টিক্যাল বা তত্ত্বীয় সমস্যা সম্পর্কে বিস্তারিত জানতে নির্দিষ্ট মডিউলে নেভিগেট করুন অথবা সরাসরি জিজ্ঞেস করুন।"


# ==========================================
# 5. DYNAMIC CSS & THEME ENGINE (CLEAN & PREMIUM)
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
        background-color: rgba(15, 23, 42, 0.92) !important;
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
        border: 1px solid rgba(56, 189, 248, 0.22);
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

    /* Clean Hero Section without Black Artifact Patch */
    .premium-hero {{
        padding: 24px 28px; 
        border: 1px solid rgba(56,189,248,0.25); 
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(30,41,59,0.88) 0%, rgba(15,23,42,0.96) 100%);
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
# 6. TOP NAVIGATION & CHAT CONTROLS
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
# 7. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<div style='font-size:.82rem;color:#38BDF8;letter-spacing:.1em;text-transform:uppercase;padding:6px 2px 12px;font-weight:700;'>বিজ্ঞান ও প্র্যাক্টিক্যাল হাব</div>", unsafe_allow_html=True)

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
# 8. HOME SCREEN
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br>", unsafe_allow_html=True)
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
# 9. DANGER DASH 2D GAME
# ==========================================
elif st.session_state.current_page == "2D Physics Game":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Danger Dash — 2D Physics Game")
    st.caption("দৌড়ান, obstacle এড়িয়ে চলুন এবং coin সংগ্রহ করুন। Keyboard অথবা Touch Control ব্যবহার করুন।")
    st.markdown("---")

    danger_dash_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #08111f; color: #e2e8f0; font-family: Arial, sans-serif; text-align: center; overflow: hidden; user-select: none; }
    #gameWrap { width: 100%; max-width: 900px; margin: auto; }
    #hud { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 8px; padding: 10px; margin-bottom: 8px; background: #111c2e; border: 1px solid #263852; border-radius: 12px; font-weight: bold; color: #7dd3fc; }
    #game { width: 100%; max-width: 900px; height: auto; border: 2px solid #263852; border-radius: 14px; background: #101c2e; box-shadow: 0 10px 35px rgba(0,0,0,.45); touch-action: none; }
    #controls { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
    button { border: 1px solid rgba(125,211,252,.35); border-radius: 14px; padding: 12px 20px; font-weight: 800; cursor: pointer; background: linear-gradient(180deg,#38bdf8,#0ea5e9); color: #06101c; font-size: 14px; box-shadow: 0 8px 22px rgba(14,165,233,.20); }
    button:active { transform: scale(.96); }
    #hint { color: #94a3b8; font-size: 13px; margin-top: 8px; }
</style>
</head>
<body>
<div id="gameWrap">
    <div id="hud">
        <span>Score: <b id="score">0</b></span>
        <span>Coins: <b id="coins">0</b></span>
        <span>Lives: <b id="lives">3</b></span>
        <span>Speed: <b id="speed">1</b>x</span>
        <span>Best: <b id="best">0</b></span>
    </div>
    <div id="stage" style="position:relative;">
        <canvas id="game" width="900" height="500"></canvas>
        <div id="startScreen" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,.72);border-radius:14px;backdrop-filter:blur(5px);">
            <div style="padding:30px 34px;border:1px solid rgba(125,211,252,.35);border-radius:22px;background:rgba(15,23,42,.92);box-shadow:0 18px 50px rgba(0,0,0,.4);">
                <div style="font-size:14px;letter-spacing:4px;color:#7dd3fc;font-weight:700;">DANGER DASH</div>
                <div style="font-size:34px;font-weight:800;margin:8px 0 18px;">READY?</div>
                <button id="startBtn" style="min-width:210px;font-size:17px;">START GAME</button>
            </div>
        </div>
    </div>
    <div id="controls">
        <button id="jumpBtn">JUMP</button>
        <button id="duckBtn">DUCK</button>
        <button id="restartBtn">RESTART</button>
    </div>
    <div id="hint">Keyboard: SPACE / ↑ = Jump, ↓ = Duck. Mobile: নিচের বোতাম চাপুন।</div>
</div>
<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const W = canvas.width, H = canvas.height, groundY = 410;
let score = 0, coins = 0, lives = 3, speed = 5, frame = 0, running = false, gameOver = false;
let best = Number(localStorage.getItem("dangerDashBest") || 0);
document.getElementById("best").textContent = best;

const player = { x: 115, y: groundY - 74, w: 48, h: 74, vy: 0, jumping: false, ducking: false, invincible: 0, anim: 0 };
let obstacles = [], coinItems = [], particles = [], clouds = [], stars = [];

for (let i = 0; i < 18; i++) stars.push({ x: Math.random() * W, y: Math.random() * 240, r: Math.random() * 2 + 1 });
for (let i = 0; i < 6; i++) clouds.push({ x: Math.random() * W, y: 55 + Math.random() * 120, w: 60 + Math.random() * 70, s: .2 + Math.random() * .35 });

function resetGame() {
    score = 0; coins = 0; lives = 3; speed = 5; frame = 0; running = false; gameOver = false;
    document.getElementById("startScreen").style.display = "flex";
    player.y = groundY - 74; player.vy = 0; player.jumping = false; player.ducking = false; player.invincible = 0;
    obstacles = []; coinItems = []; particles = [];
    updateHud();
}
function startGame() { running = true; gameOver = false; document.getElementById("startScreen").style.display = "none"; }
function updateHud() {
    document.getElementById("score").textContent = Math.floor(score);
    document.getElementById("coins").textContent = coins;
    document.getElementById("lives").textContent = lives;
    document.getElementById("speed").textContent = (speed / 5).toFixed(1);
}
function jump() { if (!gameOver && !player.jumping) { player.vy = -14; player.jumping = true; } }
function duckStart() { if (!gameOver) player.ducking = true; }
function duckEnd() { player.ducking = false; }

function spawnObstacle() {
    const types = ["rock", "spike", "box"];
    const type = types[Math.floor(Math.random() * types.length)];
    let h = type === "spike" ? 48 : 58, w = type === "rock" ? 52 : 44;
    obstacles.push({ x: W + 40, y: groundY - h, w, h, type });
}
function spawnCoin() { coinItems.push({ x: W + 30, y: groundY - 90 - Math.random() * 100, r: 11, spin: 0 }); }

function rectHit(a, b) { return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y; }
function playerBox() {
    if (player.ducking && !player.jumping) return { x: player.x + 5, y: groundY - 40, w: 58, h: 38 };
    return { x: player.x + 5, y: player.y + 5, w: 38, h: 64 };
}
function hurt() {
    if (player.invincible > 0) return;
    lives--; player.invincible = 90;
    if (lives <= 0) { gameOver = true; running = false; best = Math.max(best, Math.floor(score)); localStorage.setItem("dangerDashBest", best); }
    updateHud();
}

function update() {
    if (!running) return;
    frame++; score += 0.12 * (speed / 5);
    if (frame % 800 === 0) speed += .7;
    if (frame % Math.max(55, Math.floor(105 - speed * 5)) === 0) spawnObstacle();
    if (frame % 80 === 0 && Math.random() < .8) spawnCoin();

    player.vy += .65; player.y += player.vy;
    if (player.y >= groundY - 74) { player.y = groundY - 74; player.vy = 0; player.jumping = false; }
    if (player.invincible > 0) player.invincible--;
    player.anim += .22;

    for (let i = obstacles.length - 1; i >= 0; i--) {
        let o = obstacles[i]; o.x -= speed;
        if (rectHit(playerBox(), o)) { hurt(); obstacles.splice(i, 1); continue; }
        if (o.x + o.w < 0) obstacles.splice(i, 1);
    }
    for (let i = coinItems.length - 1; i >= 0; i--) {
        let c = coinItems[i]; c.x -= speed;
        let p = playerBox(), dx = (p.x + p.w / 2) - c.x, dy = (p.y + p.h / 2) - c.y;
        if (Math.sqrt(dx*dx + dy*dy) < 34) { coins++; score += 25; coinItems.splice(i, 1); continue; }
        if (c.x < -30) coinItems.splice(i, 1);
    }
    updateHud();
}

function draw() {
    ctx.fillStyle = "#091b36"; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "#0b1220"; ctx.fillRect(0, groundY, W, H - groundY);
    ctx.strokeStyle = "#38bdf8"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, groundY); ctx.lineTo(W, groundY); ctx.stroke();

    // Draw Player
    ctx.fillStyle = "#38bdf8"; ctx.fillRect(player.x, player.y, player.w, player.h);

    // Draw Obstacles
    ctx.fillStyle = "#ef4444";
    for (let o of obstacles) ctx.fillRect(o.x, o.y, o.w, o.h);

    // Draw Coins
    ctx.fillStyle = "#facc15";
    for (let c of coinItems) { ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI*2); ctx.fill(); }

    if (gameOver) {
        ctx.fillStyle = "rgba(2,6,23,.8)"; ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = "#fb7185"; ctx.font = "bold 40px Arial"; ctx.fillText("GAME OVER", W/2 - 120, H/2);
    }
}

function loop() { update(); draw(); requestAnimationFrame(loop); }
document.addEventListener("keydown", (e) => { if (e.code === "Space" || e.code === "ArrowUp") jump(); if (e.code === "ArrowDown") duckStart(); });
document.addEventListener("keyup", (e) => { if (e.code === "ArrowDown") duckEnd(); });
document.getElementById("jumpBtn").addEventListener("click", jump);
document.getElementById("duckBtn").addEventListener("touchstart", duckStart);
document.getElementById("duckBtn").addEventListener("touchend", duckEnd);
document.getElementById("restartBtn").addEventListener("click", resetGame);
document.getElementById("startBtn").addEventListener("click", startGame);
resetGame(); loop();
</script>
</body>
</html>
"""
    components.html(danger_dash_html, height=650, scrolling=False)


# ==========================================
# 10. DEEP ANALYSIS MODULE
# ==========================================
elif st.session_state.current_page == "Deep Analysis":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("ডিপ এনালাইসিস — Critical Physics Lab")
    st.caption("বাস্তব ঘটনা, ধারণাগত ফাঁদ, কারণ-ফল, সূত্র নির্বাচন এবং পরীক্ষামূলক ব্যাখ্যা।")
    st.markdown("---")

    critical_topics = [
        ("01 · কেন ভারী ও হালকা বস্তু vacuum-এ একই ত্বরণে পড়ে?", "বায়ুর বাধা না থাকলে সব বস্তুর ওপর মহাকর্ষীয় বল F=mg এবং a=F/m=g; ভর কেটে যায়। তাই একই স্থানে মুক্তপতনের ত্বরণ প্রায় একই। বাস্তবে পালক ও পাথরের পার্থক্য air resistance-এর কারণে।"),
        ("02 · গাড়ি হঠাৎ ব্রেক করলে যাত্রী সামনে যায় কেন?", "নিউটনের প্রথম সূত্র বা জড়তার কারণে শরীর আগের বেগ ধরে রাখতে চায়। গাড়ি থামলেও seat belt ছাড়া শরীর সামনে চলতে থাকে। Seat belt বাহ্যিক বল দিয়ে শরীরকে নিরাপদে থামায়।"),
        ("03 · ঘর্ষণ সবসময় খারাপ নয় কেন?", "হাঁটা, গাড়ির tyre grip, ব্রেকিং—সবই friction-এর সাহায্যে সম্ভব। আবার friction শক্তি নষ্ট করে ও তাপ উৎপন্ন করে। তাই friction পরিস্থিতিভেদে উপকারী বা ক্ষতিকর।"),
        ("04 · জাহাজে steel ব্যবহার করেও কেন ভাসে?", "ভাসার সিদ্ধান্ত শুধু steel-এর ঘনত্ব দিয়ে নয়; পুরো জাহাজের average density এবং displaced water-এর ওজন দিয়ে হয়। Hollow structure average density কমায়।"),
        ("05 · প্রেসার কুকারে রান্না দ্রুত হয় কেন?", "চাপ বাড়লে পানির স্ফুটনাঙ্ক বাড়ে। ফলে পানি 100°C-এর বেশি তাপমাত্রায় তরল থাকতে পারে এবং খাবারে বেশি তাপ দ্রুত পৌঁছায়।"),
        ("06 · পাহাড়ে রান্না করতে সময় বেশি লাগে কেন?", "উচ্চতায় atmospheric pressure কম, তাই পানির boiling point কমে। ফলে পানি কম তাপমাত্রায় ফুটে এবং রান্নার জন্য প্রয়োজনীয় তাপমাত্রা কম থাকে।"),
        ("07 · ফ্রিজের পেছনে ফাঁকা জায়গা রাখা হয় কেন?", "Condenser coil-কে তাপ বাইরে ছাড়তে হয়। চারপাশে বাতাস চলাচল করলে convection ও heat transfer বাড়ে। দেয়ালের সঙ্গে ঠেসে দিলে efficiency কমে।"),
        ("08 · কালো বস্তু গরম ও শীতল দুটোই দ্রুত কেন?", "কালো/ম্যাট পৃষ্ঠ radiation ভালোভাবে শোষণ ও নির্গত করে। তাই একই পরিবেশে heating ও cooling—দুই প্রক্রিয়াই তুলনামূলক দ্রুত হতে পারে।"),
        ("09 · বজ্রপাতের আলো আগে এবং শব্দ পরে আসে কেন?", "আলোর বেগ প্রায় 3×10^8 m/s, শব্দের বেগ প্রায় 340 m/s। তাই একই দূরত্বে আলো চোখে প্রায় সঙ্গে সঙ্গে পৌঁছে, শব্দ পরে আসে।"),
        ("10 · ডপলার প্রভাব কীভাবে ambulance-এর siren বদলে শোনায়?", "উৎস কাছে এলে wavefront-এর ব্যবধান কমে observed frequency বাড়ে; দূরে গেলে ব্যবধান বাড়ে এবং frequency কমে। তাই pitch পরিবর্তিত শোনা যায়।"),
        ("11 · বাদুড় চোখ ছাড়া কীভাবে সামনে এগিয়ে চলে?", "উচ্চ কম্পাঙ্কের শব্দোত্তর তরঙ্গ (Ultrasonic sound) ছেড়ে প্রতিধ্বনি শুনে বাধা ও শিকারের অবস্থান নিখুঁতভাবে নির্ধারণ করে।"),
        ("12 · নদীর পানির চেয়ে সমুদ্রের পানিতে সাঁতার কাটা সহজ কেন?", "সমুদ্রের পানিতে প্রচুর লবণ দ্রবীভূত থাকায় এর ঘনত্ব বেশি। ফলে সমুদ্রের পানি সাঁতারুর ওপর বেশি উর্ধ্বমুখী প্লবতা বল প্রয়োগ করে।"),
        ("13 · ইটের ওপর হাঁটার চেয়ে ভাঙা ইটের ওপর হাঁটা কষ্টদায়ক কেন?", "চাপ P = F/A। ভাঙা ইটের ধারালো কোণার ক্ষেত্রফল (A) অনেক কম হওয়ায় পায়ের তলায় প্রয়োগকৃত চাপ বহুগুণ বেড়ে যায়।"),
        ("14 · শীতের দিনে বিদ্যুতের তার টানটান হয়ে ছিঁড়ে যায় কেন?", "তাপমাত্রার কমার কারণে তারে তাপীয় সংকোচন ঘটে। সংকুচিত হয়ে তার দৈর্ঘ্য ছোট হতে চাওয়ায় টান বল বেড়ে ছিঁড়ে যায়।"),
        ("15 · শীতের দিনে ভেজা কাপড় দ্রুত শুকায় কেন?", "শীতকালে বাতাসে আপেক্ষিক আর্দ্রতা অত্যন্ত কম থাকায় বাতাস শুষ্ক থাকে। শুষ্ক বাতাস কাপড়ের পানি দ্রুত বাষ্পীভূত করে।"),
    ]
    for title, explanation in critical_topics:
        with st.expander(title):
            st.write(explanation)
            st.info("Moon AI বিশ্লেষণ: কারণ → সূত্র/নীতি → বাস্তব ফল—এই তিন ধাপে বিষয়টি ভাঙলে ধারণাটি পরিষ্কার হয়।")


# ==========================================
# 11. NCTB CLASS 9-10 PHYSICS CURRICULUM
# ==========================================
elif st.session_state.current_page == "NCTB Curriculum":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("৯ম-১০ম শ্রেণি পদার্থবিজ্ঞান কারিকুলাম (NCTB)")
    st.markdown("---")

    chapters = [
        ("১. ভৌত রাশি ও পরিমাপ", "রাশি, পরিমাপের একক, মাত্রা, ভার্নিয়ার স্কেল, স্লাইড ক্যালিপার্স।", r"L = M + (V \times VC)"),
        ("২. গতি (Motion)", "দূরত্ব, সরণ, বেগ, ত্বরণ, গতির সমীকরণ ও পড়ন্ত বস্তুর সূত্র।", r"v = u + at, \quad s = ut + \frac{1}{2}at^2"),
        ("৩. বল (Force)", "নিউটন গতির ৩টি সূত্র, ভরবেগ, মহাকর্ষ বল ও ঘর্ষণ বল।", r"F = ma, \quad p = mv"),
        ("৪. কাজ, ক্ষমতা ও শক্তি", "কাজ, গতিশক্তি, বিভবশক্তি, ক্ষমতার হিসাব ও শক্তির সংরক্ষণশীলতা।", r"W = F \cdot s, \quad E_k = \frac{1}{2}mv^2"),
        ("৫. পদার্থের অবস্থা ও চাপ", "চাপ, ঘনত্ব, প্যাসকেলের সূত্র, আর্কিমিডিসের নীতি ও প্লবতা।", r"P = \frac{F}{A}, \quad P = h\rho g"),
        ("৬. বস্তুর ওপর তাপের প্রভাব", "তাপ ও তাপমাত্রা, দৈর্ঘ্য সম্প্রসারণ, আপেক্ষিক তাপ ও ক্যালরিমিতি।", r"Q = ms\Delta T"),
        ("৭. তরঙ্গ ও শব্দ", "পর্যায়বৃত্ত গতি, অনুদৈর্ঘ্য ও অনুপ্রস্থ তরঙ্গ, শব্দের বেগ ও প্রতিধ্বনি।", r"v = f\lambda"),
        ("৮. আলোর প্রতিফলন", "আয়না/দর্পণ, সমতল ও গোলীয় দর্পণ, বিম্ব গঠন ও বিবর্ধন।", r"\frac{1}{f} = \frac{1}{u} + \frac{1}{v}"),
        ("৯. আলোর প্রতিসরণ", "প্রতিসরণাঙ্ক, সংকট কোণ, পূর্ণ অভ্যন্তরীণ প্রতিফলন ও লেন্স।", r"\eta = \frac{\sin i}{\sin r}"),
        ("১০. স্থির তড়িৎ", "আধান, কুলম্বের সূত্র, তড়িৎ ক্ষেত্র ও তড়িৎ বিভব।", r"F = k \frac{q_1 q_2}{r^2}"),
        ("১১. চল তড়িৎ", "ওহমের সূত্র, রোধ, শ্রেণী ও সমান্তরাল সার্কিট এবং ক্ষমতা।", r"V = IR, \quad P = VI"),
        ("১২. তড়িৎ প্রবাহের চৌম্বক ক্রিয়া", "সোলেনয়েড, তড়িচ্চুম্বক, তাড়িতচৌম্বক আবেশ ও ট্রান্সফরমার।", r"\frac{V_p}{V_s} = \frac{N_p}{N_s}"),
        ("১৩. আধুনিক পদার্থবিজ্ঞান ও ইলেকট্রনিক্স", "তেজস্ক্রিয়তা, এক্স-রে, সেমিকন্ডাক্টর, ডায়োড ও ট্রানজিস্টর।", r"E = mc^2"),
        ("১৪. জীবন বাঁচাতে পদার্থবিজ্ঞান", "ইসিজি, এক্স-রে, আল্ট্রাসোনোগ্রাফি, সিটি স্ক্যান ও এমআরআই।", "মেডিকেল ফিজিক্স ও ডায়াগনস্টিক প্রয়োগ।"),
    ]

    for chap_title, chap_desc, formula in chapters:
        with st.expander(f"{chap_title}"):
            st.write(f"**মূল বিষয়বস্তু:** {chap_desc}")
            if formula != "মেডিকেল ফিজিক্স ও ডায়াগনস্টিক প্রয়োগ।":
                st.latex(formula)


# ==========================================
# 12. SSC PRACTICAL LAB (NEW FEATURE)
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
        st.subheader("প্র্যাক্টিক্যাল খাতা (Practical Notebook) নিখুঁতভাবে লেখার নিয়ম:")
        st.markdown("""
        ১. **সাদা পৃষ্ঠা ও রেখা টানা পৃষ্ঠা:** সাধারণত খাতায় ডান দিকের সাদা পৃষ্ঠায় চিত্র, ছক ও গ্রাফ এবং বাম দিকের রেখা টানা পৃষ্ঠায় তত্ত্ব ও হিসাব লিখতে হয়।
        ২. **ধারাবাহিক পয়েন্টসমূহ:**
           - **পরীক্ষার নাম (Experiment Title):** বোর্ডের প্রশ্নানুযায়ী শিরোনাম।
           - **মূল তত্ত্ব (Theory):** প্রয়োজনীয় বৈজ্ঞানিক সূত্র ও মূলনীতি।
           - **যন্ত্রপাতি ও উপকরণ (Apparatus):** যা যা প্রয়োজন।
           - **কার্যপদ্ধতি (Procedure):** ধাপে ধাপে কাজের বিবরণ।
           - **পর্যবেক্ষণ ছক (Observation Table):** প্রাপ্ত উপাত্তের ছক।
           - **গণনা ও হিসাব (Calculations):** মান সূত্রে বসিয়ে সঠিক এককে হিসেব।
           - **ফলাফল (Result):** চূড়ান্ত মান।
           - **সতর্কতা (Precautions):** ৩টি মূল সতর্কতা।
        """)

    with prac_tab2:
        st.subheader("পদার্থবিজ্ঞান প্র্যাক্টিক্যাল (Physics Practicals)")
        
        with st.expander("পরীক্ষা ১: স্লাইড ক্যালিপার্সের সাহায্যে কোনো বস্তুর দৈর্ঘ্য, প্রস্থ ও আয়তন নির্ণয়।"):
            st.markdown("""
            * **তত্ত্ব:** $L = M + (V \times VC)$
            * **প্রয়োজনীয় উপকরণ:** স্লাইড ক্যালিপার্স, ধাতব বা কাঠের ব্লক।
            * **হিসাব:** $VC = \frac{\text{মূল স্কেলের ১ ক্ষুদ্রতম ঘর}}{\text{ভার্নিয়ার স্কেলের মোট ভাগ}}$
            * **সতর্কতা:** লম্বন ত্রুটি পরিহার করতে হবে এবং শূন্য ত্রুটি সংশোধন করতে হবে।
            """)

        with st.expander("পরীক্ষা ২: স্ক্রু গজ দিয়ে তারের প্রস্থচ্ছেদ ও আয়তন নির্ণয়।"):
            st.markdown("""
            * **তত্ত্ব:** $d = LSR + (CR \times LC)$
            * **প্রস্থচ্ছেদের ক্ষেত্রফল:** $A = \frac{\pi d^2}{4}$
            """)

    with prac_tab3:
        st.subheader("রসায়ন প্র্যাক্টিক্যাল (Chemistry Practicals)")
        
        with st.expander("পরীক্ষা ১: আণবিক ভর ও প্রশমন ট্রাইট্রেশন (NaOH + HCl)।"):
            st.markdown("""
            * **তত্ত্ব:** $S_a V_a = S_b V_b$
            * **উপকরণ:** ব্যুরেট, পিপেট, ফেনফ্থ্যালিন নির্দেশক, কোনিক্যাল ফ্লাস্ক।
            * **ফলাফল:** বর্ণ পরিবর্তনের শেষ বিন্দু (End point) চিহ্নিত করে ঘনমাত্রা বের করা।
            """)

    with prac_tab4:
        st.subheader("জীববিজ্ঞান প্র্যাক্টিক্যাল (Biology Practicals)")
        
        with st.expander("পরীক্ষা ১: অনুবীক্ষণ যন্ত্রে পেঁয়াজের কোষ ও নিউক্লিয়াস পর্যবেক্ষণ।"):
            st.markdown("""
            * **উপকরণ:** স্লাইড, আয়োডিন দ্রবণ, মাইক্রোস্কোপ, কভার স্লিপ।
            * **চিত্র নিয়ম:** পেনসিল দিয়ে পরিষ্কার সাইটোপ্লাজম ও নিউক্লিয়াস চিহ্নিত করতে হবে।
            """)

    with prac_tab5:
        st.subheader("উচ্চতর গণিত প্র্যাক্টিক্যাল (Higher Math Practicals)")
        
        with st.expander("পরীক্ষা ১: গ্রাফ পেপারে দ্বিঘাত সমীকরণ ও বহুপদী ফাংশনের লেখচিত্র অঙ্কন।"):
            st.markdown("""
            * **নিয়ম:** ছক কাগজে X ও Y অক্ষ ধরে বিন্দু পাতন করে মসৃণ বক্ররেখা আঁকতে হবে।
            """)


# ==========================================
# 13. CQ SOLVE MODULE
# ==========================================
elif st.session_state.current_page == "CQ Solve":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("CQ Solve — সৃজনশীল সমস্যা ও সমাধান")
    st.caption("গুরুত্বপূর্ণ সৃজনশীল প্রশ্ন, উত্তর এবং Moon AI ব্যাখ্যা।")
    st.markdown("---")

    chapters = ["সব অধ্যায়"] + sorted({x["chapter"] for x in CQ_PROBLEMS})
    selected = st.selectbox("অধ্যায় বেছে নিন", chapters)
    filtered = CQ_PROBLEMS if selected == "সব অধ্যায়" else [x for x in CQ_PROBLEMS if x["chapter"] == selected]

    for item in filtered:
        with st.expander(f"CQ {item['id']:02d} · {item['chapter']} · {item['question']}"):
            st.markdown("### প্রশ্ন")
            st.write(item["question"])
            st.markdown("### সঠিক সমাধান")
            st.success(item["answer"])
            st.markdown("### 🧠 Moon AI ব্যাখ্যা")
            st.info(item["moon"])


# ==========================================
# 14. BOT CHAT MODULE
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
# 15. AI LEARNING LAB
# ==========================================
elif st.session_state.current_page == "Learning Lab":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🧠 Moon AI Learning Lab")
    st.markdown("---")
    st.write("এখানে আপনি নতুন জ্ঞান ও প্র্যাক্টিক্যাল নোট দ্রুত শেখাতে পারবেন।")
    fast = st.text_input("Learning command", placeholder="if #(তথ্য) save")
    if st.button("Moon AI-কে শেখান"):
        if extract_save_command(fast):
            ok = moon_learn(extract_save_command(fast), domain="general")
            st.success("Moon AI শিখেছে।" if ok else "সংরক্ষণ ব্যর্থ হয়েছে।")


# ==========================================
# 16. THEME & SETTINGS
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

