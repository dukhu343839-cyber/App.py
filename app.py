
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
let coinItems = [];
let particles = [];
let clouds = [];
let stars = [];

for (let i = 0; i < 18; i++) {
    stars.push({
        x: Math.random() * W,
        y: Math.random() * 240,
        r: Math.random() * 2 + 1
    });
}

for (let i = 0; i < 6; i++) {
    clouds.push({
        x: Math.random() * W,
        y: 55 + Math.random() * 120,
        w: 60 + Math.random() * 70,
        s: .2 + Math.random() * .35
    });
}

function resetGame() {
    score = 0;
    coins = 0;
    lives = 3;
    speed = 5;
    frame = 0;
    running = false;
    gameOver = false;
    document.getElementById("startScreen").style.display = "flex";

    player.y = groundY - 74;
    player.vy = 0;
    player.jumping = false;
    player.ducking = false;
    player.invincible = 0;

    obstacles = [];
    coinItems = [];
    particles = [];

    updateHud();
}

function startGame() {
    running = true;
    gameOver = false;
    document.getElementById("startScreen").style.display = "none";
}

function updateHud() {
    document.getElementById("score").textContent = Math.floor(score);
    document.getElementById("coins").textContent = coins;
    document.getElementById("lives").textContent = lives;
    document.getElementById("speed").textContent =
        (speed / 5).toFixed(1);
}

function jump() {
    if (gameOver) return;
    if (!player.jumping) {
        player.vy = -14;
        player.jumping = true;
        burst(player.x + 20, player.y + player.h, "#7dd3fc", 7);
    }
}

function duckStart() {
    if (gameOver) return;
    player.ducking = true;
}

function duckEnd() {
    player.ducking = false;
}

function spawnObstacle() {
    const types = ["rock", "spike", "box"];
    const type = types[Math.floor(Math.random() * types.length)];

    let h = type === "spike" ? 48 : 58;
    let w = type === "rock" ? 52 : 44;

    obstacles.push({
        x: W + 40,
        y: groundY - h,
        w,
        h,
        type
    });
}

function spawnCoin() {
    coinItems.push({
        x: W + 30,
        y: groundY - 90 - Math.random() * 100,
        r: 11,
        spin: 0
    });
}

function burst(x, y, color, count = 15) {
    for (let i = 0; i < count; i++) {
        particles.push({
            x, y,
            vx: (Math.random() - .5) * 7,
            vy: (Math.random() - .5) * 7,
            life: 35 + Math.random() * 25,
            color,
            size: 2 + Math.random() * 4
        });
    }
}

function rectHit(a, b) {
    return (
        a.x < b.x + b.w &&
        a.x + a.w > b.x &&
        a.y < b.y + b.h &&
        a.y + a.h > b.y
    );
}

function playerBox() {
    if (player.ducking && !player.jumping) {
        return {
            x: player.x + 5,
            y: groundY - 40,
            w: 58,
            h: 38
        };
    }

    return {
        x: player.x + 5,
        y: player.y + 5,
        w: 38,
        h: 64
    };
}

function hurt() {
    if (player.invincible > 0) return;

    lives--;
    player.invincible = 90;
    burst(player.x + 20, player.y + 35, "#fb7185", 22);

    if (lives <= 0) {
        gameOver = true;
        running = false;
        best = Math.max(best, Math.floor(score));
        localStorage.setItem("dangerDashBest", best);
    }

    updateHud();
}

