"""
YOLO Detection & Frame Annotation Layer (Detection Layer)
Handles model caching, frame inference, active class filtering, and OpenCV banner rendering.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO
from app.config.defaults import DEFAULT_MODEL_PATH, PPE_REGISTRY


@st.cache_resource
def load_yolo_model(model_path: str = DEFAULT_MODEL_PATH) -> YOLO:
    """Load and cache the YOLOv8 model so it only loads once per session."""
    return YOLO(model_path)


def get_active_yolo_class_ids(enabled_ppe: Dict[str, bool]) -> List[int]:
    """
    Build the list of YOLO class IDs to detect based on enabled PPE toggles.
    Always includes class 0 ('person').
    """
    active_ids = {0}  # Always detect persons
    for key, rule in PPE_REGISTRY.items():
        if enabled_ppe.get(key, True):
            active_ids.update(rule.required_class_ids)
            if rule.exposed_body_class_id is not None:
                active_ids.add(rule.exposed_body_class_id)
    return sorted(active_ids)


def run_inference(
    model: YOLO,
    frame: np.ndarray,
    confidence_threshold: float,
    enabled_ppe: Optional[Dict[str, bool]] = None,
) -> Tuple[Any, List[Dict[str, Any]], float]:
    """
    Execute YOLO inference on a single video frame and extract structured detections.

    Returns:
        (yolo_result, detections_list, inference_ms)
    """
    start_time = time.time()

    active_classes = (
        get_active_yolo_class_ids(enabled_ppe) if enabled_ppe is not None else None
    )

    results = model(
        frame,
        conf=confidence_threshold,
        classes=active_classes,
        verbose=False,
    )
    result = results[0]
    inference_ms = round((time.time() - start_time) * 1000, 2)

    detections: List[Dict[str, Any]] = []
    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        cls_ids = result.boxes.cls.cpu().numpy().astype(int)

        for box, conf, cls_id in zip(boxes, confs, cls_ids):
            detections.append(
                {
                    "class_id": int(cls_id),
                    "class_name": model.names[int(cls_id)],
                    "conf": float(conf),
                    "bbox": [float(c) for c in box],
                }
            )

    return result, detections, inference_ms


def annotate_frame(
    result: Any,
    decision: Dict[str, Any],
    inference_ms: float,
) -> np.ndarray:
    """
    Render YOLO bounding boxes and the Decision Layer telemetry banner onto the frame,
    returning an RGB numpy array ready for Streamlit display.
    """
    annotated_frame = result.plot()
    banner_text = (
        f"{decision['alert_level']} | Score: {decision['max_severity_score']} | {inference_ms}ms"
    )
    cv2.rectangle(annotated_frame, (10, 10), (520, 50), (0, 0, 0), -1)
    cv2.putText(
        annotated_frame,
        banner_text,
        (20, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        decision["alert_color"],
        2,
    )
    return cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
