import streamlit as st
import json, datetime, random
import re
import base64
import streamlit.components.v1 as components
from io import BytesIO

from config import APP_NAME, APP_TAGLINE, COLORS
from ui_components import inject_custom_css, render_header, level_emoji
from roles import roles, resources
from gap_analysis import (
    calculate_skill_gaps,
    identify_strength_areas,
    calculate_readiness_score,
    create_radar_chart,
    create_gap_bar_chart,
)
from learning_roadmap import generate_learning_roadmap, generate_recommendation_summary, get_learning_path, get_priority_description
from quiz_engine import generate_adaptive_quiz, score_quiz
from ml_models import skill_predictor, personalizer
from ai_engine import AIEngine
from resume_parser import extract_skills_from_text
from voice_assistant import VoiceAssistant
from auth_ui import require_auth, render_logout_button

# Try importing xhtml2pdf for PDF generation (works on Windows without external dependencies)
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ──────────────────────────────────────────────
#  Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

# ──────────────────────────────────────────────
#  Authentication Check - Must be logged in
# ──────────────────────────────────────────────
require_auth()

# ──────────────────────────────────────────────
#  Session state initialisation
# ──────────────────────────────────────────────

# Load HuggingFace API key from secrets if available
_hf_key_from_secrets = ""
try:
    _hf_key_from_secrets = st.secrets.get("huggingface", {}).get("api_key", "")
except Exception:
    pass

_defaults = {
    "user_scores": {},
    "quiz_mode": False,
    "quiz_responses": {},
    "quiz": [],
    "voice_assistant": None,
    "ai_engine": None,
    "hf_key": _hf_key_from_secrets,
    "profile_name": "",
    "chat_history": [],
    "selected_role": None,
    "resume_text": "",
    "resume_skills": {},
    "last_voice_transcript": "",
    "last_voice_analysis": {},
    "last_voice_reply": "",
    "current_interview_question": "",
    "interview_active": False,
    "interview_rounds": 3,
    "interview_current_round": 0,
    "interview_questions": [],
    "interview_feedback": [],
    "interview_scores": [],
    "interview_summary": "",
    "interview_domain": "Mixed",
    "interview_qa": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Lazy-init heavy objects
if st.session_state.voice_assistant is None:
    st.session_state.voice_assistant = VoiceAssistant()

# ──────────────────────────────────────────────
#  Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=60)
    st.markdown(f"### {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.markdown("---")

    # HuggingFace API key (optional)
    if _hf_key_from_secrets:
        st.success("✓ HuggingFace API Key loaded")
        hf_key = _hf_key_from_secrets
    else:
        hf_key = st.text_input("🔑 HuggingFace API Key (optional)",
                               value=st.session_state.hf_key,
                               help="Enables AI Chat Advisor and resume AI extraction")
        hf_key = hf_key.strip()
    
    if hf_key != st.session_state.hf_key:
        st.session_state.hf_key = hf_key
        st.session_state.ai_engine = AIEngine(api_key=hf_key) if hf_key else AIEngine()

    if st.session_state.ai_engine is None:
        st.session_state.ai_engine = AIEngine(api_key=hf_key) if hf_key else AIEngine()

    if st.session_state.ai_engine and st.session_state.ai_engine.is_connected:
        st.success("✓ AI connected", icon="🤖")
    else:
        st.info("AI runs in offline mode")

    if hf_key and st.session_state.ai_engine and st.session_state.ai_engine.last_error:
        st.caption(f"⚠️ API issue: {st.session_state.ai_engine.last_error[:140]}")

    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Dashboard",
        "📋 Self-Assessment",
        "❓ Adaptive Quiz",
        "📊 Gap Analysis",
        "🗺️ Learning Roadmap",
        "🧠 AI Insights",
        "📄 Export Report",
    ])
    
    # Logout button
    render_logout_button()

# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────
def _role_reqs():
    return roles.get(st.session_state.selected_role, {})

def _need_role():
    if not st.session_state.selected_role:
        st.warning("⚠️ Please select a target role on the **Dashboard** page first.")
        return True
    return False


def _portfolio_context() -> str:
    resume_text = (st.session_state.resume_text or "").strip()
    resume_skills = st.session_state.resume_skills or {}
    skill_list = ", ".join(list(resume_skills.keys())[:8]) if resume_skills else "None provided"
    brief_resume = resume_text[:700] if resume_text else "No portfolio/resume text provided."
    return (
        f"Portfolio skills detected: {skill_list}. "
        f"Portfolio summary text: {brief_resume}"
    )


def _extract_interview_score(feedback: str) -> float:
    if not feedback:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    if match:
        try:
            return max(0.0, min(10.0, float(match.group(1))))
        except ValueError:
            return 0.0
    return 0.0

# ============================================================
#  PAGE: DASHBOARD
# ============================================================
if page == "🏠 Dashboard":
    render_header(APP_NAME, APP_TAGLINE)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.session_state.profile_name = st.text_input("👤 Your Name", value=st.session_state.profile_name)
        st.session_state.selected_role = st.selectbox(
            "🎯 Target Role",
            list(roles.keys()),
            index=list(roles.keys()).index(st.session_state.selected_role) if st.session_state.selected_role in roles else 0,
        )
    with col_b:
        if st.session_state.selected_role:
            st.markdown(f"**Required skills for {st.session_state.selected_role}:**")
            for skill, lvl in roles[st.session_state.selected_role].items():
                st.markdown(f"- {skill}: **{lvl}**/10")

    st.markdown("---")

    # ---- Resume Upload ----
    st.subheader("📄 Resume Skill Extraction")
    st.caption("Paste your resume text or key skills below — we'll auto-detect proficiency levels.")
    resume = st.text_area("Paste resume / bio here", value=st.session_state.resume_text, height=150,
                          placeholder="e.g. 5 years Python, built ML pipelines with scikit-learn, deployed on AWS…")
    if st.button("🔍 Extract Skills from Resume") and resume.strip():
        st.session_state.resume_text = resume
        # Try AI extraction first, fall back to keyword matching
        ai: AIEngine = st.session_state.ai_engine
        ai_raw = ai.extract_skills_from_resume(resume) if ai else ""
        # keyword-based extraction (always works)
        kw_skills = extract_skills_from_text(resume)
        # merge AI results if parseable
        if ai_raw:
            for part in ai_raw.split(","):
                part = part.strip()
                if ":" in part:
                    name, lvl_str = part.rsplit(":", 1)
                    try:
                        lvl = int(lvl_str.strip())
                        name = name.strip()
                        if 1 <= lvl <= 10 and name:
                            kw_skills[name] = max(kw_skills.get(name, 0), lvl)
                    except ValueError:
                        pass
        st.session_state.resume_skills = kw_skills
        # Also push into user_scores (as baseline)
        for sk, lv in kw_skills.items():
            st.session_state.user_scores[sk] = max(st.session_state.user_scores.get(sk, 0), lv)
        st.success(f"✅ Detected **{len(kw_skills)}** skills from your resume!")

    if st.session_state.resume_skills:
        with st.expander("Detected Skills", expanded=True):
            cols = st.columns(3)
            for idx, (sk, lv) in enumerate(st.session_state.resume_skills.items()):
                with cols[idx % 3]:
                    st.markdown(f"**{sk}** — {lv}/10 {level_emoji(lv)}")

    # ---- Quick overview metrics (if assessment exists) ----
    if st.session_state.selected_role and st.session_state.user_scores:
        st.markdown("---")
        st.subheader("📊 Quick Overview")
        reqs = _role_reqs()
        gaps = calculate_skill_gaps(st.session_state.user_scores, reqs)
        readiness = calculate_readiness_score(st.session_state.user_scores, reqs)
        strengths = identify_strength_areas(st.session_state.user_scores, reqs)
        gap_count = len([g for g in gaps.values() if g["gap"] > 0])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Readiness", f"{readiness}%")
        c2.metric("Skills Assessed", len(st.session_state.user_scores))
        c3.metric("At Target", len(strengths))
        c4.metric("Gaps", gap_count)

        st.plotly_chart(create_radar_chart(st.session_state.user_scores, reqs), width="stretch")

