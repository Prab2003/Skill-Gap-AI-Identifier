# learning_roadmap.py - Personalized learning plan generator

from gap_analysis import calculate_skill_gaps

def generate_learning_roadmap(user_scores, role_requirements, weeks=12):
    """Generate a prioritized 4-week learning roadmap based on skill gaps"""
    
    gaps = calculate_skill_gaps(user_scores, role_requirements)
    
    # Filter only skills with gaps
    skills_to_learn = {skill: details for skill, details in gaps.items() if details["gap"] > 0}
    
    if not skills_to_learn:
        return {
            "status": "🎉 Congratulations!",
            "message": "You have all required skills for this role!",
            "weeks": []
        }
    
    # Create 4-week learning plan
    roadmap = {
        "status": "📚 Personalized Learning Roadmap",
        "total_skills_to_develop": len(skills_to_learn),
        "estimated_weeks": weeks,
        "weeks": []
    }
    
    # Distribute skills across weeks based on priority
    skills_list = list(skills_to_learn.items())
    skills_per_week = max(1, len(skills_list) // weeks)
    
    for week_num in range(1, weeks + 1):
        start_idx = (week_num - 1) * skills_per_week
        end_idx = start_idx + skills_per_week if week_num < weeks else len(skills_list)
        
        week_skills = skills_list[start_idx:end_idx]
        
        week_plan = {
            "week": week_num,
            "focus_areas": [],
            "daily_targets": []
        }
        
        for skill, gap_info in week_skills:
            difficulty = "Beginner" if gap_info["current"] <= 3 else "Intermediate" if gap_info["current"] <= 6 else "Advanced"
            
            week_plan["focus_areas"].append({
                "skill": skill,
                "current_level": gap_info["current"],
                "target_level": gap_info["required"],
                "difficulty": difficulty,
                "priority": "🔴 High" if gap_info["priority_score"] > 15 else "🟡 Medium" if gap_info["priority_score"] > 8 else "🟢 Low"
            })
        
        # Create daily targets
        days_in_week = 6  # Study 6 days
        for day in range(1, days_in_week + 1):
            day_target = f"Day {day}: "
            if week_skills:
                skill_name = week_skills[0][0]
                day_target += f"Study {skill_name} (2-3 hours)"
            week_plan["daily_targets"].append(day_target)
        
        week_plan["daily_targets"].append(f"Day 7: Review & Practice")
        
        roadmap["weeks"].append(week_plan)
    
    return roadmap

def generate_recommendation_summary(gaps, resources):
    """Generate a summary of learning recommendations"""
    summary = {
        "immediate_actions": [],
        "short_term_goals": [],
        "timeline_estimate": ""
    }
    
    # Get top 3 priority skills
    sorted_gaps = sorted(gaps.items(), key=lambda x: x[1]["priority_score"], reverse=True)
    
    for i, (skill, gap_info) in enumerate(sorted_gaps[:3]):
        if gap_info["gap"] > 0:
            summary["immediate_actions"].append({
                "skill": skill,
                "action": f"Start with {skill}: {gap_info['gap']} levels to improve",
                "effort": "High" if gap_info["gap"] >= 5 else "Medium"
            })
    
    total_gap = sum(g["gap"] for g in gaps.values())
    
    if total_gap >= 15:
        summary["timeline_estimate"] = "8-12 weeks to reach target proficiency"
    elif total_gap >= 8:
        summary["timeline_estimate"] = "4-8 weeks to reach target proficiency"
    else:
        summary["timeline_estimate"] = "2-4 weeks to reach target proficiency"
    
    return summary

def get_learning_path(skill, current_level, target_level):
    """Generate a learning path for a specific skill"""
    
    path_stages = {
        "Beginner (1-3)": [
            "✅ Master fundamentals",
            "✅ Understand core concepts",
            "✅ Complete beginner tutorials"
        ],
        "Intermediate (4-6)": [
            "✅ Build projects",
            "✅ Practice problem-solving",
            "✅ Study advanced concepts"
        ],
        "Advanced (7-9)": [
            "✅ Contribute to open source",
            "✅ Design complex systems",
            "✅ Mentor others"
        ],
        "Expert (9-10)": [
            "✅ Master edge cases",
            "✅ Optimize for performance",
            "✅ Create original solutions"
        ]
    }
    
    return {
        "skill": skill,
        "current_level": current_level,
        "target_level": target_level,
        "levels_to_improve": target_level - current_level,
        "path": path_stages
    }
