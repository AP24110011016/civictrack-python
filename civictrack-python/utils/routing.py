"""
Automated Routing Engine
Routes complaints to correct department based on issue type
"""
from datetime import datetime, timedelta

ROUTING = {
    'pothole':      {'dept': 'Roads & Infrastructure',  'sla': 5,  'priority': 'high'},
    'garbage':      {'dept': 'Sanitation & Waste Mgmt', 'sla': 2,  'priority': 'high'},
    'drainage':     {'dept': 'Water & Drainage Dept',   'sla': 3,  'priority': 'high'},
    'streetlight':  {'dept': 'Electricity & Lighting',  'sla': 2,  'priority': 'medium'},
    'road_damage':  {'dept': 'Roads & Infrastructure',  'sla': 7,  'priority': 'medium'},
    'water_supply': {'dept': 'Water Supply Dept',       'sla': 1,  'priority': 'critical'},
    'fallen_tree':  {'dept': 'Parks & Environment',     'sla': 1,  'priority': 'critical'},
    'noise':        {'dept': 'Law & Order Dept',        'sla': 1,  'priority': 'high'},
    'encroachment': {'dept': 'Town Planning Dept',      'sla': 7,  'priority': 'low'},
    'other':        {'dept': 'Municipal Corporation',   'sla': 5,  'priority': 'medium'},
}


def auto_route(issue_type, upvotes=0):
    """Automatically route complaint to correct department"""
    r        = ROUTING.get(issue_type, ROUTING['other'])
    priority = r['priority']

    # Increase priority based on community upvotes
    if upvotes >= 50:
        priority = 'critical'
    elif upvotes >= 20 and priority == 'medium':
        priority = 'high'
    elif upvotes >= 10 and priority == 'low':
        priority = 'medium'

    return {
        'department':          r['dept'],
        'priority':            priority,
        'sla_hours':           r['sla'] * 24,
        'estimated_resolution': datetime.utcnow() + timedelta(days=r['sla']),
    }


def compute_urgency(priority, upvotes=0, created_at=None):
    """Compute urgency score 0-100"""
    scores = {'low': 20, 'medium': 40, 'high': 70, 'critical': 100}
    score  = scores.get(priority, 40)
    score += min(upvotes * 2, 20)

    if created_at:
        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600
        if age_hours > 48:
            score += 10
        if age_hours > 120:
            score += 20

    return min(score, 100)
