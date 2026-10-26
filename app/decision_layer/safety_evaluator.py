"""
Decision Layer (Safety Evaluator & Weighted Severity Scoring)
Associates detected PPE items with each detected worker and computes weighted risk scores,
compliance percentages, and class counts using dynamic weights, enabled PPE classes, and alert thresholds.
"""

from typing import Any, Dict, List, Optional
from app.config.defaults import DEFAULT_THRESHOLDS, PPE_REGISTRY


def is_inside_person(person_box: List[float], item_box: List[float]) -> bool:
    """Check if the center of a detected PPE/body item lies within a person's bounding box."""
    px1, py1, px2, py2 = person_box
    ix1, iy1, ix2, iy2 = item_box
    center_x = (ix1 + ix2) / 2
    center_y = (iy1 + iy2) / 2
    return (px1 <= center_x <= px2) and (py1 <= center_y <= py2)


def evaluate_frame_safety(
    detections: List[Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    enabled_ppe: Optional[Dict[str, bool]] = None,
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Evaluate frame safety across all detected workers using extensible PPE rules.
    """
    active_weights = {
        key: (weights.get(key, rule.default_weight) if weights else rule.default_weight)
        for key, rule in PPE_REGISTRY.items()
    }
    active_enabled = {
        key: (enabled_ppe.get(key, rule.default_enabled) if enabled_ppe else rule.default_enabled)
        for key, rule in PPE_REGISTRY.items()
    }
    active_thresholds = thresholds if thresholds is not None else DEFAULT_THRESHOLDS

    persons = [d for d in detections if d["class_id"] == 0]
    other_items = [d for d in detections if d["class_id"] != 0]

    # Count detected PPE instances by registry key for the BBox Filter bar
    ppe_counts: Dict[str, int] = {key: 0 for key in PPE_REGISTRY}
    for item in other_items:
        cid = item["class_id"]
        for key, rule in PPE_REGISTRY.items():
            if cid in rule.required_class_ids:
                ppe_counts[key] += 1

    worker_reports = []
    frame_max_score = 0.0
    total_violations: List[str] = []
    compliant_count = 0
    violating_count = 0

    for idx, person in enumerate(persons):
        p_box = person["bbox"]
        p_conf = person["conf"]

        associated = [item for item in other_items if is_inside_person(p_box, item["bbox"])]
        detected_classes = {item["class_id"]: item["conf"] for item in associated}

        worker_score = 0.0
        violations: List[str] = []

        # Evaluate each registered PPE rule dynamically
        for key, rule in PPE_REGISTRY.items():
            if not active_enabled.get(key, True):
                continue

            weight = active_weights.get(key, rule.default_weight)
            has_required_ppe = any(
                cls_id in detected_classes for cls_id in rule.required_class_ids
            )

            if not has_required_ppe:
                if rule.require_exposed_part:
                    if (
                        rule.exposed_body_class_id is not None
                        and rule.exposed_body_class_id in detected_classes
                    ):
                        conf = detected_classes[rule.exposed_body_class_id]
                        worker_score += conf * weight
                        violations.append(rule.violation_label)
                else:
                    if rule.exposed_body_class_id is not None:
                        conf = detected_classes.get(rule.exposed_body_class_id, p_conf)
                    else:
                        conf = p_conf
                    worker_score += conf * weight
                    violations.append(rule.violation_label)

        worker_score = round(worker_score, 3)
        frame_max_score = max(frame_max_score, worker_score)
        total_violations.extend(violations)

        if violations:
            violating_count += 1
        else:
            compliant_count += 1

        worker_reports.append(
            {
                "worker_id": idx + 1,
                "conf": round(p_conf, 2),
                "violations": violations,
                "severity_score": worker_score,
            }
        )

    if frame_max_score >= active_thresholds["HIGH"]:
        alert_level = "HIGH ALERT"
        color = (0, 0, 255)
    elif frame_max_score >= active_thresholds["MEDIUM"]:
        alert_level = "MEDIUM ALERT"
        color = (0, 165, 255)
    elif frame_max_score >= active_thresholds["LOW"]:
        alert_level = "LOW ALERT"
        color = (0, 255, 255)
    else:
        alert_level = "SAFE"
        color = (0, 255, 0)

    total_workers = len(persons)
    compliance_pct = (
        round((compliant_count / total_workers) * 100.0, 1)
        if total_workers > 0
        else 100.0
    )

    return {
        "worker_count": total_workers,
        "compliant_count": compliant_count,
        "violating_count": violating_count,
        "compliance_pct": compliance_pct,
        "ppe_counts": ppe_counts,
        "max_severity_score": frame_max_score,
        "alert_level": alert_level,
        "alert_color": color,
        "violations_summary": list(set(total_violations)),
        "worker_reports": worker_reports,
    }
