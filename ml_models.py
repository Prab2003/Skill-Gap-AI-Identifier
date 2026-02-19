# ml_models.py - Machine Learning models for skill prediction and personalization

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

class SkillPredictionModel:
    """ML Model to predict time needed to reach target skill level"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.train_model()
    
    def train_model(self):
        """Train the skill improvement prediction model"""
        # Synthetic training data: [current_level, target_level, learning_hours_per_week] -> weeks_to_target
        np.random.seed(42)
        
        # Generate realistic training data
        current_levels = np.random.randint(1, 8, 500)
        target_levels = np.random.randint(7, 11, 500)
        learning_hours = np.random.randint(5, 40, 500)  # hours per week
        
        # Create realistic relationship: more current skill = faster improvement
        weeks_to_target = []
        for curr, targ, hours in zip(current_levels, target_levels, learning_hours):
            gap = max(0, targ - curr)
            # More hours and higher current level = faster improvement
            improvement_rate = 1 + (hours / 10) + (curr / 10)
            weeks_needed = max(1, gap * 3 / improvement_rate)
            weeks_to_target.append(weeks_needed)
        
        X = np.column_stack([current_levels, target_levels, learning_hours])
        y = np.array(weeks_to_target)
        
        # Train model
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def predict_weeks_to_target(self, current_level, target_level, hours_per_week=10):
        """Predict weeks needed to reach target skill level"""
        if not self.is_trained:
            return None
        
        X = np.array([[current_level, target_level, hours_per_week]])
        X_scaled = self.scaler.transform(X)
        weeks = self.model.predict(X_scaled)[0]
        return max(1, round(weeks, 1))
    
    def predict_skill_at_weeks(self, current_level, weeks, hours_per_week=10):
        """Predict skill level achievable in N weeks"""
        # Approximate: skill increases by ~0.5-1 levels per week depending on effort
        improvement_rate = 0.3 + (hours_per_week / 40)  # Based on hours invested
        predicted_level = min(10, current_level + (weeks * improvement_rate))
        return round(predicted_level, 1)


class PersonalizationModel:
    """ML Model to personalize learning recommendations"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.train_model()
    
    def train_model(self):
        """Train personalization model"""
        # Features: [current_level, gap_size, priority_score, learning_style]
        # Output: recommended_resource_type (0=Course, 1=Tutorial, 2=Book, 3=Project)
        
        np.random.seed(42)
        
        current_levels = np.random.randint(0, 10, 400)
        gaps = np.random.randint(0, 10, 400)
        priorities = np.random.rand(400) * 20
        learning_styles = np.random.randint(0, 3, 400)  # 0=visual, 1=reading, 2=practical
        
        # Logic: beginners benefit from courses, high gaps need projects
        resource_types = []
        for curr, gap, prio, style in zip(current_levels, gaps, priorities, learning_styles):
            if curr < 3:
                resource_types.append(0)  # Course for beginners
            elif gap > 5 and style == 2:
                resource_types.append(3)  # Project for practical learners with big gaps
            elif style == 1:
                resource_types.append(2)  # Book for readers
            else:
                resource_types.append(1)  # Tutorial for others
        
        X = np.column_stack([current_levels, gaps, priorities, learning_styles])
        y = np.array(resource_types)
        
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def recommend_resource_type(self, current_level, gap, priority, learning_style=0):
        """Recommend resource type: 0=Course, 1=Tutorial, 2=Book, 3=Project"""
        if not self.is_trained:
            return 0
        
        X = np.array([[current_level, gap, priority, learning_style]])
        X_scaled = self.scaler.transform(X)
        recommendation = int(round(self.model.predict(X_scaled)[0]))
        return max(0, min(3, recommendation))
    
    def get_optimal_skill_order(self, gaps, role_requirements):
        """Determine optimal order to learn skills (dependencies matter)"""
        # Skills with natural dependencies: Python before ML, SQL before Data Viz
        dependencies = {
            "Machine Learning": ["Python", "Statistics"],
            "Deep Learning": ["Python", "Machine Learning"],
            "SQL": ["Python"],
            "Data Visualization": ["SQL", "Python"],
        }
        
        sorted_skills = []
        remaining = set(gaps.keys())
        
        while remaining:
            for skill in list(remaining):
                deps = dependencies.get(skill, [])
                if not deps or all(d in sorted_skills for d in deps if d in gaps):
                    sorted_skills.append(skill)
                    remaining.remove(skill)
                    break
            else:
                # If circular dependency, just add remaining
                sorted_skills.extend(remaining)
                break
        
        return sorted_skills


# Initialize models
skill_predictor = SkillPredictionModel()
personalizer = PersonalizationModel()
