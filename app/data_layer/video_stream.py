"""
Video Stream Handler (Data / Input Layer)
Manages video capture from uploaded files, local webcams, or fallback sample videos.
"""

import os
import tempfile
from typing import Optional
import cv2
from app.config.defaults import DEFAULT_SAMPLE_VIDEOS


def get_video_capture(
    use_webcam: bool = False,
    uploaded_file: Optional[object] = None,
    fallback_path: Optional[str] = None,
) -> cv2.VideoCapture:
    """
    Create and return an OpenCV VideoCapture object based on user selection.
    """
    if use_webcam:
        return cv2.VideoCapture(0)

    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        try:
            tfile.write(uploaded_file.read())
        finally:
            # Windows keeps the file locked while NamedTemporaryFile is open.
            tfile.close()
        return cv2.VideoCapture(tfile.name)

    if fallback_path and os.path.exists(fallback_path):
        return cv2.VideoCapture(fallback_path)

    for candidate in DEFAULT_SAMPLE_VIDEOS:
        if os.path.exists(candidate):
            return cv2.VideoCapture(candidate)

    # Final fallback matching original Dashboard1.py
    return cv2.VideoCapture("Construction.mp4")
