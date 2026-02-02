import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

def render_radar_chart(input_data: dict):
    """
    Renders a Radar Chart comparing User's Inputs vs 'Safe' Baselines or Max Limits.
    """
    # Normalize keys/values for display
    # Filter out non-numeric
    categories = []
    values = []
    
    for k, v in input_data.items():
        if isinstance(v, (int, float)) and v > 0 and 'gender' not in k.lower():
            categories.append(k.replace('_', ' ').title())
            values.append(v)
            
    if not categories:
        st.info("Not enough data for Radar Chart")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Status',
        line_color='#FF4B4B'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.2 if values else 100]
            )),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)  # Still valid for plotly_chart

def render_trend_chart(records: list, metric_key: str, label: str):
    """
    Renders a Line Chart for a specific metric over time.
    records: List of dicts from api.fetch_records()
    """
    if not records:
        st.info("No historical data for trends.")
        return

    # Extract Data
    dates = []
    values = []
    
    import json
    for r in records:
        try:
            d = json.loads(r['data'])
            if metric_key in d:
                dates.append(r['timestamp'])
                values.append(d[metric_key])
        except:
            continue
            
    if not dates:
        st.warning(f"No data found for {label}")
        return
        
    df = pd.DataFrame({"Date": dates, label: values})
    fig = px.line(df, x="Date", y=label, markers=True, title=f"{label} Over Time")
    fig.update_layout(xaxis_title="Checkup Date", yaxis_title=label)
    
    st.plotly_chart(fig, use_container_width=True)  # Still valid for plotly_chart
