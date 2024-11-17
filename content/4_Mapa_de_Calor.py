import streamlit as st
import pydeck as pdk
import geo_functions as gf

# Definindo a página do Streamlit
st.set_page_config(page_title="Mapa de Calor", layout="wide", page_icon=":map:")

st.title("Mapa de Calor")

with st.expander("Aviso", expanded=True):
    st.info(
        "Essa página gera um Mapa de Calor com base nos dados geoespaciais disponíveis.  "
        "O tempo de renderização da página é proporcional à quantidade de dados a ser analisados.  "   
        "Caso o processo esteja demorado demais, experimente usar os filtros no Menu Lateral para reduzir a quantidade de dados."
    )

# Verificar se o dataframe foi carregado
if 'df' not in st.session_state:
    st.warning("Por favor, faça o upload dos dados primeiro.")
    st.stop()

df = st.session_state.df

# Sidebar para configurações do mapa
with st.sidebar:
    st.subheader("Configurações do Mapa:")
    # Filtro de Mapa Base (base map)
    base_map = st.selectbox(
        "Opções de Mapa Base:",
        ["Light", "Dark", "Streets", "Satellite", "Outdoors"], index=1
    )

    # Filtros de visualização
    st.subheader("Opções de Filtros de Visualização:")

    # Filtro de intervalo de horas
    start_hour, end_hour = st.slider(
        'Selecione o intervalo de horas', 
        0, 23, 
        (0, 23),  # Intervalo padrão
        step=1
    )

    # Filtro de dias da semana
    selected_days = st.multiselect(
        "Selecione os dias da semana",
        ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'],
        default=['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    )
    
    # Mapeamento de dias da semana para números
    days_numbers = gf.map_days_to_numbers(selected_days)

    # Filtro por registrationID
    selected_registration_ids = st.multiselect(
        "Selecione os dispositivos para plotar no mapa",
        df['registrationID'].value_counts().sort_values(ascending=False).index.tolist(),
        default=df['registrationID'].value_counts().sort_values(ascending=False).nlargest(200).index.tolist()  # Default para os 200 primeiros
    )

# Aplicar filtros nos dados
with st.spinner('Filtrando os dados...'):
    filtered_data = gf.filter_data(df, start_hour, end_hour, days_numbers, selected_registration_ids)

# Verifique se o dataframe filtrado contém dados válidos
if filtered_data.empty:
    st.warning("Nenhum dado disponível após aplicar os filtros.")
    st.stop()

# Criando o objeto Deck do pydeck
try:
    deck = gf.heatmap_render(filtered_data, map=base_map, opacity=0.8)

    # Verificar se o objeto é uma instância de Deck válida
    if isinstance(deck, pdk.Deck):
        st.pydeck_chart(deck)
    else:
        st.error("O objeto gerado não é válido para exibição.")
except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o mapa: {e}")