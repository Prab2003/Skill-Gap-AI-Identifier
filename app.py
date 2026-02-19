import streamlit as st
import json, datetime
import re
import streamlit.components.v1 as components

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
from learning_roadmap import generate_learning_roadmap, generate_recommendation_summary, get_learning_path
from quiz_engine import generate_adaptive_quiz, score_quiz
from ml_models import skill_predictor, personalizer
from ai_engine import AIEngine
from resume_parser import extract_skills_from_text
from voice_assistant import VoiceAssistant
from supabase_client import supabase_enabled, load_user_state, save_user_state

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
#  Session state initialisation
# ──────────────────────────────────────────────
_defaults = {
    "user_scores": {},
    "quiz_mode": False,
    "quiz_responses": {},
    "quiz": [],
    "voice_assistant": None,
    "voice_enabled": False,
    "voice_output_enabled": True,
    "ai_engine": None,
    "hf_key": "",
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
    "cloud_loaded": False,
    "last_profile_key": "",
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

    # Voice toggle
    st.session_state.voice_enabled = st.checkbox("🎤 Voice Mode (experimental)")
    if st.session_state.voice_enabled:
        st.session_state.voice_output_enabled = st.checkbox("🔊 Voice Output + Subtitles", value=st.session_state.voice_output_enabled)

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


def _profile_key() -> str:
    """Stable, lowercase profile identifier for cloud sync."""
    return (st.session_state.profile_name or "").strip().lower()


def _render_subtitles(text: str):
    if not text:
        return
    subtitle_lines = st.session_state.voice_assistant.build_subtitles(text, words_per_line=9)
    if not subtitle_lines:
        return

    subtitle_html = "".join(f'<div class="subtitle-line">{line}</div>' for line in subtitle_lines)
    st.markdown("**Subtitles**")
    st.markdown(f'<div class="subtitle-panel">{subtitle_html}</div>', unsafe_allow_html=True)


def _speak_browser_tts(text: str, role: str = "assistant"):
    if not text or not st.session_state.voice_output_enabled:
        return

    rate = 1.0
    pitch = 1.0
    if role == "interviewer":
        rate = 0.95
        pitch = 0.95
    elif role == "candidate":
        rate = 1.05
        pitch = 1.05

    payload = json.dumps(text)
    components.html(
        f"""
        <script>
        const msg = {payload};
        if ('speechSynthesis' in window && msg) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(msg);
            utterance.rate = {rate};
            utterance.pitch = {pitch};
            utterance.volume = 1.0;
            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=0,
    )


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

    profile_key = _profile_key()
    if profile_key != st.session_state.last_profile_key:
        st.session_state.cloud_loaded = False
        st.session_state.last_profile_key = profile_key

    if supabase_enabled() and profile_key and not st.session_state.cloud_loaded:
        remote = load_user_state(profile_key)
        st.session_state.cloud_loaded = True
        if remote:
            st.session_state.user_scores.update(remote.get("user_scores", {}))
            st.session_state.resume_text = remote.get("resume_text", st.session_state.resume_text)
            st.session_state.resume_skills = remote.get("resume_skills", st.session_state.resume_skills)
            st.session_state.selected_role = remote.get("selected_role", st.session_state.selected_role)
            st.success("☁️ Loaded your profile from Supabase")

    if supabase_enabled() and profile_key:
        if st.button("☁️ Save to Supabase", key="btn_save_supabase"):
            payload = {
                "profile_name": st.session_state.profile_name,
                "selected_role": st.session_state.selected_role,
                "user_scores": st.session_state.user_scores,
                "resume_text": st.session_state.resume_text,
                "resume_skills": st.session_state.resume_skills,
            }
            if save_user_state(profile_key, payload):
                st.success("Saved to Supabase")
            else:
                st.error("Could not save to Supabase")

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
                min_value=0, max_value=10,
                value=st.session_state.user_scores.get(skill, 5),
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
            text=f"Answered {len(st.session_state.quiz_responses)}/{len(quiz)}",
        )

        for q in quiz:
            qid = q["id"]
            with st.container(border=True):
                st.markdown(f"**Q{qid+1}.** [{q['difficulty'].title()}] *{q['skill']}*")
                st.write(q["question"])
                chosen = st.radio(
                    "Select answer",
                    options=q["options"],
                    index=None,
                    key=f"quiz_opt_{qid}",
                )
                if chosen is not None:
                    st.session_state.quiz_responses[qid] = q["options"].index(chosen)

        col_sub, col_cancel = st.columns(2)
        with col_sub:
            if st.button("✅ Submit Quiz", type="primary"):
                if len(st.session_state.quiz_responses) < len(quiz):
                    st.error("Please answer all questions before submitting.")
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
                        st.caption(f"Current {d['current']} → Target {d['required']}  |  Gap: {d['gap']}")
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
            for skill, d in strengths.items():
                st.write(f"✅ **{skill}** — level {d['current']} (exceeds target by **+{d['surplus']}**)")
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

    if roadmap["weeks"]:
        for week in roadmap["weeks"]:
            with st.expander(f"**Week {week['week']}**", expanded=(week["week"] == 1)):
                for f in week["focus_areas"]:
                    st.write(f"**{f['skill']}** {f['priority']}  |  Level {f['current_level']} → {f['target_level']}  |  {f['difficulty']}")
                st.write("**Daily targets:**")
                for t in week["daily_targets"]:
                    st.write(f"  • {t}")
    else:
        st.success("🎉 All target skills achieved!")

    # Resources
    st.markdown("---")
    st.subheader("📚 Recommended Resources")
    priority_skills = [s for s in gaps if gaps[s]["gap"] > 0]
    for rank, skill in enumerate(priority_skills[:5], 1):
        with st.expander(f"{rank}. {skill} (priority {gaps[skill]['priority_score']})"):
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
    weekly_hours = st.slider("Hours you can study per week", 5, 40, 15)

    predictions = []
    for skill, d in gaps.items():
        if d["gap"] > 0:
            weeks_needed = skill_predictor.predict_weeks_to_target(d["current"], d["required"], weekly_hours)
            predictions.append({"skill": skill, "current": d["current"], "target": d["required"],
                                "weeks": weeks_needed, "priority": d["priority_score"]})
    predictions.sort(key=lambda x: x["priority"], reverse=True)

    for p in predictions:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**{p['skill']}**")
            c2.write(f"Level {p['current']} → {p['target']}")
            c3.write(f"⏱️ {p['weeks']:.1f} weeks")
            if p["weeks"] <= 4:
                c4.success("Quick")
            elif p["weeks"] <= 8:
                c4.warning("Medium")
            else:
                c4.error("Long")

    # Optimal order
    st.markdown("---")
    st.subheader("🎯 Optimal Skill Learning Order")
    order = personalizer.get_optimal_skill_order(gaps, reqs)
    for rank, skill in enumerate(order, 1):
        if gaps.get(skill, {}).get("gap", 0) > 0:
            st.write(f"**{rank}.** {skill} (priority {gaps[skill]['priority_score']:.1f})")

    # ---- AI Chat ----
    st.markdown("---")
    st.subheader("💬 AI Career Advisor")
    st.caption("Ask anything about skill development, career paths, or interview prep.")

    ai: AIEngine = st.session_state.ai_engine

    if st.session_state.voice_enabled:
        st.markdown("---")
        st.subheader("🎙️ Voice Interview Assistant")
        st.caption("Choose a mode: interviewer asks questions, or coach mode helps you improve answers.")

        mode = st.radio(
            "Voice Mode",
            ["Question Asking Mode", "Help Mode"],
            horizontal=True,
            key="voice_mode_selector",
        )

        va = st.session_state.voice_assistant
        top_gaps = [skill for skill in gaps if gaps[skill]["gap"] > 0][:3]
        top_gaps_text = ", ".join(top_gaps) if top_gaps else "general interview readiness"

        if mode == "Question Asking Mode":
            st.caption("Run a realistic multi-round interview: AI interviewer asks, you answer by voice, then receive round-by-round evaluation and final verdict.")

            cfg1, cfg2, cfg3 = st.columns([1.4, 1, 1])
            with cfg1:
                interview_domain = st.selectbox("Interview Type", ["Mixed", "Technical", "Behavioral", "Problem Solving"], index=0)
            with cfg2:
                rounds = st.slider("Rounds", 2, 5, st.session_state.interview_rounds)
            with cfg3:
                if st.session_state.interview_active:
                    st.success("Live Interview")
                else:
                    st.info("Not Started")

            st.session_state.interview_rounds = rounds

            b1, b2 = st.columns(2)
            with b1:
                if st.button("🎬 Start Mock Interview", key="start_interview_btn", type="primary"):
                    st.session_state.interview_active = True
                    st.session_state.interview_current_round = 0
                    st.session_state.interview_questions = []
                    st.session_state.interview_feedback = []
                    st.session_state.interview_scores = []
                    st.session_state.interview_summary = ""
                    st.session_state.interview_domain = interview_domain
                    st.session_state.interview_qa = []

                    portfolio_ctx = _portfolio_context()

                    first_q_prompt = (
                        f"You are an experienced interviewer for role {st.session_state.selected_role}. "
                        f"Interview type is {interview_domain}. "
                        f"Use this candidate portfolio context: {portfolio_ctx}. "
                        f"Ask round 1 of {rounds}. Focus on these gaps: {top_gaps_text}. "
                        "Ask a question that references the candidate's portfolio/project experience when possible. "
                        "Return ONLY one concise interviewer question."
                    )
                    first_question = ai.chat(first_q_prompt)
                    st.session_state.current_interview_question = first_question
                    st.session_state.interview_questions.append(first_question)

                    intro = f"Welcome to your mock interview for {st.session_state.selected_role}. Let's begin. {first_question}"
                    _render_subtitles(intro)
                    _speak_browser_tts(intro, role="interviewer")

            with b2:
                if st.button("🛑 End Interview", key="end_interview_btn"):
                    st.session_state.interview_active = False
                    st.session_state.current_interview_question = ""

            if st.session_state.interview_active and st.session_state.current_interview_question:
                round_no = st.session_state.interview_current_round + 1
                st.progress(round_no / st.session_state.interview_rounds, text=f"Round {round_no} of {st.session_state.interview_rounds}")
                st.markdown(f"**Interviewer (Round {round_no}):** {st.session_state.current_interview_question}")

                answer_audio = st.audio_input(f"Record your answer for Round {round_no}", key=f"voice_answer_audio_round_{round_no}")
                if answer_audio is not None:
                    answer_bytes = answer_audio.getvalue()
                    st.audio(answer_bytes, format="audio/wav")

                    if st.button(f"✅ Submit Answer (Round {round_no})", key=f"evaluate_voice_answer_btn_round_{round_no}"):
                        transcript = va.transcribe_audio_bytes(answer_bytes)

                        if not transcript:
                            st.error("Could not transcribe your answer. Please retry in a quieter environment.")
                        else:
                            analysis = va.analyze_transcript(transcript)
                            st.session_state.last_voice_transcript = transcript
                            st.session_state.last_voice_analysis = analysis
                            st.session_state.interview_qa.append({
                                "round": round_no,
                                "question": st.session_state.current_interview_question,
                                "answer": transcript,
                            })

                            st.markdown(f"**Your Answer Transcript:** {transcript}")
                            user_echo = f"Candidate response recorded. You said: {transcript}"
                            _render_subtitles(user_echo)
                            _speak_browser_tts(user_echo, role="candidate")
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("Words", analysis.get("word_count", 0))
                            c2.metric("Confidence", analysis.get("confidence", "Low"))
                            c3.metric("Sentiment", analysis.get("sentiment", "Neutral"))
                            c4.metric("Complexity", analysis.get("complexity", "Low"))

                            interviewer_prompt = (
                                f"Act as a strict but fair interviewer for role {st.session_state.selected_role}. "
                                f"Interview type: {st.session_state.interview_domain}. "
                                f"Question asked: {st.session_state.current_interview_question}. "
                                f"Candidate spoken answer transcript: {transcript}. "
                                "Return this exact structure: "
                                "Impression: <1 sentence>\n"
                                "Score: X/10\n"
                                "Strong points:\n- ...\n- ...\n"
                                "Improvements:\n- ...\n- ...\n"
                                "Better sample answer:\n<3-4 lines>"
                            )

                            with st.spinner("Interviewer is evaluating your answer…"):
                                interviewer_reply = ai.chat(interviewer_prompt)

                            score = _extract_interview_score(interviewer_reply)
                            st.session_state.interview_feedback.append(interviewer_reply)
                            st.session_state.interview_scores.append(score)
                            st.session_state.last_voice_reply = interviewer_reply

                            st.session_state.chat_history.append({"role": "user", "content": f"🎤 Interview answer (R{round_no}): {transcript}"})
                            st.session_state.chat_history.append({"role": "assistant", "content": interviewer_reply})

                            st.markdown("**Interviewer Feedback**")
                            st.markdown(interviewer_reply)
                            _render_subtitles(interviewer_reply)
                            _speak_browser_tts(interviewer_reply, role="interviewer")

                            is_last_round = round_no >= st.session_state.interview_rounds
                            if not is_last_round:
                                asked_questions = " | ".join(st.session_state.interview_questions)
                                qa_history = " | ".join(
                                    [f"Q{qa['round']}: {qa['question']} A: {qa['answer']}" for qa in st.session_state.interview_qa]
                                )
                                portfolio_ctx = _portfolio_context()
                                next_round = round_no + 1
                                next_q_prompt = (
                                    f"You are interviewing for role {st.session_state.selected_role}. "
                                    f"Interview type: {st.session_state.interview_domain}. "
                                    f"Candidate portfolio context: {portfolio_ctx}. "
                                    f"Previous Q&A history: {qa_history}. "
                                    f"Ask round {next_round} of {st.session_state.interview_rounds}. "
                                    f"Avoid repeating these questions: {asked_questions}. "
                                    f"Focus on gaps: {top_gaps_text}. "
                                    "Make it continuous from candidate's previous answer (follow-up when relevant). "
                                    "Return only one concise question."
                                )
                                next_question = ai.chat(next_q_prompt)
                                st.session_state.current_interview_question = next_question
                                st.session_state.interview_questions.append(next_question)
                                st.session_state.interview_current_round += 1
                                st.success("Round completed. Next question is ready.")
                                _render_subtitles(next_question)
                                _speak_browser_tts(next_question, role="interviewer")
                            else:
                                avg_score = round(sum(st.session_state.interview_scores) / max(len(st.session_state.interview_scores), 1), 2)
                                final_prompt = (
                                    f"You are an interview panel summarizing a mock interview for role {st.session_state.selected_role}. "
                                    f"Round scores: {st.session_state.interview_scores}. Average score: {avg_score}/10. "
                                    f"Round feedback notes: {' || '.join(st.session_state.interview_feedback)}. "
                                    "Provide final result in this format: "
                                    "Overall Verdict: Hire / Borderline / No-Hire\n"
                                    "Panel Summary (3 bullets)\n"
                                    "Top 3 action items before next interview."
                                )
                                with st.spinner("Interview panel is deciding…"):
                                    final_summary = ai.chat(final_prompt)

                                st.session_state.interview_summary = final_summary
                                st.session_state.interview_active = False
                                st.session_state.current_interview_question = ""

                                st.markdown("### 🧾 Final Interview Result")
                                st.metric("Average Score", f"{avg_score}/10")
                                st.markdown(final_summary)
                                _render_subtitles(final_summary)
                                _speak_browser_tts(final_summary, role="interviewer")

            elif st.session_state.interview_summary:
                avg_score = round(sum(st.session_state.interview_scores) / max(len(st.session_state.interview_scores), 1), 2)
                st.markdown("### 🧾 Last Interview Result")
                st.metric("Average Score", f"{avg_score}/10")
                st.markdown(st.session_state.interview_summary)

        else:
            st.caption("Help mode: tell your problem by voice and receive spoken coaching guidance.")

            help_audio = st.audio_input("Record what you need help with", key="voice_help_audio")
            if help_audio is not None:
                help_bytes = help_audio.getvalue()
                st.audio(help_bytes, format="audio/wav")

                if st.button("🆘 Get Voice Coaching Help", key="voice_help_btn", type="primary"):
                    transcript = va.transcribe_audio_bytes(help_bytes)

                    if not transcript:
                        st.error("Could not transcribe your voice message. Please retry.")
                    else:
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

                        st.session_state.last_voice_reply = help_reply
                        st.session_state.chat_history.append({"role": "user", "content": f"🎤 Help request: {transcript}"})
                        st.session_state.chat_history.append({"role": "assistant", "content": help_reply})

                        st.markdown("**Coach Response**")
                        st.markdown(help_reply)
                        _render_subtitles(help_reply)
                        _speak_browser_tts(help_reply, role="interviewer")

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

            if st.session_state.voice_enabled and st.session_state.voice_output_enabled:
                _render_subtitles(reply)
                _speak_browser_tts(reply, role="interviewer")

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
    gap_rows = ""
    for s, d in gaps.items():
        color = "#ff6b6b" if d["gap"] > 3 else "#ffd93d" if d["gap"] > 0 else "#4ecdc4"
        gap_rows += (
            f"<tr><td>{s}</td><td>{d['current']}</td><td>{d['required']}</td>"
            f"<td style='color:{color};font-weight:700'>{d['gap']}</td>"
            f"<td>{d['priority_score']}</td></tr>\n"
        )

    strength_list = "".join(f"<li><b>{s}</b> — level {d['current']} (+{d['surplus']} above target)</li>" for s, d in strengths.items()) or "<li>None yet</li>"

    html_report = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:'Inter',Helvetica,Arial,sans-serif;color:#e8e8e8;background:#0e1117;max-width:800px;margin:auto;padding:2rem}}
h1{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:1.2rem 1.6rem;border-radius:12px}}
h2{{color:#90a0f0;border-bottom:2px solid #667eea;padding-bottom:4px}}
p,li,td{{color:#d0d0d0}}
b{{color:#f0f0f0}}
table{{width:100%;border-collapse:collapse;margin:1rem 0}}
th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid #333}}
th{{background:#667eea;color:#fff}}
.metric{{display:inline-block;background:#1e2130;border:1px solid rgba(102,126,234,0.3);border-radius:10px;padding:1rem 2rem;margin:0.5rem;text-align:center}}
.metric b{{font-size:1.8rem;color:#90a0f0}}
</style></head><body>
<h1>🚀 {APP_NAME} — Skill Gap Report</h1>
<p><b>Name:</b> {name} &nbsp;|&nbsp; <b>Target Role:</b> {role} &nbsp;|&nbsp; <b>Date:</b> {today}</p>

<div>
<span class="metric"><b>{readiness}%</b><br>Role Readiness</span>
<span class="metric"><b>{len(strengths)}</b><br>At Target</span>
<span class="metric"><b>{len([g for g in gaps.values() if g['gap']>0])}</b><br>Gaps</span>
</div>

<h2>Skill Gap Details</h2>
<table><tr><th>Skill</th><th>Current</th><th>Required</th><th>Gap</th><th>Priority</th></tr>
{gap_rows}</table>

<h2>Strength Areas</h2>
<ul>{strength_list}</ul>

<h2>Next Steps</h2>
<ol>
<li>Focus on the highest-priority gaps listed above.</li>
<li>Take the adaptive quiz to validate your levels.</li>
<li>Follow the personalized learning roadmap in the app.</li>
</ol>
<p style="color:#777;margin-top:2rem;font-size:0.85rem">Generated by {APP_NAME} • {today}</p>
</body></html>"""

    st.subheader("Preview")
    st.components.v1.html(html_report, height=700, scrolling=True)

    st.download_button(
        label="⬇️ Download HTML Report",
        data=html_report,
        file_name=f"skillforge_report_{role.replace(' ', '_').lower()}.html",
        mime="text/html",
    )

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
