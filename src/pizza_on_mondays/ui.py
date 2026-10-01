from pathlib import Path

import streamlit as st


TITLE_COLOR = "#87CEFA"  # azul claro
ICON_PATH = Path(__file__).parent / "assets" / "moai_icon.png"


def colored_title(text: str) -> None:
    st.markdown(f"<h1 style='color:{TITLE_COLOR}'>{text}</h1>", unsafe_allow_html=True)


def colored_subheader(text: str) -> None:
    st.markdown(f"<h3 style='color:{TITLE_COLOR}'>{text}</h3>", unsafe_allow_html=True)
