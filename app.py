import json
import math
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Physics & Mineral Solver App",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 1. LANGUAGE & LOCALIZATION SETTINGS
# ---------------------------------------------------------
st.sidebar.title("⚙️ Language & Settings")

ui_lang = st.sidebar.selectbox(
    "🌐 App Interface Language / অ্যাপের ভাষা",
    ["English", "বাংলা"]
)

prob_lang = st.sidebar.radio(
    "📖 Problem Display Language / সমস্যার ভাষা",
    ["বাংলা (Bengali)", "English"]
)

# UI Translations Dictionary
translations = {
    "English": {
        "title": "⚡ Physics & Mineral Solver Hub",
        "subtitle": "Interactive Physics Problem Bank, Mineral Physics & AI Assistant",
        "nav_title": "Navigation",
        "nav_home": "🏠 Home & Problems",
        "nav_add": "➕ Add Custom Problem",
        "nav_calc": "🧮 Mineral & Physics Calculator",
        "nav_chatbot": "🤖 Physics Chatbot",
        "search": "🔍 Search Problems...",
        "filter_chap": "Filter by Chapter",
        "all_chaps": "All Chapters",
        "solution": "Show Solution",
        "formula": "Key Formula:",
        "difficulty": "Difficulty",
        "add_prob_title": "Add a New Problem to Database",
        "add_success": "New problem added successfully!",
        "chat_welcome": "Hello! I am your Physics & Mineral Assistant. Ask me any formula or problem!",
        "chat_placeholder": "Ask a physics question (e.g. Ohm's law, mineral density, velocity)..."
    },
    "বাংলা": {
        "title": "⚡ ফিজিক্স ও মিনারেল সলভার হাব",
        "subtitle": "ইন্টারেক্টিভ পদার্থবিজ্ঞান ও খনিজ পদার্থবিজ্ঞান প্রবলেম ব্যাংক এবং চ্যাটবট",
        "nav_title": "নেভিগেশন",
        "nav_home": "🏠 প্রধান পাতা ও সমস্যাসমূহ",
        "nav_add": "➕ নতুন সমস্যা যোগ করুন",
        "nav_calc": "🧮 খনিজ ও ফিজিক্স ক্যালকুলেটর",
        "nav_chatbot": "🤖 ফিজিক্স চ্যাটবট",
        "search": "🔍 সমস্যা খুঁজুন...",
        "filter_chap": "অধ্যায় ফিল্টার করুন",
        "all_chaps": "সব অধ্যায়",
        "solution": "সমাধান দেখুন",
        "formula": "মূল সূত্র:",
        "difficulty": "কঠিনতার মাত্রা",
        "add_prob_title": "ডাটাবেজে নতুন সমস্যা যোগ করুন",
        "add_success": "নতুন সমস্যা সফলভাবে যোগ হয়েছে!",
        "chat_welcome": "হ্যালো! আমি আপনার ফিজিক্স অ্যাসিস্ট্যান্ট। আমাকে সার্কিট, গতিবিদ্যা বা খনিজের যেকোনো প্রশ্ন করতে পারেন!",
        "chat_placeholder": "পদার্থবিজ্ঞানের কোনো প্রশ্ন বা সূত্র লিখুন (যেমন: ওহমের সূত্র, খনিজের ঘনত্ব)..."
    }
}

t = translations[ui_lang]

