# ---------- Scoring Configurations (Hardcoded for MVP) ----------
SCORING_CONFIG = {
    "candidate": {
    "base_salary": [
        # Range from $65k to $75k: linear interpolation from 20 to 60 points.
        {"min": 65000, "max": 75000, "score_min": 20, "score_max": 60},
        # Above $75k: start at 60, add 2 points per extra $1,000, capped at an extra 20 points.
        {"min": 75000, "max": None, "points_per_unit": 2, "unit": 1000, "max_extra": 20, "base": 60}
    ],
    "sign_on_bonus": [
        # Range from $5k to $8k: linear interpolation from 20 to 40 points.
        {"min": 5000, "max": 8000, "score_min": 20, "score_max": 40},
        # Above $8k: add 5 points per extra $500, capped at an extra 20 points.
        {"min": 8000, "max": None, "points_per_unit": 5, "unit": 500, "max_extra": 20, "base": 40}
    ],
    "remote_days": [
        # For remote work days, we simply define fixed points.
        # Less than 2 days: 0 points; exactly 2 days: 10; 3 or more: 20.
        {"value": 2, "points": 10},
        {"value": 3, "points": 20}  # Use this if remote_days >= 3.
    ],
    "outcome": {
        "success": 50,
        "failure": -50
    },
    "bonus_objectives": {
        # Bonus objectives are keyed by an id. They may refer to a specific metric.
        "debt": {"metric": "sign_on_bonus", "threshold": 7000, "bonus": 30},
    }
},  # Copy candidate_scoring_config from main.py
    "hr": {
    "base_salary": [
        # Salary <= $65k: 30 points.
        {"min": None, "max": 65000, "score": 30},
        # From $65k to $70k: linear decrease from 30 to 20.
        {"min": 65000, "max": 70000, "score_min": 30, "score_max": 20},
        # Above $70k: subtract 5 points per extra $1k from $70k, floor at -20.
        {"min": 70000, "max": None, "penalty_per_unit": 5, "unit": 1000, "base": 20, "min_score": -20}
    ],
    "sign_on_bonus": [
        # Bonus <= $5k: 20 points.
        {"min": None, "max": 5000, "score": 20},
        # $5k to $8k: linear decrease from 20 to 10.
        {"min": 5000, "max": 8000, "score_min": 20, "score_max": 10},
        # Above $8k: subtract 5 points per extra $500, floor at -10.
        {"min": 8000, "max": None, "penalty_per_unit": 5, "unit": 500, "base": 10, "min_score": -10}
    ],
    "total_compensation": [
        # Total Compensation <= $80k: 30 points.
        {"min": None, "max": 80000, "score": 30},
        # $80k to $85k: linear decrease from 30 to 10.
        {"min": 80000, "max": 85000, "score_min": 30, "score_max": 10},
        # Above $85k: flat -20.
        {"min": 85000, "max": None, "score": -20}
    ],
    "remote_days": [
        # 0 days: 10 points; 1 day: 5 points; otherwise 0.
        {"value": 0, "points": 10},
        {"value": 1, "points": 5}
    ],
    "outcome": {
        "success": 50,
        "failure": -50
    },
    "bonus_objectives": {
        "budget": {"metric": "total_compensation", "threshold": 76000, "bonus": 30}
    }
}
}

VALIDATION_RANGES = {
    "salary": {"min": 0, "max": 1000000},
    "bonus": {"min": 0, "max": 10000},
    "remote_days": {"min": 0, "max": 5}
}


