"""
Home View (Presentation Layer)
Implements the exact Stitch UI layout:
- Top 8:4 Grid:
  - Left (8/12): Live CCTV Feed & Inference View Card (with REC badge, FPS/RES badges,
    interactive CCTV HUD standby viewport / live OpenCV video stream, and dynamic BBox Filter footer
    reflecting all enabled PPE classes)
  - Right (4/12): STREAM CONTROLS Contextual Panel (Video Input Source, Use Local Webcam toggle,
    YOLO Confidence Threshold slider with badge, Start/Stop buttons, and Active Detection Profile)
- Bottom 4-Column KPI Grid: System Telemetry & Decision Layer Logs
- Bottom Incident Table: Real-Time Hazard Incident Stream
"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional
import streamlit as st
from app.config.defaults import (
    COMPLIANT_COLOR,
    PPE_REGISTRY,
    UI_REFRESH_EVERY_N_FRAMES,
    VIOLATION_COLOR,
    alert_style_for,
    hex_to_rgb,
)
from app.config.state_manager import StateManager
from app.data_layer.video_stream import open_video_source, release_video_source
from app.decision_layer.safety_evaluator import evaluate_frame_safety
from app.detection_layer.detector import (
    annotate_frame,
    get_active_yolo_class_ids,
    load_yolo_model,
    run_inference,
)


def _rgba(hex_color: str, alpha: float) -> str:
    """Convert '#RRGGBB' into a CSS rgba() string."""
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def _html_fragment(markup: str) -> str:
    """Normalize generated HTML by stripping line-leading whitespace so Markdown never treats it as an indented code block."""
    return "\n".join(
        line.strip() for line in markup.strip().splitlines() if line.strip()
    )


def _render_feed_header_html(fps: float = 54.2, res: str = "1920Ã—1080") -> str:
    """Return HTML for the Live CCTV Feed card header."""
    return _html_fragment(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; padding-bottom:12px; margin-bottom:12px; border-bottom:1px solid rgba(148,163,184,0.22);">
        <div style="display:flex; align-items:center; gap:9px; flex-wrap:wrap;">
            <span class="material-symbols-rounded" style="color:#2563EB; font-size:21px;">videocam</span>
            <span style="font-family:'Plus Jakarta Sans',sans-serif; font-size:14px; font-weight:700;">Live CCTV Feed &amp; Inference View</span>
            <span style="display:inline-flex; align-items:center; gap:5px; padding:2px 8px; border-radius:9999px; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; background:rgba(37,99,235,0.12); color:#2563EB; border:1px solid rgba(37,99,235,0.30);">
                <span style="width:6px; height:6px; border-radius:50%; background:#3B82F6; display:inline-block;"></span> REC
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="padding:3px 8px; border-radius:6px; background:rgba(148,163,184,0.12); border:1px solid rgba(148,163,184,0.25); font-family:'JetBrains Mono',monospace; font-size:11px;">
                <span style="opacity:0.6;">FPS:</span> <strong style="color:#2563EB;">{fps:.1f}</strong>
            </div>
            <div style="padding:3px 8px; border-radius:6px; background:rgba(148,163,184,0.12); border:1px solid rgba(148,163,184,0.25); font-family:'JetBrains Mono',monospace; font-size:11px;">
                <span style="opacity:0.6;">RES:</span> <strong>{res}</strong>
            </div>
            <span class="material-symbols-rounded" style="font-size:19px; opacity:0.55;">fullscreen</span>
        </div>
    </div>
    """)


