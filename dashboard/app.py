
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import os
import time

# Configuración de página
st.set_page_config(
    page_title="Valenbisi Dashboard",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1.2em;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# Conexión a Base de Datos
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=int(os.getenv('DB_PORT', 5432)),
        dbname=os.getenv('DB_NAME', 'valenbisi'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )

def load_data(query):
    conn = get_db_connection()
    return pd.read_sql(query, conn)

# Título y Descripción
st.title("🚲 Valenbisi Analytics Dashboard")
st.markdown("Monitorización en tiempo real y análisis histórico del sistema de bicicletas públicas de Valencia.")

# Sidebar - Filtros
with st.sidebar:
    st.header("filtros")
    refresh_rate = st.slider("Frecuencia de actualización (seg)", 30, 300, 60)
    
    # Auto-refresh logic handled by external rerun if needed, 
    # but Streamlit runs script top-to-bottom. 
    # For now, manual refresh button is simpler.
    if st.button("Actualizar Datos"):
        st.cache_data.clear()

# Consultas SQL
LATEST_STATUS_QUERY = """
SELECT * FROM valenbisi_latest
"""

HOURLY_TRENDS_QUERY = """
SELECT 
    hour_pk,
    AVG(avg_available_bikes) as available_bikes,
    AVG(avg_available_slots) as available_slots
FROM hourly_usage
GROUP BY 1
ORDER BY 1
"""

# Cargar datos
try:
    df_latest = load_data(LATEST_STATUS_QUERY)
    df_hourly = load_data(HOURLY_TRENDS_QUERY)
    
    # KPIs Principales
    col1, col2, col3, col4 = st.columns(4)
    
    total_stations = len(df_latest)
    active_stations = len(df_latest[df_latest['station_status'] == 'OPEN'])
    total_bikes = df_latest['available_bikes'].sum()
    total_slots = df_latest['available_slots'].sum()
    
    col1.metric("Estaciones Totales", total_stations)
    col2.metric("Estaciones Activas", active_stations)
    col3.metric("Bicis Disponibles", total_bikes)
    col4.metric("Huecos Libres", total_slots)
    
    # Mapa de Estaciones
    st.subheader("📍 Disponibilidad en Tiempo Real")
    
    # Color según disponibilidad
    df_latest['color_scale'] = df_latest['available_bikes'] / df_latest['total_capacity']
    
    fig_map = px.scatter_mapbox(
        df_latest,
        lat="latitude",
        lon="longitude",
        hover_name="station_name",
        hover_data=["available_bikes", "available_slots", "total_capacity"],
        color="available_bikes",
        size="total_capacity",
        color_continuous_scale=px.colors.sequential.Viridis,
        zoom=12,
        height=600
    )
    fig_map.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Gráficos de Análisis
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("🕒 Tendencia Horaria (Promedio)")
        if not df_hourly.empty:
            fig_hourly = px.line(
                df_hourly, 
                x='hour_pk', 
                y=['available_bikes', 'available_slots'],
                markers=True,
                labels={'value': 'Cantidad', 'hour_pk': 'Hora del día', 'variable': 'Métrica'}
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("No hay suficientes datos históricos para mostrar tendencias horarias.")
            
    with col_g2:
        st.subheader("📊 Top Estaciones con más Bicis")
        top_stations = df_latest.nlargest(10, 'available_bikes')
        fig_bar = px.bar(
            top_stations,
            x='available_bikes',
            y='station_name',
            orientation='h',
            title='Top 10 Estaciones por Disponibilidad'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabla de Datos
    with st.expander("Ver datos brutos por estación"):
        st.dataframe(df_latest)

except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.info("Asegúrate de que los contenedores están corriendo y la base de datos se ha inicializado.")

# Footer
st.markdown("---")
st.markdown("Valenbisi Dashboard © 2024")