# ============================================================
#  PAGE: SELF-ASSESSMENT
# ============================================================
elif page == "📋 Self-Assessment":
    render_header("Self-Assessment", "Rate your current proficiency for each skill (1 = no experience, 10 = expert)")

    if _need_role():
        st.stop()

    selected_role = st.session_state.selected_role
    reqs = _role_reqs()

    for skill, required in reqs.items():
        c1, c2, c3 = st.columns([3, 0.8, 0.5])
        with c1:
            val = st.slider(
                skill,
                min_value=0.0, max_value=10.0, step=0.5,
                value=float(st.session_state.user_scores.get(skill, 5)),
                key=f"sa_{skill}",
            )
            st.session_state.user_scores[skill] = val
        with c2:
            st.caption(f"Target: **{required}**")
        with c3:
            st.write(level_emoji(val))

    if st.button("💾 Save Assessment"):
        st.success("Assessment saved!")

# ============================================================
#  PAGE: ADAPTIVE QUIZ
# ============================================================
elif page == "❓ Adaptive Quiz":
    render_header("Adaptive Quiz", "Real multiple-choice questions that adapt to your level")

    if _need_role():
        st.stop()

    reqs = _role_reqs()

    if not st.session_state.quiz_mode:
        st.info("The quiz generates **real MCQ questions** per skill.  Difficulty adapts based on your self-assessment scores.")
        qps = st.slider("Questions per skill", 1, 3, 2)
        if st.button("▶️ Start Quiz"):
            quiz = generate_adaptive_quiz(
                list(reqs.keys()),
                user_levels=st.session_state.user_scores,
                questions_per_skill=qps,
            )
            st.session_state.quiz = quiz
            st.session_state.quiz_responses = {}
            st.session_state.quiz_mode = True
            st.rerun()
    else:
        quiz = st.session_state.quiz
        if not quiz:
            st.warning("No questions available for the selected role's skills. Try another role.")
            if st.button("Back"):
                st.session_state.quiz_mode = False
                st.rerun()
            st.stop()

        st.progress(
            len(st.session_state.quiz_responses) / len(quiz),
            text=f"Answered {len(st.session_state.quiz_responses)}/{len(quiz)} questions",
        )
        
        st.markdown("---")

        for idx, q in enumerate(quiz, 1):
            qid = q["id"]
            with st.container(border=True):
                st.markdown(f"**Question {idx} of {len(quiz)}** | [{q['difficulty'].title()}] *{q['skill']}*")
                st.write(q["question"])
                
                # Check if already answered
                current_answer = st.session_state.quiz_responses.get(qid)
                default_index = None
                if current_answer is not None:
                    default_index = current_answer
                
                chosen = st.radio(
                    "Select your answer:",
                    options=q["options"],
                    index=default_index,
                    key=f"quiz_opt_{qid}",
                )
                
                if chosen is not None:
                    st.session_state.quiz_responses[qid] = q["options"].index(chosen)
        
        st.markdown("---")
        
        # Show completion status
        answered = len(st.session_state.quiz_responses)
        total = len(quiz)
        if answered == total:
            st.success(f"✅ All {total} questions answered! Ready to submit.")
        else:
            st.warning(f"⚠️ {total - answered} question(s) remaining")

        col_sub, col_cancel = st.columns(2)
        with col_sub:
            if st.button("✅ Submit Quiz", type="primary", disabled=(answered < total)):
                if len(st.session_state.quiz_responses) < len(quiz):
                    st.error(f"Please answer all {total} questions before submitting. ({answered}/{total} answered)")
                else:
                    results = score_quiz(quiz, st.session_state.quiz_responses)
                    st.session_state.quiz_mode = False

                    # Show results
                    st.markdown("---")
                    st.subheader("📝 Quiz Results")
                    for skill, res in results.items():
                        emoji = "✅" if res["correct"] == res["total"] else "🔶" if res["correct"] > 0 else "❌"
                        st.write(f"{emoji} **{skill}**: {res['correct']}/{res['total']} correct → estimated level **{res['score_0_10']}**/10 (highest difficulty: {res['max_difficulty']})")
                        # Update user scores
                        prev = st.session_state.user_scores.get(skill, 0)
                        new  = round((prev + res["score_0_10"]) / 2, 1) if prev else res["score_0_10"]
                        st.session_state.user_scores[skill] = new

                    st.success("Scores updated!  Check **Gap Analysis** for the full picture.")
        with col_cancel:
            if st.button("🚫 Cancel Quiz"):
                st.session_state.quiz_mode = False
                st.rerun()

# ============================================================
#  PAGE: GAP ANALYSIS
# ============================================================
elif page == "📊 Gap Analysis":
    render_header("Gap Analysis", "Visual comparison of your skills vs role requirements")

    if _need_role():
        st.stop()

    reqs = _role_reqs()
    user_scores = st.session_state.user_scores
    gaps = calculate_skill_gaps(user_scores, reqs)
    strengths = identify_strength_areas(user_scores, reqs)
    readiness = calculate_readiness_score(user_scores, reqs)

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Role Readiness", f"{readiness}%")
    c2.metric("Skills at Target", len(strengths))
    c3.metric("Gaps to Close", len([g for g in gaps.values() if g["gap"] > 0]))
    c4.metric("Top Priority", max(gaps, key=lambda s: gaps[s]["priority_score"]) if gaps else "—")

    # Charts side-by-side
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.subheader("🕸️ Radar — You vs Required")
        st.plotly_chart(create_radar_chart(user_scores, reqs), width="stretch")
    with chart_right:
        st.subheader("📊 Gap Bar Chart")
        st.plotly_chart(create_gap_bar_chart(gaps), width="stretch")

    # Detailed cards
    st.markdown("---")
    tab_gaps, tab_strengths = st.tabs(["🔻 Gaps to Fill", "💪 Strengths"])

    with tab_gaps:
        gap_items = {k: v for k, v in gaps.items() if v["gap"] > 0}
        if gap_items:
            for skill, d in gap_items.items():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.write(f"**{skill}**")
                        st.caption(f"Current {round(d['current'], 1)} → Target {round(d['required'], 1)}  |  Gap: {round(d['gap'], 1)}")
                    with c2:
                        st.progress(d["current"] / d["required"] if d["required"] else 1)
                    with c3:
                        if d["priority_score"] > 15:
                            st.error("HIGH")
                        elif d["priority_score"] > 8:
                            st.warning("MEDIUM")
                        else:
                            st.success("LOW")
        else:
            st.success("🎉 No gaps — you meet all requirements!")

    with tab_strengths:
        if strengths:
            st.write(f"💪 You have **{len(strengths)}** skill(s) at or above target level:")
            st.write("")
            for skill, d in strengths.items():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"✅ **{skill}**")
                        st.caption(f"Your level: {round(d['current'], 1)} | Target: {round(d['required'], 1)} | Exceeds by: +{round(d['surplus'], 1)}")
                    with c2:
                        if d['surplus'] > 0:
                            st.success(f"+{round(d['surplus'], 1)} above")
                        else:
                            st.info("At target")
        else:
            st.info("Complete the assessment to see your strengths.")