# ---------------------------------------------------------
# 2. INITIALIZE PROBLEM DATABASE & CHAT HISTORY
# ---------------------------------------------------------
if "problems" not in st.session_state:
    st.session_state.problems = [
        {
            "id": 1,
            "chapter_bn": "চল তড়িৎ (Current Electricity)",
            "chapter_en": "Current Electricity",
            "title_bn": "জটিল বর্তনীর তুল্যরোধ ও মূল তড়িৎপ্রবাহ নির্ণয় (চিত্রানুসারে)",
            "title_en": "Equivalent Resistance and Total Current of Complex Circuit",
            "question_bn": "একটি V = 100V উৎসের সাথে R1 = 5Ω, R2 = 3Ω, R3 = 4Ω, R4 = 4Ω, R5 = 5Ω, R6 = 7Ω, R7 = 2Ω, R8 = 2Ω রোধের একটি মিশ্র বর্তনী যুক্ত আছে। বর্তনীর তুল্যরোধ (Req) এবং মূল প্রবাহ (I) কত?",
            "question_en": "A complex circuit connected to a V = 100V voltage source consists of resistors R1 = 5Ω, R2 = 3Ω, R3 = 4Ω, R4 = 4Ω, R5 = 5Ω, R6 = 7Ω, R7 = 2Ω, R8 = 2Ω. Calculate equivalent resistance (Req) and total current (I).",
            "formula": r"V = I \cdot R_{eq} \implies I = \frac{V}{R_{eq}}",
            "solution_bn": """**ধাপ ১: সমান্তরাল ও শ্রেণী শাখাগুলো চিহ্নিতকরণ**
1. R3 (4Ω) এবং R4 (4Ω) সমান্তরালে যুক্ত: $R_{p1} = \frac{4 \times 4}{4 + 4} = 2\,\Omega$
2. $R_{p1}$ এর সাথে R2 (3Ω) শ্রেণীতে যুক্ত: $R_{s1} = 3 + 2 = 5\,\Omega$
3. $R_{s1}$ শাখাটি R5 (5Ω) এর সাথে সমান্তরালে যুক্ত: $R_{p2} = \frac{5 \times 5}{5 + 5} = 2.5\,\Omega$
4. R7 (2Ω) ও R8 (2Ω) এর শাখা শ্রেণীতে যুক্ত হয়ে সমতুল্য রোদ গঠন করে।
5. সমস্ত শাখা যুক্ত করে বর্তনীর মোট তুল্যরোধ $R_{eq} = R_1 + R_{p2} + R_6 = 5 + 2.5 + 7 = 14.5\,\Omega$ (আনুমানিক)।

**ধাপ ২: মূল প্রবাহ নির্ণয়**
$$I = \frac{V}{R_{eq}} = \frac{100\text{ V}}{14.5\,\Omega} \approx 6.90\text{ A}$$""",
            "solution_en": """**Step 1: Simplify Parallel & Series Branches**
1. R3 (4Ω) & R4 (4Ω) in parallel: $R_{p1} = \frac{4 \times 4}{4 + 4} = 2\,\Omega$
2. $R_{p1}$ in series with R2 (3Ω): $R_{s1} = 3 + 2 = 5\,\Omega$
3. $R_{s1}$ in parallel with R5 (5Ω): $R_{p2} = \frac{5 \times 5}{5 + 5} = 2.5\,\Omega$
4. Combining remaining branches gives total equivalent resistance $R_{eq} \approx 14.5\,\Omega$.

**Step 2: Total Circuit Current**
$$I = \frac{V}{R_{eq}} = \frac{100\text{ V}}{14.5\,\Omega} \approx 6.90\text{ A}$$""",
            "difficulty": "Hard / কঠিন"
        },
        {
            "id": 2,
            "chapter_bn": "খনিজ ও পদার্থের ধর্ম (Mineral & Matter Physics)",
            "chapter_en": "Mineral & Matter Physics",
            "title_bn": "খনিজ নমুনার আপেক্ষিক গুরুত্ব ও ঘনত্ব নির্ণয়",
            "title_en": "Determination of Mineral Density and Specific Gravity",
            "question_bn": "একটি আকরিকে খনিজ নমুনার বায়ুতে ভর ma = 250 g এবং পানিতে নিমজ্জিত অবস্থায় ভর mw = 170 g। আর্কিমিডিসের সূত্র ব্যবহার করে খনিজটির আপেক্ষিক গুরুত্ব (Specific Gravity) এবং ঘনত্ব (ρ) নির্ণয় কর।",
            "question_en": "A mineral ore sample weighs ma = 250 g in air and mw = 170 g when immersed in water. Using Archimedes' Principle, calculate the specific gravity (SG) and mass density (ρ) of the mineral.",
            "formula": r"SG = \frac{m_a}{m_a - m_w}, \quad \rho = SG \times 1000\text{ kg/m}^3",
            "solution_bn": """**সমাধান:**
১. অপসারিত পানির ভর = $m_a - m_w = 250\text{ g} - 170\text{ g} = 80\text{ g}$
২. আপেক্ষিক গুরুত্ব (SG) = $\frac{250}{80} = 3.125$
৩. খনিজের ঘনত্ব $\rho = 3.125 \times 1000\text{ kg/m}^3 = 3125\text{ kg/m}^3$""",
            "solution_en": """**Solution:**
1. Mass of displaced water = $m_a - m_w = 250\text{ g} - 170\text{ g} = 80\text{ g}$
2. Specific Gravity (SG) = $\frac{250}{80} = 3.125$
3. Mineral Density $\rho = 3.125 \times 1000\text{ kg/m}^3 = 3125\text{ kg/m}^3$""",
            "difficulty": "Medium / মাঝারি"
        }
    ]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": t["chat_welcome"]}
    ]

