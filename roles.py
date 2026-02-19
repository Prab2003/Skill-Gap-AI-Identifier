# roles.py  –  Target-role definitions, required skill levels, and curated resources

roles = {
    "Data Scientist": {
        "Python": 8, "Statistics": 8, "Machine Learning": 8,
        "SQL": 7, "Data Visualization": 6, "Deep Learning": 5,
    },
    "ML Engineer": {
        "Python": 9, "Machine Learning": 9, "Deep Learning": 8,
        "Docker": 6, "System Design": 6, "Statistics": 7,
    },
    "Frontend Developer": {
        "JavaScript": 9, "React": 8, "CSS": 7,
        "Git": 7, "Testing": 6, "APIs": 6,
    },
    "Backend Developer": {
        "Python": 8, "SQL": 8, "APIs": 8,
        "Docker": 6, "System Design": 7, "Testing": 7, "Git": 7,
    },
    "Full Stack Developer": {
        "JavaScript": 8, "React": 7, "Python": 7,
        "SQL": 7, "APIs": 7, "Git": 7, "Docker": 5,
    },
    "AI Engineer": {
        "Python": 9, "Deep Learning": 9, "Machine Learning": 9,
        "NLP": 7, "Computer Vision": 6, "Docker": 6, "System Design": 6,
    },
    "Data Analyst": {
        "SQL": 8, "Python": 6, "Statistics": 7,
        "Data Visualization": 8, "Machine Learning": 4,
    },
    "DevOps Engineer": {
        "Docker": 9, "Cloud Computing": 8, "Git": 8,
        "Python": 6, "System Design": 7, "Testing": 6,
    },
}

