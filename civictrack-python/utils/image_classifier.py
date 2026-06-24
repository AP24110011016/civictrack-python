"""
Image Classification Module
Uses OpenCV and NumPy to classify civic issues from photos
"""
import cv2
import numpy as np

# Issue types and their departments
DEPARTMENTS = {
    'pothole':      'Roads & Infrastructure',
    'garbage':      'Sanitation & Waste Mgmt',
    'drainage':     'Water & Drainage Dept',
    'streetlight':  'Electricity & Lighting',
    'road_damage':  'Roads & Infrastructure',
    'water_supply': 'Water Supply Dept',
    'fallen_tree':  'Parks & Environment',
    'noise':        'Law & Order Dept',
    'encroachment': 'Town Planning Dept',
    'other':        'Municipal Corporation',
}

PRIORITIES = {
    'pothole':      'high',
    'garbage':      'high',
    'drainage':     'high',
    'streetlight':  'medium',
    'road_damage':  'medium',
    'water_supply': 'critical',
    'fallen_tree':  'critical',
    'noise':        'high',
    'encroachment': 'low',
    'other':        'medium',
}

SLA_DAYS = {
    'pothole': 5, 'garbage': 2, 'drainage': 3,
    'streetlight': 2, 'road_damage': 7, 'water_supply': 1,
    'fallen_tree': 1, 'noise': 1, 'encroachment': 7, 'other': 5
}


def extract_features(img):
    """Extract visual features from image using OpenCV and NumPy"""
    img = cv2.resize(img, (224, 224))
    img_rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w     = img.shape[:2]
    total    = h * w

    # Mean color values
    r = float(np.mean(img_rgb[:,:,0]))
    g = float(np.mean(img_rgb[:,:,1]))
    b = float(np.mean(img_rgb[:,:,2]))
    hue = float(np.mean(img_hsv[:,:,0]))
    sat = float(np.mean(img_hsv[:,:,1]))
    val = float(np.mean(img_hsv[:,:,2]))

    # Edge detection using Canny algorithm
    edges        = cv2.Canny(img_gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / total)

    # Pixel ratio calculations using NumPy boolean masking
    dark_ratio   = float(np.sum(img_gray < 60) / total)
    green_ratio  = float(np.sum(
        (img_rgb[:,:,1] > img_rgb[:,:,0]) &
        (img_rgb[:,:,1] > img_rgb[:,:,2]) &
        (img_rgb[:,:,1] > 60)) / total)
    blue_ratio   = float(np.sum(
        (img_rgb[:,:,2] > img_rgb[:,:,0] + 20) &
        (img_rgb[:,:,2] > 80)) / total)
    yellow_ratio = float(np.sum(
        (img_rgb[:,:,0] > 150) &
        (img_rgb[:,:,1] > 100) &
        (img_rgb[:,:,2] < 80)) / total)
    gray_ratio   = float(np.sum(
        (np.abs(img_rgb[:,:,0].astype(int) - img_rgb[:,:,1].astype(int)) < 20) &
        (np.abs(img_rgb[:,:,1].astype(int) - img_rgb[:,:,2].astype(int)) < 20) &
        (img_gray > 80) & (img_gray < 180)) / total)
    brown_ratio  = float(np.sum(
        (img_rgb[:,:,0] > 100) &
        (img_rgb[:,:,1] > 60) &
        (img_rgb[:,:,2] < 60) &
        (img_rgb[:,:,0] > img_rgb[:,:,2] + 40)) / total)
    texture_var  = float(np.var(img_gray))

    return {
        'r': r, 'g': g, 'b': b,
        'hue': hue, 'sat': sat, 'val': val,
        'edge_density': edge_density,
        'dark_ratio': dark_ratio,
        'green_ratio': green_ratio,
        'blue_ratio': blue_ratio,
        'yellow_ratio': yellow_ratio,
        'gray_ratio': gray_ratio,
        'brown_ratio': brown_ratio,
        'texture_var': texture_var,
    }


