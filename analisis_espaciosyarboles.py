import pandas as pd
import folium
import os
import json
import re
import geopandas as gpd
from shapely import wkt
from folium.plugins import HeatMap

# Cargar los datasets
registro_arboles_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/RegistroArboles_actualizado.csv')  # Archivo actualizado de árboles
espacios_verdes_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/EspaciosVerdes.csv')
barrios_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/Barrios.csv')

# Función para cargar y limpiar JSON (en caso de datos corruptos)
def cargar_json(geojson_str):
    try:
        geojson_str = geojson_str.replace('""', '"')  # Limpiar comillas dobles
        geojson_str = re.sub(r'([{,])\s*([A-Za-z0-9]+):', r'\1"\2":', geojson_str)
        return json.loads(geojson_str)
    except json.JSONDecodeError:
        return None

# Crear un mapa centrado en la ciudad
centro_mapa = [-27.48, -58.83]
mapa = folium.Map(location=centro_mapa, zoom_start=13)

# Contador para filas problemáticas
contador_filas_problematicas = 0

# Añadir los espacios verdes al mapa como polígonos
for _, fila in espacios_verdes_df.iterrows():
    try:
        geo_data = cargar_json(fila['st_asgeojson'])
        if geo_data is None:
            contador_filas_problematicas += 1
            continue
        coords = geo_data['coordinates'][0]
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',  # Cambiar el color a verde para espacios verdes
            fill=True,
            fill_opacity=0.3,
            popup=f"Espacio verde: {fila.get('gid', 'Sin nombre')}"
        ).add_to(mapa)
    except Exception:
        contador_filas_problematicas += 1

# Limpiar las columnas de latitud y longitud en el DataFrame de árboles
registro_arboles_df['lat'] = pd.to_numeric(registro_arboles_df['lat'], errors='coerce')
registro_arboles_df['lng'] = pd.to_numeric(registro_arboles_df['lng'], errors='coerce')

# Eliminar filas con valores NaN en latitud y longitud
registro_arboles_df = registro_arboles_df.dropna(subset=['lat', 'lng'])

# Crear un GeoDataFrame para los árboles con sus coordenadas
registro_arboles_gdf = gpd.GeoDataFrame(
    registro_arboles_df,
    geometry=gpd.points_from_xy(registro_arboles_df['lng'], registro_arboles_df['lat']),
    crs="EPSG:4326"
)

# Convertir geometrías WKT (Well-Known Text) a objetos de geometría en Geopandas para los barrios
barrios_gdf = gpd.GeoDataFrame(
    barrios_df,
    geometry=barrios_df['the_geom_barrios'].apply(lambda x: wkt.loads(x) if pd.notnull(x) else None),
    crs="EPSG:4326"
)

# Hacer una intersección espacial para asignar cada árbol a un barrio
arboles_en_barrios = gpd.sjoin(registro_arboles_gdf, barrios_gdf, how="left", predicate='within')

# Verificar las columnas del DataFrame resultante
print(arboles_en_barrios.columns)  # Esto te ayudará a identificar el nombre correcto de la columna

# Contar el número de árboles por barrio
arboles_por_barrio = arboles_en_barrios.groupby('nombre_barrio').size().reset_index(name='cantidad_arboles')

# Unir con los datos de los barrios
# Asegúrate de usar la columna correcta para unir, en este caso 'nombre_barrio' parece la correcta
barrios_con_arboles_gdf = barrios_gdf.merge(arboles_por_barrio, left_on='nombre_barrio', right_on='nombre_barrio', how='left').fillna(0)

# Contar el número de espacios verdes por barrio utilizando la columna id_barrios
espacios_verdes_por_barrio = espacios_verdes_df.groupby('id_barrios').size().reset_index(name='cantidad_espacios_verdes')

# Unir los espacios verdes por barrio con los datos de los barrios
barrios_con_datos_gdf = barrios_con_arboles_gdf.merge(espacios_verdes_por_barrio, left_on='id_barrios', right_on='id_barrios', how='left').fillna(0)

# Añadir los árboles al mapa como marcadores
for _, fila in registro_arboles_df.iterrows():
    if pd.notna(fila['lat']) and pd.notna(fila['lng']):
        folium.Marker(
            location=[fila['lat'], fila['lng']],
            popup=f"Árbol: {fila['id_arbol']}, Especie: {fila['especie']}",
            icon=folium.Icon(color='green', icon='tree')
        ).add_to(mapa)

# Añadir los polígonos de los barrios al mapa
for _, fila in barrios_gdf.iterrows():
    if fila['geometry'] is not None:
        coords = fila['geometry'].exterior.coords
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='orange',  # Color de los bordes de los barrios
            fill=True,
            fill_color='orange',  # Color de llenado
            fill_opacity=0.3,
            popup=f"Barrio: {fila.get('nombre_barrio', 'Sin nombre')}"
        ).add_to(mapa)

# Guardar el mapa base en un archivo HTML para visualizarlo
carpeta_salida = 'C:/Users/Usuario/Desktop/Datathon'
if not os.path.exists(carpeta_salida):
    os.makedirs(carpeta_salida)

mapa.save(os.path.join(carpeta_salida, 'mapa_arboles_y_espacios_verdes.html'))
print(f"Se ha guardado el mapa interactivo en: {carpeta_salida}")

# Crear el mapa de calor para los árboles
mapa_calor_arboles = folium.Map(location=centro_mapa, zoom_start=13)

# Añadir el heatmap al mapa
HeatMap(
    data=registro_arboles_gdf[['lat', 'lng']].dropna().values,
    radius=10,  # Radio del heatmap
    blur=15,    # Difuminación del heatmap
    max_zoom=1  # Zoom máximo para el heatmap
).add_to(mapa_calor_arboles)

# Guardar el mapa de calor
mapa_calor_arboles.save(os.path.join(carpeta_salida, 'mapa_calor_arboles.html'))
print("Se ha guardado el mapa de calor de árboles.")

# Crear un mapa coroplético
mapa_coropletico = folium.Map(location=centro_mapa, zoom_start=13)

# Añadir el coropleta de árboles por barrio
folium.Choropleth(
    geo_data=barrios_con_datos_gdf.to_json(),
    name='Cantidad de Árboles',
    data=barrios_con_datos_gdf,
    columns=['id_barrios', 'cantidad_arboles'],
    key_on='feature.properties.id_barrios',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Cantidad de Árboles por Barrio'
).add_to(mapa_coropletico)

# Añadir el coropleta de espacios verdes por barrio
folium.Choropleth(
    geo_data=barrios_con_datos_gdf.to_json(),
    name='Cantidad de Espacios Verdes',
    data=barrios_con_datos_gdf,
    columns=['id_barrios', 'cantidad_espacios_verdes'],
    key_on='feature.properties.id_barrios',
    fill_color='BuPu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Cantidad de Espacios Verdes por Barrio'
).add_to(mapa_coropletico)

# Añadir capas de control
folium.LayerControl().add_to(mapa_coropletico)
print(arboles_en_barrios.columns)  # Esto imprimirá las columnas disponibles en el DataFrame arboles_en_barrios

# Guardar el mapa coroplético
mapa_coropletico.save(os.path.join(carpeta_salida, 'mapa_coropletico.html'))
print("Se ha guardado el mapa coroplético.")
