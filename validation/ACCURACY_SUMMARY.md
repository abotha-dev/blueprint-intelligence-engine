# Takeoff.ai Accuracy Validation

## Aggregate Results
- Blueprints tested: 6
- Avg room detection rate: **81.5%**
- Avg area accuracy: **90.9%**
- Confidence distribution: {"low": 6, "high": 19, "medium": 6}

## Per-Blueprint Results

### corridor-house.png (mock parser)
- Detection: 83.3% (5/6 rooms)
- Area accuracy: 88.8%
- Confidence: {'low': 2, 'high': 3}
- Missed: Living Room

### family-house.svg (mock parser)
- Detection: 87.5% (7/8 rooms)
- Area accuracy: 90.5%
- Confidence: {'high': 3, 'medium': 4}
- Missed: Kitchen

### house.svg (mock parser)
- Detection: 80.0% (4/5 rooms)
- Area accuracy: 90.5%
- Confidence: {'high': 2, 'medium': 1, 'low': 1}
- Missed: Living Room

### l-shaped-house.png (mock parser)
- Detection: 80.0% (4/5 rooms)
- Area accuracy: 89.8%
- Confidence: {'high': 1, 'low': 2, 'medium': 1}
- Missed: Kitchen

### simple-house.svg (mock parser)
- Detection: 83.3% (5/6 rooms)
- Area accuracy: 94.7%
- Confidence: {'high': 5}
- Missed: Master Bedroom

### u-shaped-house.png (mock parser)
- Detection: 75.0% (6/8 rooms)
- Area accuracy: 91.0%
- Confidence: {'high': 5, 'low': 1}
- Missed: Living Room, Bedroom 2
