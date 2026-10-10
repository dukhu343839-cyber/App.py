import base64
import ast
import json
import math
import operator as op
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# Standalone build: no external image files are required.
# Moon AI and user avatars use Streamlit Material Symbols, so this file can be copied
# as-is and run without moon_ai_icon.png or user_avatar.svg.


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

if "language" not in st.session_state:
    st.session_state.language = "বাংলা"

# ChatGPT/Gemini-style local chat sessions.
_GREETING = "হ্যালো। আমি Moon AI — Physics শেখা, হিসাব এবং সমস্যা সমাধানে সাহায্য করতে পারি।"
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
        "cq": "✓  CQ Solve", "moon": "☾  Moon AI", "settings": "⚙  সেটিংস",
    },
    "English": {
        "home": "⌂  Home", "game": "◈  Danger Dash (2D Game)",
        "deep": "◎  Deep Analysis", "curr": "▣  Class 9-10 Physics",
        "cq": "✓  CQ Solve", "moon": "☾  Moon AI", "settings": "⚙  Settings",
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
    """Load structured knowledge. Learned data is data, never executable Python."""
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
    """Fast teaching API for Moon AI. Example: moon_learn('g=9.8 m/s²','physics')."""
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
    """\n    Fast teaching formats:\n      if #(পদার্থবিজ্ঞানে g=9.8 m/s²) save\n      teach #(প্রশ্ন => উত্তর | ব্যাখ্যা | physics)\n      learn #(তথ্য | chemistry)\n    """
    m=re.match(r"^\s*(?:teach|learn)\s*#\(\s*(.*?)\s*\)\s*$", text, re.I|re.S)
    if not m:
        return None
    raw=m.group(1).strip()
    parts=[p.strip() for p in raw.split("|")]
    if "=>" in parts[0]:
        q,a=parts[0].split("=>",1)
        return {"info":"", "question":q.strip(), "answer":a.strip(), "explanation":parts[1] if len(parts)>1 else "", "domain":parts[2] if len(parts)>2 else "general"}
    return {"info":parts[0], "question":"", "answer":"", "explanation":"", "domain":parts[1] if len(parts)>1 else "general"}


def teach_from_command(text):
    cmd=extract_teach_command(text)
    if cmd:
        return moon_learn(**cmd)
    learned=extract_save_command(text)
    if learned:
        return moon_learn(learned, domain="general")
    return False


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
        block=f"**{title}**\\n\\n{body}"
        if st.session_state.get("ai_explain",True) and explanation:
            block += f"\\n\\n**Moon AI ব্যাখ্যা:** {explanation}"
        blocks.append(block)
    return "\\n\\n---\\n\\n".join(blocks)


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

CQ_PROBLEMS = [{'id': 1, 'chapter': 'পরিমাপ ও ভৌত রাশি', 'question': 'একটি ভার্নিয়ার ক্যালিপার্সে মূল স্কেল পাঠ 2.3 cm, ভার্নিয়ার সমাপতন 6 এবং least count 0.01 cm। মোট পাঠ কত?', 'answer': 'মোট পাঠ = MSR + VC×LC = 2.3 + 6×0.01 = 2.36 cm।', 'moon': 'Moon AI: প্রথমে মূল স্কেল পাঠ নাও, তারপর ভার্নিয়ার সমাপতনকে least count দিয়ে গুণ করে যোগ করো।'}, {'id': 2, 'chapter': 'পরিমাপ ও ভৌত রাশি', 'question': 'একটি দৈর্ঘ্য 2.50 m এবং অনিশ্চয়তা ±0.02 m। শতকরা আপেক্ষিক অনিশ্চয়তা কত?', 'answer': 'আপেক্ষিক অনিশ্চয়তা = 0.02/2.50×100% = 0.8%।', 'moon': 'Moon AI: অনিশ্চয়তাকে পরিমাপের মান দিয়ে ভাগ করে 100 দিয়ে গুণ করলেই শতাংশ পাওয়া যায়।'}, {'id': 3, 'chapter': 'গতি', 'question': 'একটি গাড়ি প্রথম 10 s-এ 100 m এবং পরের 10 s-এ 200 m অতিক্রম করল। গড় দ্রুতি কত?', 'answer': 'মোট দূরত্ব = 300 m, মোট সময় = 20 s; গড় দ্রুতি = 15 m/s।', 'moon': 'Moon AI: গড় দ্রুতি বের করতে মোট দূরত্বকে মোট সময় দিয়ে ভাগ করতে হয়; দুই অংশের দ্রুতি সরাসরি গড় করা যাবে না।'}, {'id': 4, 'chapter': 'গতি', 'question': 'একটি বস্তু u=5 m/s বেগে চলল এবং a=2 m/s²। 6 s পরে সরণ কত?', 'answer': 's=ut+½at² = 5×6 + ½×2×36 = 66 m।', 'moon': 'Moon AI: ধ্রুব ত্বরণের ক্ষেত্রে প্রথমে প্রাথমিক বেগের সরণ এবং ত্বরণের জন্য অতিরিক্ত সরণ আলাদা করে যোগ করা যায়।'}, {'id': 5, 'chapter': 'গতি', 'question': 'একটি গাড়ি 25 m/s থেকে 5 s-এ থামে। মন্দন ও অতিক্রান্ত দূরত্ব নির্ণয় করো।', 'answer': 'a=(0−25)/5=−5 m/s²; s=(25+0)/2×5=62.5 m।', 'moon': 'Moon AI: ঋণাত্মক ত্বরণ মন্দন বোঝায়। গড় বেগ×সময় ব্যবহার করে দূরত্ব পাওয়া যায়।'}, {'id': 6, 'chapter': 'গতি', 'question': 'একটি বস্তু 45 m উচ্চতা থেকে স্থির অবস্থা থেকে পড়ে। g=10 m/s² হলে সময় কত?', 'answer': 'h=½gt² ⇒ 45=5t² ⇒ t=3 s।', 'moon': 'Moon AI: মুক্তপতনে u=0 বসিয়ে s=½gt² সমীকরণ থেকে সময় বের করা হয়।'}, {'id': 7, 'chapter': 'বল', 'question': '8 kg ভরের ব্লকে 30 N প্রয়োগ বল এবং 6 N ঘর্ষণ বিপরীত দিকে। ত্বরণ কত?', 'answer': 'নিট বল=30−6=24 N; a=24/8=3 m/s²।', 'moon': 'Moon AI: ত্বরণ নির্ধারণে প্রয়োগ বল নয়, সব বলের ভেক্টর যোগফল বা net force ব্যবহার করতে হয়।'}, {'id': 8, 'chapter': 'বল', 'question': 'একটি 0.5 kg বল 12 m/s বেগে দেয়ালে গিয়ে 0.2 s-এ 4 m/s বিপরীত বেগে ফিরে আসে। গড় বল কত?', 'answer': 'Δp=m(v−u)=0.5(−4−12)=−8 kg·m/s; |F|=8/0.2=40 N।', 'moon': 'Moon AI: সংঘর্ষে ভরবেগের পরিবর্তনকে সময় দিয়ে ভাগ করলে গড় বল পাওয়া যায়।'}, {'id': 9, 'chapter': 'বল', 'question': 'দুইটি সমান ও বিপরীত বল একটি স্থির বস্তুর ওপর কাজ করছে। বস্তুটি কি অবশ্যই ত্বরণহীন?', 'answer': 'যদি দুই বল একই সরলরেখায় সমান ও বিপরীত হয়, নিট বল শূন্য; তাই ত্বরণ শূন্য।', 'moon': 'Moon AI: নিউটনের দ্বিতীয় সূত্রে a=Fnet/m। তবে বলের দিক বা সমরেখা হওয়া গুরুত্বপূর্ণ।'}, {'id': 10, 'chapter': 'ভরবেগ', 'question': '2 kg ভরের বস্তু 6 m/s বেগে এবং 3 kg ভরের বস্তু 2 m/s বেগে একই দিকে চলছে। মোট ভরবেগ কত?', 'answer': 'p=2×6+3×2=18 kg·m/s।', 'moon': 'Moon AI: একই দিকে চললে ভরবেগগুলো বীজগাণিতিকভাবে যোগ হয়।'}, {'id': 11, 'chapter': 'কাজ ও শক্তি', 'question': '50 N বল 30° কোণে প্রয়োগ করে বাক্সকে 8 m সরানো হলো। কাজ কত?', 'answer': 'W=Fs cos30°=50×8×0.866≈346.4 J।', 'moon': 'Moon AI: শুধু সরণের দিকে থাকা বলের উপাংশ কাজ করে; তাই cosθ ব্যবহার করতে হয়।'}, {'id': 12, 'chapter': 'কাজ ও শক্তি', 'question': 'একটি 4 kg বস্তু 5 m/s থেকে 15 m/s হলো। গতিশক্তির পরিবর্তন কত?', 'answer': 'ΔK=½m(v²−u²)=2(225−25)=400 J।', 'moon': 'Moon AI: কাজ-শক্তি উপপাদ্য অনুযায়ী নিট কাজ = গতিশক্তির পরিবর্তন।'}, {'id': 13, 'chapter': 'কাজ ও শক্তি', 'question': '2 kW মোটরের মাধ্যমে 120 kg বোঝা 10 m উপরে তুলতে 8 s লাগে। দক্ষতা 75% হলে ইনপুট শক্তি কত?', 'answer': 'উপযোগী শক্তি=mgh=120×9.8×10=11760 J; output power=1470 W; input power=1470/0.75=1960 W।', 'moon': 'Moon AI: দক্ষতা=output/input। তাই আগে উপযোগী কাজ, তারপর output power এবং শেষে input power।'}, {'id': 14, 'chapter': 'কাজ ও শক্তি', 'question': 'একটি দোলকের সর্বোচ্চ বিন্দুতে বেগ শূন্য। সেখানে কোন শক্তি সর্বাধিক?', 'answer': 'মহাকর্ষীয় বিভবশক্তি সর্বাধিক এবং গতিশক্তি সর্বনিম্ন।', 'moon': 'Moon AI: যান্ত্রিক শক্তি সংরক্ষিত হলে এক বিন্দুতে গতিশক্তি কমলে বিভবশক্তি বাড়ে।'}, {'id': 15, 'chapter': 'চাপ ও তরল', 'question': 'একটি 200 N বল 0.04 m² এলাকায় কাজ করছে। চাপ কত?', 'answer': 'P=F/A=200/0.04=5000 Pa।', 'moon': 'Moon AI: ক্ষেত্রফল ছোট হলে একই বলের জন্য চাপ বেশি হয়।'}, {'id': 16, 'chapter': 'চাপ ও তরল', 'question': 'পানিতে 5 m গভীরে চাপের গেজ মান কত? ρ=1000 kg/m³, g=9.8 m/s²।', 'answer': 'P=ρgh=1000×9.8×5=49000 Pa।', 'moon': 'Moon AI: তরলের গেজ চাপ শুধু ρgh; বায়ুমণ্ডলীয় চাপ যোগ করলে absolute pressure পাওয়া যায়।'}, {'id': 17, 'chapter': 'চাপ ও তরল', 'question': 'একটি বস্তু পানিতে 0.002 m³ আয়তন ডুবিয়েছে। প্লবতা বল কত?', 'answer': 'Fb=ρVg=1000×0.002×9.8=19.6 N।', 'moon': 'Moon AI: প্লবতা বল অপসারিত তরলের ওজনের সমান।'}, {'id': 18, 'chapter': 'চাপ ও তরল', 'question': 'বরফ পানিতে ভাসে কেন?', 'answer': 'বরফের গড় ঘনত্ব পানির চেয়ে কম, তাই ভাসার জন্য প্রয়োজনীয় প্লবতা পেতে আংশিক নিমজ্জিত অবস্থাই যথেষ্ট।', 'moon': 'Moon AI: ভাসার শর্তে Fb=mg। বরফের কম ঘনত্বের কারণে এর একটি অংশ পানির ওপরে থাকে।'}, {'id': 19, 'chapter': 'তাপ', 'question': '0.5 kg পানির তাপমাত্রা 20°C থেকে 60°C করতে Q কত? c=4200 J/kg°C।', 'answer': 'Q=mcΔT=0.5×4200×40=84000 J।', 'moon': 'Moon AI: ভর, সুনির্দিষ্ট তাপ এবং তাপমাত্রা পরিবর্তন গুণ করলেই প্রয়োজনীয় তাপ পাওয়া যায়।'}, {'id': 20, 'chapter': 'তাপ', 'question': 'একটি 2 m লোহার দণ্ডের α=12×10⁻⁶/°C। তাপমাত্রা 50°C বাড়লে দৈর্ঘ্য কত বাড়বে?', 'answer': 'ΔL=αLΔT=12×10⁻⁶×2×50=0.0012 m=1.2 mm।', 'moon': 'Moon AI: রৈখিক সম্প্রসারণে মূল দৈর্ঘ্য ও তাপমাত্রা পরিবর্তন দুটোই গুরুত্বপূর্ণ।'}, {'id': 21, 'chapter': 'তাপ', 'question': 'বাষ্পীভবনে ঠান্ডা লাগে কেন?', 'answer': 'উচ্চ গতিশক্তির অণুগুলো তরল ছেড়ে বের হয়ে যায়; অবশিষ্ট অণুর গড় গতিশক্তি কমে, তাই তাপমাত্রা কমে।', 'moon': 'Moon AI: বাষ্পীভবন শুধু পৃষ্ঠে ঘটে এবং এটি আশপাশ থেকে সুপ্ত তাপ গ্রহণ করে।'}, {'id': 22, 'chapter': 'তরঙ্গ', 'question': 'f=250 Hz এবং λ=1.2 m হলে তরঙ্গের বেগ কত?', 'answer': 'v=fλ=250×1.2=300 m/s।', 'moon': 'Moon AI: তরঙ্গের বেগ কম্পাঙ্ক ও তরঙ্গদৈর্ঘ্যের গুণফল।'}, {'id': 23, 'chapter': 'তরঙ্গ', 'question': 'একটি প্রতিধ্বনি 0.8 s পরে শোনা যায়। শব্দের বেগ 340 m/s হলে দেয়ালের দূরত্ব কত?', 'answer': 'd=vt/2=340×0.8/2=136 m।', 'moon': 'Moon AI: শব্দ গিয়ে ফিরে আসে, তাই মোট পথ 2d; এজন্য 2 দিয়ে ভাগ করতে হয়।'}, {'id': 24, 'chapter': 'শব্দ', 'question': 'শব্দের বেগ 340 m/s এবং কম্পাঙ্ক 680 Hz। তরঙ্গদৈর্ঘ্য কত?', 'answer': 'λ=v/f=340/680=0.5 m।', 'moon': 'Moon AI: v=fλ থেকে λ বের করলে v/f পাওয়া যায়।'}, {'id': 25, 'chapter': 'শব্দ', 'question': 'কোনো শব্দের তীব্রতা বাড়ালে মানুষের কানে কী পরিবর্তন বেশি অনুভূত হয়?', 'answer': 'শব্দের জোর বা loudness বৃদ্ধি পায়; এটি মূলত বিস্তার/তীব্রতার সঙ্গে সম্পর্কিত।', 'moon': 'Moon AI: কম্পাঙ্ক মূলত pitch নির্ধারণ করে, আর বিস্তার/তীব্রতা loudness-এর সঙ্গে বেশি সম্পর্কিত।'}, {'id': 26, 'chapter': 'আলো', 'question': 'সমতল দর্পণের সামনে বস্তু 2 m দূরে। বিম্ব কোথায় হবে এবং বস্তু-বিম্ব দূরত্ব কত?', 'answer': 'বিম্ব দর্পণের পেছনে 2 m; বস্তু-বিম্ব দূরত্ব=4 m।', 'moon': 'Moon AI: সমতল দর্পণে বস্তু ও বিম্বের দর্পণ থেকে দূরত্ব সমান।'}, {'id': 27, 'chapter': 'আলো', 'question': 'অবতল দর্পণের f=10 cm, বস্তু u=30 cm। দর্পণ সমীকরণে বিম্বের অবস্থান নির্ণয় করো (মান convention অনুযায়ী)।', 'answer': '1/f=1/v+1/u; প্রচলিত কার্টেসিয়ান convention-এ f=−10, u=−30 ⇒ 1/v=−1/10+1/30=−1/15 ⇒ v=−15 cm।', 'moon': 'Moon AI: sign convention ঠিক রাখা জরুরি; v ঋণাত্মক মানে বিম্ব দর্পণের সামনে বাস্তব বিম্ব।'}, {'id': 28, 'chapter': 'আলো', 'question': 'একটি উত্তল লেন্সের focal length 20 cm। object 60 cm দূরে। v কত?', 'answer': '1/f=1/v−1/u; f=20, u=−60 ⇒ 1/v=1/20−1/60=1/30 ⇒ v=30 cm।', 'moon': 'Moon AI: লেন্সের sign convention ব্যবহার করে reciprocal যোগ-বিয়োগ করতে হয়।'}, {'id': 29, 'chapter': 'আলো', 'question': 'আলোর প্রতিফলনের প্রথম সূত্র কী?', 'answer': 'আপতিত রশ্মি, প্রতিফলিত রশ্মি ও অভিলম্ব একই সমতলে থাকে।', 'moon': 'Moon AI: প্রতিফলন বিশ্লেষণে normal বা অভিলম্বকে reference হিসেবে ধরতে হয়।'}, {'id': 30, 'chapter': 'প্রতিসরণ', 'question': 'বায়ু থেকে কাঁচে আলো গেলে সাধারণত বেগ কমে কেন?', 'answer': 'কাঁচের প্রতিসরণাঙ্ক বেশি; v=c/n, তাই n বাড়লে মাধ্যমে আলোর বেগ কমে।', 'moon': 'Moon AI: মাধ্যম বদলালে frequency অপরিবর্তিত থাকে, কিন্তু বেগ ও wavelength পরিবর্তিত হয়।'}, {'id': 31, 'chapter': 'প্রতিসরণ', 'question': 'কাঁচের n=1.5 এবং বায়ুতে c=3×10^8 m/s। কাঁচে আলোর বেগ কত?', 'answer': 'v=c/n=3×10^8/1.5=2×10^8 m/s।', 'moon': 'Moon AI: প্রতিসরণাঙ্ক হলো শূন্যস্থানের বেগ ও মাধ্যমের বেগের অনুপাত।'}, {'id': 32, 'chapter': 'স্থির তড়িৎ', 'question': 'দুটি আধান q1=2 μC, q2=3 μC, দূরত্ব 0.3 m। k=9×10^9 হলে বল কত?', 'answer': 'F=kq1q2/r²=9×10^9×2×10⁻⁶×3×10⁻⁶/0.09=0.6 N।', 'moon': 'Moon AI: আধানের একক microcoulomb থেকে coulomb-এ রূপান্তর না করলে উত্তর ভুল হবে।'}, {'id': 33, 'chapter': 'স্থির তড়িৎ', 'question': 'একটি 4 C আধানকে 20 J কাজ করে সরানো হলো। বিভব পার্থক্য কত?', 'answer': 'V=W/q=20/4=5 V।', 'moon': 'Moon AI: প্রতি একক আধানের জন্য কাজের পরিমাণই বিভব পার্থক্য।'}, {'id': 34, 'chapter': 'স্থির তড়িৎ', 'question': 'দুটি সমান ধনাত্মক আধানের মাঝবিন্দুতে তড়িৎ ক্ষেত্র কেমন?', 'answer': 'মাঝবিন্দুতে দুই আধানের ক্ষেত্র বিপরীতমুখী ও সমান, তাই নিট ক্ষেত্র শূন্য।', 'moon': 'Moon AI: electric field ভেক্টর; শুধু মান নয়, দিকও বিবেচনা করতে হয়।'}, {'id': 35, 'chapter': 'চল তড়িৎ', 'question': '6 Ω ও 3 Ω রোধ সমান্তরালে যুক্ত। সমতুল্য রোধ কত?', 'answer': '1/R=1/6+1/3=1/2 ⇒ R=2 Ω।', 'moon': 'Moon AI: parallel circuit-এ reciprocal যোগ হয় এবং সমতুল্য রোধ সবসময় ক্ষুদ্রতম রোধের চেয়েও কম।'}, {'id': 36, 'chapter': 'চল তড়িৎ', 'question': '4 Ω ও 8 Ω রোধ শ্রেণিতে 24 V-এর সাথে যুক্ত। মোট প্রবাহ কত?', 'answer': 'Req=12 Ω; I=V/R=24/12=2 A।', 'moon': 'Moon AI: series-এ রোধ যোগ হয় এবং একই current সব রোধে প্রবাহিত হয়।'}, {'id': 37, 'chapter': 'চল তড়িৎ', 'question': 'একটি 100 W বাল্ব 5 ঘণ্টা জ্বললে কত বৈদ্যুতিক শক্তি খরচ হয়?', 'answer': 'E=Pt=100×5×3600=1.8×10^6 J=0.5 kWh।', 'moon': 'Moon AI: watt হলো joule/second; kWh হলো শক্তির ব্যবহারিক একক।'}, {'id': 38, 'chapter': 'চল তড়িৎ', 'question': '220 V, 1100 W হিটারের রোধ কত?', 'answer': 'R=V²/P=220²/1100=44 Ω।', 'moon': 'Moon AI: P=V²/R থেকে সরাসরি R=V²/P পাওয়া যায়।'}, {'id': 39, 'chapter': 'চৌম্বক ক্রিয়া', 'question': 'চৌম্বক ক্ষেত্রে current-carrying wire-এর ওপর বল কোন কোন রাশির ওপর নির্ভর করে?', 'answer': 'F=BIL sinθ; তাই B, current I, দৈর্ঘ্য L এবং কোণ θ-এর ওপর নির্ভর করে।', 'moon': 'Moon AI: তার ও field সমান্তরাল হলে sin0=0, তাই বল শূন্য।'}, {'id': 40, 'chapter': 'তড়িৎচৌম্বক আবেশ', 'question': 'চুম্বককে coil-এর দিকে দ্রুত সরালে induced emf কেন বাড়ে?', 'answer': 'চৌম্বক ফ্লাক্সের পরিবর্তনের হার বাড়ে; Faraday-এর সূত্রে emf ∝ dΦ/dt।', 'moon': 'Moon AI: শুধু চুম্বক থাকা যথেষ্ট নয়; flux পরিবর্তন হওয়াই induced emf-এর মূল কারণ।'}, {'id': 41, 'chapter': 'ট্রান্সফরমার', 'question': 'একটি ideal transformer-এ Np=1000, Ns=200 এবং Vp=220 V। Vs কত?', 'answer': 'Vs/Vp=Ns/Np=200/1000; Vs=44 V।', 'moon': 'Moon AI: turns ratio কম হলে step-down transformer হয়।'}, {'id': 42, 'chapter': 'আধুনিক পদার্থবিজ্ঞান', 'question': 'একটি ফোটনের শক্তি frequency বাড়লে কী হয়?', 'answer': 'E=hf; frequency বাড়লে photon energy সরাসরি বাড়ে।', 'moon': 'Moon AI: Planck constant ধ্রুব, তাই frequency দ্বিগুণ হলে energy-ও দ্বিগুণ।'}, {'id': 43, 'chapter': 'আধুনিক পদার্থবিজ্ঞান', 'question': 'ভর ও শক্তির সমতুল্যতা কোন সূত্রে প্রকাশিত?', 'answer': 'E=mc²।', 'moon': 'Moon AI: খুব অল্প ভরও c² বড় হওয়ায় বিপুল শক্তির সমতুল্য হতে পারে।'}, {'id': 44, 'chapter': 'ইলেকট্রনিক্স', 'question': 'ডায়োডকে rectifier হিসেবে ব্যবহার করা যায় কেন?', 'answer': 'ডায়োড মূলত একদিকে current প্রবাহে সহজ এবং বিপরীত দিকে বাধা দেয়, তাই AC-এর একমুখী রূপ দিতে ব্যবহার করা যায়।', 'moon': 'Moon AI: diode-এর একমুখী conduction-ই rectification-এর ভিত্তি।'}, {'id': 45, 'chapter': 'মিশ্র ও সমন্বিত', 'question': 'একটি 1000 kg গাড়ি 10 m/s থেকে 20 m/s হলো। kinetic energy কত বেড়েছে?', 'answer': 'ΔK=½×1000×(20²−10²)=150000 J।', 'moon': 'Moon AI: বেগ দ্বিগুণ করলে kinetic energy চারগুণ হয়—তাই পরিবর্তনটি linear নয়।'}, {'id': 46, 'chapter': 'মিশ্র ও সমন্বিত', 'question': 'একটি 60 kg মানুষ 5 m উচ্চ সিঁড়ি 10 s-এ ওঠে। গড় ক্ষমতা কত? g=9.8।', 'answer': 'P=mgh/t=60×9.8×5/10=294 W।', 'moon': 'Moon AI: শরীরের করা উপযোগী কাজকে সময় দিয়ে ভাগ করলে গড় ক্ষমতা পাওয়া যায়।'}, {'id': 47, 'chapter': 'মিশ্র ও সমন্বিত', 'question': 'একটি বস্তু 3 m/s থেকে 9 m/s হয় 3 s-এ। uniform acceleration ধরে শেষ 3 s-এ গড় বেগ কত?', 'answer': 'Uniform acceleration-এ average velocity=(u+v)/2=(3+9)/2=6 m/s।', 'moon': 'Moon AI: ধ্রুব ত্বরণে সময়পর্বের গড় বেগ প্রান্তিক বেগ দুটির গড়ের সমান।'}, {'id': 48, 'chapter': 'মিশ্র ও সমন্বিত', 'question': 'একটি 2 kg বস্তু 10 m উচ্চতা থেকে পড়ে এবং 40 J শক্তি ঘর্ষণে হারায়। ভূমিতে kinetic energy কত? g=10।', 'answer': 'প্রাথমিক Ep=mgh=200 J; ক্ষতি 40 J; তাই K=160 J।', 'moon': 'Moon AI: শক্তি সংরক্ষণে ঘর্ষণ যান্ত্রিক শক্তির একটি অংশ তাপে রূপান্তর করে।'}, {'id': 49, 'chapter': 'মিশ্র ও সমন্বিত', 'question': 'একটি 12 V battery-তে 6 Ω এবং 3 Ω parallel branch। মোট current কত?', 'answer': 'Req=2 Ω; I=V/Req=12/2=6 A।', 'moon': 'Moon AI: আগে parallel equivalent resistance, তারপর Ohm-এর সূত্র প্রয়োগ করো।'}, {'id': 50, 'chapter': 'চৌম্বক ক্রিয়া', 'question': 'একটি 0.5 m তারে 4 A current এবং B=0.2 T, তারটি ক্ষেত্রের সাথে 90° কোণে। বল কত?', 'answer': 'F=BIL=0.2×4×0.5=0.4 N।', 'moon': 'Moon AI: 90° হলে sinθ=1, তাই F=BIL সর্বাধিক।'}]
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

    teach_cmd = extract_teach_command(text)
    if teach_cmd:
        ok = moon_learn(**teach_cmd)
        return "Moon AI শিখেছে। এখন এই জ্ঞান প্রশ্নের উত্তরে ব্যবহার করতে পারবে।" if ok else "শেখানো তথ্য সংরক্ষণ করা যায়নি।"
    learned = extract_save_command(text)
    if learned is not None:
        ok = moon_learn(learned, domain="general")
        return "Moon AI শিখেছে।" if ok else "তথ্যটি শেখানো যায়নি।"

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
    for item in CQ_PROBLEMS:
        qkey = item["question"].lower()
        if any(token in lower for token in [str(item["id"]), item["chapter"].lower()]) and any(x in lower for x in ["cq", "সমস্যা", "problem", "solve", "সমাধান", "ব্যাখ্যা"]):
            return f"**CQ {item['id']} — {item['chapter']}**\n\nপ্রশ্ন: {item['question']}\n\nউত্তর: {item['answer']}\n\nMoon AI ব্যাখ্যা: {item['moon']}"
        if any(w in lower for w in re.findall(r'[\u0980-\u09FFA-Za-z0-9]+', qkey) if len(w)>4) and len(lower)>8:
            return f"**CQ {item['id']} — {item['chapter']}**\n\nপ্রশ্ন: {item['question']}\n\nউত্তর: {item['answer']}\n\nMoon AI ব্যাখ্যা: {item['moon']}"

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
    learned_brain = brain_reply(text)
    if learned_brain:
        return learned_brain
    learned_matches = find_learning_matches(text, knowledge)
    if learned_matches:
        return "আমি শেখা তথ্য থেকে যা মিল পাচ্ছি:\n\n" + "\n".join(f"- {x}" for x in learned_matches)
    return f"তোমার প্রশ্ন: **{text}**\n\nআমি Moon AI হিসেবে local knowledge ও reasoning rules ব্যবহার করছি। Physics-এর পাশাপাশি ভবিষ্যতে Chemistry, Biology, Mathematics ও অন্যান্য domain-এর knowledge যোগ করা যাবে। প্রশ্নটি নির্দিষ্ট করলে ধাপে ধাপে উত্তর দেব।"


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
    html, body, [class*="css"], .stApp {{
        font-family: Inter, 'Noto Sans Bengali', 'Noto Sans', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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
        font-size: 0.94rem;
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
        padding: 22px 20px; border: 1px solid rgba(56,189,248,.20); border-radius: 24px;
        background: radial-gradient(circle at top right, rgba(56,189,248,.16), transparent 40%), rgba(15,23,42,.78);
        box-shadow: 0 18px 55px rgba(0,0,0,.25);
    }}
    .moon-badge {{ width:44px; height:44px; border-radius:50%; display:inline-flex; align-items:center;
        justify-content:center; background:#38bdf8; color:#07111f; font-size:24px; font-weight:700;
        box-shadow:0 0 30px rgba(56,189,248,.35); }}
    .moon-logo {{ width:42px; height:42px; object-fit:contain; vertical-align:middle;
        filter: drop-shadow(0 0 14px rgba(56,189,248,.42)); }}
    .moon-logo {{ width:42px; height:42px; object-fit:contain; vertical-align:middle;
        filter: drop-shadow(0 0 12px rgba(56,189,248,.38)); }}
    div[data-testid="stChatMessage"] {{
        margin: 6px 0 !important; padding: 0 !important;
    }}
    div[data-testid="stChatMessageContent"] {{
        font-size: .90rem !important; line-height: 1.55 !important;
    }}
    div[data-testid="stChatMessageAvatar"] img {{
        width: 30px !important; height: 30px !important;
        border-radius: 50% !important; object-fit: cover !important;
    }}
    div[data-testid="stChatMessage"] > div:first-child {{
        padding-top: 2px !important;
    }}
    .premium-hero h1 {{ font-size: 1.45rem !important; font-weight: 700 !important; letter-spacing: -.02em; }}
    .premium-hero p {{ font-size: .82rem !important; }}
    div[data-testid="stExpander"] {{ border-radius: 14px !important; border: 1px solid rgba(148,163,184,.12) !important; }}
    .stMarkdown, .stCaption, .stText {{ font-size: .92rem; }}
    .history-panel {{
        margin: 4px 0 18px 0; padding: 10px; max-width: 420px;
        border: 1px solid rgba(148,163,184,.14); border-radius: 16px;
        background: rgba(15,23,42,.88); backdrop-filter: blur(16px);
        box-shadow: 0 16px 40px rgba(0,0,0,.22);
    }}
    .history-title {{ font-size: .78rem; color: #94a3b8; padding: 4px 8px 8px; }}
    div[data-testid="column"] .stButton > button[key^="top_"] {{
        width: 42px !important; height: 38px !important; min-height: 38px !important;
        padding: 0 !important; border-radius: 12px !important;
        font-size: 1.05rem !important; background: rgba(15,23,42,.72) !important;
        border: 1px solid rgba(148,163,184,.16) !important;
    }}
    .chat-brand {{ display:flex; align-items:center; gap:12px; margin: 4px 0 18px; }}
    .crescent {{ position:relative; width:42px; height:42px; border-radius:50%; background:linear-gradient(135deg,#38bdf8,#60a5fa); box-shadow:0 0 28px rgba(56,189,248,.28); }}
    .crescent:after {{ content:""; position:absolute; width:34px; height:34px; border-radius:50%; background:#0b1325; left:12px; top:4px; }}
    .brand-title {{ font-size:1.35rem; font-weight:700; letter-spacing:-.02em; }}
    .brand-sub {{ font-size:.76rem; color:#94a3b8; margin-top:2px; }}
    
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 6. CHATGPT / GEMINI-STYLE TOP BAR
# ==========================================
# Two compact controls stay at the upper-left of every page:
# 1) New chat  2) Chat history
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
# 6. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<div style='font-size:.78rem;color:#94a3b8;letter-spacing:.08em;text-transform:uppercase;padding:4px 2px 10px;'>Moon AI</div>", unsafe_allow_html=True)

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
    if st.button(ui("cq")):
        st.session_state.current_page = "CQ Solve"
        st.rerun()
    if st.button(ui("moon")):
        st.session_state.current_page = "Physics Bot"
        st.rerun()
    if st.button("🧠  Moon AI Learning Lab"):
        st.session_state.current_page = "Learning Lab"
        st.rerun()

    if st.button(ui("settings")):
        st.session_state.current_page = "Theme Settings"
        st.rerun()


# ==========================================
# 7. HOME SCREEN
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='premium-hero'><span class='crescent'></span><h1 style='display:inline-block;margin-left:14px;color:#38BDF8;'>পদার্থবিজ্ঞান অনুশীলন ক্লাব</h1><p style='text-align:center;color:#38BDF8;font-weight:700;letter-spacing:2px;'>MOON AI PHYSICS EXPERIENCE</p></div>", unsafe_allow_html=True)
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
        border: 1px solid rgba(125,211,252,.35);
        border-radius: 14px;
        padding: 12px 20px;
        font-weight: 800;
        cursor: pointer;
        background: linear-gradient(180deg,#38bdf8,#0ea5e9);
        color: #06101c;
        font-size: 14px;
        box-shadow: 0 8px 22px rgba(14,165,233,.20);
    }
    .svgico { display:inline-flex; width:25px; height:25px; align-items:center; justify-content:center; border-radius:8px; background:rgba(255,255,255,.28); margin-right:6px; vertical-align:middle; }
    .svgico svg { width:17px; height:17px; fill:none; stroke:currentColor; stroke-width:2.2; stroke-linecap:round; stroke-linejoin:round; }
    #startBtn .svgico svg { fill:currentColor; stroke:none; }

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
                <button id="startBtn" style="min-width:210px;font-size:17px;"><span class="svgico"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg></span> START GAME</button>
            </div>
        </div>
    </div>

    <div id="controls">
        <button id="jumpBtn"><span class="svgico"><svg viewBox="0 0 24 24"><path d="M12 19V5m0 0L6 11m6-6 6 6"/></svg></span> JUMP</button>
        <button id="duckBtn"><span class="svgico"><svg viewBox="0 0 24 24"><path d="M12 5v14m0 0-6-6m6 6 6-6"/></svg></span> DUCK</button>
        <button id="restartBtn"><span class="svgico"><svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 1 0 2 5"/><path d="M20 5v6h-6"/></svg></span> RESTART</button>
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
        ("11 · কক্ষপথে astronaut ভাসে কেন?", "Astronaut ও spacecraft দুটোই পৃথিবীর দিকে free fall-এ থাকে। Gravity শূন্য নয়; বরং orbital motion-এর জন্য তারা ক্রমাগত পড়ে যেতে যেতে পৃথিবীকে miss করে। তাই apparent weight প্রায় শূন্য।"),
        ("12 · উপগ্রহ কেন পৃথিবীতে পড়ে যায় না?", "Satellite-এর tangential velocity যথেষ্ট হওয়ায় gravity তাকে বক্রপথে টানে। সে পৃথিবীর দিকে পড়ে, কিন্তু পৃথিবীর curvature-এর সঙ্গে তাল মিলিয়ে সামনে এগোয়।"),
        ("13 · গাড়ির tyre-এ tread কেন থাকে?", "Tread জল সরিয়ে contact ও grip বজায় রাখতে সাহায্য করে এবং wet road-এ hydroplaning কমাতে পারে। এটি frictional traction উন্নত করে।"),
        ("14 · গরম চায়ে চামচ ধাতব হলে হাত গরম লাগে কেন?", "ধাতুতে thermal conductivity বেশি। চামচের গরম অংশ থেকে তাপ দ্রুত হাতের দিকে পরিবাহিত হয়। কাঠ/প্লাস্টিক তুলনায় খারাপ conductor।"),
        ("15 · একই ভোল্টেজে কম রোধের যন্ত্র বেশি power নেয় কেন?", "P=V²/R। V ধ্রুব হলে R কমলে power বাড়ে। তাই low-resistance load একই voltage-এ বেশি current টানে।"),
        ("16 · parallel circuit-এ একটি bulb নষ্ট হলে অন্যটি কেন জ্বলে?", "Parallel branch-গুলো আলাদা path তৈরি করে। একটি branch open হলেও অন্য branch-এ current চলতে পারে। Series circuit-এ একটি open হলে পুরো path ভেঙে যায়।"),
        ("17 · transformer DC-তে স্বাভাবিকভাবে কাজ করে না কেন?", "Transformer induction-এর জন্য পরিবর্তনশীল magnetic flux দরকার। Steady DC-তে switch-on-এর ক্ষণ ছাড়া flux পরিবর্তন থাকে না, তাই continuous induced emf পাওয়া যায় না।"),
        ("18 · optical fibre-এ আলো দূরে যায় কীভাবে?", "Core-এর refractive index cladding-এর চেয়ে বেশি হলে suitable angle-এ total internal reflection ঘটে। আলো বারবার internal reflection করে দীর্ঘ পথ অতিক্রম করে।"),
        ("19 · আকাশ নীল কেন?", "বায়ুর অণু ছোট wavelength-এর আলো বেশি Rayleigh scattering করে। নীল/বেগুনি বেশি scatter হলেও চোখের sensitivity ও সূর্যালোকের spectrum-এর কারণে আকাশ নীল দেখায়।"),
        ("20 · সূর্যাস্তে আকাশ লাল কেন?", "সূর্যাস্তে আলোকে atmosphere-এর মধ্যে বেশি দূরত্ব অতিক্রম করতে হয়। Short wavelength বেশি scatter হয়ে যায়; চোখে পৌঁছানো direct light-এ red/orange অংশ তুলনামূলক বেশি থাকে।"),
    ]
    for title, explanation in critical_topics:
        with st.expander(title):
            st.write(explanation)
            st.info("Moon AI বিশ্লেষণ: কারণ → সূত্র/নীতি → বাস্তব ফল—এই তিন ধাপে বিষয়টি ভাঙলে ধারণাটি পরিষ্কার হয়।")

    st.markdown("### 🔬 Critical problem-solving toolkit")
    toolkit = [
        ("Free-body diagram", "প্রথমে সব বাহ্যিক বল আঁকো; তারপর প্রতিটি অক্ষ বরাবর ΣF=ma লেখো।"),
        ("Energy method", "সময় জটিল হলে W_net=ΔK বা শক্তি সংরক্ষণ ব্যবহার করো।"),
        ("Momentum method", "সংঘর্ষ/বিস্ফোরণে impulse ও momentum conservation বেশি কার্যকর।"),
        ("Sign convention", "দিককে positive ধরে সব displacement, velocity ও acceleration-এর sign একইভাবে রাখো।"),
        ("Units check", "শেষ উত্তরের unit দিয়ে সূত্রের ভুল ধরো—যেমন force অবশ্যই N, energy J।"),
        ("Limiting case", "কোনো মান 0 বা খুব বড় হলে সূত্রের ফল বাস্তবসম্মত কি না যাচাই করো।"),
    ]
    for name, text in toolkit:
        st.markdown(f"**{name}:** {text}")

    with st.expander(" গুরুত্বপূর্ণ সূত্র ও প্রতিপাদন"):
        st.latex(r"v=u+at")
        st.latex(r"s=ut+\frac{1}{2}at^2")
        st.latex(r"v^2=u^2+2as")
        st.latex(r"W_{net}=\Delta K")
        st.latex(r"P=\frac{W}{t},\quad Q=mc\Delta T")
        st.latex(r"F_b=\rho Vg,\quad P=\rho gh")
        st.latex(r"V=IR,\quad P=VI=I^2R=\frac{V^2}{R}")


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

    st.title("CQ Solve — ৫০টি উন্নত Physics Problem")
    st.caption("১৪টি অধ্যায়/থিম থেকে ৫০টি সৃজনশীল সমস্যা। প্রতিটির উত্তর, reasoning এবং Moon AI explanation দেওয়া আছে।")
    st.markdown("---")

    chapters = ["সব অধ্যায়"] + sorted({x["chapter"] for x in CQ_PROBLEMS})
    selected = st.selectbox("অধ্যায় বেছে নিন", chapters)
    filtered = CQ_PROBLEMS if selected == "সব অধ্যায়" else [x for x in CQ_PROBLEMS if x["chapter"] == selected]

    for item in filtered:
        with st.expander(f"CQ {item['id']:02d} · {item['chapter']} · {item['question']}"):
            st.markdown("### প্রশ্ন")
            st.write(item["question"])
            st.markdown("### উন্নত উত্তর")
            st.success(item["answer"])
            st.markdown("### 🧠 Moon AI ব্যাখ্যা")
            st.info(item["moon"])
            st.caption("Moon AI-কে একই প্রশ্ন করলে এই CQ-এর reasoning database থেকে ব্যাখ্যাটি দিতে পারবে।")


# 12. LOCAL MINI-AI CHAT
# ==========================================
elif st.session_state.current_page == "Physics Bot":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.markdown(
        "<div class='premium-hero'><div class='chat-brand'><span class='crescent'></span><div><div class='brand-title'>Moon AI</div><div class='brand-sub'>A calm, intelligent learning companion</div></div></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    session = _active_session()
    for msg in session["messages"]:
        if msg["role"] == "user":
            with st.chat_message("user", avatar=":material/person:"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar=":material/dark_mode:"):
                st.write(msg["content"])

    user_query = st.chat_input("Moon AI-কে প্রশ্ন করুন…")

    if user_query:
        session["messages"].append({"role": "user", "content": user_query})
        if session.get("title") == "নতুন চ্যাট":
            session["title"] = user_query[:42] + ("…" if len(user_query) > 42 else "")
        with st.chat_message("user", avatar=":material/person:"):
            st.write(user_query)
        reply = local_ai_reply(user_query)
        session["messages"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant", avatar=":material/dark_mode:"):
            st.write(reply)
        st.session_state.chat_history = session["messages"]
        if extract_save_command(user_query) is not None or extract_teach_command(user_query) is not None:
            st.rerun()


# ==========================================
# 13. MOON AI LEARNING LAB
# ==========================================
elif st.session_state.current_page == "Learning Lab":
    if st.button("‹  হোমে ফিরে যান", key="lab_home"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🧠 Moon AI Learning Lab")
    st.caption("এখান থেকে Moon AI-কে দ্রুত ও কাঠামোবদ্ধভাবে শেখাতে পারবেন। শেখানো তথ্য executable code নয়—structured knowledge হিসেবে সংরক্ষিত হয়।")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["⚡ দ্রুত শেখান", "🎓 প্রশ্ন-উত্তর শেখান", "📦 Brain Backup", "🧩 Future AI Modules"])

    with tab1:
        st.subheader("এক লাইনে দ্রুত শেখানো")
        st.code("if #(পৃথিবীর g প্রায় 9.8 m/s²) save", language="text")
        fast = st.text_input("Learning command", placeholder="if #(তথ্য) save")
        if st.button("Moon AI-কে শেখান", key="fast_learn"):
            if extract_save_command(fast):
                ok=moon_learn(extract_save_command(fast), domain="general")
                st.success("Moon AI শিখেছে।" if ok else "সংরক্ষণ ব্যর্থ হয়েছে।")
            else:
                st.warning("এই format ব্যবহার করুন: if #(তথ্য) save")

        st.subheader("Batch learning")
        batch=st.text_area("এক লাইনে একটি তথ্য দিন", height=180, placeholder="পানি H₂O\nআলোর বেগ প্রায় 3×10⁸ m/s\nDNA genetic information বহন করে")
        domain=st.selectbox("Domain", ["general","physics","chemistry","biology","mathematics","computer science","language"])
        if st.button("সবগুলো একসাথে শেখান", key="batch_learn"):
            items=[x.strip() for x in batch.splitlines() if x.strip()]
            ok=sum(1 for x in items if moon_learn(x,domain=domain))
            st.success(f"{ok}টি তথ্য শেখানো হয়েছে।")

    with tab2:
        st.subheader("প্রশ্ন → উত্তর → ব্যাখ্যা")
        q=st.text_input("প্রশ্ন")
        a=st.text_area("উত্তর")
        ex=st.text_area("Moon AI কীভাবে বুঝিয়ে বলবে?")
        d=st.selectbox("বিষয়", ["general","physics","chemistry","biology","mathematics","computer science"])
        tags=st.text_input("Tags (comma separated)")
        if st.button("এই lesson শেখান", key="lesson_learn"):
            if q and a:
                ok=moon_learn("",domain=d,question=q,answer=a,explanation=ex,tags=[x.strip() for x in tags.split(",") if x.strip()])
                st.success("Lesson Moon AI-এর brain-এ যোগ হয়েছে।" if ok else "Lesson save হয়নি।")
            else: st.warning("প্রশ্ন ও উত্তর দুটোই দিন।")

    with tab3:
        brain=load_brain()
        st.metric("Learned lessons", len(brain.get("entries",[])))
        st.download_button("⬇️ Brain JSON export", json.dumps(brain,ensure_ascii=False,indent=2), file_name="moon_ai_brain.json", mime="application/json")
        uploaded=st.file_uploader("আগের Brain JSON import করুন", type=["json"], key="brain_import")
        if uploaded is not None and st.button("Brain import করুন", key="brain_import_btn"):
            try:
                data=json.loads(uploaded.getvalue().decode("utf-8"))
                if isinstance(data,dict) and isinstance(data.get("entries"),list):
                    data["version"]=BRAIN_VERSION
                    save_brain(data)
                    st.success("Brain import সম্পন্ন হয়েছে।")
                    st.rerun()
                else: st.error("এটি Moon AI Brain JSON নয়।")
            except Exception as e: st.error(f"Import ব্যর্থ: {e}")

    with tab4:
        st.subheader("বড় AI হওয়ার জন্য modular architecture")
        st.markdown("""
- **Knowledge Engine:** Physics → Chemistry → Biology → Mathematics → General knowledge একই brain-এ রাখা যাবে।
- **Reasoning Engine:** শেখানো প্রশ্নের উত্তর + explanation আলাদা করে রাখা যায়।
- **Language Engine:** বাংলা/English এবং ভবিষ্যতে আরও ভাষা।
- **Text Analysis:** শব্দ, বাক্য, keyword, topic ও intent analysis-এর জন্য hook প্রস্তুত।
- **Vision Module:** ছবি upload/vision model connector যোগ করার জন্য আলাদা module boundary রাখা হয়েছে।
- **Model Backend:** ভবিষ্যতে local LLM বা অনুমোদিত AI API বসানো যাবে—UI ও knowledge engine না বদলিয়েও।
        """)
        st.info("গুরুত্বপূর্ণ: শুধু rule/JSON memory দিয়ে Moon AI নিজে থেকে মানুষের মতো সাধারণ AI হয়ে যাবে না। তার জন্য পরে একটি language model/reasoning model backend লাগবে। এই version সেই expansion-এর ভিত্তি তৈরি করছে।")


# ==========================================
# 14. THEME & GALLERY BACKGROUND SETTINGS
# ==========================================
elif st.session_state.current_page == "Theme Settings":
    if st.button("‹  হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("⚙  Settings / সেটিংস")
    st.caption("অ্যাপের ভাষা, থিম, ব্যাকগ্রাউন্ড এবং Moon AI learning control এক জায়গায়।")
    st.markdown("---")

    st.subheader("🌐 বিশেষ Language Change Option")
    lang = st.selectbox("App / Moon AI ভাষা", ["বাংলা", "English"], index=0 if st.session_state.language == "বাংলা" else 1)
    if st.button("ভাষা প্রয়োগ করুন / Apply Language", key="apply_language"):
        st.session_state.language = lang
        st.success("ভাষা পরিবর্তন করা হয়েছে। নতুন navigation label পরের render-এ দেখা যাবে।")
        st.rerun()

    st.subheader("🎨 Appearance")
    theme = st.radio("থিম", ["Dark Premium", "Midnight Blue"], horizontal=True)
    if theme == "Midnight Blue":
        st.markdown("<style>.stApp{background:#07152a!important}</style>", unsafe_allow_html=True)

    st.subheader("🖼️ Background")
    uploaded_file = st.file_uploader("গ্যালারি থেকে JPG/PNG বেছে নিন", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.session_state.bg_image = base64.b64encode(uploaded_file.getvalue()).decode()
        st.success("Background আপডেট হয়েছে।")
    if st.session_state.bg_image and st.button("Default background ফিরিয়ে আনুন"):
        st.session_state.bg_image = None
        st.rerun()

    st.subheader("🤖 Moon AI Controls")
    st.session_state.ai_explain = st.checkbox("Moon AI-এর উত্তরগুলোতে ধাপে ধাপে explanation দেখান", value=st.session_state.ai_explain, key="ai_explain_box")
    st.session_state.ai_cq = st.checkbox("CQ-এর উত্তর থেকে Moon AI reasoning ব্যবহার করুন", value=st.session_state.ai_cq, key="ai_cq_box")
    st.info("দ্রুত শেখাতে sidebar-এর **Moon AI Learning Lab** ব্যবহার করুন।")
    if st.button("সব শেখা তথ্য মুছে ফেলুন"):
        delete_all_memory()
        st.success("সব শেখা তথ্য পরিষ্কার করা হয়েছে।")
        st.rerun()