def _render_standby_cctv_hud_html(enabled_ppe: Dict[str, bool]) -> str:
    """Return the modern 2/3-tone blue simulated 16:9 CCTV HUD viewport dynamically showing enabled PPE classes."""
    helmet_box = (
        """
        <div style="position:absolute; top:5%; left:16%; width:68%; height:16%; border:1px solid rgba(59,130,246,0.85); background:rgba(37,99,235,0.20); border-radius:2px;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:8px; color:#FFFFFF; background:#2563EB; padding:1px 3px; position:absolute; bottom:2px; right:2px; border-radius:2px;">Helmet 0.97</span>
        </div>
        """
        if enabled_ppe.get("helmet", True)
        else ""
    )
    mask_box = (
        """
        <div style="position:absolute; top:23%; left:22%; width:56%; height:10%; border:1px solid rgba(56,189,248,0.85); background:rgba(56,189,248,0.20); border-radius:2px;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:8px; color:#FFFFFF; background:#0284C7; padding:1px 3px; position:absolute; bottom:1px; right:2px; border-radius:2px;">Mask 0.91</span>
        </div>
        """
        if enabled_ppe.get("mask", True)
        else ""
    )
    vest_box = (
        """
        <div style="position:absolute; top:36%; left:8%; width:84%; height:32%; border:1px solid rgba(79,70,229,0.85); background:rgba(79,70,229,0.20); border-radius:2px;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:8px; color:#FFFFFF; background:#4F46E5; padding:1px 3px; position:absolute; bottom:2px; right:2px; border-radius:2px;">Vest 0.92</span>
        </div>
        """
        if enabled_ppe.get("vest", True)
        else ""
    )
    gloves_box = (
        """
        <div style="position:absolute; top:70%; left:6%; width:32%; height:16%; border:1px solid rgba(14,165,233,0.85); background:rgba(14,165,233,0.20); border-radius:2px;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:8px; color:#FFFFFF; background:#0EA5E9; padding:1px 3px; position:absolute; bottom:2px; right:2px; border-radius:2px;">Gloves 0.89</span>
        </div>
        """
        if enabled_ppe.get("gloves", True)
        else ""
    )

    return _html_fragment(f"""
    <div style="position:relative; width:100%; height:410px; background:linear-gradient(180deg, #0F172A 0%, #1E293B 50%, #0F172A 100%); border-radius:12px; overflow:hidden; user-select:none; border:1px solid #1E293B;">
        <div class="cctv-scanline" style="position:absolute; inset:0; opacity:0.35; pointer-events:none;"></div>

        <!-- Top-Left HUD Alert Banner -->
        <div style="position:absolute; top:12px; left:12px; z-index:10; display:flex; align-items:center; gap:8px; background:rgba(15,23,42,0.92); padding:6px 12px; border-radius:8px; border:1px solid rgba(59,130,246,0.35); color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:11px;">
            <span style="display:inline-flex; align-items:center; gap:5px; font-weight:700; color:#60A5FA;">
                <span style="width:7px; height:7px; border-radius:50%; background:#3B82F6; display:inline-block;"></span>
                MEDIUM ALERT
            </span>
            <span style="opacity:0.4;">|</span>
            <span>Score: <strong>0.40</strong></span>
            <span style="opacity:0.4;">|</span>
            <span>Inference: <strong style="color:#38BDF8;">18.4ms</strong></span>
        </div>

        <!-- Top-Right Camera Metadata -->
        <div style="position:absolute; top:12px; right:12px; z-index:10; display:flex; align-items:center; gap:7px; background:rgba(15,23,42,0.85); padding:5px 10px; border-radius:6px; border:1px solid rgba(148,163,184,0.28); color:#CBD5E1; font-family:'JetBrains Mono',monospace; font-size:10px;">
            <span>CAM-04 [BAY_SOUTH_ZONE]</span>
            <span style="width:6px; height:6px; border-radius:50%; background:#38BDF8; display:inline-block;"></span>
        </div>

        <!-- Simulated Worker 1: Compliant (Shows all active PPE sub-boxes) -->
        <div style="position:absolute; top:22%; left:14%; width:17%; height:56%; border:2px solid #0EA5E9; background:rgba(14,165,233,0.12); border-radius:3px;">
            <div style="position:absolute; top:-22px; left:-2px; background:#0284C7; color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; padding:2px 6px; border-radius:3px 3px 0 0; white-space:nowrap;">
                âœ“ ID: #104 COMPLIANT 0.94
            </div>
            {helmet_box}
            {mask_box}
            {vest_box}
            {gloves_box}
        </div>

        <!-- Simulated Worker 2: Hazard No Helmet / Missing Gloves -->
        <div style="position:absolute; top:24%; left:40%; width:18%; height:58%; border:2px solid #2563EB; background:rgba(37,99,235,0.14); box-shadow:0 0 16px rgba(37,99,235,0.30); border-radius:3px;">
            <div style="position:absolute; top:-22px; left:-2px; background:#1D4ED8; color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; padding:2px 6px; border-radius:3px 3px 0 0; white-space:nowrap;">
                â–² ID: #107 HAZARD: NO HELMET
            </div>
            <div style="position:absolute; top:5%; left:16%; width:68%; height:18%; border:2px dashed #60A5FA; background:rgba(37,99,235,0.28); border-radius:2px;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:8px; font-weight:700; color:#FFFFFF; background:#2563EB; padding:1px 3px; position:absolute; bottom:2px; right:2px; border-radius:2px;">NO HELMET (0.88)</span>
            </div>
            <div style="position:absolute; top:28%; left:10%; width:80%; height:36%; border:1px solid rgba(79,70,229,0.85); background:rgba(79,70,229,0.20); border-radius:2px;">
                <span style="font-family:'JetBrains Mono',monospace; font-size:8px; color:#FFFFFF; background:#4F46E5; padding:1px 3px; position:absolute; bottom:2px; right:2px; border-radius:2px;">Vest 0.89</span>
            </div>
        </div>

        <!-- Simulated Worker 3: Compliant -->
        <div style="position:absolute; top:26%; left:66%; width:15%; height:54%; border:2px solid #0EA5E9; background:rgba(14,165,233,0.10); border-radius:3px;">
            <div style="position:absolute; top:-22px; left:-2px; background:#0284C7; color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; padding:2px 6px; border-radius:3px 3px 0 0; white-space:nowrap;">
                âœ“ ID: #112 COMPLIANT 0.91
            </div>
        </div>

        <!-- Simulated Worker 4: Background Compliant -->
        <div style="position:absolute; top:32%; left:85%; width:11%; height:38%; border:2px solid rgba(14,165,233,0.8); background:rgba(14,165,233,0.10); border-radius:3px;">
            <div style="position:absolute; top:-18px; left:-2px; background:#0284C7; color:#FFFFFF; font-family:'JetBrains Mono',monospace; font-size:8px; padding:1px 4px; border-radius:3px 3px 0 0; white-space:nowrap;">
                ID: #118 PPE OK 0.84
            </div>
        </div>

        <!-- Bottom Video HUD Bar -->
        <div style="position:absolute; bottom:12px; left:12px; right:12px; z-index:10; display:flex; align-items:center; justify-content:space-between; background:rgba(15,23,42,0.92); padding:7px 14px; border-radius:8px; border:1px solid rgba(148,163,184,0.25); color:#CBD5E1; font-family:'JetBrains Mono',monospace; font-size:11px;">
            <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                <span style="color:#38BDF8; font-weight:600;">((â€¢)) YOLOv8s In-Memory Stream</span>
                <span style="opacity:0.4;">|</span>
                <span>Frame: 14,892</span>
                <span style="opacity:0.4;">|</span>
                <span>Decisions/Sec: 32</span>
            </div>
            <div style="color:#93C5FD; font-weight:600;">
                Zone 3: Monitored Industrial Bay
            </div>
        </div>
    </div>
    """)