function update() {
    if (!running) return;

    frame++;
    score += 0.12 * (speed / 5);

    if (frame % 800 === 0) {
        speed += .7;
    }

    if (frame % Math.max(55, Math.floor(105 - speed * 5)) === 0) {
        spawnObstacle();
    }

    if (frame % 80 === 0 && Math.random() < .8) {
        spawnCoin();
    }

    // Player physics
    player.vy += .65;
    player.y += player.vy;

    if (player.y >= groundY - 74) {
        player.y = groundY - 74;
        player.vy = 0;
        player.jumping = false;
    }

    if (player.invincible > 0) {
        player.invincible--;
    }

    player.anim += .22;

    // Obstacles
    for (let i = obstacles.length - 1; i >= 0; i--) {
        let o = obstacles[i];
        o.x -= speed;

        if (rectHit(playerBox(), o)) {
            hurt();
            obstacles.splice(i, 1);
            continue;
        }

        if (o.x + o.w < 0) {
            obstacles.splice(i, 1);
        }
    }

    // Coins
    for (let i = coinItems.length - 1; i >= 0; i--) {
        let c = coinItems[i];
        c.x -= speed;
        c.spin += .15;

        let p = playerBox();
        let dx = (p.x + p.w / 2) - c.x;
        let dy = (p.y + p.h / 2) - c.y;

        if (Math.sqrt(dx*dx + dy*dy) < 34) {
            coins++;
            score += 25;
            burst(c.x, c.y, "#facc15", 12);
            coinItems.splice(i, 1);
            continue;
        }

        if (c.x < -30) {
            coinItems.splice(i, 1);
        }
    }

    // Particles
    for (let i = particles.length - 1; i >= 0; i--) {
        let p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += .12;
        p.life--;

        if (p.life <= 0) {
            particles.splice(i, 1);
        }
    }

    updateHud();
}

function drawBackground() {
    // Sky
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, "#091b36");
    grad.addColorStop(.55, "#12365b");
    grad.addColorStop(1, "#07121f");

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // Stars
    ctx.fillStyle = "#dbeafe";
    for (const s of stars) {
        ctx.globalAlpha = .55 + Math.sin(frame * .03 + s.x) * .2;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
    }
    ctx.globalAlpha = 1;

    // Moon
    ctx.fillStyle = "#fef3c7";
    ctx.beginPath();
    ctx.arc(760, 90, 38, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#091b36";
    ctx.beginPath();
    ctx.arc(775, 78, 38, 0, Math.PI * 2);
    ctx.fill();

    // Clouds
    ctx.fillStyle = "rgba(226,232,240,.12)";
    for (const c of clouds) {
        c.x -= c.s;
        if (c.x < -c.w) c.x = W + c.w;

        ctx.beginPath();
        ctx.arc(c.x, c.y, 22, 0, Math.PI * 2);
        ctx.arc(c.x + 25, c.y - 10, 30, 0, Math.PI * 2);
        ctx.arc(c.x + 58, c.y, 22, 0, Math.PI * 2);
        ctx.fill();
    }

    // Distant city/hills
    ctx.fillStyle = "#0a1626";
    for (let x = 0; x < W; x += 70) {
        const h = 45 + ((x * 17) % 70);
        ctx.fillRect(x, groundY - h, 55, h);
    }

    // Ground
    ctx.fillStyle = "#0b1220";
    ctx.fillRect(0, groundY, W, H - groundY);

    ctx.strokeStyle = "#1e3a56";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(W, groundY);
    ctx.stroke();

    // Road lines
    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 5;
    for (let x = -((frame * speed) % 90); x < W; x += 90) {
        ctx.beginPath();
        ctx.moveTo(x, groundY + 48);
        ctx.lineTo(x + 48, groundY + 48);
        ctx.stroke();
    }
}

