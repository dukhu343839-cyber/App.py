import json
import math
import streamlit as st

# ==========================================
# ১. পেজ কনফিগারেশন ও সাইডবার সেটআপ
# ==========================================
st.set_page_config(
    page_title="Physics Smart Solver & Notes",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# ২. প্রাথমিক ডেটাবেজ (সেশন স্টেট)
# ==========================================
if "problems" not in st.session_state:
    st.session_state.problems = [
        {
            "id": 1,
            "chapter": "গতিবিদ্যা (Kinematics)",
            "title": "প্রাসের সর্বোচ্চ উচ্চতা ও পাল্লা",
            "question": (
                "একটি বস্তুকে 20 m/s বেগে অনুভূমিকের সাথে 30° কোণে নিক্ষেপ করা"
                " হলো। বস্তুটির সর্বোচ্চ উচ্চতা কত?"
            ),
            "formula": r"H = \frac{v_0^2 \sin^2\theta}{2g}",
            "solution": (
                "দেওয়া আছে:\n"
                "$v_0 = 20\\text{ m/s}$\n"
                "$\\theta = 30^\\circ$\n"
                "$g = 9.8\\text{ m/s}^2$\n\n"
                "হিসাব:\n"
                "$H = \\frac{20^2 \\times (\\sin 30^\\circ)^2}{2 \\times 9.8} ="
                " \\frac{400 \\times 0.25}{19.6} = 5.10\\text{ m}$"
            ),
            "difficulty": "মাঝারি (Medium)",
        },
        {
            "id": 2,
            "chapter": "কাজ, ক্ষমতা ও শক্তি",
            "title": "কুয়া খালি করার কৃতকাজ",
            "question": (
                "10m গভীর এবং 2m ব্যাসার্ধের একটি পানি পূর্ণ কুয়া পাম্প দিয়ে"
                " খালি করতে কৃতকাজ কত?"
            ),
            "formula": r"W = m g h_{avg}",
            "solution": (
                "ভারকেন্দ্রের সরণ $h_{avg} = \\frac{10}{2} = 5\\text{ m}$\n"
                "পানির ভর $m = \\pi r^2 h \\times 1000 = \\pi (1)^2 (10) \\times"
                " 1000 = 31415.9\\text{ kg}$\n\n"
                "$W = 31415.9 \\times 9.8 \\times 5 = 1,539,379.1\\text{"                 " Joules}$"
            ),
            "difficulty": "কঠিন (Hard)",
        },
    ]

# ==========================================
# ৩. নেভিগেশন সাইডবার
# ==========================================
st.sidebar.title("⚛️ ফিজিক্স অ্যাপ নেভিগেশন")
menu = st.sidebar.radio(
    "মেনু নির্বাচন করুন:",
    [
        "🏠 হোম / ওভারভিউ",
        "➕ নতুন সমস্যা যোগ করুন",
        "📚 সব সমস্যা ও সমাধান",
        "🧮 লাইভ ফিজিক্স ক্যালকুলেটর",
        "💾 ব্যাকআপ ও ডেটা রিস্টোর",
    ],
)

# ==========================================
# ৪. পেজ ১: হোম / ওভারভিউ
# ==========================================
if menu == "🏠 হোম / ওভারভিউ":
    st.title("📚 পদার্থবিজ্ঞান প্রবলেম সলভার ড্যাশবোর্ড")
    st.write(
        "স্বাগতম! এখানে আপনার পদার্থবিজ্ঞানের যেকোনো গাণিতিক সমস্যা, সূত্র এবং"
        " স্টেপ-বাই-স্টেপ সমাধান সংরক্ষণ ও অনুশীলন করতে পারবেন।"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("মোট সংরক্ষিত সমস্যা", f"{len(st.session_state.problems)} টি")

    chapters = list(
        set(p["chapter"] for p in st.session_state.problems if "chapter" in p)
    )
    col2.metric("মোট কভার করা অধ্যায়", f"{len(chapters)} টি")
    col3.metric("অ্যাপ সংস্করণ", "v1.0")

    st.markdown("---")
    st.subheader("📌 সাম্প্রতিক যুক্ত হওয়া সমস্যাসমূহ")
    for prob in reversed(st.session_state.problems[-3:]):
        st.info(
            f"**[{prob.get('chapter', 'সাধারণ')}]**"
            f" {prob.get('title', 'শিরোনামহীন')}"
        )

# ==========================================
# ৫. পেজ ২: নতুন সমস্যা যোগ করার ফর্ম
# ==========================================
elif menu == "➕ নতুন সমস্যা যোগ করুন":
    st.title("➕ নতুন সমস্যা ও সমাধান যোগ করুন")

    with st.form("add_problem_form", clear_on_submit=True):
        col_ch, col_diff = st.columns([2, 1])

        chapter_list = [
            "গতিবিদ্যা (Kinematics)",
            "নিউটনীয় বলবিদ্যা",
            "কাজ, ক্ষমতা ও শক্তি",
            "মহাকর্ষ ও অভিকর্ষ",
            "পদার্থের গাঠনিক ধর্ম",
            "পর্যায়বৃত্ত গতি",
            "তরঙ্গ",
            "স্থির তড়িৎ",
            "চল তড়িৎ",
            "অন্যান্য (Custom)",
        ]
        selected_chapter = col_ch.selectbox("অধ্যায় নির্বাচন করুন", chapter_list)
        if selected_chapter == "অন্যান্য (Custom)":
            selected_chapter = col_ch.text_input("নতুন অধ্যায়ের নাম লিখুন")

        difficulty = col_diff.selectbox(
            "কঠিনতার মাত্রা", ["সহজ (Easy)", "মাঝারি (Medium)", "কঠিন (Hard)"]
        )

        title = st.text_input("সমস্যার শিরোনাম (যেমন: প্রাসের সর্বোচ্চ উচ্চতা)")
        question = st.text_area("মূল প্রশ্ন / সমস্যাটি বিশদে লিখুন")

        st.markdown(
            "**LaTeX সূত্র ইনপুট:** (উদাহরণ:`H = \\frac{v_0^2"
            " \\sin^2\\theta}{2g}`)"
        )
        formula = st.text_input("প্রয়োজনীয় সূত্র (LaTeX কোড)")

        solution = st.text_area(
            "ধাপভিত্তিক সমাধান (Markdown ও LaTeX সাপোর্ট করবে)"
        )

        submit_btn = st.form_submit_button("💾 ডাটাবেজে সেভ করুন")

        if submit_btn:
            if title and question:
                new_id = (
                    max(
                        [p.get("id", 0) for p in st.session_state.problems]
                        + [0]
                    )
                    + 1
                )
                new_problem = {
                    "id": new_id,
                    "chapter": selected_chapter,
                    "title": title,
                    "question": question,
                    "formula": formula,
                    "solution": solution,
                    "difficulty": difficulty,
                }
                st.session_state.problems.append(new_problem)
                st.success("✅ সমস্যাটি সফলভাবে সেভ করা হয়েছে!")
            else:
                st.error(
                    "⚠️ অনুগ্রহ করে অন্তত সমস্যার শিরোনাম এবং মূল প্রশ্ন পূরণ"
                    " করুন।"
                )

# ==========================================
# ৬. পেজ ৩: সমস্যা অনুসন্ধান ও দর্শন
# ==========================================
elif menu == "📚 সব সমস্যা ও সমাধান":
    st.title("📚 সংরক্ষিত সমস্যা ও সমাধান")

    col_search, col_filter = st.columns([2, 1])
    search_query = col_search.text_input("🔍 সমস্যা বা শব্দ দিয়ে খুঁজুন")

    all_chapters = ["সব অধ্যায়"] + list(
        set(p.get("chapter", "") for p in st.session_state.problems)
    )
    selected_filter = col_filter.selectbox("অধ্যায় ফিল্টার", all_chapters)

    filtered_problems = st.session_state.problems
    if selected_filter != "সব অধ্যায়":
        filtered_problems = [
            p for p in filtered_problems if p.get("chapter") == selected_filter
        ]
    if search_query:
        filtered_problems = [
            p
            for p in filtered_problems
            if search_query.lower() in p.get("title", "").lower()
            or search_query.lower() in p.get("question", "").lower()
            or search_query.lower() in p.get("chapter", "").lower()
        ]

    st.write(f"মোট ফলাফল: **{len(filtered_problems)}** টি")

    for idx, prob in enumerate(filtered_problems):
        with st.expander(
            f"📌 [{prob.get('chapter', 'General')}] {prob.get('title')}"
            f" ({prob.get('difficulty', 'N/A')})"
        ):
            st.markdown(f"**প্রশ্ন:** {prob.get('question')}")

            if prob.get("formula"):
                st.markdown("**প্রয়োজনীয় সূত্র:**")
                st.latex(prob.get("formula"))

            if prob.get("solution"):
                st.markdown("**সমাধান:**")
                st.markdown(prob.get("solution"))

            col_del, _ = st.columns([1, 4])
            if col_del.button(
                f"🗑️ মুছে ফেলুন", key=f"del_{prob.get('id', idx)}"
            ):
                st.session_state.problems = [
                    p
                    for p in st.session_state.problems
                    if p.get("id") != prob.get("id")
                ]
                st.success("মুছে ফেলা হয়েছে!")
                st.rerun()

# ==========================================
# ৭. পেজ ৪: লাইভ ক্যালকুলেটর
# ==========================================
elif menu == "🧮 লাইভ ফিজিক্স ক্যালকুলেটর":
    st.title("🧮 লাইভ ফিজিক্স সূত্র সলভার")
    st.write("মান বসিয়ে সরাসরি গাণিতিক ফলাফল হিসেব করুন:")

    calc_type = st.selectbox(
        "ক্যালকুলেটর নির্বাচন করুন:",
        [
            "১. প্রাসের গতিবিদ্যা (Projectile Motion)",
            "২. গতিশক্তি (Kinetic Energy)",
        ],
    )

    if calc_type == "১. প্রাসের গতিবিদ্যা (Projectile Motion)":
        st.subheader("প্রাসের সর্বোচ্চ উচ্চতা ($H$) ও পাল্লা ($R$) নির্ণয়")
        u = st.number_input(
            "আদিবেগ $v_0$ (m/s):", min_value=0.0, value=20.0, step=1.0
        )
        angle_deg = st.number_input(
            "নিক্ষেপ কোণ $\\theta$ (ডিগ্রি):",
            min_value=0.0,
            max_value=90.0,
            value=30.0,
            step=1.0,
        )
        g = st.number_input("অভিকর্ষজ ত্বরণ $g$ (m/s²):", value=9.8, step=0.1)

        angle_rad = math.radians(angle_deg)
        H = (u**2 * (math.sin(angle_rad) ** 2)) / (2 * g)
        R = (u**2 * math.sin(2 * angle_rad)) / g

        st.success(f"**সর্বোচ্চ উচ্চতা ($H$):** {H:.2f} meters")
        st.info(f"**অনুভূমিক পাল্লা ($R$):** {R:.2f} meters")

    elif calc_type == "২. গতিশক্তি (Kinetic Energy)":
        st.subheader("গতিশক্তি $E_k = \\frac{1}{2}mv^2$ নির্ণয়")
        m = st.number_input("বস্তুর ভর $m$ (kg):", min_value=0.0, value=5.0)
        v = st.number_input("বেগ $v$ (m/s):", min_value=0.0, value=10.0)

        Ek = 0.5 * m * (v**2)
        st.success(f"**গতিশক্তি ($E_k$):** {Ek:.2f} Joules")

# ==========================================
# ৮. পেজ ৫: ব্যাকআপ ও ডেটা রিস্টোর
# ==========================================
elif menu == "💾 ব্যাকআপ ও ডেটা রিস্টোর":
    st.title("💾 ব্যাকআপ ও ডেটা ম্যানেজমেন্ট")

    json_data = json.dumps(
        st.session_state.problems, ensure_ascii=False, indent=2
    )
    st.download_button(
        label="📥 সব নোট JSON ফাইল হিসেবে ডাউনলোড করুন",
        data=json_data,
        file_name="physics_notes_backup.json",
        mime="application/json",
    )

    st.markdown("---")
    st.subheader("📤 ব্যাকআপ JSON ফাইল আপলোড করুন")
    uploaded_file = st.file_uploader("JSON ফাইল নির্বাচন করুন", type=["json"])
    if uploaded_file is not None:
        try:
            imported_notes = json.load(uploaded_file)
            if st.button("ডেটা রিস্টোর নিশ্চিত করুন"):
                st.session_state.problems = imported_notes
                st.success("✅ সকল তথ্য রিস্টোর করা হয়েছে!")
                st.rerun()
        except Exception as e:
            st.error(f"ফাইল খুলতে সমস্যা হয়েছে: {e}")
  