def _render_bbox_footer_html(
    ppe_counts: Optional[Dict[str, int]] = None,
    enabled_ppe: Optional[Dict[str, bool]] = None,
    violation_count: int = 1,
) -> str:
    """
    Return HTML for the BBox Filter footer below the video viewport.
    Dynamically renders pills for all enabled PPE classes in PPE_REGISTRY!
    """
    default_standby_counts = {"helmet": 3, "vest": 4, "gloves": 3, "mask": 2}
    counts = ppe_counts if ppe_counts is not None else default_standby_counts
    enabled = (
        enabled_ppe
        if enabled_ppe is not None
        else {k: r.default_enabled for k, r in PPE_REGISTRY.items()}
    )

    pills_html = ""
    for key, rule in PPE_REGISTRY.items():
        if enabled.get(key, rule.default_enabled):
            c = counts.get(key, 0)
            pills_html += f"""
            <span style="display:inline-flex; align-items:center; gap:5px; padding:2px 8px; border-radius:5px; background:rgba(37,99,235,0.10); color:#2563EB; border:1px solid rgba(37,99,235,0.28); font-family:'JetBrains Mono',monospace; font-size:11px;">
                <span style="width:6px; height:6px; border-radius:50%; background:#3B82F6;"></span> {rule.label} ({c})
            </span>
            """

    return _html_fragment(f"""
    <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px; padding-top:12px; margin-top:10px; border-top:1px solid rgba(148,163,184,0.22); font-size:12px;">
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
            <span style="opacity:0.65; font-weight:500;">BBox Filter:</span>
            {pills_html}
            <span style="display:inline-flex; align-items:center; gap:5px; padding:2px 8px; border-radius:5px; background:{_rgba(VIOLATION_COLOR, 0.14)}; color:{VIOLATION_COLOR}; border:1px solid {_rgba(VIOLATION_COLOR, 0.35)}; font-family:'JetBrains Mono',monospace; font-size:11px;">
                <span style="width:6px; height:6px; border-radius:50%; background:{VIOLATION_COLOR};"></span> Violation ({violation_count})
            </span>
        </div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">
            Synced with TensorRT FP16 Engine
        </div>
    </div>
    """)


