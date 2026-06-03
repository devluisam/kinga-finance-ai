import streamlit as st

STYLES = {
    "danger":  ("rgba(255,75,75,0.12)",  "#FF4B4B", "🚨"),
    "warning": ("rgba(255,179,0,0.12)",  "#FFB300", "⚠️"),
    "info":    ("rgba(0,200,150,0.12)",  "#00C896", "✅"),
}


def render_alerts(alerts: list[dict]) -> None:
    st.markdown("### 📢 Alertas do Agente")
    if not alerts:
        st.info("Nenhum alerta para este período.")
        return

    cols = st.columns(min(len(alerts), 2))
    for i, alert in enumerate(alerts):
        level = alert.get("level", "info")
        bg, border, icon = STYLES.get(level, STYLES["info"])
        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    border:1px solid {border};
                    border-left:4px solid {border};
                    border-radius:10px;
                    padding:14px 16px;
                    margin-bottom:12px;
                    height:100%;
                ">
                    <div style="font-size:1rem;font-weight:700;color:{border};margin-bottom:6px;">
                        {icon} {alert['title']}
                    </div>
                    <div style="font-size:0.88rem;color:#ccc;margin-bottom:8px;line-height:1.5;">
                        {alert['message']}
                    </div>
                    <div style="font-size:0.83rem;color:{border};font-style:italic;">
                        💡 {alert['suggestion']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
