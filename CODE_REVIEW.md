# Code Review

## Bugs and failure risks

| # | Where | Issue | Fix | Status |
|---|---|---|---|---|
| 1 | home_view.py (video loop) | `cap.release()` ran only on normal end. Stop, a widget rerun, or an exception leaked the capture (webcam stays locked). | `try/finally` release | **Fixed** |
| 2 | video_stream.py | Upload temp file (`delete=False`) never deleted. `uploaded_file.read()` may return empty if the pointer is at the end. | `getvalue()`, delete temp file in `finally` | **Fixed** |
| 3 | video_stream.py | `cv2.VideoCapture(0)` is slow or flaky on Windows (MSMF). | Use `cv2.CAP_DSHOW` | **Fixed** |
| 4 | video_stream.py | Final fallback `"Construction.mp4"` is a relative path. The file is in `Samples/`. | Resolve from the project root | **Fixed** |
| 5 | detector.py vs safety_evaluator.py | Enabled default mismatch: `.get(key, True)` vs `rule.default_enabled`. | Use `rule.default_enabled` in both | **Fixed** |
| 6 | safety_evaluator.py | `thresholds["HIGH"]` can raise `KeyError`. Threshold order is not validated. | `.get()` with defaults, validate HIGH ≥ MEDIUM ≥ LOW | **Fixed** |
| 7 | safety_evaluator.py | Center-point association lets overlapping workers share PPE. `detected_classes` keeps the last confidence, not the max. | Best-match assignment, max confidence per class | **Fixed** |
| 8 | home_view.py (logging) | Worker IDs are per-frame indexes with no tracking. `#10{id}` gives `#1010` for worker 10. Zones are invented. Only worker 1 is logged. | `model.track(persist=True)`, log all violators | **Fixed** |
| 9 | home_view.py | FPS is `1000/inference_ms`, which is overstated. | Time the whole loop iteration | **Fixed** |

## Optimizations
- Update the header, KPI cards and footer every 5–10 frames or on change, not every frame. Use `output_format="JPEG"` for `st.image`.
- Inference: set `imgsz`, use `half=True` on GPU, skip frames or set a small buffer for webcam, and set `device` explicitly.
- Remove `time.sleep(0.01)`. Use `perf_counter`. Compute active class IDs once before the loop.
- Pin the versions in `requirements.txt`. List `torch` explicitly.
- `class.js` in the project root looks stray.

