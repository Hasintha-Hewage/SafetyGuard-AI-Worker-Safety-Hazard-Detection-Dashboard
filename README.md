# SafetyGuard AI — Worker Safety & Hazard Detection Dashboard (v2.4)

**MSc Research Project (GS/COMP/377) — Integrated Computer Vision & Hazard Detection System**

A modular, extensible **Streamlit + YOLOv8 (SH17 Dataset)** real-time Personal Protective Equipment (PPE) compliance and workplace hazard monitoring system built with a strict **5-Layer Architecture** and an enterprise **Stitch UI Design System**.

---

## 1. Quick Start

### Prerequisites
- Python 3.9+
- Dependencies: `streamlit`, `ultralytics`, `opencv-python`, `numpy`

### Run the Application
```bash
streamlit run dashboard.py
```
*(Or `streamlit run Dashboard.py` on Windows)*

---

## 2. Layered System Architecture

The codebase is organized into five decoupled layers so that computer vision models, safety decision rules, state management, and UI presentation can evolve independently:

```text
AntiGravity/
├── dashboard.py                       # Main entry point (initializes state, theme, sidebar, and page routing)
├── Dashboard1.py                      # Original legacy monolithic reference script (preserved for reference)
├── README.md                          # Developer & AI Agent architecture and maintenance guide
└── app/
    ├── config/                        # LAYER 1: Configuration, Extensible Registries & Session State
    │   ├── defaults.py                # PPE_REGISTRY, THEME_PRESETS, DEFAULT_THRESHOLDS, model/video paths
    │   └── state_manager.py           # StateManager class managing st.session_state and incident logs
    ├── data_layer/                    # LAYER 2: Video Input & Stream Capture Layer
    │   └── video_stream.py            # OpenCV VideoCapture handler (Webcam, Uploaded MP4/AVI/MOV, Fallback samples)
    ├── detection_layer/               # LAYER 3: YOLOv8 Inference & Frame Annotation Layer
    │   └── detector.py                # @st.cache_resource YOLO model loader, class filtering, and OpenCV HUD overlay
    ├── decision_layer/                # LAYER 4: Weighted Severity Scoring & Safety Evaluation Layer
    │   └── safety_evaluator.py        # Spatial person-to-PPE box association & weighted risk index computation
    └── presentation_layer/            # LAYER 5: Stitch UI Theme, Navigation, Reusable Components & Views
        ├── theme.py                   # Adaptive Dark/Light CSS injection, Google Fonts, Material Symbols, _clean_html()
        ├── navigation.py              # Left 265px Sidebar Navigation, Top System Header Bar, Light/Dark Switcher
        ├── components.py              # Two-way synchronized Slider <-> Number Input component
        └── views/
            ├── home_view.py           # Home Dashboard (8:4 Asymmetric Grid, Live CCTV/HUD, 4 KPI Cards, Incident Table)
            └── settings_view.py       # Settings View (PPE Class Toggles, Confidence, Severity Weights, Theme Colors)
```

---

## 3. Core Concepts & Data Flow

### 3.1 Extensible PPE Registry (`app/config/defaults.py`)
All PPE classes are centrally defined in `PPE_REGISTRY` using the `PPERuleConfig` dataclass (mapped to **SH17 Dataset** class IDs):
- **`helmet`** (`Safety Helmet`): Required Class `[10]`, Exposed Body Part `12` (`head`), Default Weight `0.40`
- **`vest`** (`Safety Vest`): Required Classes `[16, 15]` (`safety-vest`, `safety-suit`), Default Weight `0.30`
- **`gloves`** (`Gloves`): Required Class `[9]`, Exposed Body Part `11` (`hands`), Default Weight `0.15`
- **`mask`** (`Face Mask`): Required Classes `[5, 4]` (`face-mask`, `face-guard`), Exposed Body Part `3` (`face`), Default Weight `0.15`

> **How to Add a New PPE Class in the Future (e.g., Safety Boots or Ear Muffs):**
> Simply add a new entry to `PPE_REGISTRY` in `app/config/defaults.py`. It will **automatically** appear in:
> 1. **Settings View**: PPE Detection Classes toggle cards and Decision Layer Severity Weight sliders/number inputs.
> 2. **Home View**: BBox Filter pills under the video viewport and the Active Detection Profile card.
> 3. **Detection Layer**: Active YOLO class ID filtering (`get_active_yolo_class_ids`).
> 4. **Decision Layer**: Worker association and weighted severity scoring (`evaluate_frame_safety`).

### 3.2 Decision Layer Scoring Formula (`app/decision_layer/safety_evaluator.py`)
1. Every frame separates **Persons (`class_id == 0`)** from **PPE/Body items (`class_id != 0`)**.
2. Each PPE/body item is spatially associated with a person if its center point `(center_x, center_y)` lies inside the person's bounding box (`is_inside_person`).
3. For each enabled rule in `PPE_REGISTRY`, if none of `required_class_ids` are detected on the worker, a violation is recorded and the worker's severity score increases by:
   $$\text{Score} += \text{Confidence} \times \text{Weight}_{\text{PPE}}$$
4. Frame alert escalation is determined by the highest individual worker score (`max_severity_score`):
   - **HIGH ALERT**: $\ge 0.60$
   - **MEDIUM ALERT**: $\ge 0.30$
   - **LOW ALERT**: $\ge 0.10$
   - **SAFE**: $< 0.10$

---

## 4. Critical UI & Streamlit Engineering Rules (For Developers & AI Agents)

When modifying the Presentation Layer (`app/presentation_layer/`), keep these important architectural details in mind:

1. **HTML Normalization (`_html_fragment` / `_clean_html`)**:
   - Streamlit's `st.markdown(..., unsafe_allow_html=True)` runs strings through a CommonMark parser. Any HTML line indented by **4 or more spaces** (especially inside multi-line f-strings or after interpolated sub-blocks) will be misinterpreted by Markdown as a `<pre><code>` block!
   - **Rule**: Always wrap multi-line HTML strings in `_html_fragment()` (in `home_view.py`) or `_clean_html()` (in `theme.py`), which strips leading whitespace from every line before passing to `st.markdown`.

2. **Streamlit DOM Selectors (`[data-testid="stMain"]`)**:
   - Modern Streamlit versions use `section[data-testid="stMain"]` instead of `.main`. Always scope main-canvas CSS overrides to `[data-testid="stMain"]` or specific `data-testid` attributes (`[data-testid="stWidgetLabel"]`, `[data-testid="stFileUploaderDropzone"]`, `[data-testid="stColorPickerBlock"]`).

3. **Dynamic Dark / Light Theme Adaptation (`app/presentation_layer/theme.py`)**:
   - **Default Theme**: `"Modern Dark (Obsidian Sidebar)"` is the default preset (`DEFAULT_THEME_NAME` in `app/config/defaults.py`).
   - `_is_dark_color(hex_color)` computes relative luminance to automatically derive adaptive colors for both Dark Mode and Light Mode:
     - Typography (`{text}`), muted labels (`{muted_text}`), borders (`{card_border}`), button hover states (`{btn_hover_bg}`, `{btn_hover_text}`), and color picker swatch borders (`{swatch_border}`) all switch dynamically between Dark Mode and Light Mode.

4. **Synchronized Widget Callbacks (`on_click` / `on_change`)**:
   - Never mutate a session state key bound to an already-instantiated widget inside the main script body (which raises `StreamlitWidgetAlreadyInstantiatedError`).
   - Always use `on_change` or `on_click` callbacks (such as `_switch_to_preset` in `navigation.py` and `synced_slider_and_number` in `components.py`) so state updates execute prior to widget instantiation on rerun.

