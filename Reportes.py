import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import os

# Definir el título de la aplicación
st.title("Generación automática de reportes de la TRM:")

# Escribir la descripción de la aplicación debajo del título
st.write("Esta aplicación obtiene datos de la TRM desde una API pública, analiza los valores obtenidos, "
         "y permite descargar un reporte en PDF con las estadísticas y variaciones más importantes de la TRM, "
         "además de una gráfica que muestra las fluctuaciones de los últimos 30 días.")

# Crear una función para obtener y procesar los datos desde la API
def obtener_datos_trm():
    url = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
    
    # Obtener los datos limitados a los últimos 30 días
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

# Crear una función para generar la gráfica con cambios de color según fluctuación
def generar_grafica_corregida(df):
    plt.figure(figsize=(10, 6))

    # Dibujar cada segmento de línea en función de si el valor sube (verde) o baja (rojo)
    for i in range(1, len(df)):
        if df['valor'].iloc[i] > df['valor'].iloc[i - 1]:
            plt.plot(df['vigenciadesde'].iloc[i-1:i+1], df['valor'].iloc[i-1:i+1], color='red', marker='o')
        else:
            plt.plot(df['vigenciadesde'].iloc[i-1:i+1], df['valor'].iloc[i-1:i+1], color='green', marker='o')

    # Establecer el título y las etiquetas de los ejes
    plt.title('TRM de los últimos 30 días')
    plt.xlabel('Fecha')
    plt.ylabel('TRM')
    plt.xticks(rotation=45)

    # Ajustar el diseño para evitar el solapamiento de etiquetas
    plt.tight_layout()

    # Guardar la gráfica como un archivo temporal
    archivo_imagen = "grafica_trm_corregida.png"
    plt.savefig(archivo_imagen, format="png")
    plt.close()  # Cerrar la figura para liberar memoria
    
    return archivo_imagen

# Crear una función para generar el reporte PDF
def generar_reporte_pdf(df, grafica_archivo):
    # Definir los valores actuales y pasados
    valor_actual = df['valor'].iloc[0]  # Valor más reciente
    valor_hace_un_dia = df['valor'].iloc[1] if len(df) > 1 else valor_actual
    valor_hace_una_semana = df['valor'].iloc[6] if len(df) > 7 else valor_actual
    valor_hace_un_mes = df['valor'].iloc[29] if len(df) > 30 else valor_actual

    # Calcular estadísticas clave
    max_valor = df['valor'].max()
    min_valor = df['valor'].min()
    promedio_valor = df['valor'].mean()
    mediana_valor = df['valor'].median()

    # Calcular los porcentajes de cambio respecto a días anteriores
    porcentaje_cambio_dia = ((valor_actual - valor_hace_un_dia) / valor_hace_un_dia) * 100 if valor_hace_un_dia else 0
    porcentaje_cambio_semanal = ((valor_actual - valor_hace_una_semana) / valor_hace_una_semana) * 100 if valor_hace_una_semana else 0
    porcentaje_cambio_mensual = ((valor_actual - valor_hace_un_mes) / valor_hace_un_mes) * 100 if valor_hace_un_mes else 0

    # Crear el documento PDF
    pdf = FPDF()
    pdf.add_page()

    # Definir el título del documento
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Reporte de la TRM con datos del último mes", ln=True, align='C')
    pdf.ln(10)

    # Escribir las estadísticas clave
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Estadísticas relevantes:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Valor máximo: {max_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor mínimo: {min_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor promedio: {promedio_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Mediana: {mediana_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Último valor: {valor_actual:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace un día: {valor_hace_un_dia:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace una semana: {valor_hace_una_semana:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace un mes: {valor_hace_un_mes:.2f}", ln=True)

    # Incluir los cambios porcentuales
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Cambios porcentuales:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Porcentaje de cambio respecto al día anterior: {porcentaje_cambio_dia:.2f}%", ln=True)
    pdf.cell(200, 10, f"Porcentaje de cambio respecto a la semana anterior: {porcentaje_cambio_semanal:.2f}%", ln=True)
    pdf.cell(200, 10, f"Porcentaje de cambio respecto al mes anterior: {porcentaje_cambio_mensual:.2f}%", ln=True)

    # Insertar la gráfica en el PDF
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Gráfico de la TRM:", ln=True)
    pdf.image(grafica_archivo, x=10, y=pdf.get_y(), w=180)

    # Guardar el archivo PDF
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"TRM_Reporte_{fecha_actual}.pdf"
    pdf.output(nombre_archivo)
    
    # Eliminar el archivo temporal de la gráfica si existe
    if os.path.exists(grafica_archivo):
        os.remove(grafica_archivo)
    
    return nombre_archivo

# Previsualizar la gráfica y mostrar estadísticas antes del botón

df_trm = obtener_datos_trm()

if not df_trm.empty:
    # Obtener el valor actual y calcular el porcentaje de cambio
    valor_actual = df_trm['valor'].iloc[0]
    valor_hace_un_dia = df_trm['valor'].iloc[1] if len(df_trm) > 1 else valor_actual
    porcentaje_cambio_dia = ((valor_actual - valor_hace_un_dia) / valor_hace_un_dia) * 100 if valor_hace_un_dia else 0

    # Definir el color de visualización del porcentaje de cambio
    color = "green" if porcentaje_cambio_dia > 0 else "red"
    
    st.markdown(f"<h3>Valor Actual: <span style='color:{color}'>{valor_actual:.2f}</span></h3>", unsafe_allow_html=True)
    st.markdown(f"<h4>Porcentaje de cambio respecto al día anterior: <span style='color:{color}'>{porcentaje_cambio_dia:.2f}%</span></h4>", unsafe_allow_html=True)

    # Generar la gráfica
    grafica_archivo = generar_grafica_corregida(df_trm)

    # Mostrar la gráfica en Streamlit
    st.image(grafica_archivo)

# Crear un botón para generar y descargar el informe
if st.button("Generar y descargar informe"):
    if not df_trm.empty:
        nombre_reporte = generar_reporte_pdf(df_trm, grafica_archivo)
        
        # Habilitar la descarga del archivo PDF
        with open(nombre_reporte, "rb") as file:
            st.download_button(
                label="Descargar Reporte PDF",
                data=file,
                file_name=nombre_reporte,
                mime="application/pdf"
            )
