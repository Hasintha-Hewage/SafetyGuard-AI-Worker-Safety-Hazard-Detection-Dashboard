"""
Incident Audit Log View (Presentation Layer)
Full session history of every incident recorded by the live monitor, with
filtering, summary metrics, CSV export and clear-history controls.
"""

import pandas as pd
import streamlit as st
from app.config.defaults import COMPLIANT_COLOR, VIOLATION_COLOR
from app.config.state_manager import StateManager
from app.presentation_layer.theme import render_section_header

_COLUMNS = {
    "date": "Date",
    "timestamp": "Time",
    "worker_id": "Worker",
    "zone": "Zone",
    "status": "Status",
    "is_violation": "Violation",
    "confidence": "Confidence",
    "action": "Action",
}


def _to_dataframe(logs) -> pd.DataFrame:
    df = pd.DataFrame(logs)
    for col in _COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[list(_COLUMNS)].rename(columns=_COLUMNS)
    df["Violation"] = df["Violation"].fillna(False).astype(bool)
    return df


def render_audit_view() -> None:
    """Render the Incident Audit Log page."""
    top_left, top_right = st.columns([4, 1])
    with top_left:
        render_section_header(
            icon_name="history",
            title="Incident Audit Log",
            subtitle="Every worker-safety event recorded by the live monitor in this session.",
        )
    logs = StateManager.get_audit_logs()
    with top_right:
        if st.button(
            "Clear History",
            icon=":material/delete_sweep:",
            use_container_width=True,
            disabled=not logs,
        ):
            StateManager.clear_audit_logs()
            st.rerun()

    if not logs:
        st.info(
            "No incidents recorded yet. Start monitoring on the Home Dashboard and "
            "events will appear here.",
            icon=":material/info:",
        )
        return

    df = _to_dataframe(logs)

    # Summary metrics
    total = len(df)
    violations = int(df["Violation"].sum())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Events", total)
    m2.metric("Violations", violations)
    m3.metric("Compliance Rate", f"{(total - violations) / total * 100:.1f}%")
    m4.metric("Workers Seen", df["Worker"].nunique())

    # Filters
    with st.container(border=True):
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            view = st.selectbox(
                "Show", ["All events", "Violations only", "Compliant only"], key="audit_filter_view"
            )
        with f2:
            workers = sorted(df["Worker"].dropna().unique().tolist())
            picked = st.multiselect("Worker", workers, key="audit_filter_worker")
        with f3:
            query = st.text_input(
                "Search status / action", placeholder="e.g. No Helmet", key="audit_filter_query"
            )

    filtered = df
    if view == "Violations only":
        filtered = filtered[filtered["Violation"]]
    elif view == "Compliant only":
        filtered = filtered[~filtered["Violation"]]
    if picked:
        filtered = filtered[filtered["Worker"].isin(picked)]
    if query.strip():
        q = query.strip()
        mask = filtered["Status"].astype(str).str.contains(q, case=False, regex=False) | filtered[
            "Action"
        ].astype(str).str.contains(q, case=False, regex=False)
        filtered = filtered[mask]

    st.caption(f"Showing {len(filtered)} of {total} events (newest first)")
    def _row_style(row: pd.Series):
        color = (
            f"color: {VIOLATION_COLOR}; font-weight: 600"
            if row["Violation"]
            else f"color: {COMPLIANT_COLOR}"
        )
        return [color if col == "Status" else "" for col in row.index]

    st.dataframe(
        filtered.style.apply(_row_style, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Violation": st.column_config.CheckboxColumn("Violation"),
            "Confidence": st.column_config.ProgressColumn(
                "Confidence", min_value=0.0, max_value=1.0, format="%.2f"
            ),
        },
    )

    st.download_button(
        "Export CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="incident_audit_log.csv",
        mime="text/csv",
        icon=":material/download:",
    )
