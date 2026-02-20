# learning_roadmap.py - Personalized learning plan generator

from gap_analysis import calculate_skill_gaps

def get_level_description(level):
    """Get a human-readable description for a skill level"""
    if level <= 2:
        return "Beginner - Just starting out"
    elif level <= 4:
        return "Elementary - Basic understanding"
    elif level <= 6:
        return "Intermediate - Can work independently"
    elif level <= 8:
        return "Advanced - Strong proficiency"
    else:
        return "Expert - Mastery level"

def get_priority_description(priority_score):
    """Get a human-readable description for priority score"""
    if priority_score > 15:
        return "🔴 Critical - Focus on this first"
    elif priority_score > 8:
        return "🟡 Important - High priority"
    else:
        return "🟢 Moderate - Can be learned later"

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
        "weeks": [],
        "legend": {
            "levels": "Skill levels range from 1 (Beginner) to 10 (Expert)",
            "priority": "Priority indicates how critical this skill is for your target role",
            "timeline": f"This {weeks}-week plan is personalized based on your current skill gaps"
        }
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
                "current_level": round(gap_info["current"], 1),
                "current_description": get_level_description(gap_info["current"]),
                "target_level": round(gap_info["required"], 1),
                "target_description": get_level_description(gap_info["required"]),
                "levels_to_improve": round(gap_info["gap"], 1),
                "difficulty": difficulty,
                "priority": get_priority_description(gap_info["priority_score"]),
                "priority_score": round(gap_info["priority_score"], 1)
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
        "current_level": round(current_level, 1),
        "target_level": round(target_level, 1),
        "levels_to_improve": round(target_level - current_level, 1),
        "path": path_stages
    }