function drawPlayer() {
    if (player.invincible > 0 &&
        Math.floor(player.invincible / 6) % 2 === 0) {
        return;
    }

    let x = player.x;
    let y = player.y;

    ctx.save();

    if (player.ducking && !player.jumping) {
        y = groundY - 40;

        // Body
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(x + 5, y + 10, 55, 28);

        // Head
        ctx.fillStyle = "#fbbf24";
        ctx.beginPath();
        ctx.arc(x + 51, y + 12, 14, 0, Math.PI * 2);
        ctx.fill();

        // Eye
        ctx.fillStyle = "#111827";
        ctx.beginPath();
        ctx.arc(x + 56, y + 9, 2.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
        return;
    }

    // Running character
    const leg = Math.sin(player.anim) * 9;

    // Shadow
    ctx.fillStyle = "rgba(0,0,0,.35)";
    ctx.beginPath();
    ctx.ellipse(x + 25, groundY + 4, 27, 7, 0, 0, Math.PI * 2);
    ctx.fill();

    // Body
    ctx.fillStyle = "#38bdf8";
    ctx.fillRect(x + 10, y + 25, 30, 37);

    // Jacket detail
    ctx.fillStyle = "#0284c7";
    ctx.fillRect(x + 10, y + 47, 30, 15);

    // Head
    ctx.fillStyle = "#fbbf24";
    ctx.beginPath();
    ctx.arc(x + 25, y + 15, 17, 0, Math.PI * 2);
    ctx.fill();

    // Hair
    ctx.fillStyle = "#1e293b";
    ctx.beginPath();
    ctx.arc(x + 20, y + 5, 14, Math.PI, Math.PI * 2);
    ctx.fill();

    // Eye
    ctx.fillStyle = "#111827";
    ctx.beginPath();
    ctx.arc(x + 31, y + 12, 2.5, 0, Math.PI * 2);
    ctx.fill();

    // Arms
    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 7;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x + 11, y + 31);
    ctx.lineTo(x - 1, y + 45 + leg * .2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x + 38, y + 31);
    ctx.lineTo(x + 50, y + 44 - leg * .2);
    ctx.stroke();

    // Legs
    ctx.strokeStyle = "#1d4ed8";
    ctx.lineWidth = 9;

    ctx.beginPath();
    ctx.moveTo(x + 18, y + 60);
    ctx.lineTo(x + 9 + leg, y + 74);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x + 33, y + 60);
    ctx.lineTo(x + 43 - leg, y + 74);
    ctx.stroke();

    ctx.restore();
}

function drawObstacle(o) {
    ctx.save();

    if (o.type === "spike") {
        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.moveTo(o.x, o.y + o.h);
        ctx.lineTo(o.x + o.w / 2, o.y);
        ctx.lineTo(o.x + o.w, o.y + o.h);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = "#fecaca";
        ctx.fillRect(o.x + o.w * .45, o.y + 10, 4, 18);
    } else if (o.type === "rock") {
        ctx.fillStyle = "#64748b";
        ctx.beginPath();
        ctx.moveTo(o.x, o.y + o.h);
        ctx.lineTo(o.x + 8, o.y + 18);
        ctx.lineTo(o.x + 25, o.y);
        ctx.lineTo(o.x + o.w - 5, o.y + 15);
        ctx.lineTo(o.x + o.w, o.y + o.h);
        ctx.closePath();
        ctx.fill();
    } else {
        ctx.fillStyle = "#f97316";
        ctx.fillRect(o.x, o.y, o.w, o.h);

        ctx.strokeStyle = "#fed7aa";
        ctx.lineWidth = 3;
        ctx.strokeRect(o.x + 5, o.y + 5, o.w - 10, o.h - 10);
    }

    ctx.restore();
}

function drawCoin(c) {
    const squash = .65 + Math.abs(Math.cos(c.spin)) * .35;

    ctx.save();
    ctx.translate(c.x, c.y);
    ctx.scale(squash, 1);

    ctx.fillStyle = "#facc15";
    ctx.shadowBlur = 15;
    ctx.shadowColor = "#facc15";

    ctx.beginPath();
    ctx.arc(0, 0, c.r, 0, Math.PI * 2);
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.fillStyle = "#854d0e";
    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("$", 0, 1);

    ctx.restore();
}

function drawParticles() {
    for (const p of particles) {
        ctx.globalAlpha = Math.max(0, p.life / 50);
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, p.size, p.size);
    }
    ctx.globalAlpha = 1;
}

