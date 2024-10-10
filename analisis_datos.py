import pandas as pd
import folium
from folium.plugins import HeatMap
import os
from datetime import datetime
import re
import json
import seaborn as sns
import matplotlib.pyplot as plt

# Cargar los datasets
registro_arboles_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/RegistroArboles.csv')
espacios_verdes_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/EspaciosVerdes.csv')
puntos_verdes_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/PuntosVerdes.csv')
mantenimiento_arboles_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/MantenimientoArboles.csv')
barrios_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/Barrios.csv')

# Función para limpiar y corregir coordenadas
def corregir_coordenadas(valor):
    try:
        valor = str(valor).strip()  # Eliminar espacios
        valor = re.sub(r'[^0-9.-]', '', valor)  # Mantener solo dígitos, puntos y signos negativos

        if valor.count('.') > 1:
            partes = valor.split('.')
            valor = partes[0] + '.' + ''.join(partes[1:])  # Mantener solo el primer punto

        float_val = float(valor)

        if float_val < -90 or float_val > 90:
            return None
        return float_val
    except ValueError:
        return None

# Aplicar la función a las coordenadas del registro de árboles
registro_arboles_df['lat'] = registro_arboles_df['lat'].apply(corregir_coordenadas)
registro_arboles_df['lng'] = registro_arboles_df['lng'].apply(corregir_coordenadas)
puntos_verdes_df['lat'] = pd.to_numeric(puntos_verdes_df['lat'], errors='coerce')
puntos_verdes_df['lng'] = pd.to_numeric(puntos_verdes_df['lng'], errors='coerce')

# Filtrar datos de coordenadas válidos
registro_arboles_limpio = registro_arboles_df.dropna(subset=['lat', 'lng'])
puntos_verdes_limpio = puntos_verdes_df.dropna(subset=['lat', 'lng'])

# Crear un mapa centrado en una ubicación genérica
centro_mapa = [-27.48, -58.83]
mapa = folium.Map(location=centro_mapa, zoom_start=13)

# Función para cargar y limpiar JSON
def cargar_json(geojson_str):
    try:
        geojson_str = geojson_str.replace('""', '"')  # Limpiar comillas dobles
        geojson_str = re.sub(r'([{,])\s*([A-Za-z0-9]+):', r'\1"\2":', geojson_str)
        geojson_str = geojson_str.replace('""', '"')
        geojson_str = re.sub(r'(?<=[{\[,])\s*([A-Za-z0-9]+):', r'"\1":', geojson_str)

        return json.loads(geojson_str)
    except json.JSONDecodeError:
        return None  # Retornar None si hay un error en el JSON

# Contador de filas problemáticas
contador_filas_problematicas = 0

# Añadir espacios verdes al mapa
for _, fila in espacios_verdes_df.iterrows():
    try:
        geo_data = cargar_json(fila['st_asgeojson'])
        if geo_data is None:
            contador_filas_problematicas += 1  # Incrementar contador y omitir fila problemática
            continue

        coords = geo_data['coordinates'][0]

        # Añadir polígono al mapa
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],  # Intercambiar orden
            color='blue',
            fill=True,
            fill_opacity=0.3,
            popup=f"Espacio verde: {fila.get('gid', 'Sin nombre')}"
        ).add_to(mapa)

    except Exception:
        contador_filas_problematicas += 1  # Incrementar contador en caso de error

