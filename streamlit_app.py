import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de página
st.set_page_config(page_title="Dashboard de Ventas - Marketing", layout="wide")

st.title("📊 Dashboard Estratégico de Ventas y Marketing")
st.markdown("""
Este dashboard permite analizar diversos aspectos del negocio para apoyar la toma de decisiones estratégicas en marketing. A través de diferentes visualizaciones, puedes detectar patrones de comportamiento, evaluar el desempeño de productos, conocer las preferencias de los clientes y optimizar campañas.
""")

# --- Carga de datos con caché ---
@st.cache_data

def cargar_datos():
    df = pd.read_csv("data.csv")
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M', errors='coerce')
    df['Day'] = df['Date'].dt.day_name()
    df['Month'] = df['Date'].dt.month_name()
    df['Hour'] = df['Time'].dt.hour
    return df.dropna()

df = cargar_datos()

# --- Filtros en barra lateral ---
with st.sidebar:
    st.header("🔍 Filtros")
    fecha_min = df['Date'].min()
    fecha_max = df['Date'].max()
    fecha_inicio, fecha_fin = st.date_input("📅 Rango de Fechas", (fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)
    df_filtrado = df[(df['Date'] >= pd.to_datetime(fecha_inicio)) & (df['Date'] <= pd.to_datetime(fecha_fin))]

    if 'Product line' in df.columns:
        opciones = st.multiselect("📦 Línea de Producto", df['Product line'].unique())
        if opciones:
            df_filtrado = df_filtrado[df_filtrado['Product line'].isin(opciones)]

    meses_ordenados = [m for m in ['January', 'February', 'March'] if m in df_filtrado['Month'].unique()]
    meses_seleccionados = st.multiselect("📆 Mes", meses_ordenados)
    if meses_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Month'].isin(meses_seleccionados)]

    st.download_button(
        label="📥 Descargar datos filtrados",
        data=df_filtrado.to_csv(index=False),
        file_name="ventas_filtradas.csv",
        mime="text/csv"
    )

# --- Indicadores clave ---
st.markdown("### 📌 Indicadores Clave")
col1, col2, col3 = st.columns(3)

with col1:
    total_ventas = df_filtrado['Total'].sum()
    st.metric("💰 Ventas Totales", f"${total_ventas:,.2f}")
    st.caption("Suma total de ventas en el periodo filtrado, útil para evaluar ingresos generales.")

with col2:
    promedio_diario = df_filtrado.groupby('Date')['Total'].sum().mean()
    st.metric("📊 Promedio Diario", f"${promedio_diario:,.2f}")
    st.caption("Promedio de ingresos por día: útil para campañas por fecha o eventos especiales.")

with col3:
    total_transacciones = len(df_filtrado)
    st.metric("🧾 Total Transacciones", f"{total_transacciones:,}")
    st.caption("Cantidad total de tickets emitidos, representa el volumen operativo.")

st.markdown("---")

# --- Tabs reorganizadas por objetivo de marketing ---
tabs = st.tabs(["📈 Ventas", "📦 Productos", "⭐ Opiniones", "🧍 Tipos de Cliente", "💳 Pagos"])

# TAB 1 - Ventas
with tabs[0]:
    st.subheader("📈 Análisis de Ventas Totales")
    st.markdown("""
    Estos gráficos permiten evaluar la evolución temporal de las ventas y cómo se distribuyen entre las distintas líneas de producto. Son clave para ajustar estrategias de precios, promociones y abastecimiento.
    """)

    ventas_diarias = df_filtrado.groupby('Date')['Total'].sum().reset_index()
    fig1 = px.line(ventas_diarias, x='Date', y='Total', title='Ventas Totales por Día', markers=True, labels={'Date': 'Fecha', 'Total': 'Ventas (USD)'}, template='plotly_white')
    fig1.update_traces(line_color='darkorange')
    fig1.update_layout(title_x=0.5)
    st.plotly_chart(fig1, use_container_width=True)

    if 'Product line' in df_filtrado.columns:
        ventas_por_producto = df_filtrado.groupby('Product line')['Total'].sum().reset_index()
        fig2 = px.bar(ventas_por_producto, x='Total', y='Product line', orientation='h', title='Ventas por Línea de Producto', color='Product line', labels={'Total': 'Ventas Totales'}, template='plotly_white')
        st.plotly_chart(fig2, use_container_width=True)

# TAB 2 - Productos
with tabs[1]:
    st.subheader("📦 Rentabilidad y Correlaciones")
    st.markdown("""
    Aquí se observa la relación entre variables numéricas y el ingreso bruto por línea de producto y sucursal, útil para focalizar esfuerzos donde se maximiza la ganancia.
    """)

    data_agrupada = df.groupby(['Branch', 'Product line'])['gross income'].sum().reset_index()
    fig3 = px.bar(data_agrupada, x='Branch', y='gross income', color='Product line', barmode='group', title='Ingreso Bruto por Sucursal y Línea de Producto', text_auto=True, template='plotly_white')
    st.plotly_chart(fig3, use_container_width=True)

    numerical_cols = ['Unit price', 'Quantity', 'Tax 5%', 'Total', 'cogs', 'gross income', 'Rating']
    corr = df[numerical_cols].corr().round(2)
    fig4 = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu', zmin=-1, zmax=1, labels=dict(color='Correlación'), title='Mapa de Calor de Correlaciones')
    st.plotly_chart(fig4, use_container_width=True)

# TAB 3 - Opiniones
with tabs[2]:
    st.subheader("⭐ Satisfacción de Clientes")
    st.markdown("""
    El análisis de calificaciones permite entender cómo perciben los clientes el servicio/producto, y su relación con el monto gastado, lo cual influye en la fidelización.
    """)

    if 'Rating' in df_filtrado.columns:
        data = df_filtrado['Rating'].dropna()
        mean = data.mean()
        median = data.median()
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)

        fig5 = px.histogram(df_filtrado, x="Rating", nbins=12, opacity=0.75, color_discrete_sequence=['royalblue'])
        fig5.add_vline(x=mean, line_dash="dash", line_color="red", annotation_text=f"Media: {mean:.2f}", annotation_position="top right")
        fig5.add_vline(x=median, line_dash="dash", line_color="green", annotation_text=f"Mediana: {median:.2f}", annotation_position="top left")
        fig5.add_vline(x=q1, line_dash="dot", line_color="orange", annotation_text=f"Q1: {q1:.2f}", annotation_position="bottom right")
        fig5.add_vline(x=q3, line_dash="dot", line_color="orange", annotation_text=f"Q3: {q3:.2f}", annotation_position="bottom left")
        fig5.update_layout(template='plotly_white', bargap=0.2)
        st.plotly_chart(fig5, use_container_width=True)