function drawGameOver() {
    if (!gameOver) return;

    ctx.fillStyle = "rgba(2,6,23,.76)";
    ctx.fillRect(0, 0, W, H);

    ctx.textAlign = "center";

    ctx.fillStyle = "#fb7185";
    ctx.font = "bold 52px Arial";
    ctx.fillText("GAME OVER", W / 2, 190);

    ctx.fillStyle = "#e2e8f0";
    ctx.font = "bold 25px Arial";
    ctx.fillText(
        "Score: " + Math.floor(score),
        W / 2,
        240
    );

    ctx.fillStyle = "#7dd3fc";
    ctx.font = "bold 19px Arial";
    ctx.fillText(
        "RESTART চাপুন",
        W / 2,
        285
    );
}

function draw() {
    drawBackground();

    for (const c of coinItems) {
        drawCoin(c);
    }

    for (const o of obstacles) {
        drawObstacle(o);
    }

    drawPlayer();
    drawParticles();
    drawGameOver();
}

function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
}

document.addEventListener("keydown", function(e) {
    if (e.code === "Space" || e.code === "ArrowUp") {
        e.preventDefault();
        jump();
    }

    if (e.code === "ArrowDown") {
        e.preventDefault();
        duckStart();
    }

    if (e.code === "Enter" && gameOver) {
        resetGame();
    }
});

document.addEventListener("keyup", function(e) {
    if (e.code === "ArrowDown") {
        duckEnd();
    }
});

document.getElementById("jumpBtn").addEventListener("pointerdown", jump);

document.getElementById("duckBtn").addEventListener(
    "pointerdown",
    duckStart
);

document.getElementById("duckBtn").addEventListener(
    "pointerup",
    duckEnd
);

document.getElementById("duckBtn").addEventListener(
    "pointercancel",
    duckEnd
);

document.getElementById("restartBtn").addEventListener("click", resetGame);
document.getElementById("startBtn").addEventListener("click", startGame);

