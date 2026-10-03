import math
import re
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PAGE CONFIGURATION & CSS STYLES
# ==========================================
st.set_page_config(
    page_title="Physics Core Engine",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Dark Minimalist Slate Style CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0D1117;
        color: #C9D1D9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Clean Home Screen Option Cards */
    .option-box {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #161B22;
        color: #58A6FF;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 20px;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: monospace;
    }
    
    .stButton > button:hover {
        background-color: #21262D;
        border-color: #58A6FF;
        color: #79C0FF;
    }

    div[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Session State Initialization
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": (
            "হ্যালো! আমি আপনার ফিজিক্স অ্যাসিস্ট্যান্ট। আমাকে যেকোনো গাণিতিক"
            " হিসাব, হাই-হ্যালো বা ফিজিক্সের সমস্যা জিজ্ঞেস করতে পারেন।"
        ),
    }]

# ==========================================
# 2. SIDEBAR MENU & 2D ANIMATED GAME
# ==========================================
with st.sidebar:
    st.title("NAVIGATION & TOOLS")

    if st.button("HOME SCREEN"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.markdown("---")
    st.subheader("2D PHYSICS GAME")
    st.caption("Projectile Target Hit Simulation")

    # 2D Interactive Cannon Game HTML5 Canvas Engine
    game_canvas_code = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; background: #0D1117; color: #C9D1D9; font-family: monospace; text-align: center; }
        canvas { background: #161B22; border: 1px solid #30363D; border-radius: 6px; margin-top: 8px; }
        .controls { font-size: 11px; margin-bottom: 5px; }
        input { background: #21262D; color: #58A6FF; border: 1px solid #30363D; width: 45px; border-radius: 3px; padding: 2px; }
        button { background: #21262D; color: #79C0FF; border: 1px solid #30363D; padding: 3px 8px; border-radius: 3px; cursor: pointer; }
    </style>
    </head>
    <body>
        <div class="controls">
            Velocity: <input type="number" id="vel" value="50">
            Angle: <input type="number" id="ang" value="45">
            <button onclick="fire()">FIRE</button>
        </div>
        <canvas id="gameCanvas" width="270" height="170"></canvas>
        <div id="status" style="font-size:11px; color:#79C0FF; margin-top:4px;">Target at 200m. Launch cannon!</div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        let targetX = 200;
        let ball = {x: 10, y: 160, vx: 0, vy: 0, active: false};
        
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Ground
            ctx.fillStyle = "#30363D";
            ctx.fillRect(0, 165, canvas.width, 5);
            
            // Target
            ctx.fillStyle = "#F85149";
            ctx.fillRect(targetX, 150, 12, 15);
            
            // Cannon
            ctx.fillStyle = "#58A6FF";
            ctx.fillRect(5, 155, 12, 10);
            
            // Ball Animation
            if (ball.active) {
                ctx.beginPath();
                ctx.arc(ball.x, ball.y, 3, 0, Math.PI*2);
                ctx.fillStyle = "#79C0FF";
                ctx.fill();
            }
        }
        
        function fire() {
            if (ball.active) return;
            let v = parseFloat(document.getElementById('vel').value);
            let a = parseFloat(document.getElementById('ang').value) * Math.PI / 180;
            ball.x = 10;
            ball.y = 160;
            ball.vx = v * Math.cos(a) * 0.15;
            ball.vy = -v * Math.sin(a) * 0.15;
            ball.active = true;
            document.getElementById('status').innerText = "In Motion...";
            animate();
        }
        
        function animate() {
            if (!ball.active) return;
            ball.x += ball.vx;
            ball.y += ball.vy;
            ball.vy += 0.12; // Gravity simulation
            
            if (ball.y >= 160) {
                ball.y = 160;
                ball.active = false;
                if (Math.abs(ball.x - targetX) < 12) {
                    document.getElementById('status').innerText = "TARGET DESTROYED! Score +100";
                    targetX = 90 + Math.random() * 140;
                } else {
                    document.getElementById('status').innerText = "MISSED! Adjust angle/velocity.";
                }
            }
            draw();
            if (ball.active) requestAnimationFrame(animate);
        }
        draw();
    </script>
    </body>
    </html>
    """
    components.html(game_canvas_code, height=250)

    st.markdown("---")
    st.subheader("SETTINGS")
    st.selectbox("Theme Mode", ["Dark Slate", "Chalkboard Green"])

# ==========================================
# 3. HOME SCREEN (ONLY 4 OPTIONS)
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Deep Analysis\n(দীপ এনালাইসিস)", key="btn_deep"):
            st.session_state.current_page = "Deep Analysis"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Learning Physics Basic\n(লার্নিং ফিজিক্স বেসিক)", key="btn_basic"
        ):
            st.session_state.current_page = "Learning Physics Basic"
            st.rerun()

    with col2:
        if st.button("CQ Solve\n(সিকিউ সলভ)", key="btn_cq"):
            st.session_state.current_page = "CQ Solve"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Discussion Any Problem with Bot\n(ডিসকাশন এনি প্রবলেম উইথ বট)",
            key="btn_bot",
        ):
            st.session_state.current_page = "Bot Discussion"
            st.rerun()

# ==========================================
# 4. MODULE PAGES
# ==========================================
elif st.session_state.current_page == "Deep Analysis":
    if st.button("Back to Home"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Deep Analysis Module")
    st.markdown("---")
    st.markdown("**জটিল সার্কিট বিশ্লেষণ:**")
    st.code(
        """// ADVANCED CIRCUIT PARSING MATRIX
V_input = 100.0 // Volts
Req_calculated = 14.5 // Ohms
I_total = V_input / Req_calculated // 6.90 Amperes
Power_Dissipation = (I_total^2) * Req_calculated // 690.0 Watts""",
        language="cpp",
    )

elif st.session_state.current_page == "CQ Solve":
    if st.button("Back to Home"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("CQ Solve Module")
    st.markdown("---")

    with st.expander("CQ 1: চল তড়িৎ ও মিশ্র বর্তনী"):
        st.markdown(
            "**উদ্দীপক:** V = 100V উৎসের সাথে R1=5, R2=3, R3=4, R4=4, R5=5,"
            " R6=7 Ohm যুক্ত আছে।"
        )
        st.markdown("**গ)** বর্তনীর তুল্যরোধ নির্ণয় কর।")
        st.markdown("**ঘ)** বর্তনীর মূল তড়িৎপ্রবাহের পরিবর্তন বিশ্লেষণ কর।")

    with st.expander("CQ 2: খনিজ পদার্থের আপেক্ষিক গুরুত্ব"):
        st.markdown(
            "**উদ্দীপক:** বায়ুতে খনিজের ভর 250g এবং পানিতে নিমজ্জিত ভর 170g।"
        )
        st.markdown("**গ)** খনিজটির আপেক্ষিক গুরুত্ব নির্ণয় কর।")

elif st.session_state.current_page == "Learning Physics Basic":
    if st.button("Back to Home"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Learning Physics Basic")
    st.markdown("---")

    topic = st.selectbox(
        "বিষয় নির্বাচন করুন",
        ["ওহমের সূত্র", "খনিজের ঘনত্ব", "গতিবিদ্যা"],
    )

    if topic == "ওহমের সূত্র":
        v = st.number_input("ভোল্টেজ V (Volts)", value=100.0)
        r = st.number_input("রোধ R (Ohms)", value=14.5)
        if r > 0:
            st.code(
                f"// CALCULATED OUTPUT\nI = V / R = {v} / {r} = {v/r:.3f}"
                " Amperes",
                language="python",
            )

# ==========================================
# 5. SMART CALCULATOR & CHATBOT PAGE
# ==========================================
elif st.session_state.current_page == "Bot Discussion":
    if st.button("Back to Home"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("Discussion Any Problem with Bot")
    st.caption("Interactive Physics Solving & Calculation Engine")
    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("গাণিতিক হিসাব বা যেকোনো প্রশ্ন লিখুন...")

    if user_input:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.write(user_input)

        text = user_input.lower().strip()

        # Bot Response Decision Engine
        # 1. Casual Chat / Greetings
        if any(
            w in text
            for w in [
                "hi",
                "hello",
                "হাই",
                "হ্যালো",
                "কেমন আছো",
                "হেই",
                "কেমন আছেন",
            ]
        ):
            bot_reply = (
                "হ্যালো! আমি ভালো আছি। আপনার গাণিতিক সমস্যা বা ফিজিক্সের যেকোনো"
                " প্রশ্ন লিখে জানান।"
            )

        # 2. Math Calculation Logic Engine (e.g., 100/14.5 or 250*9.8)
        elif re.match(r"^[0-9\.\+\-\*\/\(\)\s]+$", text):
            try:
                calc_result = eval(text)
                bot_reply = (
                    f"গাণিতিক সমীকরণের ফলাফল:\n`{text}` = **{calc_result:.4f}**"
                )
            except Exception:
                bot_reply = (
                    "গাণিতিক রাশিটি গণনা করতে সমস্যা হয়েছে। অনুগ্রহ করে সঠিক"
                    " সংখ্যা ও চিহ্ন ব্যবহার করুন।"
                )

        # 3. Step-by-Step Physics Problem Solving Guidance
        elif "সার্কিট" in text or "circuit" in text or "ohm" in text:
            bot_reply = """**বর্তনী ও ওহমের সূত্র সমাধানের ধাপ:**
১. সমান্তরাল রোধগুলোর জন্য: 1/Req = 1/R1 + 1/R2
২. শ্রেণী সমবায়ের জন্য: Req = R1 + R2
৩. মূল প্রবাহ নির্ণয়: I = V / Req"""

        elif "খনিজ" in text or "density" in text or "ঘনত্ব" in text:
            bot_reply = """**খনিজের ঘনত্ব নির্ণয়ের নিয়ম:**
১. অপসারিত পানির ভর বের করুন: m_water = m_air - m_water
২. আপেক্ষিক গুরুত্ব (SG) = m_air / m_water
৩. ঘনত্ব (rho) = SG * 1000 kg/m^3"""

        else:
            bot_reply = f"""**সমাধান নির্দেশিকা ({user_input}):**
১. দেওয়া মানগুলো চিহ্নিত করুন।
২. সরাসরি ক্যালকুলেটর হিসেবে মান বসিয়ে হিসাব করতে যেকোনো সংখ্যা ও চিহ্ন পাঠাতে পারেন (যেমন: 100/14.5)।
৩. বড় গাণিতিক সমস্যায় সূত্র অনুযায়ী ধাপগুলো মেনে মান বসিয়ে সমাধান করুন।"""

        st.session_state.chat_history.append(
            {"role": "assistant", "content": bot_reply}
        )
        with st.chat_message("assistant"):
            st.write(bot_reply)
