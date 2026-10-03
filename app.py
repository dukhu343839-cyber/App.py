import base64
import math
import re
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

# Initialize Session States
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

if "bg_image" not in st.session_state:
    st.session_state.bg_image = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{
        "role": "assistant",
        "content": (
            "হ্যালো! আমি আপনার ফিজিক্স অ্যাসিস্ট্যান্ট। আমাকে যেকোনো প্রশ্ন বা"
            " গাণিতিক হিসাব জিজ্ঞেস করতে পারেন।"
        ),
    }]

# ==========================================
# 2. DYNAMIC CSS & THEME ENGINE (GEMINI FONT)
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
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    /* Gemini Standard Clean Font Styling */
    html, body, [class*="css"], .stApp {{
        font-family: 'Hind Siliguri', 'Inter', -apple-system, sans-serif;
        background-color: #0F172A;
        color: #E2E8F0;
    }}

    {bg_css}

    /* Option Cards Styling */
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

    /* Sidebar Clean Navigation */
    div[data-testid="stSidebar"] {{
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }}
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. SIDEBAR NAVIGATION (TOP-LEFT MENU)
# ==========================================
with st.sidebar:
    st.title("📌 মেনু বার")

    if st.button("🏠 হোম স্ক্রিন (Home)"):
        st.session_state.current_page = "Home"
        st.rerun()

    if st.button("🎮 ২ডি ফিজিক্স গেম (2D Physics Game)"):
        st.session_state.current_page = "2D Physics Game"
        st.rerun()

    if st.button("🧠 দীপ এনালাইসিস (Deep Analysis)"):
        st.session_state.current_page = "Deep Analysis"
        st.rerun()

    if st.button("📕 ৯-১০ম ফিজিক্স (NCTB Physics)"):
        st.session_state.current_page = "NCTB Curriculum"
        st.rerun()

    if st.button("⏳ সিকিউ সলভ (CQ Solve)"):
        st.session_state.current_page = "CQ Solve"
        st.rerun()

    if st.button("🤖 ফিজিক্স বট ও বটসেশন"):
        st.session_state.current_page = "Physics Bot"
        st.rerun()

    if st.button("🎨 থিম ও ব্যাকগ্রাউন্ড সেটিংস"):
        st.session_state.current_page = "Theme Settings"
        st.rerun()

# ==========================================
# 4. HOME SCREEN (ONLY 4 MAIN OPTIONS)
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align: center; color: #38BDF8;'>পদার্থবিজ্ঞান"
        " অনুশীলন ক্লাব</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #94A3B8;'>নিচের যেকোনো অপশন"
        " নির্বাচন করুন</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🧠 দীপ এনালাইসিস (Deep Analysis)", key="home_deep"):
            st.session_state.current_page = "Deep Analysis"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📕 লার্নিং ফিজিক্স বেসিক (৯ম-১০ম)", key="home_basic"):
            st.session_state.current_page = "NCTB Curriculum"
            st.rerun()

    with col2:
        if st.button("📋 সিকিউ সলভ (CQ Solve)", key="home_cq"):
            st.session_state.current_page = "CQ Solve"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🤖 ডিসকাশন এনি প্রবলেম উইথ বট", key="home_bot"):
            st.session_state.current_page = "Physics Bot"
            st.rerun()

