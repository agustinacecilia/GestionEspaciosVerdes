import streamlit as st
import pandas as pd
import folium
import seaborn as sns
import matplotlib.pyplot as plt
from folium.plugins import HeatMap
import json
import geopandas as gpd
from shapely import wkt
from streamlit_folium import folium_static
import plotly.express as px  # Importar plotly express para gráficos interactivos
from folium.plugins import MarkerCluster

# Cargar los datasets
@st.cache_data
def cargar_datos():
    registro_arboles_df = pd.read_csv('./data/RegistroArboles_actualizado.csv')
    espacios_verdes_df = pd.read_csv('./data/EspaciosVerdes.csv')
    puntos_verdes_df = pd.read_csv('./data/PuntosVerdes.csv')
    mantenimiento_arboles_df = pd.read_csv('./data/MantenimientoArboles.csv')
    barrios_df = pd.read_csv('./data/Barrios.csv')
    return registro_arboles_df, espacios_verdes_df, puntos_verdes_df, mantenimiento_arboles_df, barrios_df

# Configuración de la página
st.set_page_config(page_title="Gestion Corrientes Verde", layout="wide")

# Título principal de la aplicación
st.title("Gestión Corrientes Verde")

# Agregar una imagen o descripción
st.markdown(
    """
    <style>
    .title {
        color: #4CAF50; /* Cambia el color del texto */
        text-align: center; /* Centra el texto */
    }
    </style>
    <h2 class="title">Análisis y Visualizaciones</h2>
    """,
    unsafe_allow_html=True
)


# Cargar los datos
registro_arboles_df, espacios_verdes_df, puntos_verdes_df, mantenimiento_arboles_df, barrios_df = cargar_datos()

# Cargar el archivo CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Incluir Font Awesome
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# Función para calcular el porcentaje de árboles en mal estado
def calcular_porcentaje_mal_estado():
    arboles_mantenimiento_df = pd.merge(
        registro_arboles_df,
        mantenimiento_arboles_df,
        on='id_arbol', 
        how='left'
    )
    # Árboles en estado 'Malo' y 'Regular'
    arboles_malos = arboles_mantenimiento_df[
        arboles_mantenimiento_df['estado_salud'].isin(['Malo', 'Regular'])
    ]
    porcentaje_malos = (len(arboles_malos) / len(arboles_mantenimiento_df)) * 100
    return porcentaje_malos

# Guardar el porcentaje en una variable local para usarla más tarde
porcentaje_arboles_malos = calcular_porcentaje_mal_estado()

