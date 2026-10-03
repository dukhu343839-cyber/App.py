import json
import math
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & THEME ENGINE
# ==========================================
st.set_page_config(
    page_title="PHYSICS & MINERAL SOLVER ENGINE",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Premium Chalkboard CSS Injection (Zero Emojis)
st.markdown(
    """
    <style>
    /* Dark Green Chalkboard Aesthetics */
    .stApp {
        background-color: #0A1610;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header & Navigation Style */
    .main-header {
        font-family: 'Fira Code', 'Courier New', monospace;
        color: #22C55E;
        font-weight: 700;
        letter-spacing: 1px;
        border-bottom: 2px solid #132E20;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* IDE/Coding Terminal Monospace Card */
    .code-container {
        background-color: #050D08;
        border: 1px solid #1A3A29;
        border-radius: 6px;
        padding: 16px;
        font-family: 'Fira Code', 'Courier New', monospace;
        color: #A7F3D0;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    
    .code-title {
        color: #38BDF8;
        font-weight: bold;
        font-size: 1.05rem;
        border-bottom: 1px solid #132E20;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }

    .code-tag {
        background-color: #132E20;
        color: #4ADE80;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 8px;
    }

    /* Streamlit UI Components Tweaks */
    div[data-testid="stSidebar"] {
        background-color: #060E0A;
        border-right: 1px solid #132E20;
    }
    
    .stButton > button {
        background-color: #132E20;
        color: #4ADE80;
        border: 1px solid #22C55E;
        border-radius: 4px;
        font-family: 'Fira Code', monospace;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #22C55E;
        color: #0A1610;
    }

    /* Hide standard header decoration */
    header[data-testid="stHeader"] {
        background-color: rgba(10, 22, 16, 0.85);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if "problems" not in st.session_state:
    st.session_state.problems = [
        {
            "id": 1,
            "category": "Current Electricity / চল তড়িৎ",
            "title": "Complex Circuit Equivalent Resistance and Total Current",
            "code_format": """// CIRCUIT INPUT CONFIGURATION
V_source = 100.0 // Volts
R1 = 5.0; R2 = 3.0; R3 = 4.0; R4 = 4.0;
R5 = 5.0; R6 = 7.0; R7 = 2.0; R8 = 2.0; // Ohms

// EQUIVALENT RESISTANCE CALCULATION
R_p1 = (R3 * R4) / (R3 + R4);           // Parallel branch R3||R4 = 2.0 Ohm
R_s1 = R2 + R_p1;                       // Series branch = 5.0 Ohm
R_p2 = (R_s1 * R5) / (R_s1 + R5);       // Parallel branch = 2.5 Ohm
R_eq = R1 + R_p2 + R6;                  // Total Equivalent Resistance = 14.5 Ohm

// TOTAL CURRENT (OHM'S LAW)
I_total = V_source / R_eq;              // I = 100 / 14.5 = 6.90 Amperes""",
            "question_bn": "একটি V = 100V উৎসের সাথে R1=5Ω, R2=3Ω, R3=4Ω, R4=4Ω, R5=5Ω, R6=7Ω, R7=2Ω, R8=2Ω রোধের একটি মিশ্র বর্তনী যুক্ত আছে। বর্তনীর তুল্যরোধ এবং মূল প্রবাহ নির্ণয় কর।",
            "question_en": "A complex circuit connected to V = 100V source consists of resistors R1=5Ω, R2=3Ω, R3=4Ω, R4=4Ω, R5=5Ω, R6=7Ω, R7=2Ω, R8=2Ω. Find equivalent resistance Req and total current I.",
            "formula": r"V = I \cdot R_{eq} \implies I = \frac{V}{R_{eq}}",
            "difficulty": "Hard",
        },
        {
            "id": 2,
            "category": "Mineral & Matter Physics / খনিজ পদার্থবিজ্ঞান",
            "title": "Mineral Specific Gravity and Density Determination",
            "code_format": """// MINERAL METRICS DATA
m_air = 250.0;    // Mass in air (grams)
m_water = 170.0;  // Mass in water (grams)
rho_water = 1000; // Density of water (kg/m^3)

// ARCHIMEDES PRINCIPLE COMPUTATION
m_displaced = m_air - m_water;          // Displaced water mass = 80.0 g
SG = m_air / m_displaced;               // Specific Gravity = 3.125
rho_mineral = SG * rho_water;           // Density = 3125.0 kg/m^3""",
            "question_bn": "একটি খনিজ নমুনার বায়ুতে ভর ma = 250 g এবং পানিতে ভর mw = 170 g। খনিজটির আপেক্ষিক গুরুত্ব (SG) এবং ঘনত্ব (rho) নির্ণয় কর।",
            "question_en": "A mineral sample weighs ma = 250 g in air and mw = 170 g in water. Calculate the specific gravity (SG) and mass density (rho) of the mineral.",
            "formula": (
                r"SG = \frac{m_a}{m_a - m_w}, \quad \rho = SG \times"
                r" 1000\text{ kg/m}^3"
            ),
            "difficulty": "Medium",
        },
    ]

