import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# Título de la aplicación
st.title("Generación automática de reportes de la TRM:")

# Descripción debajo del título
st.write(" ")
st.write("Esta aplicación obtiene datos de la TRM desde una API pública, analiza los valores obtenidos, y permite descargar un reporte en PDF con los porcentajes de cambio más importantes de la TRM, además de un gráfico para ilustrar los movimientos de la TRM.")
st.write(" ")

# Función para obtener y procesar los datos de la API
def obtener_datos_trm():
    url = "https://www.datos.gov.co/resource/ceyp-9c7c.json"
    df = pd.DataFrame()
    limit = 10000
    offset = 0

    while True:
        params = {"$limit": limit, "$offset": offset}
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            temp_df = pd.DataFrame(data)
            if temp_df.empty:
                break
            df = pd.concat([df, temp_df], ignore_index=True)
            offset += limit
        else:
            st.error(f"Error al obtener los datos: {response.status_code}")
            break

    # Procesamiento de fechas y valores
    df['vigenciadesde'] = pd.to_datetime(df['vigenciadesde'])
    df['vigenciahasta'] = pd.to_datetime(df['vigenciahasta'])
    df['vigenciadesde'] = df['vigenciadesde'].dt.strftime('%Y-%m-%d')
    df['vigenciahasta'] = df['vigenciahasta'].dt.strftime('%Y-%m-%d')
    df['valor'] = df['valor'].astype(float)

    return df

# Función para generar la gráfica
def generar_grafica(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df['vigenciadesde'], df['valor'], marker='o')
    plt.title('Variación de la TRM a lo largo del tiempo')
    plt.xlabel('Fecha')
    plt.ylabel('TRM')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar la gráfica en un buffer en memoria
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    
    return buffer

# Función para generar el PDF del reporte
def generar_reporte_pdf(df, grafica_buffer):
    valor_actual = df['valor'].iloc[-1]
    valor_hace_un_dia = df['valor'].iloc[-2]
    valor_hace_una_semana = df['valor'].iloc[-7]
    valor_hace_un_mes = df['valor'].iloc[-30]

    max_valor = df['valor'].max()
    min_valor = df['valor'].min()
    promedio_valor = df['valor'].mean()
    mediana_valor = df['valor'].median()

    diferencia_diaria_valor = valor_actual - valor_hace_un_dia
    diferencia_semanal_valor = valor_actual - valor_hace_una_semana
    diferencia_mensual_valor = valor_actual - valor_hace_un_mes

    porcentaje_cambio_dia = (diferencia_diaria_valor / valor_hace_un_dia) * 100
    porcentaje_cambio_semanal = (diferencia_semanal_valor / valor_hace_una_semana) * 100
    porcentaje_cambio_mensual = (diferencia_mensual_valor / valor_hace_un_mes) * 100

    # Creación del PDF
    pdf = FPDF()
    pdf.add_page()

    # Título del documento
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Reporte de la TRM", ln=True, align='C')
    pdf.ln(10)

    # Valores relevantes
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Valores relevantes:", ln=True)
    pdf.cell(200, 10, f"Valor máximo: {max_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor mínimo: {min_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor promedio: {promedio_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Mediana: {mediana_valor:.2f}", ln=True)
    pdf.cell(200, 10, f"Último valor: {valor_actual:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace un día: {valor_hace_un_dia:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace una semana: {valor_hace_una_semana:.2f}", ln=True)
    pdf.cell(200, 10, f"Valor hace un mes: {valor_hace_un_mes:.2f}", ln=True)

    # Porcentajes de cambio
    pdf.ln(10)
    pdf.cell(200, 10, "Porcentaje de cambio:", ln=True)
    pdf.cell(200, 10, f"Diario: {porcentaje_cambio_dia:.2f}%", ln=True)
    pdf.cell(200, 10, f"Semanal: {porcentaje_cambio_semanal:.2f}%", ln=True)
    pdf.cell(200, 10, f"Mensual: {porcentaje_cambio_mensual:.2f}%", ln=True)

    # Insertar gráfica en el PDF
    pdf.ln(10)
    pdf.image(grafica_buffer, x=10, y=pdf.get_y(), w=180)

    # Guardar PDF
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"TRM_Reporte_{fecha_actual}.pdf"
    pdf.output(nombre_archivo)
    
    return nombre_archivo

# Botón para generar y descargar el informe
if st.button("Generar y descargar informe"):
    df_trm = obtener_datos_trm()
    grafica_buffer = generar_grafica(df_trm)
    nombre_reporte = generar_reporte_pdf(df_trm, grafica_buffer)
    
    with open(nombre_reporte, "rb") as file:
        st.download_button(
            label="Descargar Reporte PDF",
            data=file,
            file_name=nombre_reporte,
            mime="application/pdf"
        )
