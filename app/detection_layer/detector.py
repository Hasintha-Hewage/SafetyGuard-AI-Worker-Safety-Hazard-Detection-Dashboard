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
from app.config.defaults import DEFAULT_MODEL_PATH, INFERENCE_IMAGE_SIZE, PPE_REGISTRY


@st.cache_resource
def load_yolo_model(model_path: str = DEFAULT_MODEL_PATH) -> YOLO:
    """Load and cache the YOLOv8 model so it only loads once per session."""
    return YOLO(model_path)


def get_active_yolo_class_ids(enabled_ppe: Dict[str, bool]) -> List[int]:
    """
    Build the list of YOLO class IDs to detect based on enabled PPE toggles.
    Always includes class 0 ('person'). Missing keys fall back to each rule's
    `default_enabled` so this stays consistent with the Decision Layer.
    """
    active_ids = {0}  # Always detect persons
    for key, rule in PPE_REGISTRY.items():
        if enabled_ppe.get(key, rule.default_enabled):
            active_ids.update(rule.required_class_ids)
            if rule.exposed_body_class_id is not None:
                active_ids.add(rule.exposed_body_class_id)
    return sorted(active_ids)


def run_inference(
    model: YOLO,
    frame: np.ndarray,
    confidence_threshold: float,
    enabled_ppe: Optional[Dict[str, bool]] = None,
    active_classes: Optional[List[int]] = None,
    track: bool = False,
    reset_tracker: bool = False,
) -> Tuple[Any, List[Dict[str, Any]], float]:
    """
    Execute YOLO inference on a single video frame and extract structured detections.

    Args:
        active_classes: Precomputed class IDs (avoids recomputing every frame).
            If None, they are derived from `enabled_ppe`.
        track: Use the ultralytics tracker so persons keep stable `track_id`s.
        reset_tracker: Set True on the first frame of a new video to clear tracker state.

    Returns:
        (yolo_result, detections_list, inference_ms)
    """
    start_time = time.perf_counter()

    if active_classes is None and enabled_ppe is not None:
        active_classes = get_active_yolo_class_ids(enabled_ppe)

    kwargs = dict(
        conf=confidence_threshold,
        classes=active_classes,
        imgsz=INFERENCE_IMAGE_SIZE,
        verbose=False,
    )

    results = None
    if track:
        try:
            results = model.track(frame, persist=not reset_tracker, **kwargs)
        except Exception:
            # Tracker unavailable (e.g. missing optional dependency): plain detection.
            results = None
    if results is None:
        results = model(frame, **kwargs)

    result = results[0]
    inference_ms = round((time.perf_counter() - start_time) * 1000, 2)

    detections: List[Dict[str, Any]] = []
    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes.xyxy.cpu().numpy().tolist()
        confs = result.boxes.conf.cpu().numpy().tolist()
        cls_ids = result.boxes.cls.cpu().numpy().astype(int).tolist()
        ids = result.boxes.id
        track_ids = (
            ids.cpu().numpy().astype(int).tolist() if ids is not None else [None] * len(boxes)
        )

        for box, conf, cls_id, tid in zip(boxes, confs, cls_ids, track_ids):
            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": model.names[cls_id],
                    "conf": conf,
                    "bbox": box,
                    "track_id": tid,
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
        f"{decision['alert_level']} | Score: {decision['max_severity_score']:.2f} | {inference_ms:.1f}ms"
    )
    (tw, th), _ = cv2.getTextSize(banner_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
    cv2.rectangle(annotated_frame, (10, 10), (20 + tw + 10, 48), (15, 23, 42), -1)
    cv2.rectangle(annotated_frame, (10, 10), (20 + tw + 10, 48), (148, 163, 184), 1)
    cv2.putText(
        annotated_frame,
        banner_text,
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        decision["alert_color"],
        2,
        cv2.LINE_AA,
    )
    return cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
