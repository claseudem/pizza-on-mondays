import streamlit as st
import pandas as pd
import plotly.graph_objects as go
 
# Configurar página
st.set_page_config(page_title="Análisis de Acciones", layout="wide")

# Título principal
st.markdown("# 📈 Análisis de Acciones")
st.markdown("Bienvenido a tu dashboard de monitoreo de acciones")

# Cargar datos
df = pd.read_excel("/workspaces/pizza-on-mondays/src/data/datos.xlsx")

st.dataframe(df)