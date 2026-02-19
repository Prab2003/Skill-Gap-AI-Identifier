# ui_components.py - Custom Streamlit CSS and reusable UI helpers

import streamlit as st


def inject_custom_css():
    """Inject production-quality CSS into the Streamlit app."""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ---- gradient header ---- */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.6rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.35);
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.2rem; font-weight: 800; }
    .main-header p  { color: rgba(255,255,255,0.85); margin: 0.4rem 0 0; font-size: 1.05rem; }

    /* ---- metrics ---- */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ---- progress bar ---- */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        border-radius: 10px;
    }

    /* ---- sidebar ---- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #ddd !important;
    }

    /* ---- cards ---- */
    .skill-card {
        background: linear-gradient(145deg, #1e2130, #262940);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .skill-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
    }

    /* ---- badges ---- */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-danger  { background: rgba(255,107,107,0.15); color: #ff6b6b; }
    .badge-warning { background: rgba(255,217,61,0.15);  color: #ffd93d; }
    .badge-success { background: rgba(78,205,196,0.15);  color: #4ecdc4; }
    .badge-info    { background: rgba(102,126,234,0.15);  color: #667eea; }

    /* ---- chat bubbles ---- */
    .chat-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; padding: 0.75rem 1.1rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0.5rem 0; max-width: 80%; margin-left: auto;
    }
    .chat-ai {
        background: #1e2130; color: #e0e0e0;
        padding: 0.75rem 1.1rem;
        border-radius: 16px 16px 16px 4px;
        margin: 0.5rem 0; max-width: 80%;
        border: 1px solid rgba(102,126,234,0.2);
    }

    /* ---- hide default streamlit chrome for demo ---- */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }

    /* ---- download button ---- */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important; border: none !important;
        border-radius: 10px; padding: 0.6rem 2rem;
        font-weight: 600;
    }

    /* ---- expander ---- */
    details[data-testid="stExpander"] summary {
        font-weight: 600;
    }

    /* ---- tab highlight ---- */
    .stTabs [aria-selected="true"] {
        background-color: rgba(102,126,234,0.15) !important;
        border-radius: 8px 8px 0 0;
    }

    /* ---- subtitle panel ---- */
    .subtitle-panel {
        background: rgba(14, 17, 23, 0.92);
        border: 1px solid rgba(144, 160, 240, 0.45);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-top: 0.7rem;
    }
    .subtitle-line {
        color: #eef2ff;
        font-size: 1rem;
        line-height: 1.55;
        margin: 0.22rem 0;
    }

    /* ---- responsive tweaks ---- */
    @media (max-width: 1024px) {
        .main-header { padding: 1.2rem 1.3rem; }
        .main-header h1 { font-size: 1.8rem; }
        [data-testid="stMetricValue"] { font-size: 1.75rem; }
        .skill-card { padding: 1rem; }
    }

    @media (max-width: 768px) {
        .main-header { border-radius: 12px; margin-bottom: 1rem; }
        .main-header h1 { font-size: 1.5rem; }
        .main-header p { font-size: 0.95rem; }
        .subtitle-line { font-size: 0.95rem; }
        .stDownloadButton > button { width: 100%; }
    }

    @media (max-width: 480px) {
        .main-header { padding: 1rem; }
        .main-header h1 { font-size: 1.3rem; }
        [data-testid="stMetricValue"] { font-size: 1.45rem; }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str = ""):
    """Render the gradient hero header."""
    st.markdown(
        f"""<div class="main-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>""",
        unsafe_allow_html=True,
    )


def render_skill_badge(level: int) -> str:
    """Return an HTML badge string for a skill level."""
    if level <= 3:
        return f'<span class="badge badge-danger">Beginner ({level}/10)</span>'
    elif level <= 6:
        return f'<span class="badge badge-warning">Intermediate ({level}/10)</span>'
    else:
        return f'<span class="badge badge-success">Advanced ({level}/10)</span>'


def level_emoji(score: int) -> str:
    if score == 0:
        return "❌ No exp."
    elif score <= 3:
        return "🔴 Beginner"
    elif score <= 6:
        return "🟡 Intermediate"
    else:
        return "🟢 Advanced"