# ==========================================
# 5. HIGH QUALITY 2D PHYSICS GAME MODULE
# ==========================================
elif st.session_state.current_page == "2D Physics Game":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🎮 ২ডি প্রজেক্টাইল ক্যানন সিমুলেশন গেম")
    st.caption(
        "বেগ (Velocity) এবং কোণ (Angle) ঠিক করে টার্গেটে আঘাত করুন। প্রজেক্টাইল"
        " গতির বাস্তবসম্মত অনুকরণ।"
    )
    st.markdown("---")

    game_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body { margin: 0; background: #0F172A; color: #E2E8F0; font-family: 'Inter', sans-serif; text-align: center; overflow: hidden; }
        #canvas-container { display: flex; justify-content: center; flex-direction: column; align-items: center; }
        canvas { background: #1E293B; border: 2px solid #334155; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); margin-top: 5px; }
        .hud { display: flex; justify-content: space-around; width: 100%; max-width: 780px; font-size: 15px; color: #38BDF8; font-weight: bold; margin-bottom: 8px; background: #1E293B; padding: 10px; border-radius: 8px; border: 1px solid #334155; }
        .controls { display: flex; justify-content: center; gap: 15px; margin-top: 12px; align-items: center; flex-wrap: wrap; background: #1E293B; padding: 12px; border-radius: 10px; border: 1px solid #334155; width: 100%; max-width: 780px; }
        label { font-size: 14px; color: #94A3B8; font-weight: bold; }
        input[type=number] { background: #0F172A; color: #38BDF8; border: 1px solid #334155; padding: 6px; border-radius: 6px; font-weight: bold; width: 60px; text-align: center; }
        button { background: #38BDF8; color: #0F172A; border: none; padding: 8px 20px; font-weight: bold; border-radius: 6px; cursor: pointer; transition: 0.2s; font-size: 14px; }
        button:hover { background: #7DD3FC; transform: scale(1.03); }
        .reset-btn { background: #EF4444 !important; color: white !important; }
        .reset-btn:hover { background: #F87171 !important; }
    </style>
    </head>
    <body>
        <div id="canvas-container">
            <div class="hud">
                <span>🎯 স্কোর: <span id="score" style="color:#FFF;">0</span></span>
                <span>📍 টার্গেট দূরত্ব: <span id="targetDist" style="color:#FFF;">400</span>m</span>
                <span>💥 সফল আঘাত: <span id="hits" style="color:#FFF;">0</span></span>
            </div>
            <canvas id="gameCanvas" width="780" height="380"></canvas>
            <div class="controls">
                <label>বেগ $v$ (m/s): <input type="number" id="vel" value="65" min="10" max="120"></label>
                <label>কোণ $\theta$ (°): <input type="number" id="ang" value="45" min="0" max="90"></label>
                <button onclick="fire()">🚀 ফায়ার (Fire)</button>
                <button class="reset-btn" onclick="resetTarget()">🔄 নতুন টার্গেট</button>
            </div>
        </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        
        let score = 0;
        let hits = 0;
        let targetX = 400;
        let targetWidth = 35;
        let ball = { x: 40, y: 340, vx: 0, vy: 0, active: false };
        let particles = [];
        let trajectoryPath = [];

        function init() {
            resetTarget();
            draw();
        }

        function resetTarget() {
            targetX = 200 + Math.random() * 520;
            document.getElementById('targetDist').innerText = Math.round(targetX);
            ball.active = false;
            particles = [];
            trajectoryPath = [];
            draw();
        }

        function drawTrajectory() {
            let v = parseFloat(document.getElementById('vel').value);
            let a = parseFloat(document.getElementById('ang').value) * Math.PI / 180;
            let vx = v * Math.cos(a) * 0.22;
            let vy = -v * Math.sin(a) * 0.22;
            let px = 40, py = 340;
            let g = 0.15;

            ctx.beginPath();
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
            ctx.moveTo(px, py);

            for (let i = 0; i < 150; i++) {
                px += vx;
                py += vy;
                vy += g;
                if (py > 345) break;
                ctx.lineTo(px, py);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Ground Background Grid
            ctx.strokeStyle = "#334155";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0, 345);
            ctx.lineTo(canvas.width, 345);
            ctx.stroke();

            ctx.fillStyle = "#0F172A";
            ctx.fillRect(0, 345, canvas.width, 35);

            // Draw Cannon Base & Barrel
            let a = parseFloat(document.getElementById('ang').value) * Math.PI / 180;
            ctx.save();
            ctx.translate(40, 340);
            ctx.rotate(-a);
            ctx.fillStyle = "#38BDF8";
            ctx.shadowBlur = 10;
            ctx.shadowColor = "#38BDF8";
            ctx.fillRect(0, -6, 28, 12);
            ctx.restore();

            ctx.beginPath();
            ctx.arc(40, 340, 14, 0, Math.PI * 2);
            ctx.fillStyle = "#0284C7";
            ctx.fill();

            // Draw Trajectory Line
            if (!ball.active) {
                drawTrajectory();
            }

            // Draw Target Zone (Glow Effect)
            ctx.fillStyle = "#EF4444";
            ctx.shadowBlur = 15;
            ctx.shadowColor = "#EF4444";
            ctx.fillRect(targetX, 332, targetWidth, 13);
            ctx.shadowBlur = 0;

            // Draw Ball Path
            if (trajectoryPath.length > 1) {
                ctx.beginPath();
                ctx.strokeStyle = "rgba(125, 211, 252, 0.6)";
                ctx.lineWidth = 2;
                ctx.moveTo(trajectoryPath[0].x, trajectoryPath[0].y);
                for (let p of trajectoryPath) ctx.lineTo(p.x, p.y);
                ctx.stroke();
            }

            // Draw Animated Ball
            if (ball.active) {
                ctx.beginPath();
                ctx.arc(ball.x, ball.y, 5, 0, Math.PI * 2);
                ctx.fillStyle = "#F0ABFC";
                ctx.shadowBlur = 12;
                ctx.shadowColor = "#F0ABFC";
                ctx.fill();
                ctx.shadowBlur = 0;
            }

            // Draw Explosions / Particles
            for (let i = particles.length - 1; i >= 0; i--) {
                let p = particles[i];
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
                p.x += p.vx;
                p.y += p.vy;
                p.alpha -= 0.02;
                if (p.alpha <= 0) particles.splice(i, 1);
            }
        }

        function createExplosion(x, y, color) {
            for (let i = 0; i < 25; i++) {
                particles.push({
                    x: x, y: y,
                    vx: (Math.random() - 0.5) * 6,
                    vy: (Math.random() - 0.5) * 6,
                    size: Math.random() * 4 + 2,
                    color: color,
                    alpha: 1
                });
            }
        }

        function fire() {
            if (ball.active) return;
            let v = parseFloat(document.getElementById('vel').value);
            let a = parseFloat(document.getElementById('ang').value) * Math.PI / 180;
            
            ball.x = 40;
            ball.y = 340;
            ball.vx = v * Math.cos(a) * 0.22;
            ball.vy = -v * Math.sin(a) * 0.22;
            ball.active = true;
            trajectoryPath = [];
            
            animate();
        }

        function animate() {
            if (!ball.active) return;

            ball.x += ball.vx;
            ball.y += ball.vy;
            ball.vy += 0.15; // Gravity acceleration

            trajectoryPath.push({ x: ball.x, y: ball.y });

            // Check Floor Collision
            if (ball.y >= 340) {
                ball.y = 340;
                ball.active = false;

                // Check Target Hit Condition
                if (ball.x >= targetX && ball.x <= targetX + targetWidth) {
                    score += 100;
                    hits += 1;
                    document.getElementById('score').innerText = score;
                    document.getElementById('hits').innerText = hits;
                    createExplosion(ball.x, ball.y, "#34D399");
                    setTimeout(resetTarget, 1000);
                } else {
                    createExplosion(ball.x, ball.y, "#F87171");
                }
            }

            draw();
            if (ball.active || particles.length > 0) {
                requestAnimationFrame(animate);
            }
        }

        init();
    </script>
    </body>
    </html>
    """
    components.html(game_html, height=520)

# ==========================================
# 6. DEEP ANALYSIS (REAL-LIFE PHYSICS & FORMULAS)
# ==========================================
elif st.session_state.current_page == "Deep Analysis":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🧠 দীপ এনালাইসিস ও বাস্তবসম্মত উদাহরণ")
    st.markdown("---")

    tab1, tab2 = st.tabs(
        ["💡 বাস্তবসম্মত পদার্থবিজ্ঞান", "📐 মৌলিক সূত্র ও প্রতিপাদন"]
    )

    with tab1:
        with st.expander(
            "১. বাদুড় চোখ ছাড়া কীভাবে সামনে এগিয়ে চলে? (Ultrasonic Waves)"
        ):
            st.write("""
            **ব্যাখ্যা:** বাদুড় উড়ন্ত অবস্থায় উচ্চ কম্পাঙ্কের শব্দোত্তর তরঙ্গ (Ultrasonic Sound Waves - ২০,০০০ Hz এর বেশি) তৈরি করে। এই শব্দ সামনে থাকা বাধা বা শিকারে প্রতিফলিত হয়ে আবার বাদুড়ের কানে ফিরে আসে। শব্দ নির্গমন এবং প্রতিফলিত প্রতিধ্বনি শোনার মধ্যবর্তী সময় মেপে বাদুড় মস্তিষ্কের সাহায্যে বস্তুর দূরত্ব, আকার ও অবস্থান নিখুঁতভাবে হিসেব করে ফেলে। এটিকে **প্রতিধ্বনি অবস্থান নির্ধারণ (Echolocation)** বলা হয়।
            """)

        with st.expander(
            "২. ছোট লোহার পেরেক ডুবে কিন্তু বিরাট লোহার জাহাজ ভেসে থাকে কেন?"
        ):
            st.write("""
            **ব্যাখ্যা (আর্কিমিডিসের নীতি):** কোনো বস্তুকে পানিতে ডোবালে তা নিজের আয়তনের সমান পানি অপসারিত করে। একটি লোহার পেরেকের ভেতর ফাঁপা জায়গা না থাকায় এর গড় ঘনত্ব পানির ঘনত্বের চেয়ে বেশি হয়, ফলে পেরেকটি ডুবে যায়। 
            
            কিন্তু লোহার জাহাজ ভেতরে বিশালাকার ফাঁপা থাকে এবং বায়ুতে পূর্ণ থাকে। ফলে জাহাজের মোট ভরকে তার বিশাল আয়তন দিয়ে ভাগ করলে জাহাজের **গড় ঘনত্ব পানির ঘনত্বের চেয়ে অনেক কম** হয়ে যায়। জাহাজটি যে পরিমাণ পানি অপসারিত করে, তার প্লবতা বল (উর্ধ্বমুখী বল) জাহাজের মোট ওজনের সমান বা বেশি হয়, তাই জাহাজ ভেসে থাকে।
            """)

        with st.expander(
            "৩. নদীর পানির চেয়ে সমুদ্রের পানিতে সাঁতার কাটা সহজ কেন?"
        ):
            st.write("""
            **ব্যাখ্যা:** নদীর পানিতে দ্রবীভূত লবণের পরিমাণ খুবই কম থাকে, কিন্তু সমুদ্রের পানিতে প্রচুর পরিমাণে লবণ দ্রবীভূত থাকে। ফলে **সমুদ্রের পানির ঘনত্ব নদীর পানির ঘনত্বের চেয়ে বেশি** হয়। পানির ঘনত্ব বেশি হওয়ায় সমুদ্রের পানি সাঁতারুর ওপর বেশি **উর্ধ্বমুখী প্লবতা বল (Buoyancy Force)** প্রয়োগ করে, যা সাঁতারুকে সহজে ভাসিয়ে রাখে।
            """)

        with st.expander(
            "৪. ইটের ওপর হাঁটার চেয়ে ভাঙা ইটের (খোয়া) ওপর হাঁটা কষ্টদায়ক কেন?"
        ):
            st.write("""
            **ব্যাখ্যা (চাপের সূত্র $P = F/A$):** আমরা জানি, চাপ $P = \frac{F}{A}$ (বল ÷ ক্ষেত্রফল)। ইটের সমতল পৃষ্ঠের ক্ষেত্রফল বেশি হওয়ায় পায়ের তলায় প্রয়োগকৃত চাপ কম হয়। কিন্তু ভাঙা ইটের তীক্ষ্ণ ও ধারালো কোণাগুলোর সংস্পর্শ ক্ষেত্রফল ($A$) অত্যন্ত কম। ক্ষেত্রফল কমে গেলে চাপ ($P$) বহুগুণ বেড়ে যায়, যা পায়ের স্নায়ুতে বেশি ব্যথার সৃষ্টি করে।
            """)

        with st.expander(
            "৫. শীতের দিনে বিদ্যুতের তার টানটান হয়ে ছিঁড়ে যায় কেন?"
        ):
            st.write("""
            **ব্যাখ্যা (তাপীয় সংকোচন):** যেকোনো কঠিন পদার্থ ঠান্ডা হলে সংকুচিত হয়। শীতকালে তাপমাত্রা কমে গেলে বিদ্যুতের তামার বা অ্যালুমিনিয়ামের তার সংকুচিত হয়ে দৈর্ঘ্য ছোট হতে চায়। তার দুটি খুঁটির সাথে শক্ত করে বাঁধা থাকায় সংকোচনজনিত টান বল অতিরিক্ত বৃদ্ধি পায় এবং তার ছিঁড়ে যায়।
            """)

        with st.expander("৬. শীতের দিনে ভেজা কাপড় দ্রুত শুকায় কেন?"):
            st.write("""
            **ব্যাখ্যা:** কাপড় শুকানো নির্ভর করে বাতাসের **আপেক্ষিক আর্দ্রতার (Relative Humidity)** ওপর। শীতকালে বাতাসে জলীয় বাষ্পের পরিমাণ অত্যন্ত কম থাকে অর্থাৎ বাতাস শুষ্ক থাকে। শুষ্ক বাতাস দ্রুত ভেজা কাপড় থেকে পানি বাষ্পীভবন করে শুষে নিতে পারে, তাই শীতকালে কাপড় দ্রুত শুকায়।
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
# 7. BANGLADESH CLASS 9-10 PHYSICS CURRICULUM
# ==========================================
elif st.session_state.current_page == "NCTB Curriculum":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("📖 ৯ম-১০ম শ্রেণি পদার্থবিজ্ঞান কারিকুলাম (NCTB)")
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
            "ওহমের সূত্র, রোদ, শ্রেণী ও সমান্তরাল সার্কিট এবং ক্ষমতা।",
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
        with st.expander(f"📌 {chap_title}"):
            st.write(f"**মূল বিষয়বস্তু:** {chap_desc}")
            if formula != "মেডিকেল ফিজিক্স ও ডায়াগনস্টিক প্রয়োগ।":
                st.latex(formula)

# ==========================================
# 8. CQ SOLVE MODULE
# ==========================================
elif st.session_state.current_page == "CQ Solve":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("📝 সিকিউ সমাধান (Creative Questions)")
    st.markdown("---")

    with st.expander(
        "প্রশ্ন ১: ২০m উঁচু থেকে ৫০g ভরের একটি বস্তুকে ফেলে দেওয়া হলো।"
    ):
        st.write("""
        **গ) ভূমি স্পর্শ করার মুহূর্তে বেগ কত?**
        
        **সমাধান:**
        দেওয়া আছে, $u = 0$, $h = 20\text{ m}$, $g = 9.8\text{ m/s}^2$
        
        সূত্র: $v^2 = u^2 + 2gh = 0 + 2 \times 9.8 \times 20 = 392$
        $$\implies v = \sqrt{392} \approx 19.8 \text{ m/s}$$
        """)

# ==========================================
# 9. BOT DISCUSSION & CALCULATOR
# ==========================================
elif st.session_state.current_page == "Physics Bot":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🤖 ফিজিক্স চ্যাটবট ও ক্যালকুলেটর")
    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_query = st.chat_input("প্রশ্ন বা গাণিতিক হিসাব লিখুন (যেমন: 250*9.8)...")

    if user_query:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_query}
        )
        with st.chat_message("user"):
            st.write(user_query)

        text = user_query.lower().strip()

        if any(
            w in text
            for w in ["hi", "hello", "হাই", "হ্যালো", "কেমন আছো", "কেমন আছেন"]
        ):
            reply = "হ্যালো! আমি ভালো আছি। আপনার ফিজিক্সের যেকোনো প্রশ্ন বা সমীকরণ আমাকে পাঠাতে পারেন।"
        elif re.match(r"^[0-9\.\+\-\*\/\(\)\s]+$", text):
            try:
                ans = eval(text)
                reply = f"গাণিতিক ফলাফল: `{text}` = **{ans}**"
            except:
                reply = "সঠিক গাণিতিক সংখ্যা ও চিহ্ন ব্যবহার করুন।"
        else:
            reply = f"আপনার প্রশ্নটি ({user_query}) লিপিবদ্ধ করা হয়েছে। যেকোনো গাণিতিক হিসেব সরাসরি টাইপ করে ফলাফল পেয়ে যাবেন।"

        st.session_state.chat_history.append(
            {"role": "assistant", "content": reply}
        )
        with st.chat_message("assistant"):
            st.write(reply)

# ==========================================
# 10. THEME & GALLERY BACKGROUND SETTINGS
# ==========================================
elif st.session_state.current_page == "Theme Settings":
    if st.button("⬅️ হোমে ফিরে যান"):
        st.session_state.current_page = "Home"
        st.rerun()

    st.title("🎨 থিম ও ব্যাকগ্রাউন্ড সেটিংস")
    st.markdown("---")

    st.subheader("গ্যালারি থেকে ব্যাকগ্রাউন্ড ছবি আপলোড করুন")
    uploaded_file = st.file_uploader(
        "পছন্দের ছবি বেছে নিন (JPG, PNG)", type=["jpg", "jpeg", "png"]
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
