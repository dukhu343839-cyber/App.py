import base64
import ast
import json
import math
import operator as op
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="Physics Core & Analysis Engine",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "bg_image" not in st.session_state:
    st.session_state.bg_image = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": (
            "হ্যালো। আমি Moon AI — Physics শেখা, হিসাব এবং সমস্যা সমাধানে সাহায্য করতে পারি।"
        ),
    }]


# ==========================================
# 2. LOCAL AI MEMORY
# ==========================================
MEMORY_FILE = Path("moon_ai_knowledge.json")


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
    """Persist learned data as knowledge, never as executable code."""
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
    """
    Supported:
      if #(আমার নাম মেরেয়ো) save
      if #(I like physics) save
    """
    import re

    pattern = re.compile(
        r"^\s*if\s*#\(\s*(.*?)\s*\)\s*save\s*$",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.match(text)
    return match.group(1).strip() if match else None


# ==========================================
# 3. SAFE CALCULATOR
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

        if isinstance(node, ast.Constant) and isinstance(
            node.value, (int, float)
        ):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
            left = evaluate(node.left)
            right = evaluate(node.right)
            return _ALLOWED_BIN_OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
            return _ALLOWED_UNARY_OPS[type(node.op)](evaluate(node.operand))

        raise ValueError("Unsupported expression")

    result = evaluate(tree)
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Invalid result")
    return result


def looks_like_math(text):
    text = text.strip()
    return bool(text) and all(
        ch in "0123456789.+-*/()% \t" for ch in text
    ) and any(ch.isdigit() for ch in text)


# ==========================================
# 4. SMALL LOCAL AI ENGINE
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
    ("প্লবতা", "তরল বা গ্যাস কোনো নিমজ্জিত বস্তুর ওপর ঊর্ধ্বমুখী বল প্রয়োগ করে।", "Fb = ρVg"),
    ("তাপ", "তাপমাত্রার পার্থক্যের কারণে এক বস্তু থেকে অন্য বস্তুর শক্তি স্থানান্তরকে তাপ বলে।", "Q = mcΔT"),
    ("তরঙ্গ", "তরঙ্গ শক্তি বহন করে কিন্তু মাধ্যমের কণাকে স্থায়ীভাবে স্থানান্তর করে না।", "v = fλ"),
    ("শব্দ", "শব্দ একটি যান্ত্রিক তরঙ্গ; শূন্যস্থানে শব্দ চলতে পারে না।", "v = fλ"),
    ("আলো", "আলো তড়িৎচুম্বকীয় তরঙ্গ এবং শূন্যস্থানে প্রায় 3×10⁸ m/s বেগে চলে।", "c ≈ 3×10⁸ m/s"),
    ("প্রতিফলন", "আলো কোনো পৃষ্ঠে পড়ে একই মাধ্যমে ফিরে এলে তাকে প্রতিফলন বলে।", "i = r"),
    ("প্রতিসরণ", "আলো এক মাধ্যম থেকে অন্য মাধ্যমে গেলে বেগ ও দিক পরিবর্তনের ঘটনাকে প্রতিসরণ বলে।", "n = sin i / sin r"),
    ("ওহম", "নির্দিষ্ট তাপমাত্রায় রোধ অপরিবর্তিত থাকলে বিভব পার্থক্য ও তড়িৎ প্রবাহ সমানুপাতিক।", "V = IR"),
    ("বিদ্যুৎ", "তড়িৎ প্রবাহ হলো আধান প্রবাহের হার।", "I = Q/t"),
    ("রোধ", "রোধ তড়িৎ প্রবাহের বিরোধিতা করে।", "R = V/I"),
]

