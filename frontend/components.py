"""
Reusable UI Components for Streamlit Dashboard.
Render HTML cards, banners, headers, and badge indicators.
"""

import streamlit as st


def render_hero_banner(title: str, subtitle: str) -> None:
    """Render top header banner with modern typography and gradient effects."""
    html = f"""
    <div class="hero-banner">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: str = "📊", subtext: str = "") -> None:
    """Render glassmorphism statistic card.

    Args:
        label (str): Card title label.
        value (str): Main count/metric value.
        icon (str): Emoji icon.
        subtext (str): Sub-label detail.
    """
    html = f"""
    <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="metric-label">{label}</div>
            <div style="font-size: 1.4rem;">{icon}</div>
        </div>
        <div class="metric-value" style="margin-top: 8px;">{value}</div>
        <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_section_header(title: str, description: str = "", icon: str = "✨") -> None:
    """Render section header with subtitle."""
    st.markdown(
        f"""
        <div style="margin-top: 16px; margin-bottom: 12px;">
            <h3 style="margin: 0; color: #f8fafc; font-weight: 700; font-size: 1.4rem;">
                {icon} {title}
            </h3>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                {description}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