resetGame();
loop();
</script>
</body>
</html>
"""

    components.html(danger_dash_html, height=650, scrolling=False)


# ==========================================
# 9. DEEP ANALYSIS
# ==========================================
elif st.session_state.current_page == "Deep Analysis":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("দীপ এনালাইসিস ও বাস্তবসম্মত উদাহরণ")
    st.markdown("---")

    tab1, tab2 = st.tabs(
        ["বাস্তবসম্মত পদার্থবিজ্ঞান", "মৌলিক সূত্র ও প্রতিপাদন"]
    )

    with tab1:
        with st.expander(
            "১. বাদুড় চোখ ছাড়া কীভাবে সামনে এগিয়ে চলে? (Ultrasonic Waves)"
        ):
            st.write("""
            **ব্যাখ্যা:** বাদুড় উড়ন্ত অবস্থায় উচ্চ কম্পাঙ্কের শব্দোত্তর তরঙ্গ
            (Ultrasonic Sound Waves - ২০,০০০ Hz এর বেশি) তৈরি করে। এই শব্দ
            সামনে থাকা বাধা বা শিকারে প্রতিফলিত হয়ে আবার বাদুড়ের কানে ফিরে
            আসে। শব্দ নির্গমন এবং প্রতিফলিত প্রতিধ্বনি শোনার মধ্যবর্তী সময়
            মেপে বাদুড় মস্তিষ্কের সাহায্যে বস্তুর দূরত্ব, আকার ও অবস্থান
            নিখুঁতভাবে হিসেব করে ফেলে। এটিকে **প্রতিধ্বনি অবস্থান নির্ধারণ
            (Echolocation)** বলা হয়।
            """)

        with st.expander(
            "২. ছোট লোহার পেরেক ডুবে কিন্তু বিরাট লোহার জাহাজ ভেসে থাকে কেন?"
        ):
            st.write("""
            **ব্যাখ্যা (আর্কিমিডিসের নীতি):** কোনো বস্তুকে পানিতে ডোবালে তা
            নিজের আয়তনের সমান পানি অপসারিত করে। একটি লোহার পেরেকের ভেতর
            ফাঁপা জায়গা না থাকায় এর গড় ঘনত্ব পানির ঘনত্বের চেয়ে বেশি হয়,
            ফলে পেরেকটি ডুবে যায়।

            কিন্তু লোহার জাহাজ ভেতরে বিশালাকার ফাঁপা থাকে এবং বায়ুতে পূর্ণ
            থাকে। ফলে জাহাজের মোট ভরকে তার বিশাল আয়তন দিয়ে ভাগ করলে
            জাহাজের **গড় ঘনত্ব পানির ঘনত্বের চেয়ে অনেক কম** হয়ে যায়।
            জাহাজটি যে পরিমাণ পানি অপসারিত করে, তার প্লবতা বল জাহাজের মোট
            ওজনের সমান বা বেশি হয়, তাই জাহাজ ভেসে থাকে।
            """)

        with st.expander(
            "৩. নদীর পানির চেয়ে সমুদ্রের পানিতে সাঁতার কাটা সহজ কেন?"
        ):
            st.write("""
            **ব্যাখ্যা:** নদীর পানিতে দ্রবীভূত লবণের পরিমাণ খুবই কম থাকে,
            কিন্তু সমুদ্রের পানিতে প্রচুর পরিমাণে লবণ দ্রবীভূত থাকে। ফলে
            **সমুদ্রের পানির ঘনত্ব নদীর পানির ঘনত্বের চেয়ে বেশি** হয়।
            পানির ঘনত্ব বেশি হওয়ায় সমুদ্রের পানি সাঁতারুর ওপর বেশি
            **উর্ধ্বমুখী প্লবতা বল (Buoyancy Force)** প্রয়োগ করে।
            """)

        with st.expander(
            "৪. ইটের ওপর হাঁটার চেয়ে ভাঙা ইটের (খোয়া) ওপর হাঁটা কষ্টদায়ক কেন?"
        ):
            st.write("""
            **ব্যাখ্যা (চাপের সূত্র P = F/A):** ইটের সমতল পৃষ্ঠের ক্ষেত্রফল
            বেশি হওয়ায় পায়ের তলায় প্রয়োগকৃত চাপ কম হয়। কিন্তু ভাঙা
            ইটের তীক্ষ্ণ কোণাগুলোর সংস্পর্শ ক্ষেত্রফল অত্যন্ত কম। ক্ষেত্রফল
            কমে গেলে চাপ বহুগুণ বেড়ে যায়।
            """)

        with st.expander(
            "৫. শীতের দিনে বিদ্যুতের তার টানটান হয়ে যায় কেন?"
        ):
            st.write("""
            **ব্যাখ্যা:** ঠান্ডায় ধাতব তার সংকুচিত হয়ে দৈর্ঘ্য ছোট হতে চায়।
            দুই খুঁটির সাথে বাঁধা থাকায় তারে টান বৃদ্ধি পেতে পারে।
            """)

        with st.expander("৬. শীতের দিনে ভেজা কাপড় দ্রুত শুকায় কেন?"):
            st.write("""
            **ব্যাখ্যা:** কাপড় শুকানো বাতাসের আপেক্ষিক আর্দ্রতা ও
            বাষ্পীভবনের ওপর নির্ভর করে। বাতাস শুষ্ক হলে বাষ্পীভবন দ্রুত হতে
            পারে।
            """)

    with tab2:
        st.markdown("### গতিবিজ্ঞানের সূত্র প্রতিপাদন (Kinematics)")
        st.latex(r"v = u + at")
        st.latex(r"s = \left(\frac{u + v}{2}\right)t")
        st.latex(r"s = ut + \frac{1}{2}at^2")
        st.latex(r"v^2 = u^2 + 2as")

        st.markdown("### আর্কিমিডিস ও প্লবতার সূত্র")
        st.latex(r"F_{buoyancy} = V \cdot \rho \cdot g")
        st.latex(r"P = h \cdot \rho \cdot g")


# ==========================================
# 10. NCTB CLASS 9-10 PHYSICS CURRICULUM
# ==========================================
elif st.session_state.current_page == "NCTB Curriculum":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("৯ম-১০ম শ্রেণি পদার্থবিজ্ঞান কারিকুলাম (NCTB)")
    st.markdown("---")

    chapters = [
        (
            "১. ভৌত রাশি ও পরিমাপ",
            "রাশি, পরিমাপের একক, মাত্রা, ভার্নিয়ার স্কেল, স্লাইড ক্যালিপার্স।",
            r"L = M + (V \times VC)",
        ),
        (
            "২. গতি (Motion)",
            "দূরত্ব, সরণ, বেগ, ত্বরণ, গতির সমীকরণ ও পড়ন্ত বস্তুর সূত্র।",
            r"v = u + at, \quad s = ut + \frac{1}{2}at^2",
        ),
        (
            "৩. বল (Force)",
            "নিউটন গতির ৩টি সূত্র, ভরবেগ, মহাকর্ষ বল ও ঘর্ষণ বল।",
            r"F = ma, \quad p = mv",
        ),
        (
            "৪. কাজ, ক্ষমতা ও শক্তি",
            "কাজ, গতিশক্তি, বিভবশক্তি, ক্ষমতার হিসাব ও শক্তির সংরক্ষণশীলতা।",
            r"W = F \cdot s, \quad E_k = \frac{1}{2}mv^2, \quad E_p = mgh",
        ),
        (
            "৫. পদার্থের অবস্থা ও চাপ",
            "চাপ, ঘনত্ব, প্যাসকেলের সূত্র, আর্কিমিডিসের নীতি ও প্লবতা।",
            r"P = \frac{F}{A}, \quad P = h\rho g, \quad \rho = \frac{m}{V}",
        ),
        (
            "৬. বস্তুর ওপর তাপের প্রভাব",
            "তাপ ও তাপমাত্রা, দৈর্ঘ্য সম্প্রসারণ, আপেক্ষিক তাপ ও ক্যালরিমিতি।",
            r"Q = ms\Delta T, \quad \Delta L = \alpha L_1 \Delta T",
        ),
        (
            "৭. তরঙ্গ ও শব্দ",
            "পর্যায়বৃত্ত গতি, অনুদৈর্ঘ্য ও অনুপ্রস্থ তরঙ্গ, শব্দের বেগ ও প্রতিধ্বনি।",
            r"v = f\lambda, \quad d = \frac{v \cdot t}{2}",
        ),
        (
            "৮. আলোর প্রতিফলন",
            "আয়না/দর্পণ, সমতল ও গোলীয় দর্পণ, বিম্ব গঠন ও বিবর্ধন।",
            r"\frac{1}{f} = \frac{1}{u} + \frac{1}{v}, \quad m = -\frac{v}{u}",
        ),
        (
            "৯. আলোর প্রতিসরণ",
            "প্রতিসরণাঙ্ক, সংকট কোণ, পূর্ণ অভ্যন্তরীণ প্রতিফলন ও লেন্স।",
            r"\eta = \frac{\sin i}{\sin r}, \quad P = \frac{1}{f}",
        ),
        (
            "১০. স্থির তড়িৎ",
            "আধান, কুলম্বের সূত্র, তড়িৎ ক্ষেত্র ও তড়িৎ বিভব।",
            r"F = k \frac{q_1 q_2}{r^2}, \quad V = \frac{W}{q}",
        ),
        (
            "১১. চল তড়িৎ",
            "ওহমের সূত্র, রোধ, শ্রেণী ও সমান্তরাল সার্কিট এবং ক্ষমতা।",
            r"V = IR, \quad P = VI = I^2R",
        ),
        (
            "১২. তড়িৎ প্রবাহের চৌম্বক ক্রিয়া",
            "সোলেনয়েড, তড়িচ্চুম্বক, তাড়িতচৌম্বক আবেশ ও ট্রান্সফরমার।",
            r"\frac{V_p}{V_s} = \frac{N_p}{N_s} = \frac{I_s}{I_p}",
        ),
        (
            "১৩. আধুনিক পদার্থবিজ্ঞান ও ইলেকট্রনিক্স",
            "তেজস্ক্রিয়তা, এক্স-রে, সেমিকন্ডাক্টর, ডায়োড ও ট্রানজিস্টর।",
            r"E = mc^2",
        ),
        (
            "১৪. জীবন বাঁচাতে পদার্থবিজ্ঞান",
            "ইসিজি, এক্স-রে, আল্ট্রাসোনোগ্রাফি, সিটি স্ক্যান ও এমআরআই।",
            "মেডিকেল ফিজিক্স ও ডায়াগনস্টিক প্রয়োগ।",
        ),
    ]

    for chap_title, chap_desc, formula in chapters:
        with st.expander(f"{chap_title}"):
            st.write(f"**মূল বিষয়বস্তু:** {chap_desc}")
            if formula != "মেডিকেল ফিজিক্স ও ডায়াগনস্টিক প্রয়োগ।":
                st.latex(formula)


# ==========================================
# 11. CQ SOLVE MODULE
# ==========================================
elif st.session_state.current_page == "CQ Solve":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("সিকিউ সমাধান (Creative Questions)")
    st.markdown("---")

    with st.expander(
        "প্রশ্ন ১: ২০m উঁচু থেকে ৫০g ভরের একটি বস্তুকে ফেলে দেওয়া হলো।"
    ):
        st.write("""
        **গ) ভূমি স্পর্শ করার মুহূর্তে বেগ কত?**

        **সমাধান:**
        দেওয়া আছে, $u = 0$, $h = 20\text{ m}$, $g = 9.8\text{ m/s}^2$

        সূত্র: $v^2 = u^2 + 2gh = 0 + 2 \times 9.8 \times 20 = 392$

        $$\\implies v = \\sqrt{392} \\approx 19.8 \\text{ m/s}$$
        """)


# ==========================================
# 12. LOCAL MINI-AI CHAT
# ==========================================
elif st.session_state.current_page == "Physics Bot":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.markdown("<div class='premium-hero'><span class='moon-badge'>☾</span><h1 style='display:inline-block;margin-left:14px;color:#38BDF8;'>Moon AI</h1><p style='color:#94A3B8;margin-bottom:0;'>Local Physics Learning Companion</p></div>", unsafe_allow_html=True)
    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_query = st.chat_input("Moon AI-কে প্রশ্ন করুন — যেমন: 250*9.8 বা বল কী?")

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)
        reply = local_ai_reply(user_query)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
        if extract_save_command(user_query) is not None:
            st.rerun()


# ==========================================
# 13. THEME & GALLERY BACKGROUND SETTINGS
# ==========================================
elif st.session_state.current_page == "Theme Settings":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("◌  থিম ও ব্যাকগ্রাউন্ড সেটিংস")
    st.markdown("---")

    st.subheader("গ্যালারি থেকে ব্যাকগ্রাউন্ড ছবি আপলোড করুন")

    uploaded_file = st.file_uploader(
        "পছন্দের ছবি বেছে নিন (JPG, PNG)",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_img = base64.b64encode(bytes_data).decode()
        st.session_state.bg_image = base64_img
        st.success(
            "ব্যাকগ্রাউন্ড থিম সফলভাবে পরিবর্তন করা হয়েছে! হোমে গিয়ে দেখুন।"
        )

    if st.session_state.bg_image:
        if st.button("ডিফল্ট ডার্ক থিমে ফিরে যান"):
            st.session_state.bg_image = None
            st.rerun()

    st.markdown("---")
    st.subheader("Moon AI Knowledge")

    if st.button("সব শেখা তথ্য মুছে ফেলুন"):
        delete_all_memory()
        st.success("সব শেখা তথ্য মুছে ফেলা হয়েছে।")
        st.rerun()
