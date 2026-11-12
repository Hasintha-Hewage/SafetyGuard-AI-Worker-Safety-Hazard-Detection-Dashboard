"""
Settings View (Presentation Layer)
Styled to match the Stitch UI design system with clean bordered cards,
monospace telemetry badges, and Google Material Symbols:
1. PPE Detection Classes (Toggle On / Off for Safety Helmet, Safety Vest, Gloves, Face Mask)
2. YOLO Confidence Score Threshold (Synchronized Slider + Number Input)
3. Decision Layer PPE Severity Weights (Synchronized Slider + Number Input)
4. Audit Log Storage (Save toggle + CSV / SQL selector)
5. UI Theme & Color Customization (Presets + Live Color Pickers)
"""

import streamlit as st
from app.config.defaults import PPE_REGISTRY, THEME_PRESETS
from app.config.state_manager import StateManager
from app.data_layer.audit_store import AUDIT_BACKENDS, validate_audit_dir
from app.presentation_layer.components import synced_slider_and_number
from app.presentation_layer.theme import _clean_html, render_section_header


def render_settings_view() -> None:
    """Render the Stitch-styled Settings & Configuration page."""
    top_left, top_right = st.columns([4, 1])
    with top_left:
        render_section_header(
            icon_name="settings",
            title="System Settings & Decision Layer Configuration",
            subtitle="Configure AI Inference Confidence, PPE Detection Classes, Weighted Severity Matrix, and UI Theme Colors.",
        )
    with top_right:
        if st.button(
            "Reset All to Defaults",
            icon=":material/restart_alt:",
            use_container_width=True,
        ):
            StateManager.reset_to_defaults()
            st.rerun()

    # ---------------------------------------------------------
    # SECTION 1: DETECTION CLASSES TOGGLE BUTTONS
    # ---------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon_name="verified_user",
            title="1. PPE Detection Classes (Toggle On / Off)",
            subtitle="Enable or disable specific PPE classes for both YOLOv8 detection and Decision Layer evaluation.",
        )

        enabled_classes = StateManager.get_enabled_classes()
        cols = st.columns(len(PPE_REGISTRY))

        for idx, (key, rule) in enumerate(PPE_REGISTRY.items()):
            with cols[idx]:
                with st.container(border=True):
                    current_state = enabled_classes.get(key, rule.default_enabled)
                    status_icon = "check_circle" if current_state else "cancel"
                    status_text = "Active" if current_state else "Disabled"
                    badge_color = "#2563EB" if current_state else "#64748B"
                    badge_bg = (
                        "rgba(37,99,235,0.12)"
                        if current_state
                        else "rgba(148,163,184,0.14)"
                    )

                    st.markdown(
                        _clean_html(f"""
                        <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
                            <div style="display:flex; align-items:center; gap:7px;">
                                <span class="material-symbols-rounded" style="font-size:19px; color:#4F46E5;">{rule.icon}</span>
                                <span style="font-weight:700; font-size:13px;">{rule.label}</span>
                            </div>
                            <span style="display:inline-flex; align-items:center; gap:3px; padding:2px 6px; border-radius:9999px; font-family:'JetBrains Mono',monospace; font-size:10px; font-weight:700; background:{badge_bg}; color:{badge_color};">
                                <span class="material-symbols-rounded" style="font-size:12px;">{status_icon}</span> {status_text}
                            </span>
                        </div>
                        """),
                        unsafe_allow_html=True,
                    )

                    toggle_key = f"toggle_ppe_{key}"
                    new_state = st.toggle(
                        f"Enable {rule.label}",
                        value=current_state,
                        key=toggle_key,
                        help=rule.description,
                    )
                    if new_state != current_state:
                        StateManager.set_class_enabled(key, new_state)
                        st.rerun()

    # ---------------------------------------------------------
    # SECTION 2: CONFIDENCE SCORE (SLIDER + NUMBER FIELD)
    # ---------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon_name="tune",
            title="2. YOLO Confidence Score Threshold",
            subtitle="Adjust the minimum confidence score required for object detections using either the slider or the number field.",
        )

        synced_slider_and_number(
            label="YOLO Confidence Score",
            key_prefix="conf",
            current_value=StateManager.get_confidence(),
            min_value=0.05,
            max_value=0.95,
            step=0.05,
            on_update=StateManager.set_confidence,
            help_text="Minimum probability threshold (0.05 - 0.95) for YOLO bounding box detections.",
        )

    # ---------------------------------------------------------
    # SECTION 3: PPE SEVERITY WEIGHTS (SLIDER + NUMBER FIELD)
    # ---------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon_name="balance",
            title="3. Decision Layer PPE Severity Weights",
            subtitle="Adjust the penalty weight assigned when each PPE item is missing. Disabled classes are excluded from scoring.",
        )

        weights = StateManager.get_weights()
        enabled_classes = StateManager.get_enabled_classes()

        for key, rule in PPE_REGISTRY.items():
            is_enabled = enabled_classes.get(key, True)
            label_suffix = "" if is_enabled else " (Disabled)"
            synced_slider_and_number(
                label=f"{rule.label} Weight ({rule.violation_label}){label_suffix}",
                key_prefix=f"weight_{key}",
                current_value=weights.get(key, rule.default_weight),
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                on_update=lambda val, k=key: StateManager.set_weight(k, val),
                help_text=rule.description,
                disabled=not is_enabled,
            )

        active_weight_sum = sum(
            weights.get(k, r.default_weight)
            for k, r in PPE_REGISTRY.items()
            if enabled_classes.get(k, True)
        )
        st.info(
            f"**Total Active Weight Sum:** `{active_weight_sum:.2f}` — "
            f"Alert Thresholds: HIGH `≥ {StateManager.get_thresholds()['HIGH']:.2f}`, "
            f"MEDIUM `≥ {StateManager.get_thresholds()['MEDIUM']:.2f}`, "
            f"LOW `≥ {StateManager.get_thresholds()['LOW']:.2f}`",
            icon=":material/analytics:",
        )

    # ---------------------------------------------------------
    # SECTION 4: AUDIT LOG PERSISTENCE (SAVE TOGGLE + BACKEND)
    # ---------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon_name="save",
            title="4. Audit Log Storage",
            subtitle="Save every incident to disk so the Audit Log survives restarts. Choose CSV or SQL (SQLite).",
        )

        def _on_save_toggle() -> None:
            StateManager.set_audit_save_enabled(st.session_state["toggle_audit_save"])

        def _on_backend_change() -> None:
            StateManager.set_audit_backend(st.session_state["sel_audit_backend"])

        def _on_dir_change() -> None:
            StateManager.set_audit_dir(st.session_state["txt_audit_dir"])
            # Show the resolved absolute path back in the field
            st.session_state["txt_audit_dir"] = StateManager.get_audit_dir()

        st.toggle(
            "Save audit log",
            value=StateManager.is_audit_save_enabled(),
            key="toggle_audit_save",
            on_change=_on_save_toggle,
            help="When on, each detected incident is written to the selected storage.",
        )

        if StateManager.is_audit_save_enabled():
            backends = list(AUDIT_BACKENDS.keys())
            st.selectbox(
                "Storage format",
                options=backends,
                index=backends.index(StateManager.get_audit_backend()),
                key="sel_audit_backend",
                on_change=_on_backend_change,
            )
            st.text_input(
                "Save folder",
                value=StateManager.get_audit_dir(),
                key="txt_audit_dir",
                on_change=_on_dir_change,
                help="Full absolute path, e.g. D:\\AuditLogs. The folder is created if it "
                "doesn't exist. Press Enter to apply.",
            )
            dir_error = validate_audit_dir(StateManager.get_audit_dir())
            if dir_error:
                st.error(
                    f"Folder is not writable, incidents will not be saved: {dir_error}",
                    icon=":material/folder_off:",
                )
            store = StateManager.current_audit_store()
            st.caption(f"Saving to `{store.location}`")
            if StateManager.get_audit_error():
                st.error(
                    f"Could not save audit log: {StateManager.get_audit_error()}",
                    icon=":material/error:",
                )
        else:
            st.caption("Saving is off — the Audit Log only keeps this session's events in memory.")

    # ---------------------------------------------------------
    # SECTION 5: UI THEME COLORS
    # ---------------------------------------------------------
    with st.container(border=True):
        render_section_header(
            icon_name="palette",
            title="5. UI Theme & Color Customization",
            subtitle="Select a modern theme preset or customize individual surface, sidebar, and accent colors.",
        )

        preset_names = list(THEME_PRESETS.keys())
        current_preset = st.session_state.get("theme_preset", preset_names[0])
        preset_idx = (
            preset_names.index(current_preset) if current_preset in preset_names else 0
        )

        def _on_preset_change() -> None:
            chosen = st.session_state["theme_preset_selector"]
            st.session_state["theme_preset"] = chosen
            st.session_state["theme_colors"] = dict(THEME_PRESETS[chosen])

        st.selectbox(
            "Theme Color Preset",
            options=preset_names,
            index=preset_idx,
            key="theme_preset_selector",
            on_change=_on_preset_change,
        )

        theme_colors = StateManager.get_theme_colors()
        row1_c1, row1_c2, row1_c3 = st.columns(3)
        with row1_c1:
            new_primary = st.color_picker(
                "Primary Brand",
                value=theme_colors.get("primary_color", "#4F46E5"),
            )
        with row1_c2:
            new_sidebar = st.color_picker(
                "Sidebar BG",
                value=theme_colors.get("sidebar_bg_color", "#FFFFFF"),
            )
        with row1_c3:
            new_bg = st.color_picker(
                "Canvas BG",
                value=theme_colors.get("background_color", "#F8FAFC"),
            )

        row2_c1, row2_c2, row2_c3 = st.columns(3)
        with row2_c1:
            new_sec_bg = st.color_picker(
                "Card Surface",
                value=theme_colors.get("secondary_bg_color", "#FFFFFF"),
            )
        with row2_c2:
            new_text = st.color_picker(
                "Typography",
                value=theme_colors.get("text_color", "#0F172A"),
            )
        with row2_c3:
            new_accent = st.color_picker(
                "Metric Accent",
                value=theme_colors.get("accent_color", "#4F46E5"),
            )

        updated_colors = {
            "primary_color": new_primary,
            "sidebar_bg_color": new_sidebar,
            "background_color": new_bg,
            "secondary_bg_color": new_sec_bg,
            "text_color": new_text,
            "accent_color": new_accent,
        }

        if updated_colors != theme_colors:
            st.session_state["theme_colors"] = updated_colors
            st.rerun()