def classify_features(f, hint=None):
    """Score each issue type based on extracted features"""
    scores = {
        'pothole': 0.0, 'garbage': 0.0, 'drainage': 0.0,
        'streetlight': 0.0, 'road_damage': 0.0, 'water_supply': 0.0,
        'fallen_tree': 0.0, 'noise': 0.0, 'encroachment': 0.0, 'other': 0.0
    }

    # Pothole: dark irregular patches on gray asphalt
    if f['dark_ratio'] > 0.12 and f['gray_ratio'] > 0.15:
        scores['pothole'] += 0.5
    if f['dark_ratio'] > 0.20:
        scores['pothole'] += 0.3
    if f['edge_density'] > 0.10 and f['gray_ratio'] > 0.20:
        scores['pothole'] += 0.3
    if f['texture_var'] > 2000 and f['gray_ratio'] > 0.10:
        scores['pothole'] += 0.2

    # Garbage: mixed colors, high saturation, irregular texture
    if f['sat'] > 50 and f['edge_density'] > 0.12:
        scores['garbage'] += 0.4
    if f['brown_ratio'] > 0.08 and f['edge_density'] > 0.10:
        scores['garbage'] += 0.3
    if f['texture_var'] > 3000 and f['green_ratio'] < 0.15:
        scores['garbage'] += 0.2

    # Drainage: water presence, blue/dark water tones
    if f['blue_ratio'] > 0.08:
        scores['drainage'] += 0.5
    if f['blue_ratio'] > 0.15:
        scores['drainage'] += 0.3
    if f['dark_ratio'] > 0.20 and f['blue_ratio'] > 0.05:
        scores['drainage'] += 0.2

    # Streetlight: yellow/bright spots in dark image
    if f['yellow_ratio'] > 0.04 and f['val'] < 130:
        scores['streetlight'] += 0.6
    if f['val'] < 80:
        scores['streetlight'] += 0.2
    if f['yellow_ratio'] > 0.08:
        scores['streetlight'] += 0.2

    # Road damage: cracks on gray surface with high edges
    if f['edge_density'] > 0.18 and f['gray_ratio'] > 0.15:
        scores['road_damage'] += 0.5
    if f['texture_var'] > 2500 and f['gray_ratio'] > 0.20:
        scores['road_damage'] += 0.3

    # Water supply: blue tones, pipes, infrastructure
    if f['blue_ratio'] > 0.12 and f['dark_ratio'] < 0.15:
        scores['water_supply'] += 0.4
    if f['blue_ratio'] > 0.20:
        scores['water_supply'] += 0.3

    # Fallen tree: heavy green presence
    if f['green_ratio'] > 0.20:
        scores['fallen_tree'] += 0.6
    if f['green_ratio'] > 0.30:
        scores['fallen_tree'] += 0.3

    # Default scores for hard to detect visually
    scores['noise']        += 0.05
    scores['encroachment'] += 0.05

    # If no strong signal detected
    if max(scores.values()) < 0.15:
        scores['other'] = 0.4

    # Normalize to sum to 1
    total = sum(scores.values()) or 1.0
    scores = {k: round(v / total, 4) for k, v in scores.items()}

    best_type  = max(scores, key=scores.get)
    confidence = scores[best_type]

    # If confidence is low and user gave hint, trust user more
    if confidence < 0.25 and hint and hint != 'other':
        best_type  = hint
        confidence = 0.75

    return best_type, confidence, scores


def classify_image(image_path, hint=None):
    """Main function to classify a civic issue from image path"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        features                      = extract_features(img)
        predicted_type, confidence, all_scores = classify_features(features, hint)
        return {
            'predicted_type': predicted_type,
            'confidence':     round(confidence, 3),
            'department':     DEPARTMENTS.get(predicted_type, 'Municipal Corporation'),
            'priority':       PRIORITIES.get(predicted_type, 'medium'),
            'sla_days':       SLA_DAYS.get(predicted_type, 5),
            'all_scores':     all_scores,
        }
    except Exception as e:
        print(f'Classification error: {e}')
        return None


def classify_image_bytes(img_bytes, hint=None):
    """Classify from image bytes"""
    try:
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return None
        features                      = extract_features(img)
        predicted_type, confidence, all_scores = classify_features(features, hint)
        return {
            'predicted_type': predicted_type,
            'confidence':     round(confidence, 3),
            'department':     DEPARTMENTS.get(predicted_type, 'Municipal Corporation'),
            'priority':       PRIORITIES.get(predicted_type, 'medium'),
            'all_scores':     all_scores,
        }
    except Exception as e:
        print(f'Classification error: {e}')
        return None