# TAB 4 - Tipos de Cliente
with tabs[3]:
    st.subheader("🧍 Segmentación por Cliente")
    st.markdown("""
    Este gráfico permite identificar diferencias de comportamiento entre tipos de cliente (miembro o normal) respecto al gasto, lo cual sirve para campañas personalizadas.
    """)

    if 'Customer type' in df_filtrado.columns and 'Total' in df_filtrado.columns:
        tipos = df_filtrado['Customer type'].unique()
        fig6 = go.Figure()
        colores = {'Member': '#DAA520', 'Normal': '#20B2AA'}

        for tipo in tipos:
            grupo = df_filtrado[df_filtrado['Customer type'] == tipo]['Total']
            fig6.add_trace(go.Box(
                y=grupo,
                name=tipo,
                boxmean='sd',
                marker_color=colores.get(tipo, 'gray'),
                fillcolor=colores.get(tipo, 'gray'),
                line_color='black'
            ))

            stats = f"""Media: {grupo.mean():.2f}<br>Mediana: {grupo.median():.2f}<br>Q1: {grupo.quantile(0.25):.2f}<br>Q3: {grupo.quantile(0.75):.2f}"""
            fig6.add_annotation(
                x=tipo, y=grupo.median(), text=stats,
                showarrow=False, yshift=30,
                font=dict(size=10), align='left',
                bgcolor='white', bordercolor='black', borderwidth=1
            )

        fig6.update_layout(title='Distribución del Gasto por Tipo de Cliente', yaxis_title='Gasto ($)', template='plotly_white')
        st.plotly_chart(fig6, use_container_width=True)

# TAB 5 - Pagos
with tabs[4]:
    st.subheader("💳 Métodos de Pago")
    st.markdown("""
    Conocer los métodos de pago preferidos permite adaptar la oferta y mejorar la experiencia del cliente, aumentando las conversiones.
    """)

    payment_counts = df['Payment'].value_counts().reset_index()
    payment_counts.columns = ['Método de Pago', 'Frecuencia']
    fig7 = px.bar(payment_counts, x='Método de Pago', y='Frecuencia', text='Frecuencia', color='Método de Pago', title='Frecuencia de Métodos de Pago')
    fig7.update_traces(textposition='outside')
    fig7.update_layout(template='plotly_white')
    st.plotly_chart(fig7, use_container_width=True)
