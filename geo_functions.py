import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import json
from io import BytesIO
import h3
import pydeck as pdk

# Função para processar os JSON gerados pelo Infinity
@st.cache_data(ttl='1d')
def load_data(uploaded_files):
    dataframes = []
    
    for uploaded_file in uploaded_files:
        dadosBrutos = json.load(uploaded_file)
        
        signals = [
            signal
            for key in dadosBrutos
            for signal in dadosBrutos[key]['response'].get('signals', [])
        ]
        
        if signals:
            df = pd.DataFrame(signals)
            dataframes.append(df)

    df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

    df = df[["timestamp", "registrationID", "ipAddress", "latitude", "longitude", "markerColour"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values(by='timestamp', ignore_index=True)
    df = df.drop_duplicates()

    return df

@st.cache_data(ttl='1d')
def add_h3(df):
    # Função para converter lat/lng para H3 e adicionar colunas de diferentes resoluções
    
    resolutions = range(5, 16)

    # Pre-calculate H3 cells for all rows at resolution 15
    h3_cells_15 = np.vectorize(lambda lat, lng: h3.latlng_to_cell(lat, lng, res=15))(df['latitude'], df['longitude'])
    
    # Compute and assign H3 cells for all resolutions in ascending order
    for res in resolutions:  # Iterate from 10 to 15
        if res == 15:
            df[f'h3_res_{res}'] = h3_cells_15  # Assign directly for resolution 15
        else:
            df[f'h3_res_{res}'] = np.vectorize(lambda cell: h3.cell_to_parent(cell, res))(h3_cells_15)

    return df
    
# Função para exportar DataFrame como CSV e armazenar em cache
@st.cache_data(ttl='1d')
def export_csv(df):
    return df.to_csv(index=False)

# Função para exportar DataFrame como KML e armazenar em cache
@st.cache_data(ttl='1d')
def export_kml(df):
    # Converte DataFrame para GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']))
    gdf = gdf.set_crs('EPSG:4326')  # Define o CRS como WGS84
    
    # Usando BytesIO para gerar o KML em memória
    kml_buffer = BytesIO()
    gdf.to_file(kml_buffer, driver='KML')
    
    # Retorna o conteúdo do KML como bytes para download
    kml_buffer.seek(0)  # Volta para o início do buffer
    return kml_buffer.read()

# Função para mapear dias da semana para números
@st.cache_data(ttl='1d')
def map_days_to_numbers(days):
    days_map = {
        'Segunda-feira': 0,
        'Terça-feira': 1,
        'Quarta-feira': 2,
        'Quinta-feira': 3,
        'Sexta-feira': 4,
        'Sábado': 5,
        'Domingo': 6
    }
    return [days_map[day] for day in days]

# Função para filtrar os dados
@st.cache_data(ttl='1d')
def filter_data(df, start_hour=0, end_hour=23, days_numbers=None, selected_registration_ids=None):
    if days_numbers is None:
        days_numbers = [0, 1, 2, 3, 4, 5, 6]  # Todos os dias da semana
    if selected_registration_ids is None:
        selected_registration_ids = df['registrationID'].unique()  # Todos os IDs

    # Filtro por intervalo de horas
    df = df[(df['timestamp'].dt.hour >= start_hour) & (df['timestamp'].dt.hour <= end_hour)]
    
    # Filtro por dia da semana
    df = df[df['timestamp'].dt.weekday.isin(days_numbers)]
    
    # Filtro por registrationID
    df = df[df['registrationID'].isin(selected_registration_ids)]
    
    return df

@st.cache_data(ttl='1d')
def top_nth_data(df, nth=50):
    # Count occurrences of registrationID and ipAddress, then get the top 'nth' registrationIDs
    top_nth_df = (
        df.groupby(['registrationID'])
        .size()
        .reset_index(name='count')
        .nlargest(nth, 'count')
    )
    
    return top_nth_df.sort_values(by='count', ascending=False)

@st.cache_data(ttl='1d')
def groupby_h3(df, h3_grid=10):
    # Contagem das ocorrências para a coluna de H3 e depois dos registros
    h3_column = f'h3_res_{h3_grid}'

    grouped_h3 = (
        df.groupby([h3_column])
        .size()
        .reset_index(name='count')
    )
    
    # Renomeia as colunas para 'hex' e 'count'
    grouped_h3 = grouped_h3.rename(columns={h3_column: 'hex'})
    
    return grouped_h3.sort_values(by='count', ascending=False)

@st.cache_data(ttl='1d')
def heatmap_render(df, map="light", opacity=0.5):
    mapbox_styles = {
    "Light": "mapbox://styles/mapbox/light-v10",
    "Dark": "mapbox://styles/mapbox/dark-v10",
    "Streets": "mapbox://styles/mapbox/streets-v11",
    "Outdoors": "mapbox://styles/mapbox/outdoors-v11",
    "Satellite": "mapbox://styles/mapbox/satellite-v9"
}
    # Verificar se o DataFrame contém as colunas de latitude e longitude (em várias variações)
    lat_col = None
    lon_col = None
    possible_lat_names = ['latitude', 'lat', 'Lat']
    possible_lon_names = ['longitude', 'lng', 'Lng']

    # Procurar as colunas correspondentes no DataFrame
    for col in possible_lat_names:
        if col in df.columns:
            lat_col = col
            break
    for col in possible_lon_names:
        if col in df.columns:
            lon_col = col
            break

    # Se não encontrar as colunas de latitude e longitude, retornar um erro
    if lat_col is None or lon_col is None:
        raise ValueError("O DataFrame não contém colunas válidas de latitude e longitude. Verifique os nomes das colunas.")

    # Agrupar os dados por latitude e longitude e gerar a coluna 'count' com a contagem de ocorrências
    df_grouped = df.groupby([lat_col, lon_col]).size().reset_index(name='count')

    # Preparar a camada pydeck para o mapa
    layer = pdk.Layer(
        "HeatmapLayer",  # Tipo de camada para mapa de calor
        df_grouped,  # Dados agrupados
        opacity=opacity,
        get_position=[lon_col, lat_col],  # Usar as colunas encontradas de longitude e latitude
        get_weight="count",  # Usar a coluna 'count' como peso para a intensidade do mapa de calor
    )

    # Definir a visualização do mapa (view state)
    view = pdk.data_utils.compute_view(df_grouped[[lon_col, lat_col]])

    # Renderizar o mapa com a camada e o estilo selecionado
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style=mapbox_styles[map])  # A URL do estilo selecionado
    

    # Exibir o mapa no Streamlit
    return deck