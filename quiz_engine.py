# quiz_engine.py  –  Adaptive MCQ quiz engine with real answer evaluation

import random
from typing import List, Dict, Optional, Tuple

# ──────────────────────────────────────────────────────────────
#  Question bank — real multiple-choice questions per skill & difficulty
# ──────────────────────────────────────────────────────────────

QUESTION_BANK: Dict[str, Dict[str, List[dict]]] = {
    # ---- Python ----
    "Python": {
        "beginner": [
            {"q": "What is the output of print(type([]))?",
             "opts": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"], "ans": 0},
            {"q": "Which keyword defines a function in Python?",
             "opts": ["func", "define", "def", "function"], "ans": 2},
            {"q": "What does len('Hello') return?",
             "opts": ["4", "5", "6", "Error"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is a list comprehension used for?",
             "opts": ["Sorting a list", "Creating a list from an iterable in one line",
                      "Compressing a list into bytes", "Deleting list elements"], "ans": 1},
            {"q": "What does the 'yield' keyword do?",
             "opts": ["Stops the function permanently",
                      "Returns a value and pauses the generator",
                      "Raises an exception", "Creates a new thread"], "ans": 1},
            {"q": "Tuples differ from lists because tuples are…",
             "opts": ["Mutable", "Immutable", "Unordered", "Only for numbers"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is a decorator in Python?",
             "opts": ["A CSS styling tool",
                      "A function that wraps another function to extend its behavior",
                      "A type of variable", "A loop construct"], "ans": 1},
            {"q": "What is the GIL?",
             "opts": ["Global Import Library", "General Interface Layer",
                      "Global Interpreter Lock — limits true multi-threading",
                      "Graphical Interaction Loop"], "ans": 2},
        ],
        "expert": [
            {"q": "What is a metaclass in Python?",
             "opts": ["A class that creates classes", "A subclass of object",
                      "A type of decorator", "A module system"], "ans": 0},
        ],
    },
    # ---- JavaScript ----
    "JavaScript": {
        "beginner": [
            {"q": "Which company developed JavaScript?", "opts": ["Microsoft", "Netscape", "Google", "Apple"], "ans": 1},
            {"q": "How do you declare a variable that cannot be reassigned?",
             "opts": ["var x", "let x", "const x", "static x"], "ans": 2},
        ],
        "intermediate": [
            {"q": "What does '===' check?", "opts": ["Value only", "Type only", "Value and type", "Reference"], "ans": 2},
            {"q": "What is a closure?",
             "opts": ["A function with access to its outer scope variables",
                      "A terminated process", "A CSS animation", "A data type"], "ans": 0},
        ],
        "advanced": [
            {"q": "What is the event loop in JavaScript?",
             "opts": ["A for-loop variant", "Mechanism that handles async callbacks on a single thread",
                      "A DOM event handler", "A CSS animation loop"], "ans": 1},
        ],
        "expert": [
            {"q": "What is the Temporal Dead Zone (TDZ)?",
             "opts": ["Region where let/const is declared but not yet initialised",
                      "A memory leak area", "A deprecated API zone", "A testing timeout"], "ans": 0},
        ],
    },
    # ---- SQL ----
    "SQL": {
        "beginner": [
            {"q": "Which SQL clause filters rows?", "opts": ["SELECT", "WHERE", "ORDER BY", "GROUP BY"], "ans": 1},
            {"q": "What does SELECT DISTINCT do?",
             "opts": ["Selects all rows", "Removes duplicate rows", "Sorts results", "Limits output"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is the difference between INNER JOIN and LEFT JOIN?",
             "opts": ["No difference", "LEFT JOIN includes unmatched left-table rows",
                      "INNER JOIN includes NULLs", "LEFT JOIN is faster"], "ans": 1},
            {"q": "What does GROUP BY do?",
             "opts": ["Sorts data", "Groups rows sharing a value for aggregate functions",
                      "Filters groups", "Joins tables"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is a window function?",
             "opts": ["Performs calculation across a set of rows related to the current row",
                      "Opens a new database window", "A GUI element", "A type of index"], "ans": 0},
        ],
        "expert": [
            {"q": "What is a CTE (Common Table Expression)?",
             "opts": ["A permanent table", "A temporary named result set scoped to a single query",
                      "A stored procedure", "A view"], "ans": 1},
        ],
    },
    # ---- Machine Learning ----
    "Machine Learning": {
        "beginner": [
            {"q": "What is supervised learning?",
             "opts": ["Learning without labels", "Learning with labelled data",
                      "Reinforcement learning", "Unsupervised clustering"], "ans": 1},
            {"q": "What is overfitting?",
             "opts": ["Model learns noise and performs poorly on new data",
                      "Model is too simple", "Training takes too long", "Data is missing"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is cross-validation?",
             "opts": ["Training on all data", "Splitting data into folds to validate model performance",
                      "Testing in production", "Data augmentation"], "ans": 1},
            {"q": "What does regularisation do?",
             "opts": ["Speeds training", "Prevents overfitting by penalising large coefficients",
                      "Increases model complexity", "Normalises data"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is gradient descent?",
             "opts": ["A data structure", "Iterative optimisation to minimise a loss function",
                      "A neural network layer", "A feature selection method"], "ans": 1},
        ],
        "expert": [
            {"q": "What is the bias-variance tradeoff?",
             "opts": ["Balancing model complexity: low bias ↔ high variance",
                      "Balancing dataset size", "Choosing learning rate",
                      "Selecting features"], "ans": 0},
        ],
    },
    # ---- Statistics ----
    "Statistics": {
        "beginner": [
            {"q": "What is the mean of [2, 4, 6]?", "opts": ["2", "4", "6", "12"], "ans": 1},
            {"q": "What does standard deviation measure?",
             "opts": ["Central tendency", "Spread of data", "Skewness", "Kurtosis"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is a p-value?",
             "opts": ["Probability of observing results at least as extreme, assuming H0 is true",
                      "The population mean", "A data point", "A coefficient"], "ans": 0},
        ],
        "advanced": [
            {"q": "What is Bayes' theorem used for?",
             "opts": ["Calculating posterior probability from prior and likelihood",
                      "Sorting data", "Feature scaling", "Dimensionality reduction"], "ans": 0},
        ],
        "expert": [
            {"q": "When is a bootstrap method preferred over parametric tests?",
             "opts": ["When distribution assumptions are hard to verify",
                      "When data is normally distributed", "When sample size is large",
                      "Always"], "ans": 0},
        ],
    },
    # ---- React ----
    "React": {
        "beginner": [
            {"q": "What is JSX?", "opts": ["A database", "JavaScript XML — syntax extension for React",
                                           "A CSS framework", "A REST API"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What does useState return?",
             "opts": ["A boolean", "An array with [state, setter]", "A promise", "A DOM node"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is React.memo used for?",
             "opts": ["State management", "Memoising a component to prevent unnecessary re-renders",
                      "Routing", "Server-side rendering"], "ans": 1},
        ],
        "expert": [
            {"q": "What problem does React Server Components solve?",
             "opts": ["Reduces client bundle size by rendering on the server",
                      "Replaces Redux", "Improves CSS", "Handles authentication"], "ans": 0},
        ],
    },
    # ---- Deep Learning ----
    "Deep Learning": {
        "beginner": [
            {"q": "What is a neural network?",
             "opts": ["A computer network", "A model inspired by the human brain with layers of nodes",
                      "A graph database", "A sorting algorithm"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is backpropagation?",
             "opts": ["Forward data flow", "Algorithm to compute gradients for weight updates",
                      "A data augmentation technique", "A regularisation method"], "ans": 1},
        ],
        "advanced": [
            {"q": "What problem do LSTMs solve that vanilla RNNs struggle with?",
             "opts": ["Over-parameterisation", "Long-range dependency / vanishing gradient",
                      "Data preprocessing", "Batch normalisation"], "ans": 1},
        ],
        "expert": [
            {"q": "What is the key innovation of the Transformer architecture?",
             "opts": ["Self-attention mechanism replacing recurrence",
                      "Convolutional layers", "Skip connections only", "Pooling layers"], "ans": 0},
        ],
    },
    # ---- Docker ----
    "Docker": {
        "beginner": [
            {"q": "What is a Docker container?",
             "opts": ["A virtual machine", "A lightweight, isolated runtime environment",
                      "A programming language", "A database"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is a Dockerfile?",
             "opts": ["A running container", "A script with instructions to build a Docker image",
                      "A YAML config file", "A network bridge"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is Docker Compose used for?",
             "opts": ["Writing Dockerfiles", "Defining and running multi-container applications",
                      "Container security scanning", "Image compression"], "ans": 1},
        ],
        "expert": [
            {"q": "What is a multi-stage build?",
             "opts": ["Using multiple FROM statements to reduce final image size",
                      "Running containers in stages", "A CI pipeline", "A swarm mode feature"], "ans": 0},
        ],
    },
    # ---- Git ----
    "Git": {
        "beginner": [
            {"q": "What does 'git commit' do?",
             "opts": ["Uploads code to GitHub", "Saves staged changes to the local repository",
                      "Deletes a branch", "Merges branches"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is 'git rebase' used for?",
             "opts": ["Deleting commits", "Re-applying commits on top of another base tip",
                      "Creating a tag", "Initialising a repo"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is a Git hook?",
             "opts": ["A branch naming convention",
                      "A script triggered by Git events like commit or push",
                      "A merge strategy", "A remote alias"], "ans": 1},
        ],
    },
    # ---- Testing ----
    "Testing": {
        "beginner": [
            {"q": "What is a unit test?",
             "opts": ["Testing the full app", "Testing a single function or component in isolation",
                      "Performance testing", "Security testing"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is mocking?",
             "opts": ["Removing tests", "Replacing real objects with simulated ones for testing",
                      "Writing documentation", "Code formatting"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is TDD (Test-Driven Development)?",
             "opts": ["Writing tests after code", "Writing tests before code, then making them pass",
                      "A debugging tool", "A deployment strategy"], "ans": 1},
        ],
    },
    # ---- CSS ----
    "CSS": {
        "beginner": [
            {"q": "What does CSS stand for?",
             "opts": ["Cascading Style Sheets", "Computer Style Sheets",
                      "Creative Style Syntax", "Coded Style Sheets"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is Flexbox?",
             "opts": ["A JavaScript library", "A CSS layout model for arranging items in one dimension",
                      "A grid framework", "A font system"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is CSS specificity?",
             "opts": ["How fast CSS loads", "Rules determining which styles override others based on selectors",
                      "A responsiveness metric", "A colour model"], "ans": 1},
        ],
    },
    # ---- APIs ----
    "APIs": {
        "beginner": [
            {"q": "What does REST stand for?",
             "opts": ["Representational State Transfer", "Remote Execution Standard Technology",
                      "Real-time Event Streaming", "Resource Exchange Protocol"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What HTTP method is used to update a resource?",
             "opts": ["GET", "POST", "PUT", "DELETE"], "ans": 2},
        ],
        "advanced": [
            {"q": "What is the key advantage of GraphQL over REST?",
             "opts": ["Faster network", "Clients request exactly the data they need",
                      "Built-in authentication", "No server needed"], "ans": 1},
        ],
    },
    # ---- System Design ----
    "System Design": {
        "beginner": [
            {"q": "What is horizontal scaling?",
             "opts": ["Adding more powerful hardware", "Adding more machines to distribute load",
                      "Increasing memory", "Using a CDN"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is a load balancer?",
             "opts": ["A database index", "Distributes incoming traffic across servers",
                      "A caching layer", "A message queue"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is the CAP theorem?",
             "opts": ["A distributed system can guarantee at most 2 of: Consistency, Availability, Partition tolerance",
                      "A sorting algorithm", "A network protocol", "A testing principle"], "ans": 0},
        ],
    },
    # ---- NLP ----
    "NLP": {
        "beginner": [
            {"q": "What does NLP stand for?",
             "opts": ["Natural Language Processing", "Neural Layer Protocol",
                      "Non-Linear Programming", "New Language Parser"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is tokenisation?",
             "opts": ["Encrypting data", "Splitting text into smaller units (tokens)",
                      "Generating random text", "Translating languages"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is attention in NLP models?",
             "opts": ["A loss function", "Mechanism that lets the model focus on relevant parts of input",
                      "A data augmentation step", "A regularisation technique"], "ans": 1},
        ],
    },
    # ---- Computer Vision ----
    "Computer Vision": {
        "beginner": [
            {"q": "What is a convolution in CNNs?",
             "opts": ["A fully connected layer", "Applying a filter/kernel across an image to detect features",
                      "A pooling operation", "An activation function"], "ans": 1},
        ],
        "intermediate": [
            {"q": "What is transfer learning?",
             "opts": ["Training from scratch", "Reusing a pre-trained model for a new task",
                      "Data augmentation", "Feature scaling"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is an anchor box in object detection?",
             "opts": ["A bounding box template used to predict object locations",
                      "A type of activation function", "A loss function",
                      "A data augmentation method"], "ans": 0},
        ],
    },
    # ---- Data Visualization ----
    "Data Visualization": {
        "beginner": [
            {"q": "When should you use a bar chart?",
             "opts": ["Comparing categories", "Showing trends over time",
                      "Showing proportions", "Showing correlations"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is a heatmap best used for?",
             "opts": ["Showing geographic data", "Showing magnitude as colour in a matrix",
                      "Animating bar charts", "3D rendering"], "ans": 1},
        ],
        "advanced": [
            {"q": "What principle prevents chartjunk?",
             "opts": ["Maximise data-ink ratio (Tufte)", "Use 3D effects",
                      "Add grid lines everywhere", "Use bright colours"], "ans": 0},
        ],
    },
    # ---- Cloud Computing ----
    "Cloud Computing": {
        "beginner": [
            {"q": "What does IaaS stand for?",
             "opts": ["Infrastructure as a Service", "Internet as a Service",
                      "Integration as a Service", "Intelligence as a Service"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is serverless computing?",
             "opts": ["No servers exist", "Cloud provider manages servers; you deploy functions",
                      "On-premise only", "A containerisation method"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is a VPC?",
             "opts": ["Virtual Private Cloud — isolated network within the cloud",
                      "Virtual Processing Core", "Variable Pricing Calculator",
                      "Version-controlled Pipeline Configuration"], "ans": 0},
        ],
    },
    # ---- DevOps ----
    "DevOps": {
        "beginner": [
            {"q": "What does CI/CD stand for?",
             "opts": ["Continuous Integration / Continuous Delivery",
                      "Code Inspection / Code Deployment",
                      "Container Integration / Container Distribution",
                      "Cloud Infrastructure / Cloud Deployment"], "ans": 0},
        ],
        "intermediate": [
            {"q": "What is Infrastructure as Code (IaC)?",
             "opts": ["Manually configuring servers", "Managing infrastructure through code and version control",
                      "Writing application code", "A monitoring tool"], "ans": 1},
        ],
        "advanced": [
            {"q": "What is a canary deployment?",
             "opts": ["Rolling out changes to a small subset of users before full release",
                      "Deploying to all users at once", "A rollback strategy",
                      "A load testing method"], "ans": 0},
        ],
    },
}

# Difficulty ordering (lowest → highest)
DIFFICULTY_ORDER = ["beginner", "intermediate", "advanced", "expert"]


def _difficulty_for_level(level: int) -> str:
    """Map a 1-10 self-assessed level to a starting difficulty."""
    if level <= 3:
        return "beginner"
    elif level <= 5:
        return "intermediate"
    elif level <= 7:
        return "advanced"
    return "expert"


def _next_difficulty(current: str, correct: bool) -> str:
    idx = DIFFICULTY_ORDER.index(current)
    if correct:
        idx = min(idx + 1, len(DIFFICULTY_ORDER) - 1)
    else:
        idx = max(idx - 1, 0)
    return DIFFICULTY_ORDER[idx]


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def generate_adaptive_quiz(
    role_skills: List[str],
    user_levels: Optional[Dict[str, int]] = None,
    questions_per_skill: int = 2,
) -> List[dict]:
    """Return a list of MCQ dicts, *questions_per_skill* questions per skill.

    Each dict: {skill, difficulty, question, options, correct_index, id}
    """
    user_levels = user_levels or {}
    quiz: List[dict] = []
    qid = 0

    for skill in role_skills:
        if skill not in QUESTION_BANK:
            continue
        difficulty = _difficulty_for_level(user_levels.get(skill, 5))

        for _ in range(questions_per_skill):
            pool = QUESTION_BANK[skill].get(difficulty, [])
            if not pool:
                # fall back to any available difficulty
                for d in DIFFICULTY_ORDER:
                    if QUESTION_BANK[skill].get(d):
                        pool = QUESTION_BANK[skill][d]
                        difficulty = d
                        break
            if not pool:
                continue

            q = random.choice(pool)
            quiz.append({
                "id": qid,
                "skill": skill,
                "difficulty": difficulty,
                "question": q["q"],
                "options": q["opts"],
                "correct_index": q["ans"],
            })
            # Adapt for next question on the same skill: assume correct
            difficulty = _next_difficulty(difficulty, True)
            qid += 1

    # Don't shuffle - keep questions in order for better UX
    # Assign display order
    for idx, q in enumerate(quiz):
        q["display_order"] = idx
    
    return quiz


def score_quiz(quiz: List[dict], answers: Dict[int, int]) -> Dict[str, dict]:
    """Given a quiz and ``{question_id: selected_option_index}``,
    return per-skill summary: {skill: {correct, total, score_0_10, difficulty_reached}}.
    """
    skill_results: Dict[str, dict] = {}

    for q in quiz:
        skill = q["skill"]
        if skill not in skill_results:
            skill_results[skill] = {"correct": 0, "total": 0, "max_difficulty": "beginner"}
        skill_results[skill]["total"] += 1
        selected = answers.get(q["id"])
        if selected == q["correct_index"]:
            skill_results[skill]["correct"] += 1
            # track highest difficulty answered correctly
            cur = DIFFICULTY_ORDER.index(skill_results[skill]["max_difficulty"])
            got = DIFFICULTY_ORDER.index(q["difficulty"])
            if got >= cur:
                skill_results[skill]["max_difficulty"] = q["difficulty"]

    for skill, res in skill_results.items():
        ratio = res["correct"] / res["total"] if res["total"] else 0
        diff_idx = DIFFICULTY_ORDER.index(res["max_difficulty"])
        # Score formula: base from difficulty reached + bonus from accuracy
        res["score_0_10"] = min(10, round(2 + diff_idx * 2.5 + ratio * 2, 1))

    return skill_results


# Backward-compat shim for old code
def assess_skill_from_quiz(answers_dict):
    if not answers_dict:
        return 1
    correct = sum(1 for v in answers_dict.values() if v)
    return int((correct / len(answers_dict)) * 10) if answers_dict else 1