if "game_score" not in st.session_state:
    st.session_state.game_score = 0
if "game_step" not in st.session_state:
    st.session_state.game_step = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "Physics Engine Assistant Online. Ask any analytical query"
                " regarding circuit theory, mechanics, or mineral dynamics."
            ),
        }
    ]

# ==========================================
# 3. TOP BAR NAVIGATION & MINI GAME CONTROLLER
# ==========================================
col_title, col_top_right = st.columns([3, 1])

with col_title:
    st.markdown(
        "<div class='main-header'>PHYSICS & MINERAL ENGINE v2.0</div>",
        unsafe_allow_html=True,
    )

with col_top_right:
    # Popover for Top Right Corner Mini-Game & Quick Settings
    with st.popover("Mini Game / Quick Tool"):
        st.markdown("**Physics Quick Challenge**")
        st.caption("Test your physics speed solving skills.")

        # Game Questions Logic
        questions = [
            {
                "q": "Two 4 Ohm resistors in parallel give Req = ?",
                "opts": ["8 Ohm", "2 Ohm", "4 Ohm"],
                "ans": "2 Ohm",
            },
            {
                "q": (
                    "Formula for fluid pressure at depth h is:"
                ),
                "opts": ["P = h*rho*g", "P = F*A", "P = m*g"],
                "ans": "P = h*rho*g",
            },
            {
                "q": "What is the SI unit of Electric Potential?",
                "opts": ["Ampere", "Volt", "Joule"],
                "ans": "Volt",
            },
        ]

        step = st.session_state.game_step
        if step < len(questions):
            curr_q = questions[step]
            st.write(f"Q{step+1}: {curr_q['q']}")
            user_ans = st.radio(
                "Options:", curr_q["opts"], key=f"q_opt_{step}"
            )
            if st.button("Submit Answer", key=f"sub_{step}"):
                if user_ans == curr_q["ans"]:
                    st.session_state.game_score += 10
                    st.success("Correct Answer (+10 PTS)")
                else:
                    st.error("Incorrect Answer")
                st.session_state.game_step += 1
                st.rerun()
        else:
            st.write(
                f"Game Complete! Final Score: {st.session_state.game_score} PTS"
            )
            if st.button("Reset Game"):
                st.session_state.game_score = 0
                st.session_state.game_step = 0
                st.rerun()

# Language & Settings Toolbar
st.sidebar.markdown("### SYSTEM SETTINGS")
ui_lang = st.sidebar.selectbox("Language / ভাষা", ["English", "বাংলা"])
code_font_toggle = st.sidebar.checkbox("IDE Code View Style", value=True)

# Four Navigation Modules
st.markdown("### MODULE SELECTOR")
nav_module = st.radio(
    "",
    [
        "Deep Analysis",
        "CQ Solve",
        "Learning Physics Basic",
        "Discussion Any Problem with Bot",
    ],
    horizontal=True,
)

st.markdown("---")

