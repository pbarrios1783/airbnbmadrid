import folium
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from streamlit_folium import st_folium

st.title("Airbnb - Madrid")
st.subheader("Patricia Barrios")

@st.cache_data
def load_data():
    # Cargar los datos de los pisos
    df_pisos = pd.read_csv("data/pisos.csv")
    df_pisos["coord"] = gpd.points_from_xy(x=df_pisos.longitude, y=df_pisos.latitude)
    df_pisos = gpd.GeoDataFrame(df_pisos, geometry="coord").set_crs("EPSG:4326")

    # Cargar los barrios de Madrid
    df_nb_madrid = gpd.read_file('data/neighbourhoods.geojson')
    
    return df_pisos, df_nb_madrid

df_pisos, df_nb_madrid = load_data()

# Unir los datos de los barrios a los pisos
airbnb_in_madrid = gpd.sjoin(df_pisos, df_nb_madrid, how='inner')

# Obtener las listas únicas de tipos de vivienda y barrios
room_types = airbnb_in_madrid['room_type'].unique()
neighbourhoods = airbnb_in_madrid['neighbourhood'].unique()

# Crear filtros en la barra lateral
selected_room_type = st.sidebar.selectbox("Selecciona Tipo de Habitación", room_types)
selected_neighbourhoods = st.sidebar.multiselect("Selecciona un Barrio", neighbourhoods)

# Filtrar datos según los filtros seleccionados
filtered_pisos = airbnb_in_madrid[
    (airbnb_in_madrid['room_type'] == selected_room_type) &
    (airbnb_in_madrid['neighbourhood'].isin(selected_neighbourhoods))
]

# Función para categorizar precios
def categorize_price(price):
    if 0 <= price < 50:
        return "Muy Baratos"
    elif 50 <= price < 100:
        return "Baratos"
    elif 100 <= price < 200:
        return "Precio medio"
    elif 200 <= price < 1000:
        return "Caros"
    elif 1000 <= price <= 10000:
        return "Muy Caros"
    else:
        return "Precio fuera de rango"

# Aplicar la función de categorización de precios
filtered_pisos['categoria'] = filtered_pisos['price'].apply(categorize_price)

# Crear un mapa centrado en Madrid
madrid_location = [40.4268627127925, -3.6912505241863776]
m = folium.Map(location=madrid_location, zoom_start=12, width=600, height=600)

# Agregar barrios al mapa
folium.GeoJson(
    df_nb_madrid,
    name="Barrios",
    tooltip=folium.GeoJsonTooltip(fields=['neighbourhood'], labels=False, sticky=True)
).add_to(m)

# Crear un FeatureGroup para cada categoría de precio
feature_groups = {
    "Muy Baratos": folium.FeatureGroup(name="Muy Baratos"),
    "Baratos": folium.FeatureGroup(name="Baratos"),
    "Precio medio": folium.FeatureGroup(name="Precio medio"),
    "Caros": folium.FeatureGroup(name="Caros"),
    "Muy Caros": folium.FeatureGroup(name="Muy Caros")
}

# Agregar marcadores al FeatureGroup correspondiente
for idx, row in filtered_pisos.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"{row['room_type']} - {row['categoria']} - {row['price']}€",
        icon=folium.Icon(color='blue' if row['categoria'] == "Muy Baratos" else
                         'green' if row['categoria'] == "Baratos" else
                         'orange' if row['categoria'] == "Precio medio" else
                         'red' if row['categoria'] == "Caros" else
                         'darkred')
    ).add_to(feature_groups[row['categoria']])

# Agregar cada FeatureGroup al mapa
for fg in feature_groups.values():
    fg.add_to(m)

# Agregar control de capas para alternar entre capas
folium.LayerControl().add_to(m)

# Mostrar el mapa en Streamlit
st_folium(m, width=700, height=500)

