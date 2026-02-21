# config.py - Application configuration and constants

APP_NAME = "SkillForge"
APP_ICON = "🚀"
APP_TAGLINE = "AI-Powered Skill Gap Identifier & Career Accelerator"

# Color palette
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "accent": "#f093fb",
    "success": "#4ecdc4",
    "warning": "#ffd93d",
    "danger": "#ff6b6b",
    "text": "#e0e0e0",
    "bg_card": "#1e2130",
}

# Skill keyword aliases — used by resume parser to detect proficiency
SKILL_ALIASES = {
    "Python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "scipy", "streamlit"],
    "JavaScript": ["javascript", "js", "typescript", "ts", "node.js", "nodejs", "express"],
    "React": ["react", "reactjs", "react.js", "next.js", "nextjs", "redux"],
    "SQL": ["sql", "mysql", "postgresql", "postgres", "sqlite", "oracle", "t-sql", "nosql", "mongodb"],
    "Machine Learning": ["machine learning", "ml", "scikit-learn", "sklearn", "xgboost", "random forest", "logistic regression"],
    "Deep Learning": ["deep learning", "neural network", "tensorflow", "pytorch", "keras", "cnn", "rnn", "lstm", "transformer"],
    "Statistics": ["statistics", "statistical", "hypothesis testing", "regression analysis", "probability", "bayesian", "a/b testing"],
    "Data Visualization": ["data visualization", "matplotlib", "seaborn", "plotly", "d3.js", "tableau", "power bi", "grafana"],
    "Git": ["git", "github", "gitlab", "version control", "bitbucket"],
    "Docker": ["docker", "containerization", "kubernetes", "k8s", "docker-compose"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda", "sagemaker"],
    "CSS": ["css", "sass", "scss", "tailwind", "bootstrap", "styled-components", "material ui"],
    "Testing": ["testing", "unit test", "pytest", "jest", "selenium", "cypress", "tdd", "bdd"],
    "System Design": ["system design", "architecture", "microservices", "distributed systems", "scalability", "load balancing"],
    "NLP": ["nlp", "natural language processing", "text mining", "sentiment analysis", "hugging face", "bert", "gpt", "llm"],
    "Computer Vision": ["computer vision", "opencv", "image processing", "object detection", "yolo", "image classification"],
    "APIs": ["api", "rest", "restful", "graphql", "grpc", "fastapi", "swagger", "openapi"],
    "Cloud Computing": ["cloud", "azure", "gcp", "google cloud", "cloud computing", "serverless"],
    "DevOps": ["devops", "ci/cd", "jenkins", "github actions", "terraform", "ansible"],
    "Agile": ["agile", "scrum", "kanban", "sprint", "jira", "project management"],
}

# Default HuggingFace model for chat / generation
DEFAULT_HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# Difficulty labels
DIFFICULTY_LABELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "expert": "Expert",
}
