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

# Colocamos la URL de la API
url = "https://www.datos.gov.co/resource/ceyp-9c7c.json"

# Inicializamos el DataFrame vacío
df = pd.DataFrame()

# Colocamos los parámetros de la extracción
limit = 10000
offset = 0

while True:
    params = {
        "$limit": limit,
        "$offset": offset
    }

    # Hacemos la solicitud GET a la API con los parámetros de la extracción
    response = requests.get(url, params=params)
    
    # Verificamos si la solicitud fue exitosa
    if response.status_code == 200:
        # Convertimos la respuesta en JSON
        data = response.json()
        
        # Convertimos los datos a un DataFrame temporal
        temp_df = pd.DataFrame(data)
        
        if temp_df.empty:
            break
        
        # Concatenamos los datos al DataFrame principal
        df = pd.concat([df, temp_df], ignore_index=True)
        
        offset += limit
    else:
        st.error(f"Error al obtener los datos: {response.status_code}")
        break

# Convertimos las columnas de fecha a datetime
df['vigenciadesde'] = pd.to_datetime(df['vigenciadesde'])
df['vigenciahasta'] = pd.to_datetime(df['vigenciahasta'])

# Formateamos las fechas en el formato 'YYYY-MM-DD'
df['vigenciadesde'] = df['vigenciadesde'].dt.strftime('%Y-%m-%d')
df['vigenciahasta'] = df['vigenciahasta'].dt.strftime('%Y-%m-%d')

# Extendemos el dataframe
df_extendido = df.copy()
new_rows = []
for index, row in df_extendido.iterrows():
    vigenciadesde = pd.to_datetime(row['vigenciadesde'])
    vigenciahasta = pd.to_datetime(row['vigenciahasta'])
    
    if vigenciahasta > vigenciadesde:
        for day in pd.date_range(start=vigenciadesde, end=vigenciahasta):
            new_row = row.to_dict()
            new_row['vigenciadesde'] = day
            new_row['vigenciahasta'] = day
            new_rows.append(new_row)
    else:
        new_rows.append(row.to_dict())

df_extendido = pd.DataFrame(new_rows)

# Renombramos y eliminamos columnas
df_extendido = df_extendido.rename(columns={'vigenciadesde': 'fecha'})
df_extendido = df_extendido.drop('vigenciahasta', axis=1)

# Convertimos la columna 'valor' a tipo float
df_extendido['valor'] = df_extendido['valor'].astype(float)

# Agrupamos por año
df_extendido['fecha'] = pd.to_datetime(df_extendido['fecha'])
df_extendido['year'] = df_extendido['fecha'].dt.year
grouped = df_extendido.groupby('year')

# Preparamos el gráfico (sin mostrarlo en la app)
plt.figure(figsize=(10, 6))
for year, group in grouped:
    plt.scatter(group['fecha'], group['valor'], label=str(year), color='g', marker='.')

plt.xlabel('Fecha')
plt.ylabel('Valor')
plt.title('Diagrama de Dispersión Valor vs Fecha (Anual)')
plt.grid(True)
plt.tight_layout()

# Guardamos el gráfico en un archivo temporal
buffer = BytesIO()
plt.savefig(buffer, format="png")
buffer.seek(0)

# Botón para generar y descargar el reporte en PDF
if st.button("Generar y descargar reporte"):

    # Creamos el documento PDF
    pdf = FPDF()
    pdf.add_page()

    # Título centrado
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Reporte de la TRM", ln=True, align="C")

    # Agregar espacio
    pdf.ln(10)

    # Hallamos los valores de interés
    valor_actual = df_extendido['valor'].iloc[-1]
    max_valor = df_extendido['valor'].max()
    min_valor = df_extendido['valor'].min()
    promedio_valor = df_extendido['valor'].mean()

    # Agregamos los valores al PDF
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"El valor máximo alcanzado es: {max_valor}", ln=True)
    pdf.cell(200, 10, f"El valor mínimo alcanzado es: {min_valor}", ln=True)
    pdf.cell(200, 10, f"El valor promedio es: {promedio_valor}", ln=True)
    pdf.cell(200, 10, f"El último valor es: {valor_actual}", ln=True)

    # Agregar espacio
    pdf.ln(10)

    # Insertar imagen del gráfico
    pdf.image(buffer, x=10, y=pdf.get_y(), w=180)

    # Guardamos el PDF en memoria
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    # Descargar el archivo PDF
    st.download_button(
        label="Descargar informe",
        data=pdf_output,
        file_name=f"TRM_Reporte_{datetime.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf"
    )
