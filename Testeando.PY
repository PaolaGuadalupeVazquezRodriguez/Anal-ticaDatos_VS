# Importamos las librerias que vamos a usar
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Ponemos un título para el dashboard
st.title("Dashboard de Ventas")

# Añadimos laarra par subirr archivo .csv
uploaded_file = st.file_uploader("Cargar archivo CSV", type='csv')

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
# Creamos tabla con vista previa de la base de datos
    st.subheader("Visualización de datos (vendedores.csv)")
    st.dataframe(df)

# Permitimos quee se filtren los datos por Región
    st.subheader("Filtrar por Región")
    regiones = df['REGION'].unique()
    region_sel = st.selectbox("Selecciona una Región", regiones)
    df_region = df[df['REGION'] == region_sel]
    st.dataframe(df_region)

# Creamos gráficas de las tres columnas solicitadas dependiendo de la selección del usuario
    st.subheader("Gráficas de Ventas por Región")

    columnas_metricas = ['UNIDADES VENDIDAS', 'VENTAS TOTALES', 'PORCENTAJE DE VENTAS']
    metrica_sel = st.selectbox("Selecciona la métrica que deseas graficar:", columnas_metricas)

# Se grafican los datos agrupados por Región contra la variable que se haya seleccionado
# Si se selecciona unidades vendidas o ventas totales se hace la suma por Región
    if metrica_sel=='UNIDADES VENDIDAS' or metrica_sel=='VENTAS TOTALES':
        datos_graf = df.groupby('REGION')[metrica_sel].sum().sort_values(ascending=False)
        fig, ax = plt.subplots()
        datos_graf.plot(kind='bar', ax=ax, color='darkcyan', edgecolor='black')
        ax.set_xlabel("REGIÓN")
        ax.set_ylabel(metrica_sel)
        ax.set_title(f"{metrica_sel} POR REGIÓN")
        plt.xticks(rotation=45)
        st.pyplot(fig)
# Si se selecciona porcentaje de ventas se hace el promedio por Región
    else:
        datos_graf = df.groupby('REGION')[metrica_sel].mean().sort_values(ascending=False)*100
        fig, ax = plt.subplots()
        datos_graf.plot(kind='bar', ax=ax, color='darkcyan', edgecolor='black')
        ax.set_xlabel("REGIÓN")
        ax.set_ylabel(f"{metrica_sel} [%]")
        ax.set_title(f"PROMEDIO DE {metrica_sel} POR REGIÓN")
        plt.xticks(rotation=45)
        st.pyplot(fig)

# Creamos una nueva sección para seleccionar datos por vendedor, también se puede escribir directamente el nombre que se desea buscar
    st.subheader("Buscar datos por Vendedor")
    vendedores = df['NOMBRE'].unique()
    vendedor_sel = st.selectbox("Selecciona un vendedor", vendedores)
    datos_vendedor = df[df['NOMBRE'] == vendedor_sel]
    st.dataframe(datos_vendedor)

else:
    st.info("Carga un archivo CSV para comenzar.")