# ============================================================
#  PAGE: LEARNING ROADMAP
# ============================================================
elif page == "🗺️ Learning Roadmap":
    render_header("Learning Roadmap", "AI-generated weekly plan tailored to your gaps")

    if _need_role():
        st.stop()

    reqs = _role_reqs()
    user_scores = st.session_state.user_scores
    gaps = calculate_skill_gaps(user_scores, reqs)
    roadmap = generate_learning_roadmap(user_scores, reqs, weeks=4)
    recs = generate_recommendation_summary(gaps, resources)

    # Immediate actions
    st.subheader("⚡ Immediate Actions")
    for action in recs["immediate_actions"]:
        effort_icon = "🔥" if action["effort"] == "High" else "✏️"
        st.write(f"{effort_icon} **{action['skill']}**: {action['action']}")
    st.info(f"⏱️ **Timeline**: {recs['timeline_estimate']}")

    st.markdown("---")
    st.subheader("📅 Weekly Plan")
    
    # Add informative legend
    with st.expander("ℹ️ Understanding Your Roadmap", expanded=False):
        st.markdown("""
        **Skill Levels Explained:**
        - **1-2**: Beginner - Just starting out, learning basics
        - **3-4**: Elementary - Basic understanding, can follow tutorials
        - **5-6**: Intermediate - Can work independently on tasks
        - **7-8**: Advanced - Strong proficiency, can solve complex problems
        - **9-10**: Expert - Mastery level, can teach and innovate
        
        **Priority Indicators:**
        - 🔴 **Critical**: Essential for the role, focus on this immediately
        - 🟡 **Important**: High priority, should be learned soon
        - 🟢 **Moderate**: Nice to have, can be learned later
        
        **Effort Required:**
        - Each level typically requires 1-2 weeks of focused learning (10-15 hours/week)
        - The plan assumes consistent daily practice for best results
        """)

    if roadmap["weeks"]:
        for week in roadmap["weeks"]:
            with st.expander(f"**Week {week['week']}** - Skills to Focus On", expanded=(week["week"] == 1)):
                for f in week["focus_areas"]:
                    st.markdown(f"### 🎯 {f['skill']}")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Current Level:** {round(f['current_level'], 1)}/10 - _{f['current_description']}_")
                        st.write(f"**Target Level:** {round(f['target_level'], 1)}/10 - _{f['target_description']}_")
                        st.write(f"**Improvement Needed:** {round(f['levels_to_improve'], 1)} levels ({f['difficulty']} track)")
                    with col2:
                        st.info(f"{f['priority']}")
                    
                    st.divider()
                
                st.write("**📋 Daily Study Targets:**")
                for t in week["daily_targets"]:
                    st.write(f"  • {t}")
    else:
        st.success("🎉 All target skills achieved!")

    # Resources
    st.markdown("---")
    st.subheader("📚 Recommended Resources")
    st.caption("Curated learning materials prioritized by your skill gaps")
    
    priority_skills = [s for s in gaps if gaps[s]["gap"] > 0]
    for rank, skill in enumerate(priority_skills[:5], 1):
        gap_info = gaps[skill]
        priority_label = get_priority_description(gap_info['priority_score']) if 'learning_roadmap' in dir() else f"Priority Score: {gap_info['priority_score']:.0f}/20"
        
        with st.expander(f"{rank}. {skill} - {priority_label}"):
            st.write(f"**Gap to Close:** {round(gap_info['current'], 1)}/10 → {round(gap_info['required'], 1)}/10 ({round(gap_info['gap'], 1)} levels)")
            
            if skill in resources:
                for r in resources[skill]:
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"📖 **{r['title']}**")
                    c2.write(f"🏷️ {r['type']}")
                    c3.write(f"⏱️ {r['duration']}")
                    if r.get("url"):
                        st.caption(f"[{r['platform']}]({r['url']})")
            else:
                st.caption("Resources coming soon.")