def _render_kpi_grid_html(
    alert_level: str = "MEDIUM ALERT",
    compliance_pct: float = 75.0,
    worker_count: int = 4,
    compliant_count: int = 3,
    violating_count: int = 1,
    max_score: float = 0.40,
    high_threshold: float = 0.60,
    latency_ms: float = 18.4,
) -> str:
    """Render the 4-column KPI Grid HTML (red = error, amber = warning, green = safe)."""
    style = alert_style_for(alert_level)
    alert_color = style["hex"]
    alert_bg = _rgba(alert_color, 0.14)
    alert_icon = style["icon"]
    ok_color = COMPLIANT_COLOR
    haz_color = VIOLATION_COLOR

    return _html_fragment(f"""
    <div style="margin-top:22px; margin-bottom:22px;">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="material-symbols-rounded" style="font-size:18px; opacity:0.65;">speed</span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; opacity:0.7;">System Telemetry &amp; Decision Layer Logs</span>
            </div>
            <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">Sample Frequency: 60Hz</span>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:16px;">
            <!-- Card 1: SYSTEM ALERT STATUS -->
            <div class="kpi-card" style="border-color:{alert_color}55;">
                <div class="kpi-card-top">
                    <span class="kpi-label">System Alert Status</span>
                    <div class="kpi-icon-box" style="background:{alert_bg};">
                        <span class="material-symbols-rounded" style="font-size:18px; color:{alert_color};">{alert_icon}</span>
                    </div>
                </div>
                <div class="kpi-value-row">
                    <span style="font-family:'Plus Jakarta Sans',sans-serif; font-size:19px; font-weight:800; color:{alert_color};">{alert_level}</span>
                </div>
                <div class="kpi-footer">
                    <span>Safety Compliance:</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-weight:700; color:{alert_color};">{compliance_pct:.1f}%</span>
                </div>
            </div>

            <!-- Card 2: ACTIVE WORKERS DETECTED -->
            <div class="kpi-card">
                <div class="kpi-card-top">
                    <span class="kpi-label">Active Workers Detected</span>
                    <div class="kpi-icon-box" style="background:rgba(37,99,235,0.10);">
                        <span class="material-symbols-rounded" style="font-size:18px; color:#2563EB;">groups</span>
                    </div>
                </div>
                <div class="kpi-value-row">
                    <span style="font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:700;">{worker_count}</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">person instances</span>
                </div>
                <div class="kpi-footer">
                    <span>Compliant / Violating:</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-weight:600;">
                        <span style="color:{ok_color};">{compliant_count} OK</span> / <span style="color:{haz_color}; font-weight:700;">{violating_count} HAZ</span>
                    </span>
                </div>
            </div>

            <!-- Card 3: MAX SEVERITY SCORE -->
            <div class="kpi-card">
                <div class="kpi-card-top">
                    <span class="kpi-label">Max Severity Score</span>
                    <div class="kpi-icon-box" style="background:{alert_bg};">
                        <span class="material-symbols-rounded" style="font-size:18px; color:{alert_color};">speed</span>
                    </div>
                </div>
                <div class="kpi-value-row">
                    <span style="font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:700; color:{alert_color};">{max_score:.2f}</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">/ 1.00 index</span>
                </div>
                <div class="kpi-footer">
                    <span>Escalation Trigger:</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-weight:600;">&gt; {high_threshold:.2f} (High Alert)</span>
                </div>
            </div>

            <!-- Card 4: INFERENCE LATENCY -->
            <div class="kpi-card">
                <div class="kpi-card-top">
                    <span class="kpi-label">Inference Latency</span>
                    <div class="kpi-icon-box" style="background:rgba(14,165,233,0.12);">
                        <span class="material-symbols-rounded" style="font-size:18px; color:#0284C7;">timer</span>
                    </div>
                </div>
                <div class="kpi-value-row">
                    <span style="font-family:'JetBrains Mono',monospace; font-size:28px; font-weight:700; color:#0284C7;">{latency_ms:.1f}</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">ms / frame</span>
                </div>
                <div class="kpi-footer">
                    <span>Hardware Profile:</span>
                    <span style="font-family:'JetBrains Mono',monospace; font-weight:600;">CUDA TensorRT FP16</span>
                </div>
            </div>
        </div>
    </div>
    """)