PHYSICS_PROBLEMS = [
    ("গতি", "একটি গাড়ি 20 s-এ 400 m অতিক্রম করল। গড় বেগ কত?", "v = s/t = 400/20 = 20 m/s। তাই উত্তর 20 m/s।"),
    ("ত্বরণ", "একটি গাড়ির বেগ 5 s-এ 10 m/s থেকে 30 m/s হলো। ত্বরণ কত?", "a = (v-u)/t = (30-10)/5 = 4 m/s²।"),
    ("বল", "5 kg ভরের বস্তুকে 3 m/s² ত্বরণ দিতে কত বল লাগবে?", "F = ma = 5×3 = 15 N।"),
    ("ওজন", "10 kg ভরের বস্তুর ওজন পৃথিবীতে কত? g=9.8 m/s² ধরো।", "W = mg = 10×9.8 = 98 N।"),
    ("কাজ", "20 N বল দিয়ে একটি বাক্সকে 5 m সরানো হলো। কাজ কত?", "W = Fs = 20×5 = 100 J।"),
    ("ক্ষমতা", "একটি যন্ত্র 600 J কাজ 20 s-এ করে। ক্ষমতা কত?", "P = W/t = 600/20 = 30 W।"),
    ("গতিশক্তি", "2 kg ভরের বস্তু 10 m/s বেগে চলছে। গতিশক্তি কত?", "Ek = 1/2 mv² = 1/2×2×100 = 100 J।"),
    ("বিভবশক্তি", "2 kg বস্তু 5 m উচ্চতায় আছে। g=9.8 m/s² হলে Ep কত?", "Ep = mgh = 2×9.8×5 = 98 J।"),
    ("চাপ", "100 N বল 2 m² ক্ষেত্রফলে প্রয়োগ করা হলো। চাপ কত?", "P = F/A = 100/2 = 50 Pa।"),
    ("ঘনত্ব", "একটি বস্তুর ভর 600 g এবং আয়তন 200 cm³। ঘনত্ব কত?", "ρ = m/V = 600/200 = 3 g/cm³।"),
    ("তরঙ্গ", "কম্পাঙ্ক 50 Hz ও তরঙ্গদৈর্ঘ্য 2 m হলে তরঙ্গের বেগ কত?", "v = fλ = 50×2 = 100 m/s।"),
    ("বিদ্যুৎ", "12 V বিভব পার্থক্যে 4 Ω রোধে প্রবাহ কত?", "I = V/R = 12/4 = 3 A।"),
    ("বিদ্যুৎ ক্ষমতা", "220 V লাইনে 2 A প্রবাহ হলে ক্ষমতা কত?", "P = VI = 220×2 = 440 W।"),
    ("মুক্তপতন", "স্থির অবস্থা থেকে 20 m নিচে পড়লে g=9.8 m/s² ধরে শেষ বেগ কত?", "v² = u²+2gh = 392; তাই v ≈ 19.8 m/s।"),
    ("তরলের চাপ", "তরলের গভীরতা বাড়লে চাপ কেন বাড়ে?", "P = ρgh; ρ ও g ধ্রুব হলে h বাড়ার সাথে চাপও বাড়ে।"),
]

ALIASES = {"force":"বল", "motion":"গতি", "velocity":"বেগ", "acceleration":"ত্বরণ", "pressure":"চাপ", "density":"ঘনত্ব", "gravity":"মহাকর্ষ", "work":"কাজ", "power":"ক্ষমতা", "energy":"শক্তি", "wave":"তরঙ্গ", "sound":"শব্দ", "light":"আলো", "reflection":"প্রতিফলন", "refraction":"প্রতিসরণ", "ohm":"ওহম", "electricity":"বিদ্যুৎ", "resistance":"রোধ"}

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

    learned = extract_save_command(text)
    if learned is not None:
        return "শেখা সম্পন্ন হয়েছে।" if save_memory_item(learned) else "তথ্যটি শেখানো যায়নি।"

    if any(p in lower for p in ["তোমার নির্মাতা", "নির্মাতা", "কে বানিয়েছে", "কে তৈরি করেছে", "creator", "maker", "who created you", "who made you"]):
        return "আমি moo.ai-এর দ্বারা নির্মিত।"
    if any(p in lower for p in ["তুমি কে", "তোমার নাম কি", "তোমার নাম কী", "who are you", "your name"]):
        return "আমি Moon AI — এই অ্যাপের ভিতরে চলা একটি ছোট local learning AI।"
    if any(p in lower for p in ["কি শিখেছ", "কী শিখেছ", "কি কি শিখেছ", "what did you learn", "learned"]):
        if not knowledge:
            return "এখনও কোনো নতুন তথ্য শেখানো হয়নি।"
        return "আমি যে তথ্যগুলো শিখেছি:\n\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(knowledge))
    if any(p in lower for p in ["সব শেখা মুছে", "সব শেখানো মুছে", "forget everything", "reset learning"]):
        delete_all_memory()
        return "শেখা তথ্যগুলো পরিষ্কার করা হয়েছে।"
    if any(p in lower for p in ["hi", "hello", "hey", "হাই", "হ্যালো", "আসসালামু আলাইকুম", "কেমন আছো", "কেমন আছেন"]):
        return "হ্যালো। আমি Moon AI। Physics, calculation এবং শেখার প্রশ্ন করতে পারো।"
    if looks_like_math(text):
        try:
            ans = safe_eval(text)
            return f"ফলাফল: `{text}` = **{ans}**"
        except Exception:
            return "গাণিতিক expression-টি সঠিক নয়। যেমন: `250*9.8`"
    for title, question, solution in PHYSICS_PROBLEMS:
        if title.lower() in lower and any(x in lower for x in ["সমস্যা", "problem", "solve", "সমাধান", "উদাহরণ"]):
            return f"**{title} সমস্যা**\n\nপ্রশ্ন: {question}\n\nসমাধান: {solution}"
    for key, explanation, formula in PHYSICS_KNOWLEDGE:
        if key.lower() in lower:
            return f"**{key}**\n\n{explanation}\n\nসূত্র: `{formula}`"
    for alias, key in ALIASES.items():
        if alias in lower:
            for k, explanation, formula in PHYSICS_KNOWLEDGE:
                if k == key:
                    return f"**{k}**\n\n{explanation}\n\nসূত্র: `{formula}`"
    learned_matches = find_learning_matches(text, knowledge)
    if learned_matches:
        return "আমি শেখা তথ্য থেকে যা মিল পাচ্ছি:\n\n" + "\n".join(f"- {x}" for x in learned_matches)
    return f"তোমার প্রশ্ন: **{text}**\n\nআমি Moon AI হিসেবে offline/localভাবে কাজ করছি। Physics-এর ধারণা, সূত্র, গাণিতিক হিসাব এবং উদাহরণ-ভিত্তিক সমস্যা সমাধান করতে পারি। প্রশ্নটি একটু নির্দিষ্ট করে বললে ধাপে ধাপে সমাধান দেব।"


