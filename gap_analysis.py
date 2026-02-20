import plotly.graph_objects as go


def calculate_skill_gaps(user_scores, role_requirements):
    """Calculate skill gaps with priority scoring"""
    gaps = {}

    for skill, required in role_requirements.items():
        current = round(user_scores.get(skill, 0), 1)
        gap = round(max(required - current, 0), 1)

        # Priority score: combines gap size and importance
        priority_score = gap * (required / 10) if required > 0 else 0
        
        gaps[skill] = {
            "current": current,
            "required": round(required, 1),
            "gap": gap,
            "priority_score": round(priority_score, 1),
            "status": "Strong ✓" if gap == 0 else f"Gap: {gap}"
        }

    # Sort by priority score (descending)
    sorted_gaps = dict(sorted(gaps.items(), key=lambda x: x[1]["priority_score"], reverse=True))
    return sorted_gaps

def identify_strength_areas(user_scores, role_requirements):
    """Identify areas where user meets or exceeds requirements"""
    strengths = {}
    for skill, required in role_requirements.items():
        current = round(user_scores.get(skill, 0), 1)
        if current >= required:
            strengths[skill] = {
                "current": current,
                "required": round(required, 1),
                "surplus": round(current - required, 1)
            }
    return strengths

def calculate_readiness_score(user_scores, role_requirements):
    """Calculate overall readiness as percentage (0-100)"""
    if not role_requirements:
        return 0
    
    total_required = sum(role_requirements.values())
    total_current = sum(min(user_scores.get(skill, 0), req) for skill, req in role_requirements.items())
    
    readiness = (total_current / total_required * 100) if total_required > 0 else 0
    return min(100, round(readiness, 1))


# ─────────────────────────────────────────────
#  Plotly visualisation helpers
# ─────────────────────────────────────────────

def create_radar_chart(user_scores: dict, role_requirements: dict) -> go.Figure:
    """Return a Plotly radar (spider) chart comparing current vs required."""
    skills = list(role_requirements.keys())
    required = [role_requirements[s] for s in skills]
    current  = [user_scores.get(s, 0) for s in skills]

    # Close the polygon
    skills_closed  = skills + [skills[0]]
    required_closed = required + [required[0]]
    current_closed  = current + [current[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=required_closed, theta=skills_closed, fill="toself",
        name="Required", line_color="#ff6b6b",
        fillcolor="rgba(255,107,107,0.10)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=current_closed, theta=skills_closed, fill="toself",
        name="Your Level", line_color="#4ecdc4",
        fillcolor="rgba(78,205,196,0.20)",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 10], showticklabels=True, tickfont_size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        margin=dict(l=60, r=60, t=30, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        height=420,
    )
    return fig


def create_gap_bar_chart(gaps: dict) -> go.Figure:
    """Horizontal bar chart: current vs required per skill."""
    skills_with_gap = [s for s, d in gaps.items() if d["gap"] > 0]
    if not skills_with_gap:
        skills_with_gap = list(gaps.keys())[:6]

    current_vals  = [gaps[s]["current"]  for s in skills_with_gap]
    required_vals = [gaps[s]["required"] for s in skills_with_gap]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=skills_with_gap, x=required_vals, name="Required",
        orientation="h", marker_color="rgba(255,107,107,0.6)",
    ))
    fig.add_trace(go.Bar(
        y=skills_with_gap, x=current_vals, name="Current",
        orientation="h", marker_color="rgba(78,205,196,0.8)",
    ))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(range=[0, 10], title="Level"),
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=max(250, len(skills_with_gap) * 50),
    )
    return fig