def _render_incident_table_html(logs: List[Dict[str, Any]]) -> str:
    """Render the Real-Time Hazard Incident Stream table HTML in 2/3-tone blue palette."""
    rows_html = ""
    for item in logs[:6]:
        if item.get("is_violation"):
            badge_html = f"""
            <span style="display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:9999px; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; background:{_rgba(VIOLATION_COLOR, 0.14)}; color:{VIOLATION_COLOR}; border:1px solid {_rgba(VIOLATION_COLOR, 0.35)};">
                <span class="material-symbols-rounded" style="font-size:13px;">error</span> {item['status']}
            </span>
            """
        else:
            badge_html = f"""
            <span style="display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:9999px; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; background:{_rgba(COMPLIANT_COLOR, 0.12)}; color:{COMPLIANT_COLOR}; border:1px solid {_rgba(COMPLIANT_COLOR, 0.30)};">
                <span class="material-symbols-rounded" style="font-size:13px;">check_circle</span> {item['status']}
            </span>
            """

        rows_html += f"""
        <tr>
            <td style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.65;">{item['timestamp']}</td>
            <td style="font-family:'JetBrains Mono',monospace; font-weight:700;">{item['worker_id']}</td>
            <td style="font-weight:500;">{item['zone']}</td>
            <td>{badge_html}</td>
            <td style="font-family:'JetBrains Mono',monospace;">{item['confidence']:.2f}</td>
            <td style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.75;">{item['action']}</td>
        </tr>
        """

    return _html_fragment(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:12px; margin-bottom:6px; border-bottom:1px solid rgba(148,163,184,0.22);">
        <div style="display:flex; align-items:center; gap:8px;">
            <span class="material-symbols-rounded" style="color:#4F46E5; font-size:20px;">receipt_long</span>
            <span style="font-family:'Plus Jakarta Sans',sans-serif; font-size:14px; font-weight:700;">Real-Time Hazard Incident Stream</span>
        </div>
        <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.55;">Auto-refresh: 1s</span>
    </div>
    <div style="overflow-x:auto;">
        <table class="incident-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Tracking ID</th>
                    <th>Location Zone</th>
                    <th>Detected Status</th>
                    <th>Confidence</th>
                    <th>Action Taken</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """)


def render_home_view() -> None:
    """Render the Stitch Home Dashboard view."""
    enabled_map = StateManager.get_enabled_classes()

    # =========================================================
    # TOP 8:4 ASYMMETRIC GRID (Feed Left + Stream Controls Right)
    # =========================================================
    col_feed, col_controls = st.columns([2, 1], gap="medium")

    with col_feed:
        with st.container(border=True):
            feed_header_placeholder = st.empty()
            feed_header_placeholder.markdown(
                _render_feed_header_html(fps=54.2, res="1920Ã—1080"),
                unsafe_allow_html=True,
            )

            video_placeholder = st.empty()
            video_placeholder.markdown(
                _render_standby_cctv_hud_html(enabled_ppe=enabled_map),
                unsafe_allow_html=True,
            )

            feed_footer_placeholder = st.empty()
            feed_footer_placeholder.markdown(
                _render_bbox_footer_html(
                    ppe_counts=None,
                    enabled_ppe=enabled_map,
                    violation_count=1,
                ),
                unsafe_allow_html=True,
            )

    with col_controls:
        with st.container(border=True):
            # Stream Controls Panel Header
            st.markdown(
                _html_fragment("""
                <div style="display:flex; align-items:center; justify-content:space-between; padding-bottom:12px; margin-bottom:12px; border-bottom:1px solid rgba(148,163,184,0.22);">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:28px; height:28px; border-radius:7px; background:rgba(79,70,229,0.12); display:flex; align-items:center; justify-content:center;">
                            <span class="material-symbols-rounded" style="color:#4F46E5; font-size:18px;">tune</span>
                        </div>
                        <span style="font-family:'Plus Jakarta Sans',sans-serif; font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.06em;">Stream Controls</span>
                    </div>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; padding:3px 8px; border-radius:5px; background:rgba(148,163,184,0.14); opacity:0.75;">DEVICE: GPU:0</span>
                </div>
                """),
                unsafe_allow_html=True,
            )

            # 1. Video Input Source
            st.markdown(
                '<div style="font-size:12px; font-weight:600; margin-bottom:4px;">Video Input Source</div>',
                unsafe_allow_html=True,
            )
            uploaded_file = st.file_uploader(
                "Upload Industrial Video MP4/AVI",
                type=["mp4", "avi", "mov"],
                help="MAX 500MB â€¢ H.264 / HEVC",
                label_visibility="collapsed",
            )

            # 2. Use Local Webcam Toggle Box
            with st.container(border=True):
                wc_left, wc_right = st.columns([3, 1], vertical_alignment="center")
                with wc_left:
                    st.markdown(
                        _html_fragment("""
                        <div style="display:flex; align-items:center; gap:9px;">
                            <div style="width:28px; height:28px; border-radius:7px; border:1px solid rgba(148,163,184,0.28); display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                                <span class="material-symbols-rounded" style="font-size:16px; opacity:0.75;">camera</span>
                            </div>
                            <div>
                                <div style="font-size:12px; font-weight:600; line-height:1.2;">Use Local Webcam</div>
                                <div style="font-family:'JetBrains Mono',monospace; font-size:10px; opacity:0.6;">Hardware V4L2 (Source 0)</div>
                            </div>
                        </div>
                        """),
                        unsafe_allow_html=True,
                    )
                with wc_right:
                    use_webcam = st.toggle(
                        "Webcam",
                        value=False,
                        label_visibility="collapsed",
                    )

            # 3. YOLO Confidence Threshold Slider Card
            current_conf = StateManager.get_confidence()
            if "home_slider_conf" not in st.session_state:
                st.session_state["home_slider_conf"] = current_conf

            def _on_home_conf_change() -> None:
                StateManager.set_confidence(st.session_state["home_slider_conf"])

            with st.container(border=True):
                st.markdown(
                    _html_fragment(f"""
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
                        <span style="display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;">
                            <span class="material-symbols-rounded" style="color:#4F46E5; font-size:17px;">tune</span>
                            YOLO Confidence Threshold
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700; color:#4F46E5; background:rgba(79,70,229,0.10); padding:2px 8px; border-radius:5px; border:1px solid rgba(79,70,229,0.25);">{current_conf:.2f}</span>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )
                confidence_threshold = st.slider(
                    "YOLO Confidence Threshold",
                    min_value=0.05,
                    max_value=0.95,
                    step=0.05,
                    key="home_slider_conf",
                    on_change=_on_home_conf_change,
                    label_visibility="collapsed",
                )
                st.markdown(
                    _html_fragment("""
                    <div class="slider-custom-ticks">
                        <span>0.10 (High Recall)</span>
                        <span>0.50 (Balanced)</span>
                        <span>0.95 (High Precision)</span>
                    </div>
                    """),
                    unsafe_allow_html=True,
                )

            # 4. Action Buttons (Start / Stop Monitoring)
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                run_processing = st.button(
                    "Start Monitoring",
                    icon=":material/play_arrow:",
                    type="primary",
                    use_container_width=True,
                )
            with btn_col2:
                stop_processing = st.button(
                    "Stop Monitoring",
                    icon=":material/stop:",
                    use_container_width=True,
                )

            # 5. Active Detection Profile Card
            weights_map = StateManager.get_weights()
            active_count = sum(
                1 for k, r in PPE_REGISTRY.items() if enabled_map.get(k, r.default_enabled)
            )

            dot_colors = {
                "helmet": "#2563EB",
                "vest": "#4F46E5",
                "gloves": "#0284C7",
                "mask": "#38BDF8",
            }
            priority_labels = {
                "helmet": "Critical",
                "vest": "High",
                "gloves": "Moderate",
                "mask": "Moderate",
            }

            profile_rows = ""
            for key, rule in PPE_REGISTRY.items():
                is_on = enabled_map.get(key, rule.default_enabled)
                w_val = weights_map.get(key, rule.default_weight)
                dot_c = dot_colors.get(key, "#2563EB") if is_on else "#94A3B8"
                p_label = priority_labels.get(key, "Normal") if is_on else "Disabled"
                profile_rows += f"""
                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:4px; padding:5px 0; font-size:12px; opacity:{'1.0' if is_on else '0.45'};">
                    <span style="display:inline-flex; align-items:center; gap:7px; font-weight:500;">
                        <span style="width:7px; height:7px; border-radius:50%; background:{dot_c}; display:inline-block; flex-shrink:0;"></span>
                        {rule.label}
                    </span>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:11px; opacity:0.75;">Weight: {w_val:.2f} ({p_label})</span>
                </div>
                """

            st.markdown(
                _html_fragment(f"""
                <div style="border:1px solid rgba(148,163,184,0.25); border-radius:12px; overflow:hidden; margin-top:4px;">
                    <div style="padding:9px 12px; background:rgba(148,163,184,0.10); display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(148,163,184,0.18);">
                        <span style="display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600;">
                            <span class="material-symbols-rounded" style="font-size:17px; opacity:0.7;">list_alt</span>
                            Active Detection Profile
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace; font-size:10px; opacity:0.65;">{active_count} Classes Active</span>
                    </div>
                    <div style="padding:10px 12px;">
                        {profile_rows}
                        <div style="margin-top:8px; padding-top:8px; border-top:1px solid rgba(148,163,184,0.18); display:flex; align-items:center; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:11px;">
                            <span style="opacity:0.65;">Decision Logic:</span>
                            <span style="color:#4F46E5; font-weight:600;">Weighted Severity Matrix</span>
                        </div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True,
            )

    # =========================================================
    # BOTTOM 4-COLUMN KPI GRID & INCIDENT STREAM TABLE
    # =========================================================
    thresholds = StateManager.get_thresholds()
    kpi_placeholder = st.empty()
    kpi_placeholder.markdown(
        _render_kpi_grid_html(
            alert_level="MEDIUM ALERT",
            compliance_pct=75.0,
            worker_count=4,
            compliant_count=3,
            violating_count=1,
            max_score=0.40,
            high_threshold=thresholds.get("HIGH", 0.60),
            latency_ms=18.4,
        ),
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        incident_table_placeholder = st.empty()
        incident_table_placeholder.markdown(
            _render_incident_table_html(StateManager.get_incident_logs()),
            unsafe_allow_html=True,
        )

    # =========================================================
    # REAL-TIME VIDEO PROCESSING EXECUTION
    # =========================================================
    if stop_processing:
        st.toast("Monitoring stopped.", icon=":material/pause_circle:")
        return

    if run_processing:
        try:
            model = load_yolo_model(st.session_state["model_path"])
        except Exception as exc:
            st.error(f"Failed to load YOLO model: {exc}", icon=":material/error:")
            return

        cap, temp_path = open_video_source(
            use_webcam=use_webcam, uploaded_file=uploaded_file
        )

        if not cap.isOpened():
            release_video_source(cap, temp_path)
            st.error(
                "Could not open video source. Please check file path or webcam connection.",
                icon=":material/error:",
            )
            return

        weights = StateManager.get_weights()
        enabled_ppe = StateManager.get_enabled_classes()
        active_classes = get_active_yolo_class_ids(enabled_ppe)  # compute once per run
        refresh_every = max(1, UI_REFRESH_EVERY_N_FRAMES)
        frame_idx = 0
        last_tick = time.perf_counter()
        live_fps = 0.0

        try:
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    st.info("End of video stream reached.", icon=":material/info:")
                    break

                frame_idx += 1
                h, w = frame.shape[:2]

                # Run YOLO Inference (tracking gives workers stable IDs across frames)
                result, detections, inference_ms = run_inference(
                    model=model,
                    frame=frame,
                    confidence_threshold=confidence_threshold,
                    enabled_ppe=enabled_ppe,
                    active_classes=active_classes,
                    track=True,
                    reset_tracker=(frame_idx == 1),
                )

                # Evaluate Frame via Decision Layer
                decision = evaluate_frame_safety(
                    detections=detections,
                    weights=weights,
                    enabled_ppe=enabled_ppe,
                    thresholds=thresholds,
                )

                # End-to-end FPS (decode + inference + render), smoothed
                now_tick = time.perf_counter()
                inst_fps = 1.0 / max(now_tick - last_tick, 1e-6)
                last_tick = now_tick
                live_fps = inst_fps if live_fps == 0.0 else 0.9 * live_fps + 0.1 * inst_fps

                # Update Annotated Video Frame (every frame)
                annotated_frame_rgb = annotate_frame(result, decision, inference_ms)
                video_placeholder.image(
                    annotated_frame_rgb,
                    channels="RGB",
                    width="stretch",
                    output_format="JPEG",
                )

                # Heavier HTML widgets are refreshed periodically, not every frame
                if frame_idx % refresh_every == 1 or refresh_every == 1:
                    feed_header_placeholder.markdown(
                        _render_feed_header_html(fps=round(live_fps, 1), res=f"{w}Ã—{h}"),
                        unsafe_allow_html=True,
                    )
                    feed_footer_placeholder.markdown(
                        _render_bbox_footer_html(
                            ppe_counts=decision.get("ppe_counts", {}),
                            enabled_ppe=enabled_ppe,
                            violation_count=decision.get("violating_count", 0),
                        ),
                        unsafe_allow_html=True,
                    )
                    kpi_placeholder.markdown(
                        _render_kpi_grid_html(
                            alert_level=decision["alert_level"],
                            compliance_pct=decision["compliance_pct"],
                            worker_count=decision["worker_count"],
                            compliant_count=decision["compliant_count"],
                            violating_count=decision["violating_count"],
                            max_score=decision["max_severity_score"],
                            high_threshold=thresholds.get("HIGH", 0.60),
                            latency_ms=inference_ms,
                        ),
                        unsafe_allow_html=True,
                    )

                # Log periodic worker status into Real-Time Hazard Incident Stream
                if frame_idx % 12 == 1 and decision["worker_reports"]:
                    now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    reports = decision["worker_reports"]
                    violators = [r for r in reports if r["violations"]]
                    # Log every violating worker (capped); otherwise one compliant sample
                    to_log = violators[:3] if violators else reports[:1]
                    # Insert in reverse so the first worker ends up on top
                    for rep in reversed(to_log):
                        has_v = len(rep["violations"]) > 0
                        StateManager.add_incident_log(
                            {
                                "timestamp": now_str,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "worker_id": f"#{rep['worker_id']}",
                                "zone": "Live Feed",
                                "status": ", ".join(rep["violations"])
                                if has_v
                                else "Compliant (Full PPE)",
                                "is_violation": has_v,
                                "confidence": rep.get("conf", 0.90),
                                "action": "Audio Hooter Triggered" if has_v else "Logged",
                            }
                        )
                    incident_table_placeholder.markdown(
                        _render_incident_table_html(StateManager.get_incident_logs()),
                        unsafe_allow_html=True,
                    )

        finally:
            release_video_source(cap, temp_path)