# ==========================================
# 5. DYNAMIC CSS & THEME ENGINE
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
        background-color: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(8px);
    }}
    """

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Hind Siliguri', 'Inter', -apple-system, sans-serif;
        background-color: #0F172A;
        color: #E2E8F0;
    }}

    {bg_css}

    .option-card {{
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}

    .stButton > button {{
        width: 100%;
        border-radius: 10px;
        padding: 16px;
        font-size: 1.1rem;
        font-weight: 600;
        background-color: #1E293B;
        color: #38BDF8;
        border: 1px solid #334155;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background-color: #38BDF8;
        color: #0F172A;
        border-color: #38BDF8;
    }}

    div[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #07111f 0%, #0b1730 100%);
        border-right: 1px solid rgba(56,189,248,.18);
    }}
    div[data-testid="stSidebar"] .stButton > button {{
        min-height: 48px; margin: 5px 0; border-radius: 14px;
        background: linear-gradient(135deg, rgba(30,41,59,.96), rgba(15,23,42,.96));
        border: 1px solid rgba(148,163,184,.16); color: #dbeafe;
        text-align: left; box-shadow: 0 8px 22px rgba(0,0,0,.16);
    }}
    div[data-testid="stSidebar"] .stButton > button:hover {{
        transform: translateX(3px); border-color: rgba(56,189,248,.65);
        box-shadow: 0 10px 28px rgba(14,165,233,.16);
    }}
    .premium-hero {{
        padding: 30px 24px; border: 1px solid rgba(56,189,248,.20); border-radius: 24px;
        background: radial-gradient(circle at top right, rgba(56,189,248,.16), transparent 40%), rgba(15,23,42,.78);
        box-shadow: 0 18px 55px rgba(0,0,0,.25);
    }}
    .moon-badge {{ width:52px; height:52px; border-radius:50%; display:inline-flex; align-items:center;
        justify-content:center; background:#38bdf8; color:#07111f; font-size:30px; font-weight:700;
        box-shadow:0 0 30px rgba(56,189,248,.35); }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 6. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("Navigation")

    if st.button("⌂  হোম স্ক্রিন (Home)"):
        st.session_state.current_page = "Home"
        st.rerun()

    if st.button("◈  Danger Dash (2D Game)"):
        st.session_state.current_page = "2D Physics Game"
        st.rerun()

    if st.button("◎ দীপ এনালাইসিস (Deep Analysis)"):
        st.session_state.current_page = "Deep Analysis"
        st.rerun()

    if st.button("▣  ৯-১০ম ফিজিক্স (NCTB Physics)"):
        st.session_state.current_page = "NCTB Curriculum"
        st.rerun()

    if st.button("✓  সিকিউ সলভ (CQ Solve)"):
        st.session_state.current_page = "CQ Solve"
        st.rerun()

    if st.button("☾  Moon AI"):
        st.session_state.current_page = "Physics Bot"
        st.rerun()

    if st.button("◌  থিম ও ব্যাকগ্রাউন্ড সেটিংস"):
        st.session_state.current_page = "Theme Settings"
        st.rerun()


# ==========================================
# 7. HOME SCREEN
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='premium-hero'><span class='moon-badge'>☾</span><h1 style='display:inline-block;margin-left:14px;color:#38BDF8;'>পদার্থবিজ্ঞান অনুশীলন ক্লাব</h1><p style='text-align:center;color:#38BDF8;font-weight:700;letter-spacing:2px;'>MOON AI PHYSICS EXPERIENCE</p></div>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #94A3B8;'>নিচের যেকোনো অপশন "
        "নির্বাচন করুন</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("◎ দীপ এনালাইসিস (Deep Analysis)", key="home_deep"):
            st.session_state.current_page = "Deep Analysis"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("▣ লার্নিং ফিজিক্স বেসিক (৯ম-১০ম)", key="home_basic"):
            st.session_state.current_page = "NCTB Curriculum"
            st.rerun()

    with col2:
        if st.button("✓ সিকিউ সলভ (CQ Solve)", key="home_cq"):
            st.session_state.current_page = "CQ Solve"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("☾ ডিসকাশন উইথ Moon AI", key="home_bot"):
            st.session_state.current_page = "Physics Bot"
            st.rerun()


# ==========================================
# 8. DANGER DASH 2D GAME
# ==========================================
elif st.session_state.current_page == "2D Physics Game":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Danger Dash — 2D")
    st.caption(
        "দৌড়ান, obstacle এড়িয়ে চলুন এবং coin সংগ্রহ করুন। "
        "Keyboard অথবা Mobile touch control ব্যবহার করুন।"
    )
    st.markdown("---")

    danger_dash_html = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    * { box-sizing: border-box; }
    body {
        margin: 0;
        background: #08111f;
        color: #e2e8f0;
        font-family: Arial, sans-serif;
        text-align: center;
        overflow: hidden;
        user-select: none;
    }

    #gameWrap {
        width: 100%;
        max-width: 900px;
        margin: auto;
    }

    #hud {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 8px;
        padding: 10px;
        margin-bottom: 8px;
        background: #111c2e;
        border: 1px solid #263852;
        border-radius: 12px;
        font-weight: bold;
        color: #7dd3fc;
    }

    #game {
        width: 100%;
        max-width: 900px;
        height: auto;
        border: 2px solid #263852;
        border-radius: 14px;
        background: #101c2e;
        box-shadow: 0 10px 35px rgba(0,0,0,.45);
        touch-action: none;
    }

    #controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 10px;
    }

    button {
        border: 0;
        border-radius: 10px;
        padding: 12px 22px;
        font-weight: bold;
        cursor: pointer;
        background: #38bdf8;
        color: #06101c;
        font-size: 15px;
    }

    button:active {
        transform: scale(.96);
    }

    #hint {
        color: #94a3b8;
        font-size: 13px;
        margin-top: 8px;
    }
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
                <button id="startBtn" style="min-width:190px;font-size:17px;">START GAME</button>
            </div>
        </div>
    </div>

    <div id="controls">
        <button id="jumpBtn">JUMP</button>
        <button id="duckBtn">DUCK</button>
        <button id="restartBtn">RESTART</button>
    </div>

    <div id="hint">
        Keyboard: SPACE / ↑ = Jump, ↓ = Duck. Mobile: নিচের বোতাম চাপুন।
    </div>
</div>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const W = canvas.width;
const H = canvas.height;
const groundY = 410;

let score = 0;
let coins = 0;
let lives = 3;
let speed = 5;
let frame = 0;
let running = false;
let gameOver = false;

let best = Number(localStorage.getItem("dangerDashBest") || 0);
document.getElementById("best").textContent = best;

const player = {
    x: 115,
    y: groundY - 74,
    w: 48,
    h: 74,
    vy: 0,
    jumping: false,
    ducking: false,
    invincible: 0,
    anim: 0
};

let obstacles = [];
let coinItems = 
