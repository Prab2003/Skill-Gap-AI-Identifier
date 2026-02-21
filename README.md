# Skill-Gap-Identifier

An AI-powered career skill gap analyzer that helps users identify their strengths, weaknesses, and provides personalized learning roadmaps.

## Features

- **Authentication System**: Local session-based access
- **Self-Assessment**: Evaluate your skills across multiple competencies
- **Adaptive Quiz**: Smart questioning system that adapts to your knowledge level
- **Gap Analysis**: Visual representation of skill gaps vs. target role requirements
- **Learning Roadmap**: Personalized learning paths with resource recommendations
- **Test Mode**: Real-time knowledge testing with AI-powered evaluation
- **Help Mode**: Voice coaching with transcript analysis
- **Export Reports**: Download comprehensive PDF reports with charts
- **AI Career Advisor**: Chat with AI for career guidance and interview prep

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.x
- **Storage**: In-session local state
- **AI/ML**: HuggingFace API, scikit-learn
- **Charts**: Plotly, Kaleido

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Prab2003/Skill-Gap-Identifier.git
cd Skill-Gap-Identifier
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

## Configuration

Create `.streamlit/secrets.toml`:
```toml
[huggingface]
api_key = "your-hf-api-key"  # Optional
```

## Usage

1. Click **Continue** on the access screen
2. Select your **target role** on the Dashboard
3. Complete the **Self-Assessment** to rate your current skills
4. Take the **Adaptive Quiz** for objective skill evaluation
5. Review your **Gap Analysis** and **Learning Roadmap**
6. Use **Test Mode** to practice with AI-evaluated questions
7. Get coaching via **Help Mode** with voice input
8. Export your progress as a **PDF Report**

## License

MIT License