# Crear una función para mostrar los mapas de puntos verdes y espacios verdes
def mostrar_mapa_puntos_espacios(espacios_verdes_filtrados):
    centro_mapa = [-27.48, -58.83]
    mapa = folium.Map(location=centro_mapa, zoom_start=13)

    # Calcular la cantidad de puntos verdes y espacios verdes
    cantidad_puntos_verdes = puntos_verdes_df.dropna(subset=['lat', 'lng']).shape[0]
    cantidad_espacios_verdes = espacios_verdes_filtrados.shape[0]

     # Calcular la cantidad de puntos verdes y espacios verdes
    cantidad_puntos_verdes = puntos_verdes_df.dropna(subset=['lat', 'lng']).shape[0]
    cantidad_espacios_verdes = espacios_verdes_filtrados.shape[0]

    # Mostrar íconos representativos en la interfaz
    col1, col2 = st.columns(2)

    # Icono de Punto Verde (Reciclaje) con hover
    with col1:
        st.markdown(f"<strong>Puntos Verdes:</strong> ", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="icon">
                <i class="fa-solid fa-recycle fa-2xl" style="color: #4CAF50;"></i>
                <span class="tooltip">Cantidad de Puntos Verdes: {cantidad_puntos_verdes}</span>
            </div>
        """, unsafe_allow_html=True)

    # Icono de Espacio Verde con hover
    with col2:
        st.markdown(f"<strong>Espacios Verdes:</strong> ", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="icon">
                <i class="fa-solid fa-tree fa-2xl" style="color: #4CAF50;"></i>
                <span class="tooltip">Cantidad de Espacios Verdes: {cantidad_espacios_verdes}</span>
            </div>
        """, unsafe_allow_html=True)

    # Añadir los puntos verdes
    for _, fila in puntos_verdes_df.dropna(subset=['lat', 'lng']).iterrows():
        folium.Marker(
            location=[fila['lat'], fila['lng']],
            popup=f"Punto verde: {fila['ubicacion']}",
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(mapa)

    # Añadir los espacios verdes filtrados
    for _, fila in espacios_verdes_filtrados.iterrows():
        try:
            geo_data = json.loads(fila['st_asgeojson'])
            coords = geo_data['coordinates'][0]
            folium.Polygon(
                locations=[(coord[1], coord[0]) for coord in coords],
                color='blue',
                fill=True,
                fill_opacity=0.3,
                popup=f"Espacio verde: {fila.get('gid', 'Sin nombre')}"
            ).add_to(mapa)
        except Exception:
            continue

    # Mostrar el mapa
    folium_static(mapa)

# Crear un gráfico de estados de salud de los árboles
def grafico_estado_salud():
    st.write("""
        Los árboles son esenciales para la salud de nuestra ciudad como la calidad del aire y así también para el bienestar de los ciudadanos.
        En esta sección, se analiza el estado de salud de los árboles de la ciudad de Corrientes, 
        ayudando a identificar áreas que requieren mayor mantenimiento para su conservación, asegurando que nuestros árboles 
        sigan beneficiando a la comunidad y al medio ambiente.
    """)
    
    arboles_mantenimiento_df = pd.merge(
        registro_arboles_df,
        mantenimiento_arboles_df,
        on='id_arbol', 
        how='left'
    )
    
    # Conteo del estado de salud
    conteo_estado_salud = arboles_mantenimiento_df['estado_salud'].value_counts().reset_index()
    conteo_estado_salud.columns = ['Estado de Salud', 'Cantidad']

    # Crear el gráfico de barras interactivo con Plotly Express
    fig = px.bar(
        conteo_estado_salud,
        x='Estado de Salud',
        y='Cantidad',
        title='Estado de Salud de los Árboles',
        color='Estado de Salud',
        hover_data={'Cantidad': True},
        labels={'Estado de Salud': 'Estado de Salud', 'Cantidad': 'Número de Árboles'},
        color_discrete_sequence=[
            px.colors.qualitative.Alphabet[9],
            px.colors.qualitative.Alphabet[15],
            px.colors.qualitative.Plotly[6],
            px.colors.qualitative.Plotly[1]
        ],
    )

    # Personalizar la apariencia del gráfico
    fig.update_layout(
        xaxis_title='Estado de Salud',
        yaxis_title='Número de Árboles',
        plot_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo claro
        paper_bgcolor='rgba(245, 245, 245, 1)',  # Fondo del gráfico
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco del hover
            bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
            font=dict(color='#333', size=14)  # Color y tamaño del texto
        ),
        height=600,  # Ajustar la altura del gráfico
    )
    
    # Actualizar las etiquetas de hover
    fig.update_traces(
        hovertemplate='<b>Estado de Salud:</b> %{x}<br><b>Cantidad de Árboles:</b> %{y}<extra></extra>'
    )
    
    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)

    # Mostrar el porcentaje de árboles que requieren mantenimiento
    porcentaje_arboles_malos = calcular_porcentaje_mal_estado()  # Asegúrate de que esta función esté definida
    st.write(f"**Porcentaje de árboles que necesitan mantenimiento**: {porcentaje_arboles_malos:.2f}%")

    # Crear gráfico de dona para el porcentaje de árboles que requieren mantenimiento
    estado_mantenimiento = ['Malo', 'Regular', 'No Requiere Mantenimiento']
    cantidades = [
        len(arboles_mantenimiento_df[arboles_mantenimiento_df['estado_salud'] == 'Malo']),
        len(arboles_mantenimiento_df[arboles_mantenimiento_df['estado_salud'] == 'Regular']),
        len(arboles_mantenimiento_df) - len(arboles_mantenimiento_df[arboles_mantenimiento_df['estado_salud'].isin(['Malo', 'Regular'])])
    ]

    fig_dona = px.pie(
        names=estado_mantenimiento,
        values=cantidades,
        hole=0.6,  # Hacer una dona
        color_discrete_sequence=[
            px.colors.qualitative.Prism[3],
            px.colors.qualitative.Plotly[6],
            px.colors.qualitative.Plotly[1]  # Puedes cambiar este color si es necesario
        ],  # Colores personalizados para malo, regular y no requiere mantenimiento
    )

    # Personalizar la apariencia del gráfico de dona
    fig_dona.update_traces(
        hovertemplate='<b>Tipo de Mantenimiento:</b> %{label}<br><b><extra></extra>',
        textposition='inside',  # Asegurar que el texto esté dentro de las porciones
        insidetextorientation='radial',  # Forzar que el texto esté dentro de la porción
        textfont_size=12,  # Ajustar el tamaño del texto
        textfont_color='white',  # Forzar que el color del texto sea blanco en todas las porciones
        insidetextfont=dict(size=12, color='white')
)

    # Personalizar el layout del gráfico
    fig_dona.update_layout(
        showlegend=False,  # Quitar la leyenda
        margin=dict(l=0, r=0, t=0, b=0),  # Márgenes pequeños para hacerla compacta
        height=250,  # Ajustar el alto
        width=250,   # Ajustar el ancho
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Fondo transparente
        paper_bgcolor='rgba(0, 0, 0, 0)',  # Fondo transparente
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco del hover
            bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
            font=dict(color='#333', size=14)  # Color del texto y tamaño
        )
    )

    # Mostrar la gráfica de dona justo debajo del texto
    st.plotly_chart(fig_dona, use_container_width=True)

    # Parte adicional: Gráfico de mantenimientos realizados por año
    st.subheader("Mantenimientos realizados por año")

    # Asegurarse de que la columna 'fecha_mantenimiento' esté en formato de fecha
    mantenimiento_arboles_df['prox_fecha_mante'] = pd.to_datetime(mantenimiento_arboles_df['prox_fecha_mante'], errors='coerce')

    # Extraer el año del mantenimiento
    mantenimiento_arboles_df['año_mantenimiento'] = mantenimiento_arboles_df['prox_fecha_mante'].dt.year

    # Filtrar años válidos
    primer_año = mantenimiento_arboles_df['año_mantenimiento'].min()
    ultimo_año = mantenimiento_arboles_df['año_mantenimiento'].max()
    mantenimientos_por_año = mantenimiento_arboles_df[mantenimiento_arboles_df['año_mantenimiento'].between(primer_año, ultimo_año)]

    # Contar el número de mantenimientos por año
    mantenimientos_por_año = mantenimientos_por_año.groupby('año_mantenimiento').size().reset_index(name='cantidad_mantenimientos')

    # Crear el gráfico de línea para mostrar los mantenimientos a través de los años
    fig_mantenimientos = px.line(
        mantenimientos_por_año,
        x='año_mantenimiento',
        y='cantidad_mantenimientos',
        title='Frecuencia de Mantenimientos de Árboles desde el año 2023',
        labels={'año_mantenimiento': 'Año', 'cantidad_mantenimientos': 'Cantidad de Mantenimientos'},
        markers=True,
        color_discrete_sequence=px.colors.qualitative.Vivid  # Colores vibrantes
    )

    # Personalizar el gráfico
    fig_mantenimientos.update_layout(
        xaxis_title='Año',
        yaxis_title='Cantidad de Mantenimientos',
        plot_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo claro
        paper_bgcolor='rgba(245, 245, 245, 1)',  # Fondo del gráfico
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco del hover
            bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
            font=dict(color='#333', size=14)  # Color y tamaño del texto
        ),
        height=400,
    )

    # Actualizar las etiquetas de hover
    fig_mantenimientos.update_traces(
        hovertemplate='<b>Año:</b> %{x}<br><b>Cantidad de Mantenimientos:</b> %{y}<extra></extra>'
    )
    
    # Mostrar el gráfico de mantenimientos en Streamlit
    st.plotly_chart(fig_mantenimientos)


