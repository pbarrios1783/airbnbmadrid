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
    # Load apartment data
    df_pisos = pd.read_csv("pisos.csv")
    df_pisos["coord"] = gpd.points_from_xy(x=df_pisos.longitude, y=df_pisos.latitude)
    df_pisos = gpd.GeoDataFrame(df_pisos, geometry="coord").set_crs("EPSG:4326")
    
    # Load Madrid neighborhoods
    df_nb_madrid = gpd.read_file('neighbourhoods.geojson')
    
    # Join neighborhood data to apartments
    airbnb_in_madrid = gpd.sjoin(df_pisos, df_nb_madrid, how='inner')
    
    # Categorize prices
    airbnb_in_madrid['categoria'] = airbnb_in_madrid['price'].apply(categorize_price)
    
    return airbnb_in_madrid, df_nb_madrid

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

# Load data once
if 'data' not in st.session_state:
    st.session_state.data, st.session_state.neighborhoods = load_data()

# Get unique lists of room types and neighborhoods
room_types = st.session_state.data['room_type'].unique()
neighbourhoods = st.session_state.data['neighbourhood'].unique()

# Create filters in the sidebar
selected_room_type = st.sidebar.selectbox("Selecciona Tipo de Habitación", room_types)
selected_neighbourhoods = st.sidebar.multiselect("Selecciona un Barrio", neighbourhoods)

# Filter data based on selected filters
filtered_pisos = st.session_state.data[
    (st.session_state.data['room_type'] == selected_room_type) &
    (st.session_state.data['neighbourhood'].isin(selected_neighbourhoods))
]

# Create map only if filters have changed
map_key = f"{selected_room_type}-{'-'.join(sorted(selected_neighbourhoods))}"
if 'current_map_key' not in st.session_state or st.session_state.current_map_key != map_key:
    st.session_state.current_map_key = map_key
    
    madrid_location = [40.4268627127925, -3.6912505241863776]
    m = folium.Map(location=madrid_location, zoom_start=12, width=600, height=600)
    
    # Add neighborhoods to the map
    folium.GeoJson(
        st.session_state.neighborhoods,
        name="Barrios",
        tooltip=folium.GeoJsonTooltip(fields=['neighbourhood'], labels=False, sticky=True)
    ).add_to(m)
    
    # Create a FeatureGroup for each price category
    feature_groups = {
        "Muy Baratos": folium.FeatureGroup(name="Muy Baratos"),
        "Baratos": folium.FeatureGroup(name="Baratos"),
        "Precio medio": folium.FeatureGroup(name="Precio medio"),
        "Caros": folium.FeatureGroup(name="Caros"),
        "Muy Caros": folium.FeatureGroup(name="Muy Caros")
    }
    
    # Add markers to the corresponding FeatureGroup
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
    
    # Add each FeatureGroup to the map
    for fg in feature_groups.values():
        fg.add_to(m)
    
    # Add layer control to toggle between layers
    folium.LayerControl().add_to(m)
    
    # Store the map in session state
    st.session_state.current_map = m

# Display the map in Streamlit
st_folium(st.session_state.current_map, width=700, height=500)