# Añadir puntos verdes al mapa
for _, fila in puntos_verdes_limpio.iterrows():
    if fila['lat'] is not None and fila['lng'] is not None:
        folium.Marker(
            location=[fila['lat'], fila['lng']],
            popup=f"Punto verde: {fila['ubicacion']}",
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(mapa)

# Análisis de mantenimiento de árboles
# Unir datos de mantenimiento con registros de árboles
arboles_mantenimiento_df = pd.merge(
    registro_arboles_limpio,
    mantenimiento_arboles_df,
    on='id_arbol',  # Columna en ambos DataFrames
    how='left',
    suffixes=('_arbol', '_mantenimiento')
)

# Filtrar datos de árboles con coordenadas limpias y estado de salud
arboles_mantenimiento_limpio = arboles_mantenimiento_df.dropna(subset=['lat', 'lng', 'estado_salud'])

# Verificar el número de árboles únicos en ambos archivos
num_arboles_registro = registro_arboles_df['id_arbol'].nunique()
num_arboles_mantenimiento = mantenimiento_arboles_df['id_arbol'].nunique()

print(f"Cantidad de árboles únicos en RegistroArboles.csv: {num_arboles_registro}")
print(f"Cantidad de árboles únicos en MantenimientoArboles.csv: {num_arboles_mantenimiento}")

# Crear un nuevo DataFrame con los datos del árbol faltante
nuevo_arbol = pd.DataFrame({
    'id_arbol': [7190],
    'direccion': ['Sin información'],  # Puedes poner 'Sin información' si no tienes la dirección
    'tipo_vereda': ['Sin información'],
    'lado_vereda': ['Sin información'],
    'especie': ['Sin información'],
    'tipo_tendido': ['Sin información'],
    'distancia_entre_ar': [None],  # Si no tienes la distancia, puedes dejarlo en blanco (None)
    'distancia_al_muro': [None],
    'activo': [True],  # Puedes asumir que el árbol está activo
    'lng': [None],  # Sin coordenadas
    'lat': [None]
})

# Filtrar columnas vacías antes de la concatenación
nuevo_arbol = nuevo_arbol.dropna(axis=1, how='all')  # Eliminar columnas vacías
nuevo_arbol = nuevo_arbol[registro_arboles_df.columns.intersection(nuevo_arbol.columns)]  # Asegúrate de que el nuevo árbol tenga solo las columnas necesarias

# Agregar el nuevo árbol al DataFrame original
registro_arboles_df_actualizado = pd.concat([registro_arboles_df, nuevo_arbol], ignore_index=True)

# Guardar el archivo actualizado
registro_arboles_df_actualizado.to_csv('C:/Users/Usuario/Desktop/Datathon/RegistroArboles_actualizado.csv', index=False)

print("Se ha agregado el árbol con id_arbol 7190 al archivo RegistroArboles_actualizado.csv")

# Volver a cargar los datos de mantenimiento de árboles
mantenimiento_arboles_df = pd.read_csv('C:/Users/Usuario/Desktop/Datathon/MantenimientoArboles.csv')

# Volver a hacer el conteo
# Contar árboles únicos en ambos DataFrames
arboles_unicos_registro = registro_arboles_df_actualizado['id_arbol'].nunique()
arboles_unicos_mantenimiento = mantenimiento_arboles_df['id_arbol'].nunique()

# Hacer un merge para verificar la relación entre los árboles
arboles_mantenimiento_df = pd.merge(
    registro_arboles_df_actualizado,
    mantenimiento_arboles_df,
    on='id_arbol',  # Columna en ambos DataFrames
    how='left',
    suffixes=('_arbol', '_mantenimiento')
)

# Contar por estado de salud en el archivo de mantenimiento
conteo_estado_salud = arboles_mantenimiento_df['estado_salud'].value_counts()

# Verificar árboles faltantes entre los dos archivos
arboles_faltantes_mantenimiento = set(mantenimiento_arboles_df['id_arbol']) - set(registro_arboles_df_actualizado['id_arbol'])

if arboles_faltantes_mantenimiento:
    print(f"Árboles en MantenimientoArboles.csv no encontrados en RegistroArboles_actualizado.csv: {arboles_faltantes_mantenimiento}")

# Añadir árboles con coordenadas válidas al mapa
for _, arbol in registro_arboles_limpio.iterrows():
    folium.Marker(
        location=[arbol['lat'], arbol['lng']],
        popup=f"ID Árbol: {arbol['id_arbol']}, Especie: {arbol.get('especie', 'Sin información')}",
        icon=folium.Icon(color='green', icon='tree')
    ).add_to(mapa)

# Crear el mapa de calor
heatmap = folium.Map(location=centro_mapa, zoom_start=13)
heat_data = [[row['lat'], row['lng']] for index, row in arboles_mantenimiento_limpio.iterrows()]
HeatMap(heat_data).add_to(heatmap)

# Guardar el mapa de calor
def guardar_mapa(mapa, nombre_archivo):
    carpeta = 'mapas_generados'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    ruta = os.path.join(carpeta, nombre_archivo)
    mapa.save(ruta)

# Guardar el mapa completo con los árboles
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
guardar_mapa(mapa, f'mapa_arboles_completo_con_arboles_{timestamp}.html')

# Guardar el mapa de calor
guardar_mapa(heatmap, f'mapa_calor_arboles_{timestamp}.html')

# Crear gráficas de conteo de árboles por estado de salud
plt.figure(figsize=(10, 6))
sns.countplot(x='estado_salud', data=arboles_mantenimiento_df, order=conteo_estado_salud.index, palette='viridis', hue='estado_salud')
plt.title('Conteo de árboles por estado de salud')
plt.xlabel('Estado de salud')
plt.ylabel('Número de árboles')
plt.xticks(rotation=45)
plt.tight_layout()

# Guardar la gráfica
grafica_filename = f'conteo_estado_salud_{timestamp}.png'
plt.savefig(os.path.join('C:/Users/Usuario/Desktop/Datathon', grafica_filename))
plt.show()

print(f"Gráfica guardada como: {grafica_filename}")
print(f"Total de árboles agregados al mapa: {len(registro_arboles_limpio)}")