# Crear una función para mostrar el mapa de árboles mediante un mapa de calor, la cantidad total y especies
# Mapa de calor de árboles
def mostrar_mapa_calor_arboles():
    centro_mapa = [-27.48, -58.83]
    heatmap = folium.Map(location=centro_mapa, zoom_start=13)
    
    # Datos para el HeatMap
    heat_data = [[row['lat'], row['lng']] for index, row in registro_arboles_df.dropna(subset=['lat', 'lng']).iterrows()]
    HeatMap(heat_data).add_to(heatmap)

    # Mostrar el mapa
    folium_static(heatmap)

    # Reemplazar valores nulos en la columna 'especie' con 'Especie desconocida'
    registro_arboles_df['especie'] = registro_arboles_df['especie'].fillna('Especie desconocida').str.strip().str.lower()

    # Asegurar de que todas las variaciones de nombres similares estén unificadas
    registro_arboles_df['especie'] = registro_arboles_df['especie'].replace({
            'sin información': 'especie desconocida',  # Unificar variantes
            'desconocido': 'especie desconocida',
            'sin identificar': 'especie desconocida'
    })

    # Convertir a mayúsculas solo la primera letra de cada palabra (si es necesario para mantener estilo)
    registro_arboles_df['especie'] = registro_arboles_df['especie'].str.title()

    # Calcular la cantidad total de árboles
    cantidad_arboles = registro_arboles_df.dropna(subset=['lat', 'lng']).shape[0]

    # Calcular la cantidad de especies de árboles y sus nombres
    especies_conteo = registro_arboles_df['especie'].value_counts()
    cantidad_especies = especies_conteo.shape[0]

    # Mostrar la cantidad total de árboles
    st.write(f"**Cantidad total de árboles**: {cantidad_arboles}")

    # Mostrar la cantidad total de especies de árboles
    st.write(f"**Cantidad total de especies de árboles**: {cantidad_especies}")

    # Mostrar un gráfico de líneas de la cantidad de árboles por especie
    conteo_especies = especies_conteo.reset_index()
    conteo_especies.columns = ['Especie', 'Cantidad']

    # Crear el gráfico de barras horizontales para especies de arboles
    fig = px.bar(
    conteo_especies,
    x='Cantidad',
    y='Especie',
    orientation='h',  # Cambia a orientación horizontal
    title='Cantidad de Árboles por Especie',
    color='Especie',  # Mantener la leyenda de colores
    color_discrete_sequence=[
        px.colors.qualitative.Alphabet[6],
        px.colors.qualitative.Alphabet[0],
        px.colors.qualitative.Alphabet[11],
        px.colors.qualitative.Dark2[0],
        px.colors.qualitative.Alphabet[20],
        px.colors.qualitative.Plotly[2],
        px.colors.qualitative.Plotly[7],
        px.colors.qualitative.Plotly[3],
        px.colors.qualitative.G10[5]
        ],
    )

    # Actualizar los trazos para desactivar la etiqueta predeterminada y mostrar solo la personalizada
    fig.update_traces(
    hovertemplate='<b>Cantidad:</b> %{x}<extra></extra>',
    showlegend=True  # Mantener la leyenda
    )

    # Personalizar el layout del gráfico
    fig.update_layout(
    xaxis_title='Cantidad',
    yaxis_title='Especie',
    plot_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo claro
    paper_bgcolor='rgba(245, 245, 245, 1)',  # Fondo del gráfico
    hoverlabel=dict(
        bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco del hover
        bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
        font=dict(color='#333', size=14)  # Color del texto y tamaño
    ),
    height=900,  # Ajustar el alto del gráfico
    width=1200,  # Ajustar el ancho del gráfico
    margin=dict(l=40, r=40, t=40, b=200),  # Ajustar los márgenes
    yaxis=dict(tickmode='linear', dtick=1, automargin=True),  # Ajustar el espaciado de las etiquetas en el eje Y
    hovermode="y"  # Mostrar hover interactivo en el eje Y
)

    fig.update_yaxes(tickfont=dict(size=9))  # Ajustar el tamaño de fuente de las etiquetas

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)

    # Definir una lista de especies nativas de Corrientes
    especies_nativas_corrientes = ['Jacarandá', 'Lapacho Rosado', 'Lapacho amarillo', 'Lapacho', 'Ingá', 'Ceibo', 'Ombú', 'Sauce', 'Urunday',
    'Pata de Buey (Nativa)', 'Ñangapirí','Palo Borracho', 'Guayaba', 'Mango', 'Sauce criollo', 'Albizia', 'Mamon','Ambaí','Lapachillo','Curupí',
    'Tipa Blanca', 'Tecoma Lapachillo','Timbó Colorado','Timbó Blanco']

   # Convertir la lista de especies nativas a minúsculas para la comparación
    especies_nativas_corrientes = [especie.lower().strip() for especie in especies_nativas_corrientes]

    # Filtrar las especies presentes en el dataset
    especies_presentes = registro_arboles_df['especie'].unique()

    # Normalizar las especies presentes también
    especies_presentes = [especie.lower().strip() for especie in especies_presentes]

    # Comparar las especies nativas presentes en el dataset (normalizadas)
    especies_nativas_presentes = [especie for especie in especies_presentes if especie in especies_nativas_corrientes]

    # Calcular la cantidad de especies totales y especies nativas
    cantidad_total_especies = len(especies_presentes)
    cantidad_especies_nativas = len(especies_nativas_presentes)

    # Calcular el porcentaje de especies nativas sobre el total de especies
    porcentaje_especies_nativas = (cantidad_especies_nativas / cantidad_total_especies) * 100

    # Mostrar la cantidad y el porcentaje de especies nativas
    st.write(f"**Cantidad de especies nativas**: {cantidad_especies_nativas}")

    # Calcular el porcentaje de especies no nativas
    porcentaje_no_nativas = 100 - porcentaje_especies_nativas

    # Crear un DataFrame para la gráfica de dona
    data_porcentaje = pd.DataFrame({
    'Tipo de Especies': ['Nativas', 'No Nativas'],
    'Porcentaje': [porcentaje_especies_nativas, porcentaje_no_nativas]
    })

    # Crear el gráfico de dona para el porcentaje de especies nativas
    fig_dona_porcentaje = px.pie(
    data_porcentaje,
    values='Porcentaje',
    names='Tipo de Especies',
    hole=0.6,  # Hacer una dona
    color_discrete_sequence=[
                 px.colors.qualitative.Alphabet[0],
                 px.colors.qualitative.Alphabet[20]],  # Colores personalizados para nativas y no nativas
    )
    
    fig_dona_porcentaje.update_traces(
    hovertemplate='<b>Tipo de especie:</b> %{label}<br><b><extra></extra>'
    )


    # Personalizar el layout del gráfico
    fig_dona_porcentaje.update_layout(
    showlegend=False,  # Quitar la leyenda
    margin=dict(l=0, r=0, t=0, b=0),  # Márgenes pequeños para hacerla compacta
    height=200,  # Ajustar el alto
    width=200,   # Ajustar el ancho
    plot_bgcolor='rgba(0, 0, 0, 0)',  # Fondo transparente
    paper_bgcolor='rgba(0, 0, 0, 0)',  # Fondo transparente
    hoverlabel=dict(
         bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco del hover
         bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
         font=dict(color='#333', size=14)  # Color del texto y tamaño
    ))

    # Crear columnas para alinear texto y gráfico de dona
    col1, col2 = st.columns([0.5, 1.2])  # Ajustar el tamaño de las columnas

    # Mostrar el porcentaje de especies nativas
    st.write(f"**Porcentaje de especies nativas**: ")

    # Mostrar la gráfica de dona justo debajo del texto
    st.plotly_chart(fig_dona_porcentaje, use_container_width=True)