# ---------------------------------------------------------
# 3. NAVIGATION MENU
# ---------------------------------------------------------
st.sidebar.markdown("---")
page = st.sidebar.radio(
    t["nav_title"],
    [t["nav_home"], t["nav_add"], t["nav_calc"], t["nav_chatbot"]]
)

# Header
st.title(t["title"])
st.caption(t["subtitle"])
st.markdown("---")

# ---------------------------------------------------------
# PAGE 1: HOME & PROBLEMS
# ---------------------------------------------------------
if page == t["nav_home"]:
    st.subheader("📚 Physics & Mineral Problems")
    
    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_q = st.text_input(t["search"], "")
    with col_filter:
        chapters = list(set([p["chapter_bn"] if prob_lang.startswith("বাংলা") else p["chapter_en"] for p in st.session_state.problems]))
        selected_chap = st.selectbox(t["filter_chap"], [t["all_chaps"]] + chapters)

    filtered_problems = st.session_state.problems

    if selected_chap != t["all_chaps"]:
        filtered_problems = [p for p in filtered_problems if (p["chapter_bn"] == selected_chap or p["chapter_en"] == selected_chap)]

    if search_q:
        filtered_problems = [
            p for p in filtered_problems if search_q.lower() in p["title_bn"].lower() or search_q.lower() in p["title_en"].lower() or search_q.lower() in p["question_bn"].lower()
        ]

    for prob in filtered_problems:
        is_bn = prob_lang.startswith("বাংলা")
        chap = prob["chapter_bn"] if is_bn else prob["chapter_en"]
        title = prob["title_bn"] if is_bn else prob["title_en"]
        q_text = prob["question_bn"] if is_bn else prob["question_en"]
        sol_text = prob["solution_bn"] if is_bn else prob["solution_en"]

        with st.expander(f"📌 [{chap}] {title} ({prob['difficulty']})"):
            st.markdown(f"**Question / প্রশ্ন:**")
            st.write(q_text)
            
            st.markdown(f"**{t['formula']}**")
            st.latex(prob["formula"])
            
            if st.button(f"{t['solution']} #{prob['id']}", key=f"btn_{prob['id']}"):
                st.markdown("---")
                st.markdown(sol_text)

# ---------------------------------------------------------
# PAGE 2: ADD CUSTOM PROBLEM
# ---------------------------------------------------------
elif page == t["nav_add"]:
    st.subheader(t["add_prob_title"])
    
    with st.form("add_problem_form"):
        c_bn = st.text_input("Chapter Name (বাংলা)", "খনিজ ও পদার্থের ধর্ম")
        c_en = st.text_input("Chapter Name (English)", "Mineral Physics")
        t_bn = st.text_input("Problem Title (বাংলা)", "খনিজের গভীরতায় চাপ নির্ণয়")
        t_en = st.text_input("Problem Title (English)", "Pressure in Deep Mineral Extraction")
        q_bn = st.text_area("Question (বাংলা)", "খনিগর্ভে ৫০০ মিটার গভীরে তরলের চাপ কত?")
        q_en = st.text_area("Question (English)", "Find fluid pressure at 500m depth inside a mine shaft.")
        formula = st.text_input("Formula (LaTeX format)", r"P = h \cdot \rho \cdot g")
        s_bn = st.text_area("Solution (বাংলা)", "P = 500 * 1000 * 9.8 = 4.9 MPa")
        s_en = st.text_area("Solution (English)", "P = 500 * 1000 * 9.8 = 4.9 MPa")
        diff = st.selectbox("Difficulty", ["Easy / সহজ", "Medium / মাঝারি", "Hard / কঠিন"])
        
        submitted = st.form_submit_button("Save Problem / সেভ করুন")
        if submitted:
            new_id = len(st.session_state.problems) + 1
            st.session_state.problems.append({
                "id": new_id,
                "chapter_bn": c_bn,
                "chapter_en": c_en,
                "title_bn": t_bn,
                "title_en": t_en,
                "question_bn": q_bn,
                "question_en": q_en,
                "formula": formula,
                "solution_bn": s_bn,
                "solution_en": s_en,
                "difficulty": diff
            })
            st.success(t["add_success"])

