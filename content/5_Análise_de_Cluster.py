import streamlit as st
import pydeck as pdk
import geopandas as gpd
import geo_functions as gf
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN

# Streamlit UI Setup
st.set_page_config(page_title="Análise de Cluster", layout="wide", page_icon=":map:")

st.title("Análise de Cluster")

if 'df' not in st.session_state:
    st.warning("Por favor, faça o upload dos dados primeiro.")
    st.stop()

df = st.session_state.df

# Sidebar configurations
with st.sidebar:
    st.subheader("Configurações do Mapa:")
    marker_size = st.slider(
        "Tamanho dos pontos",
        min_value=1,
        max_value=200,
        value=100,  # Valor inicial
        step=1
    )
    base_map = st.selectbox("Opções de Mapa Base:", ["Light", "Dark", "Streets", "Satellite", "Outdoors"], index=1)

    st.subheader("Opções de Filtros de Visualização:")
    start_hour, end_hour = st.slider('Selecione o intervalo de horas', 0, 23, (0, 23), step=1)
    selected_days = st.multiselect("Selecione os dias da semana", 
                                  ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
                                  default=['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'])
    days_numbers = gf.map_days_to_numbers(selected_days)
    selected_registration_ids = st.multiselect("Selecione os dispositivos para plotar no mapa", 
                                               df['registrationID'].value_counts().index.tolist(), 
                                               default=df['registrationID'].value_counts().nlargest(50).index.tolist())

# Apply filters
filtered_data = gf.filter_data(df, start_hour, end_hour, days_numbers, selected_registration_ids)

if filtered_data.empty:
    st.warning("Nenhum dado disponível após aplicar os filtros.")
    st.stop()

# DBSCAN Parameters
st.subheader("Parâmetros do DBSCAN")
col1, col2 = st.columns(2)
with col1:
    eps = st.number_input("Valor de Eps (Distância máxima)", min_value=0.0, value=5.0, step=1.0)
with col2:
    min_samples = st.number_input("Número mínimo de pontos em cada Cluster (min_samples)", min_value=1, value=10)

# Verifica se já existe o estado em cache
if 'dbscan_results' not in st.session_state:
    try:
        gdf = gf.to_gdf(filtered_data)
        gdf_clusterizado, centroides = gf.apply_dbscan(gdf, eps, min_samples)

        # Armazena o resultado no cache
        st.session_state.dbscan_results = {
            'gdf_clusterizado': gdf_clusterizado,
            'centroides': centroides
        }

        st.success("DBSCAN aplicado com sucesso!")

    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")
else:
    gdf_clusterizado = st.session_state.dbscan_results['gdf_clusterizado']
    centroides = st.session_state.dbscan_results['centroides']

    # Gerar cores distintas para cada registrationID
    number_registrationIDs = len(gdf_clusterizado['registrationID'].unique())
    colors = gf.gen_colors(number_registrationIDs)

    # Cria um dicionário de cores para cada registrationID
    registrationID_to_color = {registration_id: colors[idx] for idx, registration_id in enumerate(gdf_clusterizado['registrationID'].unique())}

    # Create the layers for pydeck
    layers = []

    # Camada de pontos (ScatterplotLayer)
    for registration_id, color_value in registrationID_to_color.items():
        cluster_data = gdf_clusterizado[gdf_clusterizado['registrationID'] == registration_id]
        if len(cluster_data) > 0:  
            # Cor única para cada registrationID
            layers.append(pdk.Layer("ScatterplotLayer", cluster_data, 
                                    get_position=["longitude", "latitude"], 
                                    get_radius=marker_size, 
                                    get_fill_color=color_value, 
                                    pickable=True, opacity=0.8,))  # Adiciona a legenda com registrationID

    # Camada de buffers (PolygonLayer)
    for cluster in centroides['cluster'].unique():
        buffer_data = centroides[centroides['cluster'] == cluster]
        if len(buffer_data) > 0:
            # Converter a geometria de buffer para coordenadas de exterior
            buffer_data['coordinates'] = buffer_data['buffer'].apply(lambda geom: list(geom.exterior.coords) if geom else []).tolist()
            
            # Adiciona a camada de buffer para o pydeck
            color_value = [255,255,0] # Garante que a cor é usada de forma cíclica
            layers.append(pdk.Layer("PolygonLayer", buffer_data, 
                                    get_polygon=["coordinates"], 
                                    get_fill_color=color_value, 
                                    pickable=True, opacity=0.4,))  # Adiciona a legenda com registrationID

    # Set the initial view of the map
    view = pdk.ViewState(latitude=gdf_clusterizado.geometry.y.mean(), 
                         longitude=gdf_clusterizado.geometry.x.mean(), zoom=11)

    deck = pdk.Deck(layers=layers,
                    initial_view_state=view,
                    tooltip={
                        'html': '<b>ID:</b> {registrationID}',
                        'style': {
                            'color': 'white'
                        }
                    }, map_style=pdk.map_styles.LIGHT
    )
    st.pydeck_chart(deck)

    # Geocoding para o centroide
    st.subheader("Geocoding do Centroide do Cluster")
    st.write("Clique no botão abaixo para encontrar o endereço do ponto central de cada cluster:")
    if st.button("Geocodificar"):
        if not centroides.empty:
            geolocator = Nominatim(user_agent="cluster_geocoder")
            first_cluster = centroides.iloc[0]
            location = geolocator.reverse((first_cluster['latitude'], first_cluster['longitude']), language='pt', timeout=10)
            if location:
                st.success(f"O endereço do centroide do primeiro cluster é: {location.address}")
            else:
                st.error("Não foi possível encontrar o endereço.")
        else:
            st.warning("Nenhum centroide disponível para geocodificação.")