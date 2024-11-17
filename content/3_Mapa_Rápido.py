import streamlit as st
import pydeck as pdk
import geo_functions as gf

# Definindo a página do Streamlit
st.set_page_config(page_title="Mapa Rápido", layout="wide", page_icon=":map:")

st.title("Visualização do Mapa:")

# Verifica se os dados estão no session_state (se já foram carregados)
if 'df' not in st.session_state:
    st.warning("Por favor, faça o upload dos dados primeiro na página de [upload](upload).")
    st.stop()

df = st.session_state.df

# Sidebar para configurações do mapa
with st.sidebar:
    st.subheader("Configurações do Mapa:")
    
    # Slider para ajustar o tamanho dos pontos
    marker_size = st.slider(
        "Tamanho dos pontos",
        min_value=0,
        max_value=200,
        value=100,  # Valor inicial
        step=20
    )

    # Toggle para escolher se os pontos serão coloridos pela coluna 'markerColour'
    color_by_column = st.toggle("Cores Individuais", value=False)

    # Expander para filtros de intervalo de horas e dia da semana
    st.subheader("Filtros de Visualização:")

    # Filtros de intervalo de horas
    start_hour, end_hour = st.slider(
        'Selecione o intervalo de horas', 
        0, 23, 
        (0, 23),  # Valor inicial do intervalo
        step=1
    )

    # Filtros de dia da semana
    selected_days = st.multiselect(
        "Selecione os dias da semana",
        ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
        default=['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    )
    
    days_numbers = gf.map_days_to_numbers(selected_days)

    # Filtro de registrationID (fora do expander)
    filter_by_registrationID = st.toggle("Filtrar por dispositivo")
    selected_registration_ids = df['registrationID'].unique()  # Inicializa com todos os IDs de dispositivo
    if filter_by_registrationID:
        selected_registration_ids = st.multiselect(
            "Selecione os dispositivos para plotar no mapa",
            df['registrationID'].unique(),
            default=df['registrationID'].unique()  # Todos os IDs selecionados por padrão
        )

# Aplica os filtros aos dados
filtered_data = gf.filter_data(df, start_hour, end_hour, days_numbers, selected_registration_ids)

# Se 'Colorir pontos' estiver ativado, usa a coluna 'markerColour'
color_column = 'markerColour' if color_by_column else None

# Exibe o mapa
if not df.empty:
    st.info(f"Exibindo **{len(filtered_data)}** registros.")
    st.map(filtered_data, size=marker_size, color=color_column)
else:
    st.write("Nenhum dado disponível para exibir.")
