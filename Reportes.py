import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

# Título de la app
st.title("Generación automática de reportes de la TRM")

# Descripción debajo del título
st.write("Esta aplicación obtiene datos de la TRM desde una API pública, analiza los valores obtenidos, y permite descargar un reporte en PDF con las estadísticas más importantes y variaciones de la TRM.")

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

# Función para generar la gráfica
def generar_grafica(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df['vigenciadesde'], df['valor'], marker='o')
    plt.title('Variación de la TRM a lo largo del tiempo')
    plt.xlabel('Fecha')
    plt.ylabel('TRM')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar la gráfica como un archivo temporal
    archivo_imagen = "grafica_trm.png"
    plt.savefig(archivo_imagen, format="png")
    plt.close()  # Cerrar la figura para liberar memoria
    
    return archivo_imagen

# Función para generar el PDF del reporte
def generar_reporte_pdf(df, grafica_archivo):
    valor_actual = df['valor'].iloc[0]  # Valor más reciente
    valor_hace_un_dia = df['valor'].iloc[1] if len(df) > 1 else valor_actual
    valor_hace_una_semana = df['valor'].iloc[7] if len(df) > 7 else valor_actual
    valor_hace_un_mes = df['valor'].iloc[30] if len(df) > 30 else valor_actual

    max_valor = df['valor'].max()
    min_valor = df['valor'].min()
    promedio_valor = df['valor'].mean()
    mediana_valor = df['valor'].median()

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

    # Insertar gráfica en el PDF
    pdf.ln(10)
    pdf.image(grafica_archivo, x=10, y=pdf.get_y(), w=180)

    # Guardar PDF
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"TRM_Reporte_{fecha_actual}.pdf"
    pdf.output(nombre_archivo)
    
    # Eliminar el archivo de la gráfica temporal
    os.remove(grafica_archivo)
    
    return nombre_archivo

# Botón para generar y descargar el informe
if st.button("Generar y descargar informe"):
    df_trm = obtener_datos_trm()
    if not df_trm.empty:
        grafica_archivo = generar_grafica(df_trm)
        nombre_reporte = generar_reporte_pdf(df_trm, grafica_archivo)
        
        with open(nombre_reporte, "rb") as file:
            st.download_button(
                label="Descargar Reporte PDF",
                data=file,
                file_name=nombre_reporte,
                mime="application/pdf"
            )
