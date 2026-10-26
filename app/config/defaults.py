"""
Default configuration values and extensible registries for the Hazard Detection System.
To add a new PPE class or theme preset in the future, simply extend the dictionaries below.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

# Model & Video Defaults
DEFAULT_MODEL_PATH = (
    "E://Desktop 7-18-2026//Downloads//PPE//Model//Colab Model//"
    "sh17_ppe_detection//yolov8s_sh17//weights//best.pt"
)
DEFAULT_SAMPLE_VIDEOS = [
    "Samples/Construction.mp4",
    "Construction.mp4",
    "Samples/Example.mp4",
    "Samples/Video.mp4",
]
DEFAULT_CONFIDENCE = 0.40


@dataclass
class PPERuleConfig:
    """Extensible definition for a PPE detection rule."""
    key: str
    label: str
    violation_label: str
    icon: str                            # Google Material Symbol name
    default_weight: float
    default_enabled: bool
    required_class_ids: List[int]        # At least one of these classes means PPE is worn
    exposed_body_class_id: Optional[int] # Optional body part class ID (e.g., bare hands, head, face)
    require_exposed_part: bool           # If True, violation triggers only when exposed body part is detected
    description: str


# Extensible PPE Class Registry (SH17 Dataset Class IDs)
# 0: person, 3: face, 4: face-guard, 5: face-mask, 9: gloves,
# 10: helmet, 11: hands, 12: head, 15: safety-suit, 16: safety-vest
PPE_REGISTRY: Dict[str, PPERuleConfig] = {
    "helmet": PPERuleConfig(
        key="helmet",
        label="Safety Helmet",
        violation_label="No Helmet",
        icon="engineering",
        default_weight=0.40,
        default_enabled=True,
        required_class_ids=[10],
        exposed_body_class_id=12,
        require_exposed_part=False,
        description="Detects missing safety helmet (Class 10: helmet, Class 12: exposed head).",
    ),
    "vest": PPERuleConfig(
        key="vest",
        label="Safety Vest",
        violation_label="No Safety Vest",
        icon="checkroom",
        default_weight=0.30,
        default_enabled=True,
        required_class_ids=[16, 15],
        exposed_body_class_id=None,
        require_exposed_part=False,
        description="Detects missing safety vest or safety suit (Class 16: safety-vest, Class 15: safety-suit).",
    ),
    "gloves": PPERuleConfig(
        key="gloves",
        label="Gloves",
        violation_label="No Gloves",
        icon="back_hand",
        default_weight=0.15,
        default_enabled=True,
        required_class_ids=[9],
        exposed_body_class_id=11,
        require_exposed_part=False,
        description="Detects missing safety gloves (Class 9: gloves, Class 11: bare hands).",
    ),
    "mask": PPERuleConfig(
        key="mask",
        label="Face Mask",
        violation_label="No Face Mask",
        icon="masks",
        default_weight=0.15,
        default_enabled=True,
        required_class_ids=[5, 4],
        exposed_body_class_id=3,
        require_exposed_part=False,
        description="Detects missing face-mask or face-guard (Class 5: face-mask, Class 4: face-guard, Class 3: face).",
    ),
}

# Default Severity Alert Thresholds
DEFAULT_THRESHOLDS: Dict[str, float] = {
    "HIGH": 0.60,
    "MEDIUM": 0.30,
    "LOW": 0.10,
}

# Dribbble-Inspired Modern Sidebar Themes (Light & Dark Variations)
DEFAULT_THEME_NAME = "Modern Dark (Obsidian Sidebar)"

THEME_PRESETS: Dict[str, Dict[str, str]] = {
    "Modern Dark (Obsidian Sidebar)": {
        "primary_color": "#6366F1",
        "background_color": "#0B0D13",
        "secondary_bg_color": "#131620",
        "sidebar_bg_color": "#131620",
        "text_color": "#F8FAFC",
        "accent_color": "#818CF8",
    },
    "Modern Light (Clean Sidebar)": {
        "primary_color": "#4F46E5",
        "background_color": "#F8FAFC",
        "secondary_bg_color": "#FFFFFF",
        "sidebar_bg_color": "#FFFFFF",
        "text_color": "#0F172A",
        "accent_color": "#4F46E5",
    },
    "Cobalt Enterprise Light": {
        "primary_color": "#2563EB",
        "background_color": "#F4F7FB",
        "secondary_bg_color": "#FFFFFF",
        "sidebar_bg_color": "#FFFFFF",
        "text_color": "#0F172A",
        "accent_color": "#2563EB",
    },
    "Emerald Slate Dark": {
        "primary_color": "#10B981",
        "background_color": "#090D16",
        "secondary_bg_color": "#111827",
        "sidebar_bg_color": "#111827",
        "text_color": "#F9FAFB",
        "accent_color": "#34D399",
    },
}
