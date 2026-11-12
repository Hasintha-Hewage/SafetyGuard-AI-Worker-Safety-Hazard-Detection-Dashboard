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


def _best_person_index(persons: List[Dict[str, Any]], item_box: List[float]) -> Optional[int]:
    """
    Pick the single person an item belongs to. The item's center must lie inside the
    person box; when several qualify, prefer the largest share of the item's area inside
    the person, then the smallest (tightest) person box.
    """
    ix1, iy1, ix2, iy2 = item_box
    item_area = max((ix2 - ix1) * (iy2 - iy1), 1e-6)
    best_idx: Optional[int] = None
    best_key = None
    for i, person in enumerate(persons):
        p_box = person["bbox"]
        if not is_inside_person(p_box, item_box):
            continue
        px1, py1, px2, py2 = p_box
        iw = max(0.0, min(ix2, px2) - max(ix1, px1))
        ih = max(0.0, min(iy2, py2) - max(iy1, py1))
        key = (-(iw * ih) / item_area, (px2 - px1) * (py2 - py1))
        if best_key is None or key < best_key:
            best_key, best_idx = key, i
    return best_idx


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

    # Tolerate missing keys and mis-ordered values (HIGH >= MEDIUM >= LOW).
    high = active_thresholds.get("HIGH", DEFAULT_THRESHOLDS["HIGH"])
    medium = min(active_thresholds.get("MEDIUM", DEFAULT_THRESHOLDS["MEDIUM"]), high)
    low = min(active_thresholds.get("LOW", DEFAULT_THRESHOLDS["LOW"]), medium)

    persons = [d for d in detections if d["class_id"] == 0]
    other_items = [d for d in detections if d["class_id"] != 0]

    # Assign every item to exactly one person so overlapping workers don't share PPE.
    items_by_person: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(len(persons))}
    for item in other_items:
        best = _best_person_index(persons, item["bbox"])
        if best is not None:
            items_by_person[best].append(item)

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

        # Keep the highest confidence per class
        detected_classes: Dict[int, float] = {}
        for item in items_by_person[idx]:
            cid = item["class_id"]
            if item["conf"] > detected_classes.get(cid, -1.0):
                detected_classes[cid] = item["conf"]

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
                # Stable tracker ID when available, else per-frame index
                "worker_id": person.get("track_id") or idx + 1,
                "conf": round(p_conf, 2),
                "violations": violations,
                "severity_score": worker_score,
            }
        )

    if frame_max_score >= high:
        alert_level = "HIGH ALERT"
        color = (216, 78, 29)  # Deep Royal Blue (RGB: #1D4ED8)
    elif frame_max_score >= medium:
        alert_level = "MEDIUM ALERT"
        color = (235, 99, 37)  # Vibrant Cobalt Blue (RGB: #2563EB)
    elif frame_max_score >= low:
        alert_level = "LOW ALERT"
        color = (248, 189, 56)  # Sky Blue (RGB: #38BDF8)
    else:
        alert_level = "SAFE"
        color = (235, 165, 14)  # Crisp Cyan Blue (RGB: #0EA5E9)

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