# ==========================================
# MODULE 1: DEEP ANALYSIS
# ==========================================
if nav_module == "Deep Analysis":
    st.subheader("Deep Numerical & Analytical Breakdown")

    for prob in st.session_state.problems:
        st.markdown(
            f"""
        <div class="code-container">
            <div class="code-tag">ID: #{prob['id']} | CATEGORY: {prob['category']} | DIFFICULTY: {prob['difficulty']}</div>
            <div class="code-title">{prob['title']}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown("**Structured Problem Statement:**")
        q_text = (
            prob["question_bn"] if ui_lang == "বাংলা" else prob["question_en"]
        )
        st.info(q_text)

        if code_font_toggle:
            st.markdown("**Code-Style Formula & Variable Logic:**")
            st.code(prob["code_format"], language="javascript")

        st.markdown("**Mathematical Expression:**")
        st.latex(prob["formula"])
        st.markdown("---")

# ==========================================
# MODULE 2: CQ SOLVE (CREATIVE QUESTIONS)
# ==========================================
elif nav_module == "CQ Solve":
    st.subheader("Creative Question (CQ) Solver")

    col_s, col_f = st.columns([2, 1])
    search_term = col_s.text_input("Filter CQs by term...", "")
    category_filter = col_f.selectbox(
        "Category",
        [
            "All Categories",
            "Current Electricity / চল তড়িৎ",
            "Mineral & Matter Physics / খনিজ পদার্থবিজ্ঞান",
        ],
    )

    filtered = st.session_state.problems
    if category_filter != "All Categories":
        filtered = [p for p in filtered if p["category"] == category_filter]

    for prob in filtered:
        with st.expander(f"CQ #{prob['id']}: {prob['title']}"):
            st.markdown(
                "**Stem / উদ্দীপক:** "
                + (
                    prob["question_bn"]
                    if ui_lang == "বাংলা"
                    else prob["question_en"]
                )
            )
            st.markdown("**Core Formula:**")
            st.latex(prob["formula"])

            st.markdown("**Executable Logic View:**")
            st.code(prob["code_format"], language="cpp")

# ==========================================
# MODULE 3: LEARNING PHYSICS BASIC
# ==========================================
elif nav_module == "Learning Physics Basic":
    st.subheader("Interactive Physics Fundamentals Engine")

    topic = st.selectbox(
        "Select Fundamental Module",
        [
            "1. Ohm's Law & Circuit Analysis",
            "2. Mineral Hydrostatics & Hydrodynamic Pressure",
            "3. Kinematic Equations of Motion",
        ],
    )

    if "Ohm's Law" in topic:
        st.markdown("#### Ohm's Law Calculation Engine")
        col1, col2 = st.columns(2)
        v_in = col1.number_input("Voltage V (Volts)", value=100.0)
        r_in = col2.number_input("Resistance R (Ohms)", value=14.5)

        if r_in > 0:
            i_out = v_in / r_in
            st.code(
                f"// EXECUTION OUTPUT\nVoltage = {v_in} V\nResistance ="
                f" {r_in} Ohm\nCurrent I = {i_out:.4f} Amperes",
                language="python",
            )

    elif "Mineral Hydrostatics" in topic:
        st.markdown("#### Mineral Density & Archimedes Analysis")
        col1, col2 = st.columns(2)
        m_a = col1.number_input("Mass in Air (g)", value=250.0)
        m_w = col2.number_input("Mass in Water (g)", value=170.0)

        if m_a > m_w:
            sg = m_a / (m_a - m_w)
            density = sg * 1000.0
            st.code(
                f"// ARCHIMEDES COMPUTATION\nDisplaced Mass = {m_a - m_w}"
                f" g\nSpecific Gravity = {sg:.3f}\nCalculated Density ="
                f" {density:.2f} kg/m^3",
                language="python",
            )

    elif "Kinematic Equations" in topic:
        st.markdown("#### Projectile & Displacement Physics")
        u = st.number_input("Initial Velocity u (m/s)", value=20.0)
        a = st.number_input("Acceleration a (m/s^2)", value=9.8)
        t = st.number_input("Time t (seconds)", value=5.0)

        s = (u * t) + (0.5 * a * (t**2))
        v = u + (a * t)
        st.code(
            f"// KINEMATICS MATRIX\nFinal Velocity v = {v:.2f} m/s\nTotal"
            f" Displacement s = {s:.2f} meters",
            language="python",
        )

# ==========================================
# MODULE 4: DISCUSSION ANY PROBLEM WITH BOT
# ==========================================
elif nav_module == "Discussion Any Problem with Bot":
    st.subheader("Physics AI Discussion Bot")
    st.caption(
        "Interactive console for physics algorithms, mineral equations, and"
        " circuit troubleshooting."
    )

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_query = st.chat_input("Enter physics problem or variable query...")

    if user_query:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_query}
        )
        with st.chat_message("user"):
            st.write(user_query)

        q_lower = user_query.lower()
        if "ohm" in q_lower or "circuit" in q_lower or "বর্তনী" in q_lower:
            bot_resp = (
                "Ohm's Law Statement: V = I * R. In complex circuits,"
                " simplify parallel branches using 1/Req = sum(1/Rn) and series"
                " branches using Req = sum(Rn)."
            )
        elif "mineral" in q_lower or "density" in q_lower or "খনিজ" in q_lower:
            bot_resp = (
                "Mineral Density Protocol: Specific Gravity (SG) = Mass_Air /"
                " (Mass_Air - Mass_Water). Density = SG * 1000 kg/m^3."
            )
        elif "pressure" in q_lower or "চাপ" in q_lower:
            bot_resp = (
                "Fluid/Mine Pressure Logic: Hydrostatic Pressure P = h * rho *"
                " g, where h is depth, rho is fluid density, and g = 9.8"
                " m/s^2."
            )
        else:
            bot_resp = (
                f"Query processed: '{user_query}'. For numerical solving, navigate"
                " to 'Learning Physics Basic' or inspect problem code structures"
                " in 'Deep Analysis'."
            )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": bot_resp}
        )
        with st.chat_message("assistant"):
            st.write(bot_resp)