# ============================================================
#  PAGE: AI INSIGHTS
# ============================================================
elif page == "🧠 AI Insights":
    render_header("AI Insights", "ML predictions + AI career advisor chat")

    if _need_role():
        st.stop()

    reqs = _role_reqs()
    user_scores = st.session_state.user_scores
    gaps = calculate_skill_gaps(user_scores, reqs)

    # ---- ML Predictions ----
    st.subheader("⏰ ML Time-to-Target Predictions")
    st.caption("AI-powered estimates based on your current level, target level, and study hours")
    
    weekly_hours = st.slider("Hours you can study per week", 5, 40, 15, 
                             help="More hours = faster progress. Typical: 10-20 hours/week")

    predictions = []
    for skill, d in gaps.items():
        if d["gap"] > 0:
            weeks_needed = skill_predictor.predict_weeks_to_target(d["current"], d["required"], weekly_hours)
            predictions.append({"skill": skill, "current": d["current"], "target": d["required"],
                                "weeks": weeks_needed, "priority": d["priority_score"], "gap": d["gap"]})
    predictions.sort(key=lambda x: x["priority"], reverse=True)

    for p in predictions:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**{p['skill']}**")
            c2.write(f"📊 Level {round(p['current'], 1)} → {round(p['target'], 1)} ({round(p['gap'], 1)} levels)")
            c3.write(f"⏱️ ~{p['weeks']:.1f} weeks")
            if p["weeks"] <= 4:
                c4.success("⚡ Quick win")
            elif p["weeks"] <= 8:
                c4.warning("📅 Medium term")
            else:
                c4.error("🎯 Long term")

    # Optimal order
    st.markdown("---")
    st.subheader("🎯 Optimal Skill Learning Order")
    st.caption("Prioritized based on role requirements, skill gaps, and learning efficiency")
    
    order = personalizer.get_optimal_skill_order(gaps, reqs)
    for rank, skill in enumerate(order, 1):
        if gaps.get(skill, {}).get("gap", 0) > 0:
            priority_desc = get_priority_description(gaps[skill]['priority_score'])
            st.write(f"**{rank}.** {skill} - {priority_desc}")

    # ---- AI Chat ----
    st.markdown("---")
    st.subheader("💬 AI Career Advisor")
    st.caption("Ask anything about skill development, career paths, or interview prep.")

    ai: AIEngine = st.session_state.ai_engine

    st.markdown("---")
    st.subheader("📝 Knowledge Test & Voice Coaching")
    st.caption("Take adaptive tests with instant feedback, or get voice coaching help.")

    mode = st.radio(
        "Select Mode",
        ["Test Mode", "Help Mode"],
        horizontal=True,
        key="voice_mode_selector",
    )

    va = st.session_state.voice_assistant
    top_gaps = [skill for skill in gaps if gaps[skill]["gap"] > 0][:5]
    top_gaps_text = ", ".join(top_gaps) if top_gaps else "general skills"

    if mode == "Test Mode":
        st.caption("📝 Take a real-time knowledge test with questions tailored to your weak areas. Get instant scoring and improvement recommendations.")

        cfg1, cfg2 = st.columns([2, 1])
        with cfg1:
            test_domain = st.selectbox(
                "Test Focus Area", 
                ["Weakest Skills (Adaptive)", "Technical Skills", "Behavioral & Soft Skills", "Mixed - All Skills"],
                index=0,
                help="Choose which areas to test"
            )
        with cfg2:
            num_questions = st.slider("Questions", 3, 10, 5, help="Number of test questions")

        # Initialize test state
        if 'test_active' not in st.session_state:
            st.session_state.test_active = False
        if 'test_questions' not in st.session_state:
            st.session_state.test_questions = []
        if 'test_current_index' not in st.session_state:
            st.session_state.test_current_index = 0
        if 'test_answers' not in st.session_state:
            st.session_state.test_answers = []
        if 'test_scores' not in st.session_state:
            st.session_state.test_scores = []
        if 'test_feedback' not in st.session_state:
            st.session_state.test_feedback = []

        b1, b2 = st.columns(2)
        with b1:
            if st.button("🎯 Start Test", key="start_test_btn", type="primary", disabled=st.session_state.test_active):
                # Generate all test questions upfront
                st.session_state.test_active = True
                st.session_state.test_current_index = 0
                st.session_state.test_answers = []
                st.session_state.test_scores = []
                st.session_state.test_feedback = []
                st.session_state.test_questions = []

                with st.spinner("Generating personalized test questions..."):
                    # Determine focus based on selection
                    if "Weakest" in test_domain:
                        focus_skills = top_gaps[:num_questions]
                        test_type = "adaptive weakness"
                    elif "Technical" in test_domain:
                        tech_skills = [s for s in gaps.keys() if any(kw in s.lower() for kw in ['python', 'java', 'sql', 'cloud', 'api', 'framework', 'algorithm', 'data structure'])]
                        focus_skills = tech_skills[:num_questions] if tech_skills else list(gaps.keys())[:num_questions]
                        test_type = "technical"
                    elif "Behavioral" in test_domain:
                        soft_skills = [s for s in gaps.keys() if any(kw in s.lower() for kw in ['communication', 'leadership', 'teamwork', 'problem solving', 'collaboration', 'management'])]
                        focus_skills = soft_skills[:num_questions] if soft_skills else list(gaps.keys())[:num_questions]
                        test_type = "behavioral"
                    else:
                        focus_skills = list(gaps.keys())[:num_questions]
                        test_type = "mixed"

                    # Generate questions
                    for i, skill in enumerate(focus_skills[:num_questions], 1):
                        skill_level = st.session_state.user_scores.get(skill, 1)
                        gap_size = gaps.get(skill, {}).get('gap', 0)
                        
                        question_prompt = (
                            f"You are testing knowledge for the role: {st.session_state.selected_role}. "
                            f"Generate ONE {test_type} question for the skill: {skill}. "
                            f"Candidate's current level: {skill_level}/10, Gap: {gap_size}. "
                            f"Question difficulty should match their current level + 1. "
                            f"Make it practical and scenario-based when possible. "
                            f"Return ONLY the question text, no numbering or prefix."
                        )
                        question = ai.chat(question_prompt)
                        st.session_state.test_questions.append({
                            'id': i,
                            'skill': skill,
                            'question': question,
                            'level': skill_level,
                            'gap': gap_size
                        })
                
                st.success(f"✅ Test ready with {len(st.session_state.test_questions)} questions!")
                st.rerun()

        with b2:
            if st.button("🛑 End Test", key="end_test_btn", disabled=not st.session_state.test_active):
                st.session_state.test_active = False
                st.session_state.test_current_index = 0

        # Display test questions
        if st.session_state.test_active and st.session_state.test_questions:
            current_idx = st.session_state.test_current_index
            total_questions = len(st.session_state.test_questions)

            if current_idx < total_questions:
                # Show progress
                progress_val = min(1.0, (current_idx + 1) / total_questions)
                st.progress(progress_val, text=f"Question {current_idx + 1} of {total_questions}")
                
                current_q = st.session_state.test_questions[current_idx]
                
                # Display question
                st.markdown("---")
                st.markdown(f"### 📝 Question {current_q['id']}")
                st.info(f"**Skill Being Tested:** {current_q['skill']} (Your level: {round(current_q['level'], 1)}/10, Gap: {round(current_q['gap'], 1)})")
                st.markdown(f"**Question:** {current_q['question']}")
                
                # Answer input
                answer_key = f"test_answer_{current_idx}"
                user_answer = st.text_area(
                    "Your Answer:",
                    height=150,
                    key=answer_key,
                    placeholder="Type your answer here... Be specific and detailed."
                )

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    submit_disabled = not user_answer or len(user_answer.strip()) < 10
                    if st.button("✅ Submit Answer", key=f"submit_{current_idx}", type="primary", disabled=submit_disabled):
                        # Evaluate the answer
                        with st.spinner("🤖 AI is evaluating your answer..."):
                            eval_prompt = (
                                f"You are an expert evaluator for the role: {st.session_state.selected_role}. "
                                f"Skill being tested: {current_q['skill']}. "
                                f"Question: {current_q['question']}. "
                                f"Candidate's answer: {user_answer}. "
                                f"Candidate's current skill level: {current_q['level']}/10. "
                                f"\n\nProvide evaluation in this EXACT format:"
                                f"\n\nScore: X/10"
                                f"\n\n✅ Strong Points:"
                                f"\n- [point 1]"
                                f"\n- [point 2]"
                                f"\n\n⚠️ Areas to Improve:"
                                f"\n- [improvement 1]"
                                f"\n- [improvement 2]"
                                f"\n\n💡 Better Answer Approach:"
                                f"\n[3-4 sentences showing a stronger answer]"
                                f"\n\n🎯 Recommendation:"
                                f"\n[Specific advice on how to improve this skill]"
                            )
                            
                            feedback = ai.chat(eval_prompt)
                            
                            # Extract score
                            score = 5  # default
                            import re
                            score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)\s*/\s*10', feedback)
                            if score_match:
                                score = float(score_match.group(1))
                            
                            # Store results
                            st.session_state.test_answers.append(user_answer)
                            st.session_state.test_scores.append(score)
                            st.session_state.test_feedback.append({
                                'question': current_q['question'],
                                'skill': current_q['skill'],
                                'answer': user_answer,
                                'score': score,
                                'feedback': feedback
                            })
                            
                            # Show immediate feedback
                            st.markdown("---")
                            st.markdown("### 📊 Your Score & Feedback")
                            
                            score_color = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
                            st.metric("Score", f"{score}/10", delta=f"{score_color}")
                            
                            st.markdown(feedback)
                            
                            # Move to next question
                            if current_idx + 1 < total_questions:
                                st.session_state.test_current_index += 1
                                if st.button("➡️ Next Question", key=f"next_{current_idx}", type="primary"):
                                    st.rerun()
                            else:
                                st.success("🎉 Test completed! View your results below.")
                                st.session_state.test_active = False
                                
                            st.rerun()
                
                with col2:
                    if st.button("⏭️ Skip Question", key=f"skip_{current_idx}"):
                        st.session_state.test_answers.append("(Skipped)")
                        st.session_state.test_scores.append(0)
                        st.session_state.test_feedback.append({
                            'question': current_q['question'],
                            'skill': current_q['skill'],
                            'answer': "(Skipped)",
                            'score': 0,
                            'feedback': "Question skipped - no evaluation available."
                        })
                        st.session_state.test_current_index += 1
                        st.rerun()

        # Show test results summary
        if not st.session_state.test_active and st.session_state.test_scores:
            st.markdown("---")
            st.markdown("## 📊 Test Results Summary")
            
            total_score = sum(st.session_state.test_scores)
            max_score = len(st.session_state.test_scores) * 10
            avg_score = total_score / len(st.session_state.test_scores)
            percentage = (total_score / max_score) * 100
            
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Score", f"{total_score}/{max_score}")
            col2.metric("Average", f"{avg_score:.1f}/10")
            col3.metric("Percentage", f"{percentage:.1f}%")
            
            grade = "A+" if percentage >= 90 else "A" if percentage >= 80 else "B" if percentage >= 70 else "C" if percentage >= 60 else "D" if percentage >= 50 else "F"
            col4.metric("Grade", grade)
            
            # Performance interpretation
            if percentage >= 80:
                st.success(f"🎉 Excellent performance! You demonstrated strong knowledge in {test_domain}.")
            elif percentage >= 60:
                st.info(f"👍 Good effort! You have a solid foundation but there's room for improvement.")
            else:
                st.warning(f"📚 Keep learning! Focus on strengthening these skills through practice and study.")
            
            # Detailed feedback for each question
            with st.expander("📋 View Detailed Feedback for All Questions", expanded=False):
                for i, fb in enumerate(st.session_state.test_feedback, 1):
                    st.markdown(f"### Question {i}: {fb['skill']}")
                    st.markdown(f"**Q:** {fb['question']}")
                    st.markdown(f"**Your Answer:** {fb['answer']}")
                    st.markdown(f"**Score:** {fb['score']}/10")
                    st.markdown(fb['feedback'])
                    st.markdown("---")
            
            # Overall recommendations
            st.markdown("### 🎯 Overall Recommendations")
            weak_areas = [fb['skill'] for fb in st.session_state.test_feedback if fb['score'] < 6]
            strong_areas = [fb['skill'] for fb in st.session_state.test_feedback if fb['score'] >= 8]
            
            if strong_areas:
                st.success(f"**✅ Strong Areas:** {', '.join(strong_areas)}")
            if weak_areas:
                st.warning(f"**⚠️ Focus on improving:** {', '.join(weak_areas)}")
            
            # Action plan
            st.markdown("**📈 Next Steps:**")
            if weak_areas:
                st.markdown(f"1. Review learning materials for: {', '.join(weak_areas[:3])}")
                st.markdown("2. Practice with real projects or case studies")
                st.markdown("3. Retake the test to track your improvement")
            else:
                st.markdown("1. Continue building on your strong foundation")
                st.markdown("2. Challenge yourself with advanced topics")
                st.markdown("3. Consider sharing your knowledge by mentoring others")

    else:
        st.caption("Help mode: tell your problem by voice and receive spoken coaching guidance.")

        # Initialize coaching session state
        if 'coaching_active' not in st.session_state:
            st.session_state.coaching_active = False
        if 'coaching_response' not in st.session_state:
            st.session_state.coaching_response = ""

        help_audio = st.audio_input("Record what you need help with", key="voice_help_audio")
        if help_audio is not None:
            help_bytes = help_audio.getvalue()
            st.audio(help_bytes, format="audio/wav")

            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🆘 Get Voice Coaching Help", key="voice_help_btn", type="primary", disabled=st.session_state.coaching_active):
                    transcript = va.transcribe_audio_bytes(help_bytes)

                    if not transcript:
                        st.error("Could not transcribe your voice message. Please retry.")
                    else:
                        st.session_state.coaching_active = True
                        analysis = va.analyze_transcript(transcript)
                        st.session_state.last_voice_transcript = transcript
                        st.session_state.last_voice_analysis = analysis

                        st.markdown(f"**Transcript:** {transcript}")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Words", analysis.get("word_count", 0))
                        c2.metric("Confidence", analysis.get("confidence", "Low"))
                        c3.metric("Sentiment", analysis.get("sentiment", "Neutral"))
                        c4.metric("Complexity", analysis.get("complexity", "Low"))

                        help_prompt = (
                            f"Act as an interview coach for role {st.session_state.selected_role}. "
                            f"User's voice message: {transcript}. "
                            f"Priority skill gaps: {top_gaps_text}. "
                            "Provide practical help in this format: "
                            "1) Quick diagnosis, 2) Step-by-step fix plan (max 5 steps), "
                            "3) One model answer/example the user can say in an interview."
                        )

                        with st.spinner("Generating coaching response…"):
                            help_reply = ai.chat(help_prompt)

                        st.session_state.coaching_response = help_reply
                        st.session_state.last_voice_reply = help_reply
                        st.session_state.chat_history.append({"role": "user", "content": f"🎤 Help request: {transcript}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": help_reply})

                        st.markdown("**Coach Response**")
                        st.markdown(help_reply)
            
            with col2:
                if st.button("⏹️ End Session", key="end_coaching_btn", type="secondary", disabled=not st.session_state.coaching_active):
                    st.session_state.coaching_active = False
                    
                    # Generate a warm closing message
                    farewell_messages = [
                        "Great work today! Remember, practice makes progress. Feel free to come back anytime! 👋",
                        "You're on the right track! Keep practicing and you'll see improvement. Good luck! 🌟",
                        "Session ended. Thank you for your time today. Keep working on those skills! 💪",
                        "Nice working with you! Remember to review the feedback and practice regularly. See you next time! 😊",
                        "Coaching session complete! You've got this - stay focused and keep improving! 🎯"
                    ]
                    farewell = random.choice(farewell_messages)
                    
                    st.success(farewell)
                    st.session_state.chat_history.append({"role": "assistant", "content": f"🤝 {farewell}"})
                    
                    st.session_state.coaching_response = ""
                    st.rerun()

        # Show current coaching response if active
        if st.session_state.coaching_active and st.session_state.coaching_response:
            with st.expander("📋 Current Coaching Session", expanded=True):
                st.info("💡 Coaching session is active. Review the guidance above and click 'End Session' when you're ready to finish.")
                st.markdown(st.session_state.coaching_response)

    # Show chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask the AI advisor…"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build context
        ctx = (f"User targets role: {st.session_state.selected_role}. "
               f"Current scores: {json.dumps({s: user_scores.get(s, 0) for s in reqs})}. "
               f"Top gaps: {', '.join(s for s in list(gaps)[:3] if gaps[s]['gap'] > 0)}.")

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = ai.chat(prompt, context=ctx)
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ============================================================
#  PAGE: EXPORT REPORT
# ============================================================
elif page == "📄 Export Report":
    render_header("Export Report", "Download a professional skill-gap report")

    if _need_role():
        st.stop()

    reqs = _role_reqs()
    user_scores = st.session_state.user_scores
    gaps = calculate_skill_gaps(user_scores, reqs)
    strengths = identify_strength_areas(user_scores, reqs)
    readiness = calculate_readiness_score(user_scores, reqs)

    name = st.session_state.profile_name or "User"
    role = st.session_state.selected_role
    today = datetime.date.today().strftime("%B %d, %Y")

    # Build HTML report
    
    # Executive summary
    total_gaps = len([g for g in gaps.values() if g['gap'] > 0])
    avg_gap = round(sum(g['gap'] for g in gaps.values()) / len(gaps), 1) if gaps else 0
    critical_gaps = [s for s, d in gaps.items() if d['priority_score'] > 15]
    
    # Readiness interpretation
    if readiness >= 90:
        readiness_msg = "Excellent! You're highly qualified for this role."
        readiness_color = "#4ecdc4"
    elif readiness >= 70:
        readiness_msg = "Good! You have most of the required skills. Focus on closing key gaps."
        readiness_color = "#90a0f0"
    elif readiness >= 50:
        readiness_msg = "Fair. You're on the right track but need to develop several skills."
        readiness_color = "#ffd93d"
    else:
        readiness_msg = "Getting started. Focus on building foundational skills first."
        readiness_color = "#ff6b6b"
    
    # Detailed gap rows with recommendations
    gap_rows = ""
    for s, d in gaps.items():
        if d["gap"] > 0:
            color = "#ff6b6b" if d["gap"] > 3 else "#ffd93d" if d["gap"] > 0 else "#4ecdc4"
            priority_badge = "🔴 CRITICAL" if d["priority_score"] > 15 else "🟡 HIGH" if d["priority_score"] > 8 else "🟢 MEDIUM"
            
            # Generate personalized recommendation based on skill, current level, and gap
            current_lvl = d["current"]
            gap_size = d["gap"]
            
            # Determine skill category
            tech_skills = ["Python", "JavaScript", "Java", "C++", "SQL", "React", "Node.js", "Docker", "Kubernetes", "AWS", "Azure", "Git"]
            is_tech = any(tech.lower() in s.lower() for tech in tech_skills)
            
            # Build detailed recommendation
            if current_lvl <= 2:  # Beginner
                if gap_size > 5:
                    action = f"Start with beginner-friendly courses on {s}. Complete 3-4 structured tutorials, then build 2 simple projects to apply concepts. Join {s} communities for support."
                elif gap_size > 3:
                    action = f"Take a comprehensive {s} course covering fundamentals. Practice daily for 1-2 hours and complete at least one guided project."
                else:
                    action = f"Watch intro videos on {s} basics, complete interactive tutorials, and practice with coding challenges or examples."
            elif current_lvl <= 5:  # Intermediate
                if gap_size > 4:
                    action = f"Enroll in advanced {s} courses. Build 2-3 real-world projects and contribute to open-source. Study advanced patterns and best practices."
                elif gap_size > 2:
                    action = f"Practice {s} through project-based learning. Build an end-to-end application and review industry best practices."
                else:
                    action = f"Deepen {s} knowledge with specialized tutorials. Complete 1 medium-complexity project and optimize for {role} requirements."
            else:  # Advanced
                if gap_size > 2:
                    action = f"Master advanced {s} concepts for {role}. Build production-grade projects, mentor others, and stay updated with latest trends."
                else:
                    action = f"Fine-tune {s} expertise with edge cases and optimizations. Review real-world {role} case studies and architectural patterns."
            
            gap_rows += f"""
            <tr>
                <td><b>{s}</b></td>
                <td style='text-align:center'>{round(d['current'], 1)}/10</td>
                <td style='text-align:center'>{round(d['required'], 1)}/10</td>
                <td style='color:{color};font-weight:700;text-align:center'>{round(d['gap'], 1)}</td>
                <td style='text-align:center'>{priority_badge}</td>
                <td style='font-size:0.9rem'>{action}</td>
            </tr>
            """
    
    if not gap_rows:
        gap_rows = "<tr><td colspan='6' style='text-align:center;color:#4ecdc4'>🎉 No gaps detected — you meet all requirements!</td></tr>"
    
    # Strength details
    strength_list = ""
    if strengths:
        for s, d in strengths.items():
            surplus_badge = f"+{round(d['surplus'], 1)}" if d['surplus'] > 0 else "At Target"
            strength_list += f"""
            <div style='background:#1e2130;border-left:4px solid #4ecdc4;padding:1rem;margin:0.5rem 0;border-radius:6px'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                        <b style='font-size:1.1rem;color:#4ecdc4'>✅ {s}</b>
                        <p style='margin:0.3rem 0 0 0;color:#999'>Current Level: {round(d['current'], 1)}/10 | Target: {round(d['required'], 1)}/10</p>
                    </div>
                    <span style='background:#4ecdc4;color:#000;padding:0.4rem 1rem;border-radius:20px;font-weight:700'>{surplus_badge}</span>
                </div>
            </div>
            """
    else:
        strength_list = "<p style='color:#999;font-style:italic'>No strengths identified yet. Complete the assessment to see your strongest areas.</p>"
    
    # Learning path recommendations
    learning_recommendations = ""
    gap_skills = [(s, d) for s, d in gaps.items() if d['gap'] > 0]
    if gap_skills:
        # Sort by priority
        sorted_gaps = sorted(gap_skills, key=lambda x: x[1]['priority_score'], reverse=True)[:5]
        for idx, (skill, details) in enumerate(sorted_gaps, 1):
            current = details['current']
            target = details['required']
            gap = details['gap']
            
            # Generate personalized learning path
            if current <= 2:  # Beginner path
                phase1 = f"<b>Phase 1 (Weeks 1-2):</b> Complete a beginner {skill} course covering core concepts. Watch 10-15 video tutorials and take notes."
                phase2 = f"<b>Phase 2 (Weeks 3-4):</b> Follow 3-5 hands-on tutorials to build simple projects. Practice coding daily for at least 1 hour."
                phase3 = f"<b>Phase 3 (Weeks 5+):</b> Build your first independent {skill} project. Get code reviews from experienced developers."
            elif current <= 5:  # Intermediate path
                phase1 = f"<b>Phase 1 (Weeks 1-2):</b> Study advanced {skill} topics relevant to {role}. Review official documentation and architectural patterns."
                phase2 = f"<b>Phase 2 (Weeks 3-5):</b> Build a production-ready {skill} project with proper testing and CI/CD. Apply industry best practices."
                phase3 = f"<b>Phase 3 (Weeks 6+):</b> Contribute to open-source {skill} projects. Mentor juniors and write technical articles to solidify knowledge."
            else:  # Advanced path
                phase1 = f"<b>Phase 1 (Weeks 1-2):</b> Master cutting-edge {skill} techniques used in {role}. Study system design and scalability patterns."
                phase2 = f"<b>Phase 2 (Weeks 3-4):</b> Architect and build a complex {skill} solution. Optimize for performance, security, and maintainability."
                phase3 = f"<b>Phase 3 (Weeks 5+):</b> Lead {skill} initiatives, conduct code reviews, and publish advanced tutorials or speak at conferences."
            
            # Resources based on current level
            if current <= 3:
                resources = f"Recommended: Udemy/Coursera beginner courses, freeCodeCamp, YouTube tutorials, interactive coding platforms like Codecademy"
            elif current <= 6:
                resources = f"Recommended: Pluralsight/LinkedIn Learning, MDN docs, GitHub projects, LeetCode/HackerRank challenges"
            else:
                resources = f"Recommended: Advanced courses, tech conferences, research papers, architecture blogs, open-source contributions"
            
            learning_recommendations += f"""
            <div style='background:#1e2130;padding:1.2rem;margin:1rem 0;border-radius:8px;border-left:4px solid #667eea'>
                <div style='font-size:1.1rem;margin-bottom:0.8rem'>
                    <b style='color:#90a0f0'>{idx}. {skill}</b> 
                    <span style='color:#999'>— Go from level {round(current, 1)} to {round(target, 1)} ({round(gap, 1)} level gap)</span>
                </div>
                <div style='background:#1a1d2e;padding:1rem;border-radius:6px;margin:0.5rem 0'>
                    <p style='margin:0.5rem 0;line-height:1.8'>{phase1}</p>
                    <p style='margin:0.5rem 0;line-height:1.8'>{phase2}</p>
                    <p style='margin:0.5rem 0;line-height:1.8'>{phase3}</p>
                </div>
                <div style='margin-top:0.8rem;padding:0.8rem;background:rgba(102,126,234,0.1);border-radius:6px'>
                    <p style='margin:0;font-size:0.9rem;color:#b0b8f0'><b>📚 Resources:</b> {resources}</p>
                </div>
                <div style='margin-top:0.8rem;display:flex;justify-content:space-between;font-size:0.9rem;color:#999'>
                    <span>⏱️ Estimated time: {round(gap * 2, 1)}-{round(gap * 4, 1)} weeks</span>
                    <span>🎯 Priority: {'Critical' if details['priority_score'] > 15 else 'High' if details['priority_score'] > 8 else 'Medium'}</span>
                </div>
            </div>
            """
    else:
        learning_recommendations = "<p style='color:#4ecdc4;font-size:1.1rem'>🎉 No gaps to address — maintain and expand your current skillset!</p>"

    # Generate personalized next steps based on readiness
    if readiness < 50:
        next_steps_content = f"""
        <li><b>Start with Fundamentals</b> — You have {total_gaps} skills to develop. Begin with the 🔴 critical priorities: {', '.join(critical_gaps[:3]) if critical_gaps else 'focus on basic skills'}.</li>
        <li><b>Set a Structured Learning Schedule</b> — Dedicate 10-15 hours per week to learning. Create a daily routine with specific time blocks for studying.</li>
        <li><b>Take Beginner Courses</b> — Enroll in comprehensive courses that cover foundational concepts for your weakest skills.</li>
        <li><b>Build Simple Projects</b> — Apply what you learn by creating 2-3 beginner-level projects to solidify understanding.</li>
        <li><b>Join Learning Communities</b> — Connect with others learning the same skills for support, resources, and motivation.</li>
        <li><b>Track Progress Weekly</b> — Retake the assessment every 2 weeks to see improvements and adjust your learning plan.</li>
        <li><b>Be Patient and Consistent</b> — Reaching {role} readiness is a marathon, not a sprint. Celebrate small wins along the way!</li>
"""
    elif readiness < 70:
        next_steps_content = f"""
        <li><b>Prioritize Critical Gaps</b> — Focus on {len(critical_gaps)} critical skills: {', '.join(critical_gaps[:3]) if critical_gaps else 'highest priority areas'}. These will have the biggest impact.</li>
        <li><b>Take the Adaptive Quiz</b> — Validate your self-assessment with MCQ questions. This helps identify knowledge gaps within each skill.</li>
        <li><b>Build Real-World Projects</b> — Create 2-3 portfolio projects that demonstrate your {role} skills. Focus on quality over quantity.</li>
        <li><b>Study Best Practices</b> — Review industry standards, design patterns, and architectural approaches used in {role} positions.</li>
        <li><b>Contribute to Open Source</b> — Find beginner-friendly issues on GitHub projects related to your target skills.</li>
        <li><b>Network with Professionals</b> — Connect with {role} professionals on LinkedIn. Ask for informational interviews to learn more.</li>
        <li><b>Update Your Resume</b> — Highlight your {len(strengths)} strength areas prominently. Include links to your projects and GitHub.</li>
"""
    elif readiness < 90:
        next_steps_content = f"""
        <li><b>Fine-Tune Remaining Gaps</b> — You're close! Focus on closing the {total_gaps} remaining gaps to reach full readiness for {role}.</li>
        <li><b>Deepen Expertise</b> — Go beyond basics in your weaker areas. Study advanced topics, edge cases, and optimization techniques.</li>
        <li><b>Build Production-Ready Projects</b> — Create complex projects with proper testing, CI/CD, monitoring, and documentation.</li>
        <li><b>Validate with Quizzes</b> — Take the adaptive quiz to confirm your skill levels objectively. Aim for high scores on critical skills.</li>
        <li><b>Practice System Design</b> — For {role} roles, practice designing scalable systems and explaining your architectural decisions.</li>
        <li><b>Prepare Interview Stories</b> — Document your {len(strengths)} strengths with specific examples using the STAR method (Situation, Task, Action, Result).</li>
        <li><b>Start Applying</b> — Your {readiness}% readiness is strong. Begin applying to {role} positions while continuing to improve.</li>
"""
    else:
        next_steps_content = f"""
        <li><b>You're Job-Ready!</b> — With {readiness}% readiness and {len(strengths)} skills at/above target, you're well-qualified for {role} positions.</li>
        <li><b>Polish Your Applications</b> — Tailor your resume and cover letter to highlight your strengths and relevant project experience.</li>
        <li><b>Prepare for Interviews</b> — Practice technical interviews, system design, and behavioral questions specific to {role}.</li>
        <li><b>Showcase Your Work</b> — Build a portfolio website or GitHub profile showcasing your best projects with clear README files.</li>
        <li><b>Network Actively</b> — Attend industry events, join {role} communities, and leverage your network for job referrals.</li>
        <li><b>Continue Learning</b> — Stay current with industry trends. Set aside time weekly to learn emerging technologies.</li>
        <li><b>Consider Leadership</b> — Mentor others, write technical blogs, or speak at meetups to establish yourself as an expert.</li>
"""

    # Generate chart images for the report
    radar_chart_img = ""
    gap_chart_img = ""
    try:
        import warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        
        # Create radar chart
        radar_fig = create_radar_chart(user_scores, reqs)
        radar_bytes = radar_fig.to_image(format="png", width=800, height=600)
        radar_b64 = base64.b64encode(radar_bytes).decode()
        radar_chart_img = f'<img src="data:image/png;base64,{radar_b64}" style="width:100%;max-width:800px;border-radius:8px;margin:1rem 0" alt="Radar Chart">'
        
        # Create gap bar chart
        gap_fig = create_gap_bar_chart(gaps)
        gap_bytes = gap_fig.to_image(format="png", width=800, height=600)
        gap_b64 = base64.b64encode(gap_bytes).decode()
        gap_chart_img = f'<img src="data:image/png;base64,{gap_b64}" style="width:100%;max-width:800px;border-radius:8px;margin:1rem 0" alt="Gap Bar Chart">'
    except Exception as e:
        # If chart export fails, show a note
        st.info(f"📊 Chart generation: {str(e)[:100]}")
        radar_chart_img = '<div style="background:#1a1d2e;padding:2rem;border-radius:8px;text-align:center;color:#999;font-style:italic;margin:1rem 0"><p>📊 Radar Chart - View in Gap Analysis page</p></div>'
        gap_chart_img = '<div style="background:#1a1d2e;padding:2rem;border-radius:8px;text-align:center;color:#999;font-style:italic;margin:1rem 0"><p>📊 Gap Bar Chart - View in Gap Analysis page</p></div>'

    html_report = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:'Inter',Helvetica,Arial,sans-serif;color:#e8e8e8;background:#0e1117;max-width:1000px;margin:auto;padding:2rem}}