# Función para mostrar un gráfico de torta con el porcentaje de espacios verdes por barrio
def mostrar_grafico_espacios_barrios():
    # Contar el número de espacios verdes por barrio
    espacios_verdes_por_barrio = espacios_verdes_df.groupby('id_barrios').size().reset_index(name='cantidad_espacios_verdes')

    # Combinar los datos de barrios y espacios verdes
    barrios_con_datos = barrios_df.merge(espacios_verdes_por_barrio, left_on='id_barrios', right_on='id_barrios', how='left').fillna(0)

    # Calcular el total de espacios verdes
    total_espacios_verdes = barrios_con_datos['cantidad_espacios_verdes'].sum()

    # Calcular el porcentaje de espacios verdes por barrio
    barrios_con_datos['porcentaje_espacios_verdes'] = (barrios_con_datos['cantidad_espacios_verdes'] / total_espacios_verdes) * 100

    # Defino la combinación de colores fuera de la función de la gráfica
    set3_color = px.colors.qualitative.Set3
    set2_color = px.colors.qualitative.Set2
    pastel_color = px.colors.qualitative.Pastel
    pastel2_color = px.colors.qualitative.Pastel2

    # Combinar colores de ambas paletas
    combinar_paletas = set3_color + pastel_color + set2_color + pastel2_color + set3_color + pastel_color + set2_color + pastel2_color # Esto combina ambas listas
    # Crear gráfico de dona
    fig = px.pie(
        barrios_con_datos, 
        names='nombre_barrio', 
        values='porcentaje_espacios_verdes',
        title='Porcentaje de Espacios Verdes por Barrio',
        hole=0.3,
        width=800,  # Ajustar ancho del gráfico
        height=600,  # Ajustar alto del gráfico
        color_discrete_sequence=combinar_paletas
    )

    # Personalizar el layout para incluir fondo
    fig.update_layout(
        plot_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo de la gráfica
        paper_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo del papel (área exterior)
    )

    # Actualizar el gráfico para eliminar los porcentajes fuera de la torta y sus líneas
    fig.update_traces(
        textposition='inside',     # Coloca el texto dentro de la porción del gráfico
        showlegend=True,  # Asegura que la leyenda esté activa
        pull=[0]*len(barrios_con_datos),  # Asegura que no haya "pull" (líneas externas)
        hovertemplate='<b>Nombre del Barrio:</b> %{label}<br><b>Porcentaje de Espacios Verdes:</b> %{percent:.2%}<extra></extra>',  # Formato del hover
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 1)',  # Fondo blanco
            bordercolor='rgba(76, 175, 80, 1)',  # Borde verde
            font=dict(color='#333')  # Texto en color gris oscuro
        )
    )

    # Calcular la cantidad de barrios
    cantidad_barrios = len(barrios_con_datos)

    # Mostrar el texto de la cantidad de barrios en Streamlit
    st.markdown(f"**Cantidad de barrios:** {cantidad_barrios}")

    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig)

    st.markdown("""
## Conclusiones y Recomendaciones:
- **Árboles en la ciudad**: Se puede observar que la ciudad esta casi en su totalidad poblada de árboles y con variadas especies, con un porcentaje alto en buen estado.
- **Mantenimiento prioritario**: Es esencial priorizar el mantenimiento de los árboles en mal estado ya que el porcentaje es menor.
- **Puntos verdes en la ciudad**: Análisis de buena distribución de los puntos verdes en distintas ubicaciones.
- **Ampliación de puntos verdes**: Aumentar los puntos verdes para mejorar el acceso de los ciudadanos y fomentar el reciclaje en más barrios.
- **Espacios verdes en la ciudad**: Mediante este análisis es notable la cantidad de espacios verdes y sus distintas clasificaciones como plazas, palozeta, costanera, paseo, playa, espacio deportivo.
- **Plan de expansión de espacios verdes**: Los barrios con menos espacios verdes deben ser priorizados en la planificación urbana para reducir el déficit de áreas verdes.
""")

