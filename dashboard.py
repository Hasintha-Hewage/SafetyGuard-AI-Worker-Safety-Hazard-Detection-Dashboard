"""
Main Entry Point — AI Worker Safety Monitoring System
Follows a clean Layered Architecture:
- app.config             : Configuration, Extensible PPE Registry & Session State Layer
- app.data_layer         : Video Capture & Stream Input Layer
- app.detection_layer    : YOLOv8 Inference & Annotation Layer
- app.decision_layer     : Weighted Severity Scoring & Safety Evaluation Layer
- app.presentation_layer : UI Theme, Dribbble Left Sidebar Navigation, Home & Settings Views
"""

import streamlit as st
from app.config.state_manager import StateManager
from app.presentation_layer.navigation import render_navigation, render_sidebar_footer
from app.presentation_layer.theme import apply_custom_theme
from app.presentation_layer.views.home_view import render_home_view
from app.presentation_layer.views.settings_view import render_settings_view


def main() -> None:
    st.set_page_config(
        page_title="AI Worker Safety Monitoring System",
        page_icon=":material/shield_person:",
        layout="wide",
    )

    # 1. Initialize Application State Layer
    StateManager.initialize()

    # 2. Apply Dynamic UI Theme Colors & Google Material Symbols
    apply_custom_theme()

    # 3. Render Top Section of Modern Left Sidebar Navigation (Home / Settings)
    selected_page = render_navigation()

    # 4. Route to Active View in Presentation Layer (also renders contextual sidebar controls)
    if selected_page == "Home":
        render_home_view()
    elif selected_page == "Settings":
        render_settings_view()

    # 5. Render Bottom Sidebar Footer (Light/Dark Mode Switcher + Researcher Profile Card)
    render_sidebar_footer()


if __name__ == "__main__":
    main()
