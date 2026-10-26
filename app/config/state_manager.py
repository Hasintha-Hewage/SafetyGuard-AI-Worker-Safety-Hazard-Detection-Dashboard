"""
State Manager (Configuration & State Layer)
Centralizes all Streamlit session state operations, live incident log history,
and synchronized widget helpers (Slider <-> Number Input) for weights and thresholds.
"""

from typing import Any, Dict, List
import streamlit as st
from app.config.defaults import (
    DEFAULT_CONFIDENCE,
    DEFAULT_MODEL_PATH,
    DEFAULT_THEME_NAME,
    DEFAULT_THRESHOLDS,
    PPE_REGISTRY,
    THEME_PRESETS,
)


DEFAULT_INCIDENT_LOGS: List[Dict[str, Any]] = [
    {
        "timestamp": "14:32:08.412",
        "worker_id": "#107",
        "zone": "South Scaffolding Bay 2",
        "status": "Missing Hardhat",
        "is_violation": True,
        "confidence": 0.88,
        "action": "Audio Hooter Triggered",
    },
    {
        "timestamp": "14:31:54.120",
        "worker_id": "#104",
        "zone": "Rebar Assembly Zone",
        "status": "Compliant (Full PPE)",
        "is_violation": False,
        "confidence": 0.94,
        "action": "Logged",
    },
    {
        "timestamp": "14:31:22.091",
        "worker_id": "#112",
        "zone": "Perimeter Crane Base",
        "status": "Compliant (Full PPE)",
        "is_violation": False,
        "confidence": 0.91,
        "action": "Logged",
    },
]


class StateManager:
    """Manages application state in st.session_state."""

    @staticmethod
    def initialize() -> None:
        """Initialize all default session state variables if not already present."""
        if "app_initialized" in st.session_state:
            if (
                st.session_state.get("theme_preset") not in THEME_PRESETS
                or not st.session_state.get("dark_default_migrated")
            ):
                st.session_state["theme_preset"] = DEFAULT_THEME_NAME
                st.session_state["theme_colors"] = dict(THEME_PRESETS[DEFAULT_THEME_NAME])
                st.session_state["dark_default_migrated"] = True
            if "incident_logs" not in st.session_state:
                st.session_state["incident_logs"] = list(DEFAULT_INCIDENT_LOGS)
            return

        st.session_state["current_page"] = "Home"
        st.session_state["model_path"] = DEFAULT_MODEL_PATH
        st.session_state["confidence_threshold"] = DEFAULT_CONFIDENCE

        # Initialize PPE weights & enabled flags from PPE_REGISTRY
        st.session_state["ppe_weights"] = {
            key: rule.default_weight for key, rule in PPE_REGISTRY.items()
        }
        st.session_state["ppe_enabled"] = {
            key: rule.default_enabled for key, rule in PPE_REGISTRY.items()
        }

        # Initialize Alert Thresholds
        st.session_state["alert_thresholds"] = dict(DEFAULT_THRESHOLDS)

        # Initialize Theme Settings
        st.session_state["theme_preset"] = DEFAULT_THEME_NAME
        st.session_state["theme_colors"] = dict(THEME_PRESETS[DEFAULT_THEME_NAME])
        st.session_state["dark_default_migrated"] = True

        # Initialize Live Incident Logs
        st.session_state["incident_logs"] = list(DEFAULT_INCIDENT_LOGS)

        st.session_state["app_initialized"] = True

    @staticmethod
    def reset_to_defaults() -> None:
        """Reset all configurable settings back to defaults."""
        st.session_state["confidence_threshold"] = DEFAULT_CONFIDENCE
        st.session_state["ppe_weights"] = {
            key: rule.default_weight for key, rule in PPE_REGISTRY.items()
        }
        st.session_state["ppe_enabled"] = {
            key: rule.default_enabled for key, rule in PPE_REGISTRY.items()
        }
        st.session_state["alert_thresholds"] = dict(DEFAULT_THRESHOLDS)
        st.session_state["theme_preset"] = DEFAULT_THEME_NAME
        st.session_state["theme_colors"] = dict(THEME_PRESETS[DEFAULT_THEME_NAME])
        st.session_state["incident_logs"] = list(DEFAULT_INCIDENT_LOGS)

        keys_to_remove = [
            k for k in st.session_state.keys()
            if k.startswith(("slider_", "num_", "toggle_", "home_slider_"))
        ]
        for k in keys_to_remove:
            del st.session_state[k]

    @staticmethod
    def get_confidence() -> float:
        return float(st.session_state.get("confidence_threshold", DEFAULT_CONFIDENCE))

    @staticmethod
    def set_confidence(value: float) -> None:
        val = round(float(value), 2)
        st.session_state["confidence_threshold"] = val

    @staticmethod
    def get_weights() -> Dict[str, float]:
        return st.session_state.get("ppe_weights", {})

    @staticmethod
    def set_weight(ppe_key: str, value: float) -> None:
        val = round(float(value), 2)
        st.session_state["ppe_weights"][ppe_key] = val

    @staticmethod
    def get_enabled_classes() -> Dict[str, bool]:
        return st.session_state.get("ppe_enabled", {})

    @staticmethod
    def set_class_enabled(ppe_key: str, enabled: bool) -> None:
        st.session_state["ppe_enabled"][ppe_key] = bool(enabled)

    @staticmethod
    def get_thresholds() -> Dict[str, float]:
        return st.session_state.get("alert_thresholds", dict(DEFAULT_THRESHOLDS))

    @staticmethod
    def set_threshold(level: str, value: float) -> None:
        val = round(float(value), 2)
        st.session_state["alert_thresholds"][level] = val

    @staticmethod
    def get_theme_colors() -> Dict[str, str]:
        return st.session_state.get(
            "theme_colors", dict(THEME_PRESETS[DEFAULT_THEME_NAME])
        )

    @staticmethod
    def get_incident_logs() -> List[Dict[str, Any]]:
        return st.session_state.get("incident_logs", list(DEFAULT_INCIDENT_LOGS))

    @staticmethod
    def add_incident_log(entry: Dict[str, Any]) -> None:
        logs = st.session_state.get("incident_logs", list(DEFAULT_INCIDENT_LOGS))
        logs.insert(0, entry)
        st.session_state["incident_logs"] = logs[:15]