# Nueva función para filtrar espacios verdes por clasificación
def filtrar_espacios_verdes(clasificacion):
    if clasificacion and clasificacion != "TODOS":
        return espacios_verdes_df[espacios_verdes_df['clasificacion'] == clasificacion]
    return espacios_verdes_df

# Nueva función para mostrar la gráfica de espacios verdes como gráfica de torta
def mostrar_grafica_espacios_verdes(espacios_verdes_filtrados):
    if clasificacion_espacio == "TODOS":
        conteo_por_clasificacion = espacios_verdes_filtrados['clasificacion'].value_counts().reset_index()
        conteo_por_clasificacion.columns = ['Clasificación', 'Cantidad']

         # Crear gráfica de barras verticales interactiva
        fig = px.bar(
            conteo_por_clasificacion,
            x='Clasificación',
            y='Cantidad',
            title='Cantidad de Espacios Verdes por Clasificación',
            color='Clasificación',  # Color por clasificación
            color_discrete_sequence=[
                px.colors.qualitative.Pastel[3],  
                px.colors.qualitative.Pastel[4], 
                px.colors.qualitative.Pastel[5],    
                px.colors.qualitative.Pastel[1],  
                px.colors.qualitative.Pastel[7],       
                px.colors.qualitative.Pastel[8],       
                px.colors.qualitative.Pastel[9],
            ]
        )

       # Personalizar el layout para la gráfica de barras
        fig.update_layout(
            plot_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo de la gráfica
            paper_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo del papel (área exterior)
            height=600,  # Ajustar la altura de la gráfica
            width=700,   # Ajustar el ancho de la gráfica
            showlegend=False,  # Ocultar leyenda para barras
            margin=dict(l=40, r=40, t=40, b=80),  # Ajustar márgenes
        )

        # Personalizar los trazos y las etiquetas de hover
        fig.update_traces(
            hovertemplate='<b>Clasificación:</b> %{x}<br><b>Cantidad:</b> %{y}<extra></extra>',  # Extra elimina el color al lado del hover
            hoverlabel=dict(
                bgcolor='white',  # Fondo blanco
                bordercolor='green',  # Borde verde
                font=dict(size=14, color='black'),  # Tamaño y color del texto
            ),
        )


        # Mostrar gráfica de barras en Streamlit
        st.plotly_chart(fig)

