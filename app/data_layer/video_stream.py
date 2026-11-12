"""
Video Stream Handler (Data / Input Layer)
Manages video capture from uploaded files, local webcams, or fallback sample videos.
"""

import os
import tempfile
from typing import Optional, Tuple
import cv2
from app.config.defaults import DEFAULT_SAMPLE_VIDEOS, PROJECT_ROOT


def open_video_source(
    use_webcam: bool = False,
    uploaded_file: Optional[object] = None,
    fallback_path: Optional[str] = None,
) -> Tuple[cv2.VideoCapture, Optional[str]]:
    """
    Open a video source and return (capture, temp_path).

    temp_path is a temporary file created for an uploaded video (else None).
    The caller must pass both to `release_video_source` when finished so the
    capture is released and the temp file is deleted.
    """
    if use_webcam:
        # DirectShow opens much faster / more reliably than MSMF on Windows.
        if os.name == "nt":
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # keep latency low for live feeds
        return cap, None

    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        try:
            # getvalue() is independent of the stream read pointer.
            data = (
                uploaded_file.getvalue()
                if hasattr(uploaded_file, "getvalue")
                else uploaded_file.read()
            )
            tfile.write(data)
        finally:
            # Windows keeps the file locked while NamedTemporaryFile is open.
            tfile.close()
        return cv2.VideoCapture(tfile.name), tfile.name

    if fallback_path and os.path.exists(fallback_path):
        return cv2.VideoCapture(fallback_path), None

    for candidate in DEFAULT_SAMPLE_VIDEOS:
        if os.path.exists(candidate):
            return cv2.VideoCapture(candidate), None

    # Final fallback matching original Dashboard1.py (resolved from the project root)
    return cv2.VideoCapture(str(PROJECT_ROOT / "Samples" / "Construction.mp4")), None


def release_video_source(
    cap: Optional[cv2.VideoCapture], temp_path: Optional[str] = None
) -> None:
    """Release the capture and delete any temporary upload file."""
    if cap is not None:
        cap.release()
    if temp_path:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def get_video_capture(
    use_webcam: bool = False,
    uploaded_file: Optional[object] = None,
    fallback_path: Optional[str] = None,
) -> cv2.VideoCapture:
    """
    Backward-compatible wrapper returning only the capture.
    Note: temp files for uploads are not cleaned up; prefer `open_video_source`.
    """
    cap, _ = open_video_source(use_webcam, uploaded_file, fallback_path)
    return cap
