import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Simple Data Dashboard")

uploaded_file = st.file_uploader("Choose a file", type='csv')

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Data Preview")
    st.write(df.head())

    st.subheader("Data Summary")
    st.write(df.describe())

    st.subheader("Filter Data")
    columns = df.columns.tolist()
    selected_column = st.selectbox("Select region to filter by", columns)
    unique_values = df[selected_column].unique()
    selected_value = st.selectbox("Select value", unique_values)

    filtered_df = df[df[selected_column] == selected_value]
    st.write(filtered_df)

else:
    with st.spinner("Waiting for file upload..."):
        st.empty()

#Muestre la tabla y pueda ser filtrada por Region.
#Muestre gráficas de Unidades Vendidas, Ventas Totales y Porcentajes de Ventas.
#Muestre los datos de un vendedor específico