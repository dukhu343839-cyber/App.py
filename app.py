
import streamlit as st
import sqlite3, json, re, math, ast, operator as op, hashlib, time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "moon_data"
MODEL_DIR = DATA_DIR / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "moon_brain.db"

st.set_page_config(page_title="Moon AI", page_icon="☾", layout="wide")

# ============================================================
# 1) LOCAL BRAIN — SQLite + FTS5
# ============================================================
def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("""
    CREATE TABLE IF NOT EXISTS knowledge(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      domain TEXT NOT NULL DEFAULT 'general',
      question TEXT DEFAULT '',
      answer TEXT NOT NULL,
      explanation TEXT DEFAULT '',
      tags TEXT DEFAULT '',
      source TEXT DEFAULT 'user',
      created_at REAL NOT NULL,
      updated_at REAL NOT NULL,
      hash TEXT UNIQUE
    )""")
    con.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts
    USING fts5(question,answer,explanation,tags,domain,content='knowledge',content_rowid='id')""")
    con.execute("""CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge BEGIN
      INSERT INTO knowledge_fts(rowid,question,answer,explanation,tags,domain)
      VALUES(new.id,new.question,new.answer,new.explanation,new.tags,new.domain);
    END""")
    con.execute("""CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge BEGIN
      INSERT INTO knowledge_fts(knowledge_fts,rowid,question,answer,explanation,tags,domain)
      VALUES('delete',old.id,old.question,old.answer,old.explanation,old.tags,old.domain);
    END""")
    con.commit()
    return con

def add_knowledge(domain, question, answer, explanation="", tags="", source="user"):
    answer=(answer or "").strip()
    if not answer: return False,"উত্তর/তথ্য খালি রাখা যাবে না।"
    vals=[(domain or "general").strip(),(question or "").strip(),answer,
          (explanation or "").strip(),(tags or "").strip(),source]
    h=hashlib.sha256(json.dumps(vals,ensure_ascii=False).encode()).hexdigest()
    con=db()
    try:
        now=time.time()
        con.execute("""INSERT INTO knowledge(domain,question,answer,explanation,tags,source,created_at,updated_at,hash)
        VALUES(?,?,?,?,?,?,?,?,?)""",(*vals,now,now,h))
        con.commit(); return True,"Moon AI শিখেছে।"
    except sqlite3.IntegrityError:
        return False,"এই তথ্যটি Brain-এ আগে থেকেই আছে।"
    finally: con.close()

def search_knowledge(query, limit=8):
    tokens=[x for x in re.findall(r"[\u0980-\u09FFA-Za-z0-9]+",query.casefold()) if len(x)>1]
    con=db(); rows=[]
    if tokens:
        fts=" OR ".join('"'+x.replace('"','')+'"' for x in tokens[:14])
        try:
            rows=con.execute("""SELECT k.id,k.domain,k.question,k.answer,k.explanation,k.tags,k.source
            FROM knowledge_fts f JOIN knowledge k ON k.id=f.rowid
            WHERE knowledge_fts MATCH ? ORDER BY bm25(knowledge_fts) LIMIT ?""",(fts,limit)).fetchall()
        except sqlite3.Error: pass
    if not rows:
        like=f"%{query}%"
        rows=con.execute("""SELECT id,domain,question,answer,explanation,tags,source FROM knowledge
        WHERE question LIKE ? OR answer LIKE ? OR explanation LIKE ? OR tags LIKE ? OR domain LIKE ?
        ORDER BY updated_at DESC LIMIT ?""",(like,like,like,like,like,limit)).fetchall()
    con.close(); return rows

def brain_count():
    con=db(); n=con.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]; con.close(); return n

CORE=[
("physics","পৃথিবীর অভিকর্ষজ ত্বরণ g এর মান কত?","প্রায় 9.8 m/s²; অনেক স্কুল সমস্যায় 10 m/s² ধরা হয়।","g মুক্তপতনের ত্বরণ।","gravity"),
("physics","নিউটনের দ্বিতীয় সূত্র কী?","F = ma।","নিট বল ভর ও ত্বরণের গুণফলের সমান।","newton,force"),
("chemistry","পানির সংকেত কী?","H₂O।","দুই H ও এক O।","water"),
("biology","DNA কী বহন করে?","DNA বংশগত তথ্য বহন করে।","DNA-এর sequence জীবের বৈশিষ্ট্যের তথ্য বহন করে।","dna"),
("math","পিথাগোরাসের উপপাদ্য কী?","অতিভুজ² = ভূমি² + লম্ব²।","সমকোণী ত্রিভুজের বাহুগুলোর সম্পর্ক।","geometry"),
]
def seed():
    if brain_count(): return
    for x in CORE: add_knowledge(*x,source="core")
seed()

# ============================================================
# 2) SAFE MATH REASONING
# ============================================================
BIN={ast.Add:op.add,ast.Sub:op.sub,ast.Mult:op.mul,ast.Div:op.truediv,ast.Pow:op.pow,ast.Mod:op.mod,ast.FloorDiv:op.floordiv}
UN={ast.UAdd:op.pos,ast.USub:op.neg}
def calc(expr):
    tree=ast.parse(expr,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.BinOp) and type(n.op) in BIN: return BIN[type(n.op)](ev(n.left),ev(n.right))
        if isinstance(n,ast.UnaryOp) and type(n.op) in UN: return UN[type(n.op)](ev(n.operand))
        raise ValueError
    x=ev(tree)
    if isinstance(x,float) and not math.isfinite(x): raise ValueError
    return x

# ============================================================
# 3) LOCAL LANGUAGE MODEL ADAPTER
# ============================================================
@st.cache_resource(show_spinner=False)
def load_local_model(model_path):
    try:
        from llama_cpp import Llama
        return Llama(
            model_path=str(model_path),
            n_ctx=4096,
            n_threads=max(2, __import__("os").cpu_count() or 4),
            n_batch=256,
            verbose=False,
        )
    except Exception:
        return None

def available_models():
    return sorted(MODEL_DIR.glob("*.gguf"))

def selected_model_path():
    models = available_models()
    if not models:
        return None
    wanted = st.session_state.get("selected_model")
    if wanted:
        for p in models:
            if p.name == wanted:
                return p
    return models[0]

def model_answer(question, retrieved, history):
    model_path = selected_model_path()
    if model_path is None: return None, "no_model"
    llm=load_local_model(model_path)
    if llm is None: return None, "load_failed"

    context="\n\n".join(
        f"[{r[1]}] Q: {r[2]}\nA: {r[3]}\nExplanation: {r[4]}"
        for r in retrieved[:6]
    )
    recent="\n".join(f"{role}: {text}" for role,text in history[-8:])
    system=("You are Moon AI, an independent local assistant. "
            "Answer naturally and accurately. Use retrieved knowledge as evidence, "
            "but do not blindly repeat irrelevant entries. If uncertain, say so. "
            "For calculations show concise steps. Prefer Bengali when the user writes Bengali.")
    prompt=f"""<|system|>
{system}
<|user|>
Relevant Moon Brain:
{context or "(none)"}

