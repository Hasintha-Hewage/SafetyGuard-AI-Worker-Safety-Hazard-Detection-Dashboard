"""
Reusable UI Components (Presentation Layer)
Provides a synchronized Slider + Number Input component for effortless two-way binding.
"""

from typing import Callable, Optional
import streamlit as st


def synced_slider_and_number(
    label: str,
    key_prefix: str,
    current_value: float,
    min_value: float = 0.0,
    max_value: float = 1.0,
    step: float = 0.05,
    on_update: Optional[Callable[[float], None]] = None,
    help_text: Optional[str] = None,
    disabled: bool = False,
) -> float:
    """
    Render a paired Slider and Number Input that stay synchronized in real time.
    Changing the slider updates the number field, and changing the number field updates the slider.
    """
    slider_key = f"slider_{key_prefix}"
    num_key = f"num_{key_prefix}"

    rounded_val = round(float(current_value), 2)

    if slider_key not in st.session_state:
        st.session_state[slider_key] = rounded_val
    if num_key not in st.session_state:
        st.session_state[num_key] = rounded_val

    def _on_slider_change() -> None:
        val = round(float(st.session_state[slider_key]), 2)
        st.session_state[num_key] = val
        if on_update:
            on_update(val)

    def _on_num_change() -> None:
        val = round(float(st.session_state[num_key]), 2)
        st.session_state[slider_key] = val
        if on_update:
            on_update(val)

    col_slider, col_num = st.columns([3, 1])
    with col_slider:
        st.slider(
            label=label,
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=slider_key,
            on_change=_on_slider_change,
            help=help_text,
            disabled=disabled,
        )
    with col_num:
        st.number_input(
            label=f"{label} (Value)",
            min_value=min_value,
            max_value=max_value,
            step=step,
            format="%.2f",
            key=num_key,
            on_change=_on_num_change,
            label_visibility="visible",
            disabled=disabled,
        )

    return float(st.session_state[slider_key])
