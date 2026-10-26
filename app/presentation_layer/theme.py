"""
Theme Manager (Presentation Layer)
Implements the exact Stitch UI design system:
- Google Fonts: Inter, Plus Jakarta Sans, JetBrains Mono, and Material Symbols Rounded
- Left 260px Sidebar with workspace badge, MAIN MENU + LIVE badge, active #EEF2FF pill with 3.5px left bar,
  segmented Light/Dark appearance switcher, and MSc Research CORE profile card
- Sticky Top System Header Bar with EDGE ENGINE RUNNING badge and Export Telemetry button
- Custom KPI cards, BBox Filter pills, and Real-Time Hazard Incident Stream table styles
"""

import streamlit as st
from app.config.state_manager import StateManager


def _clean_html(markup: str) -> str:
    """Strip line-leading whitespace so Markdown never parses HTML lines as indented code blocks."""
    return "\n".join(
        line.strip() for line in markup.strip().splitlines() if line.strip()
    )


def _is_dark_color(hex_color: str) -> bool:
    """Determine if a hex color is dark based on relative luminance."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return luminance < 0.5


def apply_custom_theme() -> None:
    """Inject the Stitch CSS design system and adaptive Light/Dark variables."""
    colors = StateManager.get_theme_colors()
    primary = colors.get("primary_color", "#4F46E5")
    bg = colors.get("background_color", "#F8FAFC")
    sec_bg = colors.get("secondary_bg_color", "#FFFFFF")
    sidebar_bg = colors.get("sidebar_bg_color", "#FFFFFF")
    text = colors.get("text_color", "#0F172A")
    accent = colors.get("accent_color", "#4F46E5")

    is_dark = _is_dark_color(bg)
    sb_dark = _is_dark_color(sidebar_bg)

    sb_text = "#F8FAFC" if sb_dark else "#0F172A"
    sb_muted = "#94A3B8" if sb_dark else "#64748B"
    sb_border = "#1E293B" if sb_dark else "#E2E8F0"
    sb_hover_bg = "rgba(255, 255, 255, 0.05)" if sb_dark else "#F1F5F9"
    sb_surface = "#0F172A" if sb_dark else "#F8FAFC"
    sb_active_bg = f"{primary}24" if sb_dark else "#EEF2FF"
    sb_active_text = "#818CF8" if sb_dark else primary

    card_border = "#1E293B" if is_dark else "#E2E8F0"
    subtle_bg = "#0F172A" if is_dark else "#F8FAFC"
    muted_text = "#94A3B8" if is_dark else "#64748B"
    btn_hover_bg = "rgba(255, 255, 255, 0.05)" if is_dark else "#EEF2FF"
    btn_hover_text = "#FFFFFF" if is_dark else primary
    swatch_border = "#334155" if is_dark else "#0F172A"

    custom_css = f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap" rel="stylesheet">

    <style>
        /* Hide default Streamlit top header decoration to allow custom Top Header Bar */
        header[data-testid="stHeader"] {{
            background: transparent !important;
            height: 2rem !important;
        }}
        .block-container {{
            padding-top: 0.6rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 1600px !important;
        }}

        /* Global Fonts & Colors */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
        }}
        .stApp {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: {text} !important;
            letter-spacing: -0.02em;
        }}
        .font-mono {{
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* Material Symbols Rounded */
        .material-symbols-rounded {{
            font-family: 'Material Symbols Rounded' !important;
            font-weight: normal;
            font-style: normal;
            font-size: 20px;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            vertical-align: middle;
            user-select: none;
        }}
        .material-symbols-rounded.filled {{
            font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 20;
        }}

        /* =========================================================
           LEFT SIDEBAR NAVIGATION (Stitch 260px Layout)
           ========================================================= */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {sb_border} !important;
            min-width: 265px !important;
            max-width: 265px !important;
        }}
        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
            padding-top: 0.5rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: {sb_border} !important;
            margin: 0.75rem 0 !important;
        }}

        /* Brand Header inside Sidebar */
        .sb-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 6px 4px 14px 4px;
            margin-bottom: 12px;
            border-bottom: 1px solid {sb_border};
        }}
        .sb-header-left {{
            display: flex;
            align-items: center;
            gap: 11px;
        }}
        .sb-logo-box {{
            width: 36px;
            height: 36px;
            border-radius: 11px;
            background: linear-gradient(135deg, #4338CA, {primary}, #6366F1);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px {primary}40;
            flex-shrink: 0;
        }}
        .sb-logo-box .material-symbols-rounded {{
            color: #FFFFFF !important;
            font-size: 20px;
        }}
        .sb-brand-name {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 700;
            font-size: 14px;
            color: {sb_text} !important;
            line-height: 1.2;
        }}
        .sb-brand-tag {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: {sb_muted} !important;
            font-weight: 500;
        }}
        .sb-chevron-btn {{
            width: 28px;
            height: 28px;
            border-radius: 7px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {sb_muted} !important;
        }}

        /* MAIN MENU + LIVE Row */
        .sb-menu-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 8px;
            margin-bottom: 8px;
        }}
        .sb-section-label {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {sb_muted} !important;
        }}
        .sb-live-pill {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            background: {sb_hover_bg};
            color: {sb_muted} !important;
        }}

        /* Sidebar Navigation Buttons */
        [data-testid="stSidebar"] .stButton > button {{
            width: 100% !important;
            justify-content: flex-start !important;
            text-align: left !important;
            background-color: transparent !important;
            color: {sb_muted} !important;
            border: 1px solid transparent !important;
            border-radius: 9px !important;
            padding: 0.55rem 0.75rem !important;
            font-weight: 500 !important;
            font-size: 13px !important;
            transition: all 0.15s ease !important;
            box-shadow: none !important;
            margin-bottom: 2px !important;
        }}
        [data-testid="stSidebar"] .stButton > button * {{
            color: {sb_muted} !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background-color: {sb_hover_bg} !important;
            color: {sb_text} !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover * {{
            color: {sb_text} !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background-color: {sb_active_bg} !important;
            color: {sb_active_text} !important;
            border: 1px solid {primary}22 !important;
            border-left: 3.5px solid {primary} !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"] * {{
            color: {sb_active_text} !important;
        }}

        /* Sidebar Researcher Profile Card */
        .sb-profile-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: {sec_bg};
            border: 1px solid {sb_border};
            border-radius: 12px;
            padding: 10px 12px;
            margin-top: 10px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
        }}
        .sb-profile-left {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .sb-avatar-wrap {{
            position: relative;
            width: 36px;
            height: 36px;
        }}
        .sb-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: {sb_hover_bg};
            border: 2px solid {primary}33;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .sb-avatar .material-symbols-rounded {{
            color: {sb_muted} !important;
            font-size: 19px;
        }}
        .sb-status-dot {{
            position: absolute;
            bottom: 0;
            right: 0;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: #10B981;
            border: 2px solid {sec_bg};
        }}
        .sb-profile-name {{
            font-size: 12px;
            font-weight: 700;
            color: {sb_text} !important;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .sb-core-badge {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 9px;
            font-weight: 600;
            padding: 1px 4px;
            border-radius: 4px;
            background: {sb_hover_bg};
            color: {sb_muted} !important;
        }}
        .sb-profile-role {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            color: {sb_muted} !important;
            margin-top: 1px;
        }}

        /* =========================================================
           TOP SYSTEM HEADER BAR
           ========================================================= */
        .stitch-top-header {{
            background-color: {sec_bg};
            border: 1px solid {card_border};
            border-radius: 14px;
            padding: 12px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }}
        .stitch-header-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .stitch-header-icon {{
            width: 34px;
            height: 34px;
            border-radius: 9px;
            background: {primary}14;
            border: 1px solid {primary}28;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {primary} !important;
        }}
        .stitch-header-icon .material-symbols-rounded {{
            color: {primary} !important;
            font-size: 20px;
        }}
        .stitch-header-title {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 15px;
            font-weight: 700;
            color: {text} !important;
            line-height: 1.25;
            margin: 0;
        }}
        .stitch-header-sub {{
            font-size: 11px;
            color: {muted_text} !important;
            margin: 0;
        }}
        .stitch-header-right {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .edge-running-pill {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 5px 11px;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.10);
            border: 1px solid rgba(16, 185, 129, 0.30);
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            color: #059669 !important;
        }}
        .edge-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #10B981;
        }}
        .notif-btn {{
            position: relative;
            width: 34px;
            height: 34px;
            border-radius: 9px;
            border: 1px solid {card_border};
            background: {sec_bg};
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: {muted_text} !important;
        }}
        .notif-dot {{
            position: absolute;
            top: 6px;
            right: 6px;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #F97316;
        }}
        .export-pill-btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 13px;
            border-radius: 9px;
            background: {primary};
            color: #FFFFFF !important;
            font-size: 12px;
            font-weight: 600;
            box-shadow: 0 2px 8px {primary}33;
        }}
        .export-pill-btn .material-symbols-rounded {{
            color: #FFFFFF !important;
            font-size: 17px;
        }}

        /* =========================================================
           MAIN WORKSPACE CARDS & STREAM CONTROLS
           ========================================================= */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {sec_bg} !important;
            border: 1px solid {card_border} !important;
            border-radius: 16px !important;
            padding: 1.1rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
        }}

        /* Main Workspace Buttons (Start / Stop Monitoring, Reset, etc.) */
        [data-testid="stMain"] .stButton > button {{
            border-radius: 11px !important;
            font-weight: 600 !important;
            font-size: 12px !important;
            padding: 0.55rem 0.9rem !important;
            transition: all 0.16s ease !important;
            border: 1px solid {card_border} !important;
            background-color: {sec_bg} !important;
            color: {text} !important;
        }}
        [data-testid="stMain"] .stButton > button * {{
            color: {text} !important;
        }}
        [data-testid="stMain"] .stButton > button:hover,
        [data-testid="stMain"] .stButton > button:focus,
        [data-testid="stMain"] .stButton > button:active {{
            background-color: {btn_hover_bg} !important;
            border-color: {primary} !important;
            color: {btn_hover_text} !important;
        }}
        [data-testid="stMain"] .stButton > button:hover *,
        [data-testid="stMain"] .stButton > button:focus *,
        [data-testid="stMain"] .stButton > button:active * {{
            color: {btn_hover_text} !important;
        }}

        /* Primary Action Button (Start Monitoring) */
        [data-testid="stMain"] .stButton > button[kind="primary"] {{
            background-color: {primary} !important;
            color: #FFFFFF !important;
            border-color: {primary} !important;
            box-shadow: 0 4px 12px {primary}33 !important;
        }}
        [data-testid="stMain"] .stButton > button[kind="primary"] * {{
            color: #FFFFFF !important;
        }}
        [data-testid="stMain"] .stButton > button[kind="primary"]:hover,
        [data-testid="stMain"] .stButton > button[kind="primary"]:focus,
        [data-testid="stMain"] .stButton > button[kind="primary"]:active {{
            background-color: {primary} !important;
            filter: brightness(1.08) !important;
            color: #FFFFFF !important;
            border-color: {primary} !important;
        }}
        [data-testid="stMain"] .stButton > button[kind="primary"]:hover *,
        [data-testid="stMain"] .stButton > button[kind="primary"]:focus *,
        [data-testid="stMain"] .stButton > button[kind="primary"]:active * {{
            color: #FFFFFF !important;
        }}

        /* Styled File Uploader Dropzone & Upload Button inside Stream Controls */
        [data-testid="stFileUploaderDropzone"] {{
            background-color: {subtle_bg} !important;
            border: 1.5px dashed {card_border} !important;
            border-radius: 12px !important;
            padding: 1rem !important;
            color: {text} !important;
            transition: border-color 0.2s ease, background-color 0.2s ease;
        }}
        [data-testid="stFileUploaderDropzone"] * {{
            color: {text} !important;
        }}
        [data-testid="stFileUploaderDropzone"] small {{
            color: {muted_text} !important;
        }}
        [data-testid="stFileUploaderDropzone"]:hover {{
            border-color: {primary} !important;
        }}
        [data-testid="stFileUploaderDropzone"] button {{
            background-color: {sec_bg} !important;
            color: {text} !important;
            border: 1px solid {card_border} !important;
            border-radius: 9px !important;
            font-weight: 600 !important;
            transition: all 0.16s ease !important;
        }}
        [data-testid="stFileUploaderDropzone"] button * {{
            color: {text} !important;
        }}
        [data-testid="stFileUploaderDropzone"] button:hover,
        [data-testid="stFileUploaderDropzone"] button:focus,
        [data-testid="stFileUploaderDropzone"] button:active {{
            background-color: {btn_hover_bg} !important;
            border-color: {primary} !important;
            color: {btn_hover_text} !important;
        }}
        [data-testid="stFileUploaderDropzone"] button:hover *,
        [data-testid="stFileUploaderDropzone"] button:focus *,
        [data-testid="stFileUploaderDropzone"] button:active * {{
            color: {btn_hover_text} !important;
        }}

        /* =========================================================
           DYNAMIC FORM WIDGETS & LABELS (LIGHT / DARK ADAPTIVE)
           ========================================================= */
        /* Widget Labels (Sliders, Number Inputs, Toggles, Selectboxes, File Uploaders, Color Pickers) */
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span,
        [data-testid="stMain"] label,
        [data-testid="stMain"] label p,
        [data-testid="stMain"] label span,
        .stSlider label,
        .stNumberInput label,
        .stSelectbox label,
        .stToggle label,
        .stColorPicker label {{
            color: {text} !important;
            font-weight: 500 !important;
        }}

        /* Tooltip / Help Icons next to Widget Labels */
        [data-testid="stTooltipHoverTarget"] svg,
        [data-testid="stWidgetLabel"] svg {{
            color: {muted_text} !important;
            fill: {muted_text} !important;
        }}

        /* Number Input Field & Stepper (+/-) Buttons */
        [data-testid="stNumberInputContainer"],
        .stNumberInput div[data-baseweb="input"],
        .stNumberInput div[data-baseweb="base-input"] {{
            background-color: {subtle_bg} !important;
            border-color: {card_border} !important;
            color: {text} !important;
            border-radius: 9px !important;
        }}
        .stNumberInput input,
        [data-testid="stNumberInputField"] {{
            background-color: transparent !important;
            color: {text} !important;
            -webkit-text-fill-color: {text} !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important;
        }}
        [data-testid="stNumberInputStepDown"],
        [data-testid="stNumberInputStepUp"] {{
            background-color: transparent !important;
            color: {text} !important;
        }}
        [data-testid="stNumberInputStepDown"] svg,
        [data-testid="stNumberInputStepUp"] svg {{
            fill: {text} !important;
            color: {text} !important;
        }}
        [data-testid="stNumberInputStepDown"]:hover,
        [data-testid="stNumberInputStepUp"]:hover {{
            background-color: {btn_hover_bg} !important;
            color: {btn_hover_text} !important;
        }}

        /* Selectbox / Dropdown Field */
        .stSelectbox div[data-baseweb="select"] > div {{
            background-color: {subtle_bg} !important;
            border-color: {card_border} !important;
            color: {text} !important;
            border-radius: 9px !important;
        }}
        .stSelectbox div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] div {{
            color: {text} !important;
        }}
        .stSelectbox div[data-baseweb="select"] svg {{
            fill: {muted_text} !important;
        }}

        /* Slider Min/Max Tick Bar Labels */
        [data-testid="stTickBarMin"],
        [data-testid="stTickBarMax"] {{
            color: {muted_text} !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* Color Picker Swatches (Visible dark border in Light Mode so white/light swatches stand out) */
        [data-testid="stColorPickerBlock"] {{
            border: 1.5px solid {swatch_border} !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08) !important;
        }}

        /* Scanline Overlay for Standby CCTV Viewport */
        .cctv-scanline {{
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
            background-size: 100% 4px;
        }}

        /* Custom KPI Card Styling */
        .kpi-card {{
            background-color: {sec_bg};
            border: 1px solid {card_border};
            border-radius: 14px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
            height: 100%;
        }}
        .kpi-card-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .kpi-label {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {muted_text} !important;
        }}
        .kpi-icon-box {{
            width: 28px;
            height: 28px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .kpi-value-row {{
            margin-top: 12px;
            display: flex;
            align-items: baseline;
            gap: 8px;
        }}
        .kpi-footer {{
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid {card_border};
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 11px;
            color: {muted_text} !important;
        }}

        /* Incident Table Styling */
        .incident-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 12px;
        }}
        .incident-table th {{
            background-color: {subtle_bg};
            color: {muted_text} !important;
            font-family: 'JetBrains Mono', monospace;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 10px 16px;
            border-bottom: 1px solid {card_border};
        }}
        .incident-table td {{
            padding: 10px 16px;
            border-bottom: 1px solid {card_border};
            color: {text} !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_section_header(icon_name: str, title: str, subtitle: str = "") -> None:
    """Render a modern section header with a Google Material Symbol icon badge."""
    colors = StateManager.get_theme_colors()
    primary = colors.get("primary_color", "#4F46E5")
    sub_html = (
        f'<div style="font-size:0.8rem; opacity:0.65; margin-top:2px; margin-bottom:10px;">{subtitle}</div>'
        if subtitle
        else '<div style="margin-bottom:6px;"></div>'
    )
    st.markdown(
        _clean_html(f"""
        <div style="display:flex; align-items:center; gap:9px; margin-bottom:2px;">
            <div style="width:30px; height:30px; border-radius:8px; background:{primary}15; display:inline-flex; align-items:center; justify-content:center;">
                <span class="material-symbols-rounded" style="color:{primary}; font-size:18px;">{icon_name}</span>
            </div>
            <div style="font-family:'Plus Jakarta Sans',sans-serif; font-size:0.95rem; font-weight:700;">{title}</div>
        </div>
        {sub_html}
        """),
        unsafe_allow_html=True,
    )