Recent conversation:
{recent}

Question:
{question}
<|assistant|>"""
    out=llm(prompt,max_tokens=700,temperature=0.35,top_p=0.9,stop=["<|user|>"])
    text=out["choices"][0]["text"].strip()
    return text,"local_model"

# ============================================================
# 4) RESPONSE ENGINE
# ============================================================
def teach_command(q):
    m=re.match(r"^\s*if\s*#\(\s*(.*?)\s*\)\s*save\s*$",q,re.I|re.S)
    if m: return add_knowledge("general","",m.group(1),"","user-learned")
    m=re.match(r"^\s*teach\s*#\(\s*(.*?)\s*=>\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\)\s*$",q,re.I|re.S)
    if m: return add_knowledge(m.group(4),m.group(1),m.group(2),m.group(3),"taught")
    return None

def fallback_answer(q,retrieved):
    if q.strip() and all(c in "0123456789.+-*/()% \t" for c in q) and any(c.isdigit() for c in q):
        try: return f"হিসাবের ফল: **{calc(q)}**"
        except: pass
    if retrieved:
        blocks=[]
        for _,domain,question,answer,explanation,tags,source in retrieved[:4]:
            b=f"**{question or domain.title()}**\n\n{answer}"
            if explanation: b+=f"\n\n**Moon AI ব্যাখ্যা:** {explanation}"
            blocks.append(b)
        return "\n\n---\n\n".join(blocks)
    return ("এই প্রশ্নের জন্য Moon Brain-এ এখনও যথেষ্ট তথ্য নেই। "
            "Learning Lab থেকে আমাকে শেখাতে পারেন। একটি local GGUF model যোগ করলে "
            "Moon AI একই Brain ব্যবহার করে আরও স্বাভাবিকভাবে উত্তর তৈরি করবে।")

def moon_reply(q,history):
    teach=teach_command(q)
    if teach:
        return teach[1]
    hits=search_knowledge(q,8)
    ans,status=model_answer(q,hits,history)
    if ans: return ans
    return fallback_answer(q,hits)

# ============================================================
# 5) CHAT HISTORY
# ============================================================
def ensure_chat():
    if "chat_id" not in st.session_state:
        con=db(); now=time.time()
        cur=con.execute("CREATE TABLE IF NOT EXISTS chats(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,created_at REAL,updated_at REAL)")
        con.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id INTEGER,role TEXT,content TEXT,created_at REAL)")
        con.commit()
        cur=con.execute("INSERT INTO chats(title,created_at,updated_at) VALUES(?,?,?)",("New Chat",now,now))
        st.session_state.chat_id=cur.lastrowid; con.commit(); con.close()
ensure_chat()

def load_chat(cid):
    con=db(); rows=con.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id",(cid,)).fetchall(); con.close(); return rows
def save_chat_msg(cid,role,text):
    con=db(); now=time.time()
    con.execute("INSERT INTO messages(chat_id,role,content,created_at) VALUES(?,?,?,?)",(cid,role,text,now))
    con.execute("UPDATE chats SET title=CASE WHEN title='New Chat' THEN ? ELSE title END,updated_at=? WHERE id=?",(text[:45].replace("\n"," "),now,cid))
    con.commit(); con.close()

if "messages" not in st.session_state: st.session_state.messages=load_chat(st.session_state.chat_id)

# ============================================================
# 6) UI
# ============================================================
st.markdown("""<style>
.stApp{background:#0b1020;color:#e8eefc}.block-container{max-width:960px;padding-top:1rem}
.moon-head{border:1px solid #223452;background:linear-gradient(135deg,#0e172b,#102b42);border-radius:20px;padding:22px 26px}
.title{font-size:31px;font-weight:750}.sub{font-size:14px;color:#91a3bf}
.small{font-size:12px;color:#7185a4}
</style>""",unsafe_allow_html=True)

st.markdown("""<div class="moon-head"><div class="title">☾ Moon AI</div>
<div class="sub">Independent local AI · Brain + Retrieval + Local Model</div></div>""",unsafe_allow_html=True)

a,b,c=st.columns([1,1,4])
with a:
    if st.button("＋ New chat",use_container_width=True):
        con=db(); now=time.time(); cur=con.execute("INSERT INTO chats(title,created_at,updated_at) VALUES(?,?,?)",("New Chat",now,now)); con.commit(); con.close()
        st.session_state.chat_id=cur.lastrowid; st.session_state.messages=[]; st.rerun()
with b:
    if st.button("☷ History",use_container_width=True):
        st.session_state.history_open=not st.session_state.get("history_open",False)
with c:
    mods=available_models()
    st.markdown(f"<div class='small'>Brain: {brain_count():,} entries · Local model: {'READY' if mods else 'not installed'}</div>",unsafe_allow_html=True)

if st.session_state.get("history_open"):
    con=db(); hs=con.execute("SELECT id,title FROM chats ORDER BY updated_at DESC LIMIT 30").fetchall(); con.close()
    for cid,title in hs:
        if st.button(title or "New Chat",key=f"h{cid}",use_container_width=True):
            st.session_state.chat_id=cid; st.session_state.messages=load_chat(cid); st.session_state.history_open=False; st.rerun()

for role,text in st.session_state.messages:
    with st.chat_message(role,avatar="☾" if role=="assistant" else "○"):
        st.markdown(text)

prompt=st.chat_input("Moon AI-কে প্রশ্ন করুন…")
if prompt:
    st.session_state.messages.append(("user",prompt)); save_chat_msg(st.session_state.chat_id,"user",prompt)
    with st.spinner("Moon AI ভাবছে…"):
        answer=moon_reply(prompt,st.session_state.messages)
    st.session_state.messages.append(("assistant",answer)); save_chat_msg(st.session_state.chat_id,"assistant",answer)
    st.rerun()

with st.expander("🧠 Learning Lab"):
    st.write("Moon AI-কে সরাসরি শেখান। তথ্য SQLite Brain-এ থাকবে।")
    d=st.selectbox("Domain",["general","physics","chemistry","biology","math","computer","language","other"])
    q=st.text_input("Question / concept")
    ans=st.text_area("Answer / fact")
    ex=st.text_area("Explanation")
    tags=st.text_input("Tags")
    if st.button("Brain-এ শেখাও",type="primary"):
        ok,msg=add_knowledge(d,q,ans,ex,tags,"user")
        st.success(msg) if ok else st.warning(msg)

with st.expander("⚙️ Local Model"):
    st.write("কোনো cloud API ছাড়াই CPU/GPU-তে local GGUF model চালানোর জায়গা।")
    st.code(str(MODEL_DIR / "moon-model.gguf"))
    st.caption("এই folder-এ একটি compatible .gguf model রাখুন। App স্বয়ংক্রিয়ভাবে প্রথম model ব্যবহার করবে।")
    if available_models():
        st.success("Local model file পাওয়া গেছে।")
    else:
        st.info("এখনো GGUF model যোগ করা হয়নি। Brain-only mode চালু আছে।")
  