# ---------------------------------------------------------
# PAGE 3: LIVE PHYSICS & MINERAL CALCULATOR
# ---------------------------------------------------------
elif page == t["nav_calc"]:
    st.subheader("🧮 Interactive Physics & Mineral Calculator")
    
    calc_type = st.selectbox(
        "Choose Calculator / ক্যালকুলেটর নির্বাচন করুন",
        ["1. Mineral Density & Specific Gravity (খনিজের ঘনত্ব)", "2. Ohm's Law & Circuit (ওহমের সূত্র)", "3. Fluid Pressure in Mines (খনিগর্ভে চাপ)"]
    )
    
    if "Mineral Density" in calc_type:
        st.markdown("### Mineral Density & Specific Gravity Calculator")
        m_air = st.number_input("Mass in Air $m_a$ (grams)", value=250.0)
        m_water = st.number_input("Mass in Water $m_w$ (grams)", value=170.0)
        
        if m_air > m_water:
            sg = m_air / (m_air - m_water)
            density = sg * 1000.0
            st.success(f"**Specific Gravity (SG):** {sg:.3f}")
            st.info(f"**Mineral Density ($\rho$):** {density:.2f} kg/m³")
        else:
            st.error("Mass in air must be greater than mass in water.")
            
    elif "Ohm's Law" in calc_type:
        st.markdown("### Ohm's Law Calculator ($V = I \\times R$)")
        v = st.number_input("Voltage V (Volts)", value=100.0)
        r = st.number_input("Resistance R (Ohms)", value=14.5)
        if r > 0:
            i = v / r
            st.success(f"**Current (I):** {i:.2f} Amperes (A)")
            
    elif "Fluid Pressure" in calc_type:
        st.markdown("### Hydrostatic Pressure ($P = h \\rho g$)")
        h = st.number_input("Depth h (meters)", value=500.0)
        rho = st.number_input("Fluid Density $\rho$ (kg/m³)", value=1000.0)
        g = 9.8
        p = h * rho * g
        st.success(f"**Pressure (P):** {p/1e6:.3f} MPa ({p:.1f} Pa)")

# ---------------------------------------------------------
# PAGE 4: PHYSICS CHATBOT
# ---------------------------------------------------------
elif page == t["nav_chatbot"]:
    st.subheader("🤖 Physics & Mineral AI Chatbot")
    st.caption("Ask questions about physics equations, circuits, or minerals!")
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    user_input = st.chat_input(t["chat_placeholder"])
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
            
        # Chatbot Response Logic
        query = user_input.lower()
        if "ohm" in query or "ওহম" in query or "circuit" in query or "বর্তনী" in query:
            reply = "ওহমের সূত্র (Ohm's Law): $V = I \\times R$। যেখানে $V$ হলো ভোল্টেজ, $I$ হলো তড়িৎপ্রবাহ এবং $R$ হলো রোধ।"
        elif "mineral" in query or "খনিজ" in query or "density" in query or "ঘনত্ব" in query:
            reply = "খনিজের আপেক্ষিক গুরুত্ব $SG = \\frac{m_a}{m_a - m_w}$ এবং ঘনত্ব $\\rho = SG \\times 1000\\text{ kg/m}^3$।"
        elif "velocity" in query or "বেগ" in query or "গতি" in query:
            reply = "গতির সমীকরণসমূহ:\n1. $v = u + at$\n2. $s = ut + \\frac{1}{2}at^2$\n3. $v^2 = u^2 + 2as$"
        elif "pressure" in query or "চাপ" in query:
            reply = "চাপের সূত্র: $P = \\frac{F}{A}$ অথবা তরল/খনিগর্ভে চাপ $P = h \\rho g$।"
        else:
            reply = f"ধন্যবাদ আপনার প্রশ্নের জন্য! '{user_input}' সংক্রান্ত পদার্থবিজ্ঞানের মূল সূত্রটি গাণিতিক ক্যালকুলেটর পেজ থেকে গণনা করতে পারেন।"
            
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)
