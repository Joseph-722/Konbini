# dashboard_mejorado.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de página
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

st.title("📊 Dashboard Interactivo de Ventas")
st.markdown("""
Este dashboard permite visualizar la evolución de las ventas, con filtros y vistas dinámicas para facilitar el análisis temporal y de comportamiento.
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

    # Filtro de fecha
    fecha_min = df['Date'].min()
    fecha_max = df['Date'].max()
    fecha_inicio, fecha_fin = st.date_input("📅 Rango de Fechas", (fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)

    df_filtrado = df[(df['Date'] >= pd.to_datetime(fecha_inicio)) & (df['Date'] <= pd.to_datetime(fecha_fin))]

    # Filtro por línea de producto
    if 'Product line' in df.columns:
        opciones = st.multiselect("📦 Línea de Producto", df['Product line'].unique())
        if opciones:
            df_filtrado = df_filtrado[df_filtrado['Product line'].isin(opciones)]

    # Filtro por mes
    meses_ordenados = [m for m in ['January', 'February', 'March'] if m in df_filtrado['Month'].unique()]
    meses_seleccionados = st.multiselect("📆 Mes", meses_ordenados)
    if meses_seleccionados:
        df_filtrado = df_filtrado[df_filtrado['Month'].isin(meses_seleccionados)]

    # Botón para descargar datos
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
    st.metric("💰 Ventas Totales", f"${df_filtrado['Total'].sum():,.2f}")
    st.caption("Suma total en el periodo filtrado")

with col2:
    promedio_diario = df_filtrado.groupby('Date')['Total'].sum().mean()
    st.metric("📊 Promedio Diario", f"${promedio_diario:,.2f}")
    st.caption("Promedio diario de ventas")

with col3:
    st.metric("🧾 Total Transacciones", f"{len(df_filtrado):,}")
    st.caption("Cantidad de tickets generados")

st.markdown("---")

# --- Tabs de visualizaciones ---
tabs = st.tabs(["📈 Ventas", "🧾 Transacciones", "⏰ Tiempo", "⭐ Opiniones", "🧮 Otros"])

# Tab 1: Ventas
with tabs[0]:
    st.subheader("📈 Evolución de Ventas Totales")
    ventas_diarias = df_filtrado.groupby('Date')['Total'].sum().reset_index()
    fig1 = px.line(ventas_diarias, x='Date', y='Total', title='Ventas Totales por Día', markers=True, labels={'Date': 'Fecha', 'Total': 'Ventas (USD)'}, template='plotly_white')
    fig1.update_traces(line_color='darkorange')
    fig1.update_layout(title_x=0.5)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📅 Promedio de Ventas por Día de la Semana")
    ventas_dia = df_filtrado.groupby('Day')['Total'].mean().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).reset_index()
    fig3 = px.bar(ventas_dia, x='Day', y='Total', title='Promedio de Ventas Semanal', labels={'Total': 'Promedio (USD)'}, template='plotly_white', color_discrete_sequence=['#636EFA'])
    st.plotly_chart(fig3, use_container_width=True)

# Tab 2: Transacciones
with tabs[1]:
    st.subheader("🧾 Cantidad de Transacciones por Día")
    transacciones = df_filtrado.groupby('Date').size().reset_index(name='Cantidad')
    fig2 = px.bar(transacciones, x='Date', y='Cantidad', title='Transacciones Diarias', labels={'Cantidad': 'Número'}, template='plotly_white')
    st.plotly_chart(fig2, use_container_width=True)

# Tab 3: Tiempo
with tabs[2]:
    st.subheader("⏰ Distribución de Ventas por Hora del Día")
    fig4 = px.histogram(df_filtrado, x='Hour', y='Total', nbins=24, title='Ventas por Hora', labels={'Hour': 'Hora del Día', 'Total': 'Ventas Totales'}, template='plotly_white')
    st.plotly_chart(fig4, use_container_width=True)

# Tab 4: Opiniones
with tabs[3]:
    st.subheader("📊 Distribución de Calificaciones de Clientes")

    if "Rating" in df_filtrado.columns:
        data = df_filtrado["Rating"]
        mean = data.mean()
        median = data.median()
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)

        fig = go.Figure()

        # Histograma
        fig.add_trace(go.Histogram(
            x=data,
            nbinsx=12,
            marker=dict(color="royalblue", line=dict(color='white', width=1)),
            opacity=0.75,
            name="Frecuencia"
        ))

        # Líneas verticales sin etiquetas para no superponer
        fig.add_vline(x=mean, line_dash="dash", line_color="red", line_width=2)
        fig.add_vline(x=median, line_dash="dash", line_color="green", line_width=2)
        fig.add_vline(x=q1, line_dash="dot", line_color="orange", line_width=2)
        fig.add_vline(x=q3, line_dash="dot", line_color="orange", line_width=2)

        # Recuadro de estadísticas a la derecha del gráfico
        # Usamos anotaciones posicionadas fuera del rango del histograma
        max_count = np.histogram(data, bins=12)[0].max()
        y_base = max_count * 0.9
        x_stats = data.max() + 0.3  # Posición a la derecha del histograma

        stats = [
            ("Media", mean, "red"),
            ("Mediana", median, "green"),
            ("Q1", q1, "orange"),
            ("Q3", q3, "orange")
        ]

        for i, (label, val, color) in enumerate(stats):
            fig.add_annotation(
                x=x_stats,
                y=y_base - i * max_count * 0.12,
                text=f"{label}: {val:.2f}",
                showarrow=False,
                font=dict(color=color, size=12),
                align="left",
                bgcolor="white",
                bordercolor=color,
                borderwidth=1
            )

        fig.update_layout(
            title="Distribución de Calificaciones",
            xaxis_title="Calificación",
            yaxis_title="Frecuencia",
            bargap=0.05,
            template="plotly_white",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("💰 Gasto Total por Tipo de Cliente")
    if "Customer type" in df_filtrado.columns and "Total" in df_filtrado.columns:
        fig_box = px.box(df_filtrado, x="Customer type", y="Total", color="Customer type", points="outliers", color_discrete_sequence=px.colors.qualitative.Set2)
        tipos = df_filtrado["Customer type"].unique()
        for tipo in tipos:
            grupo = df_filtrado[df_filtrado["Customer type"] == tipo]["Total"]
            stats = f"""Media: {grupo.mean():.2f}\nMediana: {grupo.median():.2f}\nQ1: {grupo.quantile(0.25):.2f}\nQ3: {grupo.quantile(0.75):.2f}"""
            fig_box.add_annotation(x=tipo, y=grupo.max() * 0.5, text=stats, showarrow=False, font=dict(size=10), xanchor="center", align="left", bgcolor="white", bordercolor="black")
        fig_box.update_layout(title="Boxplot de Gastos por Tipo de Cliente", template="plotly_white")
        st.plotly_chart(fig_box, use_container_width=True)

# Tab 5: Otros
with tabs[4]:
    st.subheader("📈 Relación entre Costo e Ingreso Bruto")
    fig_scatter = px.scatter(df, x='cogs', y='gross income', title='Costo vs Ingreso Bruto', labels={'cogs': 'Costo', 'gross income': 'Ingreso'}, opacity=0.6, color_discrete_sequence=['darkorange'])
    fig_scatter.update_layout(template='plotly_white', title_x=0)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.subheader("💳 Frecuencia de Métodos de Pago")
    payment_counts = df['Payment'].value_counts().reset_index()
    payment_counts.columns = ['Método de Pago', 'Frecuencia']
    fig_bar = px.bar(payment_counts, x='Método de Pago', y='Frecuencia', text='Frecuencia', color='Método de Pago', title='Métodos de Pago', labels={'Frecuencia': 'Transacciones'})
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(template='plotly_white', title_x=0)
    st.plotly_chart(fig_bar, use_container_width=True)

# Reflexión
st.markdown("---")
st.markdown("### 💬 Reflexión Final")
st.markdown("""
El análisis interactivo revela patrones valiosos como días pico, comportamiento por hora, y diferencias por tipo de cliente. 
Con esta base, puedes integrar más gráficos y predicciones para enriquecer la toma de decisiones.
""")