# ---- Curated learning resources per skill ----
resources = {
    "Python": [
        {"title": "Python for Everybody", "type": "Course", "duration": "4 weeks", "platform": "Coursera", "url": "https://coursera.org/specializations/python"},
        {"title": "Real Python Tutorials", "type": "Tutorials", "duration": "Self-paced", "platform": "realpython.com", "url": "https://realpython.com"},
        {"title": "Fluent Python (2nd ed.)", "type": "Book", "duration": "8 weeks", "platform": "O'Reilly", "url": "https://oreilly.com"},
    ],
    "JavaScript": [
        {"title": "The Odin Project – JS Path", "type": "Course", "duration": "12 weeks", "platform": "theodinproject.com", "url": "https://theodinproject.com"},
        {"title": "JavaScript.info", "type": "Tutorials", "duration": "Self-paced", "platform": "javascript.info", "url": "https://javascript.info"},
    ],
    "React": [
        {"title": "React – The Complete Guide", "type": "Course", "duration": "10 weeks", "platform": "Udemy", "url": "https://udemy.com"},
        {"title": "Official React Docs", "type": "Tutorials", "duration": "Self-paced", "platform": "react.dev", "url": "https://react.dev"},
    ],
    "SQL": [
        {"title": "SQL for Data Science", "type": "Course", "duration": "4 weeks", "platform": "Coursera", "url": "https://coursera.org"},
        {"title": "Mode SQL Tutorial", "type": "Tutorials", "duration": "Self-paced", "platform": "mode.com", "url": "https://mode.com/sql-tutorial"},
    ],
    "Statistics": [
        {"title": "Statistics & Probability – Khan Academy", "type": "Course", "duration": "6 weeks", "platform": "Khan Academy", "url": "https://khanacademy.org"},
        {"title": "Think Stats (free book)", "type": "Book", "duration": "4 weeks", "platform": "greenteapress.com", "url": "https://greenteapress.com/thinkstats"},
    ],
    "Machine Learning": [
        {"title": "Machine Learning Specialization (Andrew Ng)", "type": "Course", "duration": "10 weeks", "platform": "Coursera", "url": "https://coursera.org/specializations/machine-learning-introduction"},
        {"title": "Hands-On ML with Scikit-Learn & TF", "type": "Book", "duration": "12 weeks", "platform": "O'Reilly", "url": "https://oreilly.com"},
    ],
    "Deep Learning": [
        {"title": "Deep Learning Specialization", "type": "Course", "duration": "16 weeks", "platform": "Coursera", "url": "https://coursera.org/specializations/deep-learning"},
        {"title": "fast.ai Practical DL", "type": "Course", "duration": "7 weeks", "platform": "fast.ai", "url": "https://course.fast.ai"},
    ],
    "Data Visualization": [
        {"title": "Data Visualization with Python", "type": "Course", "duration": "5 weeks", "platform": "Coursera", "url": "https://coursera.org"},
        {"title": "Storytelling with Data", "type": "Book", "duration": "3 weeks", "platform": "Amazon", "url": "https://storytellingwithdata.com"},
    ],
    "Git": [
        {"title": "Git & GitHub Crash Course", "type": "Tutorials", "duration": "1 week", "platform": "YouTube / freeCodeCamp", "url": "https://youtube.com"},
        {"title": "Pro Git (free book)", "type": "Book", "duration": "2 weeks", "platform": "git-scm.com", "url": "https://git-scm.com/book"},
    ],
    "Docker": [
        {"title": "Docker for Beginners", "type": "Course", "duration": "3 weeks", "platform": "KodeKloud", "url": "https://kodekloud.com"},
        {"title": "Docker Deep Dive", "type": "Book", "duration": "4 weeks", "platform": "Pluralsight", "url": "https://pluralsight.com"},
    ],
    "CSS": [
        {"title": "CSS for JS Developers", "type": "Course", "duration": "6 weeks", "platform": "css-for-js.dev", "url": "https://css-for-js.dev"},
        {"title": "CSS Tricks", "type": "Tutorials", "duration": "Self-paced", "platform": "css-tricks.com", "url": "https://css-tricks.com"},
    ],
    "Testing": [
        {"title": "Testing Python with pytest", "type": "Tutorials", "duration": "3 weeks", "platform": "realpython.com", "url": "https://realpython.com"},
        {"title": "Test-Driven Development by Example", "type": "Book", "duration": "4 weeks", "platform": "Amazon", "url": "https://amazon.com"},
    ],
    "APIs": [
        {"title": "Designing RESTful APIs", "type": "Course", "duration": "3 weeks", "platform": "Udacity", "url": "https://udacity.com"},
        {"title": "FastAPI Official Tutorial", "type": "Tutorials", "duration": "1 week", "platform": "fastapi.tiangolo.com", "url": "https://fastapi.tiangolo.com/tutorial"},
    ],
    "System Design": [
        {"title": "System Design Interview", "type": "Book", "duration": "6 weeks", "platform": "Amazon", "url": "https://amazon.com"},
        {"title": "Grokking System Design", "type": "Course", "duration": "8 weeks", "platform": "educative.io", "url": "https://educative.io"},
    ],
    "NLP": [
        {"title": "HuggingFace NLP Course", "type": "Course", "duration": "4 weeks", "platform": "huggingface.co", "url": "https://huggingface.co/learn/nlp-course"},
        {"title": "Speech & Language Processing", "type": "Book", "duration": "12 weeks", "platform": "Stanford (free)", "url": "https://web.stanford.edu/~jurafsky/slp3"},
    ],
    "Computer Vision": [
        {"title": "CS231n – CNNs for Visual Recognition", "type": "Course", "duration": "10 weeks", "platform": "Stanford (free)", "url": "https://cs231n.stanford.edu"},
    ],
    "Cloud Computing": [
        {"title": "AWS Cloud Practitioner Essentials", "type": "Course", "duration": "4 weeks", "platform": "AWS", "url": "https://aws.amazon.com/training"},
        {"title": "Google Cloud Fundamentals", "type": "Course", "duration": "4 weeks", "platform": "Coursera", "url": "https://coursera.org"},
    ],
    "DevOps": [
        {"title": "DevOps with Docker, K8s & Terraform", "type": "Course", "duration": "8 weeks", "platform": "Udemy", "url": "https://udemy.com"},
    ],
    "Agile": [
        {"title": "Agile with Atlassian Jira", "type": "Course", "duration": "2 weeks", "platform": "Coursera", "url": "https://coursera.org"},
    ],
    "AWS": [
        {"title": "AWS Solutions Architect Associate", "type": "Course", "duration": "8 weeks", "platform": "A Cloud Guru", "url": "https://acloudguru.com"},
    ],
}
