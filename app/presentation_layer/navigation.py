"""
Navigation Component (Presentation Layer)
Implements the exact Stitch UI Left Sidebar Navigation and Top System Header Bar:
- Workspace Brand Badge (SafetyGuard AI • Hazard Detection v2.4)
- MAIN MENU + LIVE badge with:
  1. Home Dashboard (CV-01)
  2. Settings
  3. YOLOv8 Weights (v8s-pt)
  4. Incident Audit Log
- Bottom Appearance (Light / Dark) segmented switcher and MSc Research CORE Profile Card
- Top System Header Bar with EDGE ENGINE RUNNING status pill and Export Telemetry action
"""

import streamlit as st
from app.config.defaults import THEME_PRESETS
from app.config.state_manager import StateManager
from app.presentation_layer.theme import _clean_html, _is_dark_color


def render_navigation() -> str:
    """
    Render the Stitch Left Sidebar Navigation and Top System Header Bar.
    Returns the active page name ('Home' or 'Settings').
    """
    current_page = st.session_state.get("current_page", "Home")
    active_nav = st.session_state.get("active_nav_item", current_page)

    # 1. Top Workspace Brand Header + MAIN MENU + LIVE Badge
    st.sidebar.markdown(
        _clean_html("""
        <div class="sb-header">
            <div class="sb-header-left">
                <div class="sb-logo-box">
                    <span class="material-symbols-rounded filled">shield_person</span>
                </div>
                <div>
                    <div class="sb-brand-name">SafetyGuard AI</div>
                    <div class="sb-brand-tag">Hazard Detection v2.4</div>
                </div>
            </div>
        </div>

        <div class="sb-menu-header">
            <span class="sb-section-label">Main Menu</span>
            <span class="sb-live-pill">LIVE</span>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # 2. Navigation Menu Items matching Stitch UI
    if st.sidebar.button(
        "Home Dashboard   ·   CV-01",
        icon=":material/grid_view:",
        key="side_nav_home",
        type="primary" if active_nav == "Home" else "secondary",
        use_container_width=True,
    ):
        st.session_state["current_page"] = "Home"
        st.session_state["active_nav_item"] = "Home"
        st.rerun()

    if st.sidebar.button(
        "Settings",
        icon=":material/settings:",
        key="side_nav_settings",
        type="primary" if active_nav == "Settings" else "secondary",
        use_container_width=True,
    ):
        st.session_state["current_page"] = "Settings"
        st.session_state["active_nav_item"] = "Settings"
        st.rerun()

    if st.sidebar.button(
        "YOLOv8 Weights   ·   v8s-pt",
        icon=":material/deployed_code:",
        key="side_nav_weights",
        type="primary" if active_nav == "Weights" else "secondary",
        use_container_width=True,
    ):
        st.session_state["current_page"] = "Settings"
        st.session_state["active_nav_item"] = "Weights"
        st.rerun()

    if st.sidebar.button(
        "Incident Audit Log",
        icon=":material/history:",
        key="side_nav_audit",
        type="primary" if active_nav == "Audit" else "secondary",
        use_container_width=True,
    ):
        st.session_state["current_page"] = "Home"
        st.session_state["active_nav_item"] = "Audit"
        st.rerun()

    # 3. Render Top System Header Bar in Main Workspace
    st.markdown(
        _clean_html("""
        <div class="stitch-top-header">
            <div class="stitch-header-left">
                <div class="stitch-header-icon">
                    <span class="material-symbols-rounded">analytics</span>
                </div>
                <div>
                    <h1 class="stitch-header-title">AI-Based Worker Safety Monitoring Dashboard</h1>
                    <p class="stitch-header-sub">MSc Research Project (GS/COMP/377) — Integrated Computer Vision &amp; Hazard Detection System</p>
                </div>
            </div>
            <div class="stitch-header-right">
                <div class="edge-running-pill">
                    <span class="edge-dot"></span>
                    <span>EDGE ENGINE RUNNING</span>
                </div>
                <div class="notif-btn" title="Active notifications">
                    <span class="material-symbols-rounded" style="font-size:19px;">notifications</span>
                    <span class="notif-dot"></span>
                </div>
                <div class="export-pill-btn">
                    <span class="material-symbols-rounded">download</span>
                    <span>Export Telemetry</span>
                </div>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    return st.session_state.get("current_page", "Home")


def render_sidebar_footer() -> None:
    """
    Render the bottom footer of the Stitch Left Sidebar:
    - Segmented Appearance (Light / Dark) Switcher
    - MSc Research CORE Profile Card
    """
    st.sidebar.markdown("<div style='height: 140px;'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="sb-menu-header"><span class="sb-section-label">Appearance</span></div>',
        unsafe_allow_html=True,
    )

    colors = StateManager.get_theme_colors()
    is_dark = _is_dark_color(colors.get("sidebar_bg_color", "#FFFFFF"))

    def _switch_to_preset(preset_name: str) -> None:
        st.session_state["theme_preset"] = preset_name
        st.session_state["theme_preset_selector"] = preset_name
        st.session_state["theme_colors"] = dict(THEME_PRESETS[preset_name])

    col_light, col_dark = st.sidebar.columns(2)
    with col_light:
        st.button(
            "Light",
            icon=":material/light_mode:",
            key="sb_theme_light",
            type="primary" if not is_dark else "secondary",
            use_container_width=True,
            on_click=_switch_to_preset,
            args=("Modern Light (Clean Sidebar)",),
        )

    with col_dark:
        st.button(
            "Dark",
            icon=":material/dark_mode:",
            key="sb_theme_dark",
            type="primary" if is_dark else "secondary",
            use_container_width=True,
            on_click=_switch_to_preset,
            args=("Modern Dark (Obsidian Sidebar)",),
        )

    # Researcher Profile Card matching Stitch UI
    st.sidebar.markdown(
        _clean_html("""
        <div class="sb-profile-card">
            <div class="sb-profile-left">
                <div class="sb-avatar-wrap">
                    <div class="sb-avatar">
                        <span class="material-symbols-rounded">person</span>
                    </div>
                    <span class="sb-status-dot" title="System Online"></span>
                </div>
                <div>
                    <div class="sb-profile-name">
                        <span>MSc Research</span>
                        <span class="sb-core-badge">CORE</span>
                    </div>
                    <div class="sb-profile-role">GS/COMP/377 • YOLOv8s</div>
                </div>
            </div>
            <span class="material-symbols-rounded" style="font-size:18px; opacity:0.55;">more_vert</span>
        </div>
        """),
        unsafe_allow_html=True,
    )