# Sidebar para navegación
st.sidebar.title("Opciones de visualización")
opcion = st.sidebar.selectbox(
    "Selecciona una visualización:",
    ["Puntos y Espacios Verdes", "Árboles y Especies", "Estado de Salud de Árboles", "Espacios Verdes en Barrios"]
)

# Mostrar las visualizaciones según la opción seleccionada
if opcion == "Puntos y Espacios Verdes":
    st.subheader("Mapa e info de Puntos Verdes y Espacios Verdes en la ciudad de Corrientes")
    st.write("""
        Los **Puntos Verdes** son lugares habilitados para la correcta disposición de residuos reciclables, 
        contribuyendo a la concientización ambiental y al cuidado de nuestros **espacios verdes.** 
        Al reciclar y hacer uso de estos puntos, ayudamos a mantener nuestras áreas verdes más limpias y saludables.
    """)
    
    # Nueva opción en la barra lateral para filtrar espacios verdes (solo para Puntos y Espacios Verdes)
    clasificacion_espacio = st.sidebar.selectbox(
        "Selecciona la clasificación de espacios verdes:",
        ["TODOS"] + list(espacios_verdes_df['clasificacion'].dropna().unique())  # Filtramos los NaN
    )
    # Filtrar los espacios verdes según la clasificación seleccionada
    espacios_verdes_filtrados = filtrar_espacios_verdes(clasificacion_espacio)
    # Mostrar el mapa de puntos y espacios verdes filtrados
    mostrar_mapa_puntos_espacios(espacios_verdes_filtrados)
    # Mostrar la gráfica de espacios verdes según clasificación
    mostrar_grafica_espacios_verdes(espacios_verdes_filtrados)

elif opcion == "Árboles y Especies":
    st.subheader("Mapa de calor Árboles")
    st.write("""
        Se muestra un **Mapa de Calor** de los árboles en la ciudad de Corrientes. 
        En este mapa, es posible observar la densidad de árboles en las diferentes áreas de la ciudad.
        Notablemente, se puede ver que la ciudad está densamente poblada con árboles, especialmente en ciertas zonas 
        donde la concentración es más alta.
    """)
    mostrar_mapa_calor_arboles()
elif opcion == "Estado de Salud de Árboles":
    st.subheader("Gráfico del Estado de Salud de los Árboles")
    grafico_estado_salud()
elif opcion == "Espacios Verdes en Barrios":
    st.subheader("Gráfico de Espacios Verdes en los Barrios de la Ciudad")
    mostrar_grafico_espacios_barrios()

# Footer
st.markdown("""
    <div class="footer">
        <p>
            <a href="https://datos.ciudaddecorrientes.gov.ar/dataset?groups=zoonosis" target="_blank">Fuente: Dataset del Portal de Datos Abiertos de Corrientes</a>
        </p>
        <hr>
        <p>© 2024 Desarrollado por Leguiza Agustina</p>
    </div>
""", unsafe_allow_html=True)