h1{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1.5rem 2rem;border-radius:12px;box-shadow:0 8px 32px rgba(102,126,234,0.5);text-align:center}}
h2{{color:#90a0f0;border-bottom:3px solid #667eea;padding-bottom:10px;margin-top:3rem}}
h3{{color:#b0b8f0;margin-top:1.5rem;margin-bottom:0.8rem}}
p,li,td{{color:#d0d0d0;line-height:1.7}}
b{{color:#f0f0f0}}
table{{width:100%;border-collapse:collapse;margin:1.5rem 0;font-size:0.95rem;box-shadow:0 4px 12px rgba(0,0,0,0.3)}}
th,td{{text-align:left;padding:14px;border-bottom:1px solid #2a2d3a}}
th{{background:#667eea;color:#fff;font-weight:600;text-transform:uppercase;font-size:0.85rem;letter-spacing:0.5px}}
tr:nth-child(even){{background:#16181f}}
tr:hover{{background:#1e2130}}
.metric{{display:inline-block;background:linear-gradient(135deg,#1e2130,#2a2d3a);border:2px solid rgba(102,126,234,0.5);border-radius:12px;padding:1.5rem 2rem;margin:0.5rem;text-align:center;min-width:140px;box-shadow:0 4px 12px rgba(0,0,0,0.3)}}
.metric b{{font-size:2.5rem;color:#90a0f0;display:block;margin-bottom:0.5rem;font-weight:700}}
.metric span{{font-size:0.9rem;color:#999;text-transform:uppercase;letter-spacing:1px}}
.summary-box{{background:linear-gradient(135deg,#1e2130,#262a3d);border-radius:12px;padding:2rem;margin:2rem 0;border-left:5px solid #90a0f0;box-shadow:0 4px 20px rgba(0,0,0,0.3)}}
.info-box{{background:#1a1d2e;border-radius:10px;padding:1.2rem;margin:1.5rem 0;border:1px solid #2a2d3a;box-shadow:0 2px 8px rgba(0,0,0,0.2)}}
img{{display:block;margin:1rem auto;box-shadow:0 4px 20px rgba(0,0,0,0.5);border-radius:8px}}
.info-box{{background:#1a1d2e;border-radius:8px;padding:1rem;margin:1rem 0;border:1px solid #333}}
</style></head><body>
<h1>🚀 {APP_NAME} — Comprehensive Skill Gap Report</h1>
<p style='font-size:1.05rem'><b>Name:</b> {name} &nbsp;|&nbsp; <b>Target Role:</b> {role} &nbsp;|&nbsp; <b>Report Date:</b> {today}</p>

<h2>📊 Executive Summary</h2>
<div class="summary-box">
    <div style='display:flex;justify-content:space-around;flex-wrap:wrap;margin-bottom:1rem'>
        <div class="metric">
            <b style='color:{readiness_color}'>{readiness}%</b>
            <span>Role Readiness</span>
        </div>
        <div class="metric">
            <b>{len(gaps)}</b>
            <span>Total Skills</span>
        </div>
        <div class="metric">
            <b style='color:#4ecdc4'>{len(strengths)}</b>
            <span>At/Above Target</span>
        </div>
        <div class="metric">
            <b style='color:#ff6b6b'>{total_gaps}</b>
            <span>Skills to Develop</span>
        </div>
    </div>
    <div class="info-box">
        <p style='margin:0;font-size:1.05rem'><b>Assessment:</b> {readiness_msg}</p>
        <p style='margin:0.5rem 0 0 0;color:#999'>Average skill gap: {avg_gap} levels | Critical priorities: {len(critical_gaps)} skills</p>
    </div>
</div>

<h2>� Visual Analysis</h2>
<div style='display:flex;flex-wrap:wrap;gap:2rem;justify-content:space-around;margin:2rem 0'>
    <div style='flex:1;min-width:300px'>
        <h3 style='text-align:center;color:#90a0f0'>🕸️ Radar Chart: Your Skills vs Required</h3>
        {radar_chart_img}
    </div>
    <div style='flex:1;min-width:300px'>
        <h3 style='text-align:center;color:#90a0f0'>📊 Gap Analysis Bar Chart</h3>
        {gap_chart_img}
    </div>
</div>

<h2>�🔍 Detailed Skill Gap Analysis</h2>
<p style='color:#999;margin-bottom:1rem'>This table shows all required skills for the <b>{role}</b> role, your current level, and recommended actions to close each gap.</p>
<table>
    <tr>
        <th>Skill Name</th>
        <th style='text-align:center'>Your Level</th>
        <th style='text-align:center'>Required</th>
        <th style='text-align:center'>Gap</th>
        <th style='text-align:center'>Priority</th>
        <th>Recommended Action</th>
    </tr>
    {gap_rows}
</table>

<div class="info-box">
    <p style='margin:0;font-size:0.9rem'><b>Understanding Priority Levels:</b></p>
    <ul style='margin:0.5rem 0;padding-left:1.5rem;font-size:0.9rem'>
        <li><b>🔴 CRITICAL:</b> Essential skill with large gap — focus on this immediately</li>
        <li><b>🟡 HIGH:</b> Important skill that impacts job performance significantly</li>
        <li><b>🟢 MEDIUM:</b> Useful skill that can be developed after higher priorities</li>
    </ul>
</div>

<h2>💪 Your Strength Areas</h2>
<p style='color:#999;margin-bottom:1rem'>These are skills where you meet or exceed the required level. Leverage these strengths in your job applications and interviews!</p>
{strength_list}

<h2>🗺️ Personalized Learning Path</h2>
<p style='color:#999;margin-bottom:1rem'>Focus on these top priority skills in order. Each skill includes specific recommendations and estimated learning timeframes.</p>
{learning_recommendations}

<h2>✅ Actionable Next Steps for {name}</h2>
<p style='color:#999;margin-bottom:1rem'>Personalized action plan based on your {readiness}% readiness for the {role} role:</p>
<div style='background:#1e2130;padding:1.5rem;border-radius:10px;margin:1rem 0'>
    <ol style='padding-left:1.5rem;line-height:2.2'>
{next_steps_content}
    </ol>
</div>

<h2>📚 Recommended Resources</h2>
<div class="info-box">
    <ul style='padding-left:1.5rem'>
        <li><b>Online Learning:</b> Coursera, Udemy, Pluralsight, LinkedIn Learning</li>
        <li><b>Practice Platforms:</b> LeetCode, HackerRank, CodeWars, Exercism</li>
        <li><b>Documentation:</b> Official docs for your target technologies and frameworks</li>
        <li><b>Community:</b> GitHub, Stack Overflow, Reddit communities for your field</li>
        <li><b>Mentorship:</b> Connect with professionals in your target role via LinkedIn or local meetups</li>
    </ul>
</div>

<div style='margin-top:3rem;padding-top:1.5rem;border-top:1px solid #333;text-align:center'>
    <p style='color:#777;font-size:0.85rem'>Generated by <b>{APP_NAME}</b> • {today}</p>
    <p style='color:#666;font-size:0.8rem'>This report is based on your self-assessment and the requirements for {role}.<br>
    Validate your skills through quizzes and real-world projects for the most accurate career planning.</p>
</div>
</body></html>"""

    st.subheader("📋 Report Overview")
    
    # Summary cards before preview
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Readiness Score", f"{readiness}%", 
                delta="Ready" if readiness >= 80 else "In Progress",
                delta_color="normal" if readiness >= 80 else "off")
    col2.metric("✅ Strengths", len(strengths))
    col3.metric("🎯 Skills to Develop", total_gaps)
    col4.metric("🔴 Critical Gaps", len(critical_gaps))
    
    st.info(f"💡 **Assessment:** {readiness_msg}")
    
    # Show top 3 priorities
    if critical_gaps:
        with st.expander("🔍 Top Priority Skills to Focus On", expanded=True):
            for idx, skill in enumerate(critical_gaps[:3], 1):
                gap_info = gaps[skill]
                st.write(f"**{idx}. {skill}** — Gap: {round(gap_info['gap'], 1)} levels | Priority Score: {round(gap_info['priority_score'], 1)}")
    
    st.markdown("---")
    st.subheader("📄 Full Report Preview")
    st.caption("Scroll through the preview below or download as PDF/HTML for offline viewing")
    st.components.v1.html(html_report, height=700, scrolling=True)

    st.markdown("---")
    st.subheader("⬇️ Download Your Report")
    st.write("Save this comprehensive report to share with mentors, track your progress, or use in job applications.")
    
    col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 1])
    
    # Generate PDF if xhtml2pdf is available
    pdf_data = None
    if PDF_AVAILABLE:
        try:
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_report, dest=pdf_buffer)
            if not pisa_status.err:
                pdf_data = pdf_buffer.getvalue()
            pdf_buffer.close()
        except Exception as e:
            st.warning(f"PDF generation failed: {str(e)[:50]}...")
    
    # Download buttons
    with col_dl1:
        if pdf_data:
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name=f"skillforge_report_{role.replace(' ', '_').lower()}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Downloads a professional PDF report",
                use_container_width=True
            )
        else:
            st.info("⚠️ PDF generation unavailable")
    
    with col_dl2:
        st.download_button(
            label="📄 Download HTML Report",
            data=html_report,
            file_name=f"skillforge_report_{role.replace(' ', '_').lower()}_{datetime.date.today().strftime('%Y%m%d')}.html",
            mime="text/html",
            help="Downloads an HTML file you can open in any browser",
            use_container_width=True
        )
    
    with col_dl3:
        if pdf_data:
            st.success(f"PDF: {len(pdf_data) // 1024}KB")
        else:
            st.info(f"HTML: {len(html_report) // 1024}KB")
    
    # Help note for PDF conversion
    if not pdf_data:
        st.caption("💡 **Tip:** Download the HTML file, open it in your browser, and use 'Print to PDF' (Ctrl+P → Save as PDF)")



# ──────────────────────────────────────────────
#  Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#888;font-size:0.85rem'>"
    f"Built with ❤️ using Streamlit • {APP_NAME} © {datetime.date.today().year}"
    f"</div>",
    unsafe_allow_html=True,
)
