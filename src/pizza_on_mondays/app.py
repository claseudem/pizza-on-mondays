from pathlib import Path

import streamlit as st

ICON_PATH = Path(__file__).parent / "assets" / "moai_icon.png"

PAGES = [
    st.Page("pages/1_🏠_Inicio.py", title="Inicio", icon="🏠", default=True),
    st.Page("pages/2_🔎_Descriptor_de_empresas.py", title="Descriptor de empresas", icon="🔎"),
    st.Page("pages/3_📈_QuantStats_vs_Benchmark.py", title="QuantStats vs Benchmark", icon="📈"),
]


def main() -> None:
    st.set_page_config(page_title="MoaInvest", page_icon=str(ICON_PATH), layout="wide")
    st.navigation(PAGES).run()


if __name__ == "__main__":
    main()
