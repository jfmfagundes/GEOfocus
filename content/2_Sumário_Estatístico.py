import streamlit as st
import pandas as pd
#import locale
import altair as alt
import geo_functions as gf

# Definindo a página do Streamlit
st.set_page_config(page_title="Sumário Estatítico", layout="wide")

# Função interna para consulta do IP
st.title("Sumário Estatísticos dos Dados:")

# Verifica se os dados estão no session_state (se já foram carregados)
if 'df' not in st.session_state:
    st.warning("Por favor, faça o upload dos dados primeiro na página de [upload](upload).")
    st.stop()

df = st.session_state.df

# Exibe o sumário e a amostra dos dados
st.header("Resumo dos Dados:")
col1, col2, col3, col4 = st.columns([1.5,2.5,2,2])
col1.metric("**Quantidade IDs Únicos:**", value=df['registrationID'].unique().size)
#col2.metric("**Tamanho do Dataset:**", value=f'{locale.format_string("%d", len(df), grouping=True)} linhas')
col2.metric("**Tamanho do Dataset:**", value=f'{len(df)} linhas')
col3.metric("**Data Inicial:**", value=df['timestamp'].min().strftime('%d-%m-%Y'))
col4.metric("**Data Final:**", value=df['timestamp'].max().strftime('%d-%m-%Y'))
st.divider()
st.header("Gráficos:")
st.subheader("Dispositivos mais presentes na base de dados:")

# Filtros de intervalo de horas
nth = st.slider(
    "Selecione a **quantidade** de dispositivos a serem apresentados:", 
    0, 100, 
    (50),  # Valor inicial do intervalo
    step=10
)

# Contagem dos valores na combinação das colunas 'registrationID'
top_nth_registrationID = gf.top_nth_data(df, nth)

bars_registrationID = (
                        alt.Chart(top_nth_registrationID).mark_bar().encode(
                        alt.X("registrationID")
                        .sort(op="sum", field="count", order="descending")
                        .title(None),
                        alt.Y("count").aggregate('sum')
                        .title('Contagem'),
                        alt.Color("sum(count):Q", scale=alt.Scale(scheme='reds'), legend=None)
                    ).properties(
                        title="Dispositivos mais presentes na base de dados",
                    )
)

col1_2, col2_2 = st.columns([2.5,1.5])
col1_2.altair_chart(bars_registrationID, theme="streamlit", use_container_width=True)
col2_2.markdown(f'Lista dos **{len(top_nth_registrationID)}** dispositivos mais frequentes.')
col2_2.dataframe(top_nth_registrationID, hide_index=True)

st.subheader("Mapa de calor:")

# Create a mapping of English day names to Portuguese names
days_portuguese = {
    'Monday': 'Segunda-feira',
    'Tuesday': 'Terça-feira',
    'Wednesday': 'Quarta-feira',
    'Thursday': 'Quinta-feira',
    'Friday': 'Sexta-feira',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
}

# Extracting the day of the week and hour in a single operation
hm_df = df[['timestamp', 'registrationID']]
hm_df['weekday'] = hm_df['timestamp'].dt.day_name().map(days_portuguese)
hm_df['hour'] = hm_df['timestamp'].dt.hour  # Extract hour from timestamp

# Prepare data for heat map by grouping by day of the week and hour, counting occurrences
heat_map_data = hm_df.groupby(['weekday', 'hour']).size().reset_index(name='count')

# Create heat map using Altair
base = alt.Chart(heat_map_data, title="Mapa de Calor Anotado da Base de Dados").encode(
    alt.X("hour:O", title="Hora").axis(labelAngle=0),  # Use hour directly
    alt.Y("weekday:O", title=None, sort=list(days_portuguese.values()))  # Sort weekdays
)

heatmap_text = base.mark_text(baseline='middle').encode(
    x='hour:O',
    y='weekday:O',
    text='count:Q',
    color=alt.condition(
        alt.datum.count > 5000, 
        alt.value('white'),
        alt.value('black')
    )  # Display count values as text
)

heat_map = base.mark_rect().encode(
    alt.Color("count:Q",
              title="Total",
              scale=alt.Scale(scheme='reds'), 
              legend=None),  # Use count for color encoding
    tooltip=[
        alt.Tooltip("hour:O", title="Hora"),
        alt.Tooltip("weekday:O", title="Dia da Semana"),
        alt.Tooltip("count:Q", title="Total"),
    ],
)

# Combine heatmap and text annotations
final_heatmap = heat_map + heatmap_text

# Apply configurations to remove axis domains and set step width
final_heatmap = final_heatmap.configure_view(
    strokeWidth=0,
    step=40
).configure_axis(
    domain=False
)

# Display heat map in Streamlit (if using Streamlit)
st.altair_chart(final_heatmap, use_container_width=True)

st.subheader("Distribuição de frequência por dia de semana e por horário:")
# Plotando o gráfico para a distribuição por dia da semana
bars_weekdays = (
    alt.Chart(heat_map_data)
    .mark_bar()
    .encode(
        alt.X("weekday:O", title=None, sort=list(days_portuguese.values())),  # Ordenação manual dos dias
        alt.Y("sum(count):Q", title="Contagem"),  # Usando 'sum(count)' para calcular a soma de ocorrências
        alt.Color("sum(count):Q",
                  scale=alt.Scale(scheme='reds'),
                  legend=None,),
        tooltip=[
        alt.Tooltip("weekday:O", title="Dia da Semana:"),
        alt.Tooltip("sum(count):Q", title="Total:"),
    ],
    )
)

# Plotando o gráfico para a distribuição por hora
bars_hours = (
    alt.Chart(heat_map_data)
    .mark_bar()
    .encode(
        alt.X("hour:O", title=None).axis(labelAngle=0),
        alt.Y("sum(count):Q", title=None),
        alt.Color("sum(count):Q", scale=alt.Scale(scheme='reds'), legend=None,),
        tooltip=[
        alt.Tooltip("hour:O", title="Hora:"),
        alt.Tooltip("sum(count):Q", title="Total:"),
    ],
    )
)

# Exibindo os gráficos lado a lado no Streamlit
col1_3, col2_3 = st.columns([2, 3])  # Ajustando a largura das colunas
col1_3.altair_chart(bars_weekdays, use_container_width=True)
col2_3.altair_chart(bars_hours, use_container_width=True)