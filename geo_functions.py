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

def to_gdf(df):
    coord_columns = {
        'latitude': 'longitude',
        'lat': 'lng'
    }
    lat_col = lng_col = None
    for lat, lng in coord_columns.items():
        if lat.lower() in df.columns.str.lower() and lng.lower() in df.columns.str.lower():
            lat_col = df.columns[df.columns.str.lower() == lat.lower()][0]
            lng_col = df.columns[df.columns.str.lower() == lng.lower()][0]
            break
    if lat_col is None or lng_col is None:
        raise ValueError("O DataFrame não contém as colunas de coordenadas esperadas.")
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[lng_col], df[lat_col]))
    gdf.set_crs('EPSG:4326', allow_override=True, inplace=True)
    return gdf.to_crs('EPSG:3857')

def apply_dbscan(gdf, eps, min_samples):
    """
    Aplica o algoritmo DBSCAN no GeoDataFrame e calcula os centroides dos clusters.
    
    Parâmetros:
    gdf (GeoDataFrame): O GeoDataFrame contendo os dados geoespaciais.
    eps (float): Distância máxima entre dois pontos para que sejam considerados parte do mesmo cluster.
    min_samples (int): Número mínimo de pontos necessários para formar um cluster.
    
    Retorna:
    GeoDataFrame: O GeoDataFrame com os clusters atribuídos e geometria dos centroides.
    """
    
    # Verificar se o GeoDataFrame está no CRS correto (EPSG:3857), e se não, converter
    if gdf.crs != 'EPSG:3857':
        gdf = gdf.to_crs(epsg=3857)
    
    # Inicializa a coluna de cluster com -1 (ruído)
    gdf['cluster'] = -1
    cluster_id = 0  

    # Agrupa por 'registrationID' e aplica DBSCAN
    for reg_id, group in gdf.groupby('registrationID'):
        coords = np.column_stack((group.geometry.x, group.geometry.y))
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
        
        # Atualiza a coluna 'cluster' apenas para os grupos processados
        for label in set(db.labels_):
            if label != -1:  # Ignora ruídos
                gdf.loc[group.index[db.labels_ == label], 'cluster'] = cluster_id
                cluster_id += 1  # Incrementa o ID do cluster

    # Filtra os clusters que possuem pelo menos um ponto (exclui os ruídos)
    gdf_clusterizado = gdf[gdf['cluster'] != -1]
    
    # Conta o número de pontos por cluster (por 'registrationID' e 'cluster')
    contagem_pontos_cluster = gdf_clusterizado.groupby(['registrationID', 'cluster']).size().reset_index(name='points')

    # Calcula os centroides dos clusters (geometria média)
    centroides = gdf_clusterizado.groupby(['registrationID', 'cluster'])['geometry'].apply(lambda x: x.unary_union.centroid).reset_index()
    centroides.columns = ['registrationID', 'cluster', 'geometry']
    centroides = centroides.set_crs('EPSG:3857', allow_override=True, inplace=True)

    # Merge para incluir a contagem de pontos
    centroides = centroides.merge(contagem_pontos_cluster, on=['registrationID', 'cluster'], how='inner')

    # Cria um buffer de raio 'eps' metros em torno do centroide do cluster
    centroides['buffer'] = centroides.geometry.buffer(250)
    centroides = centroides.set_geometry("buffer")

    # Converte para o CRS original (EPSG:4326) antes de retornar
    gdf_clusterizado = gdf_clusterizado.to_crs(epsg=4326)
    centroides = centroides.to_crs(epsg=4326)
    centroides = centroides.set_geometry("geometry")
    centroides = centroides.to_crs(epsg=4326)

  
    return gdf_clusterizado, centroides

# Função para gerar cores distintas
def gen_colors(n):
    """
    Gera n cores distintas no formato RGB.
    Cada cor será uma combinação única de Red, Green e Blue.
    """
    colors = []
    step = 255 // n  # Dividimos o intervalo 0-255 em n partes

    for i in range(n):
        # A cada i, a cor muda nas três componentes RGB
        red = (i * step) % 255
        green = ((i * 2 * step) + 85) % 255  # Deslocamento para garantir uma variação mais ampla
        blue = ((i * 3 * step) + 170) % 255  # Outro deslocamento
        colors.append([red, green, blue])  # Adiciona a cor gerada à lista
    
    return colors