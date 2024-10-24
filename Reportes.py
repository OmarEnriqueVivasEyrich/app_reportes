import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import os

# Título de la app
st.title("Generación automática de reportes de la TRM:")

# Descripción debajo del título
st.write("Esta aplicación obtiene datos de la TRM desde una API pública, analiza los valores obtenidos, "
         "y permite descargar un reporte en PDF con las estadísticas y variaciones más importantes de la TRM, "
         "además de una gráfica que muestra las fluctuaciones de los últimos 30 días.")

# Función para obtener y procesar los datos de la API
def obtener_datos_trm():
    url = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
    
    # Obtener solo los últimos 30 días de datos
    params = {
        "$order": "vigenciadesde DESC",
        "$limit": 30  # Limitar a los últimos 30 registros
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        df['vigenciadesde'] = pd.to_datetime(df['vigenciadesde'])
        df['valor'] = df['valor'].astype(float)
        return df
    else:
        st.error(f"Error al obtener los datos: {response.status_code}")
        return pd.DataFrame()

# Función para generar la gráfica con cambios de color corregidos
def generar_grafica_corregida(df):
    plt.figure(figsize=(10, 6))

    # Dibujar cada segmento de línea de acuerdo a si sube (rojo) o baja (verde)
    for i in range(1, len(df)):
        if df['valor'].iloc[i] > df['valor'].iloc[i - 1]:
            plt.plot(df['vigenciadesde'].iloc[i-1:i+1], df['valor'].iloc[i-1:i+1], color='red', marker='o')
        else:
            plt.plot(df['vigenciadesde'].iloc[i-1:i+1], df['valor'].iloc[i-1:i+1], color='green', marker='o')

    plt.title('TRM de los últimos 30 días')
    plt.xlabel('Fecha')
    plt.ylabel('TRM')
    plt.xticks(rotation=45)

    # Ajustar el diseño para que las etiquetas no se solapen
    plt.tight_layout()

    # Guardar la gráfica como un archivo temporal
    archivo_imagen = "grafica_trm_corregida.png"
    plt.savefig(archivo_imagen, format="png")
    plt.close()  # Cerrar la figura para liberar memoria
    
    return archivo_imagen

# Función para mostrar estadísticas antes del gráfico
def mostrar_estadisticas(df):
    valor_actual = df['valor'].iloc[0]
    valor_hace_un_dia = df['valor'].iloc[1] if len(df) > 1 else valor_actual
    porcentaje_cambio_dia = ((valor_actual - valor_hace_un_dia) / valor_hace_un_dia) * 100 if valor_hace_un_dia else 0
    
    color = "green" if porcentaje_cambio_dia > 0 else "red"
    
    # Mostrar estadísticas con color según el cambio
    st.markdown(f"<h3>Valor Actual: <span style='color:{color}'>{valor_actual:.2f}</span></h3>", unsafe_allow_html=True)
    st.markdown(f"<h4>Porcentaje de cambio respecto al día anterior: <span style='color:{color}'>{porcentaje_cambio_dia:.2f}%</span></h4>", unsafe_allow_html=True)

# Previsualización de la gráfica y mostrar estadísticas antes del botón
df_trm = obtener_datos_trm()

if not df_trm.empty:
    # Mostrar estadísticas
    mostrar_estadisticas(df_trm)

    # Generar y mostrar la gráfica
    grafica_archivo = generar_grafica_corregida(df_trm)
    st.image(grafica_archivo)

# Botón para generar y descargar el informe
if st.button("Generar y descargar informe"):
    if not df_trm.empty:
        nombre_reporte = generar_reporte_pdf(df_trm, grafica_archivo)
        
        with open(nombre_reporte, "rb") as file:
            st.download_button(
                label="Descargar Reporte PDF",
                data=file,
                file_name=nombre_reporte,
                mime="application/pdf"
            )
