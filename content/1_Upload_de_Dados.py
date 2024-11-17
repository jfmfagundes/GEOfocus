import streamlit as st
import geo_functions as gf
#import locale


# Definindo a página
st.set_page_config(page_title="Upload de Dados", layout="wide")
#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
st.title("Upload do arquivo do Tracker:")
st.markdown("_Versão Beta_")

#Código necessário para desativar o menu interativo de download do st.dataframe
st.markdown(
            """
            <style>
            [data-testid="stElementToolbar"] {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

st.subheader("Upload dos dados:")
uploaded_files = st.file_uploader("Escolha um ou mais arquivos para enviar:", type='json', accept_multiple_files=True)

df = st.session_state.get('df')  # Tenta acessar os dados do session_state

# Se os dados já estão no session_state, não precisa fazer o upload novamente
if 'df' not in st.session_state and uploaded_files:
    # Processa os arquivos e armazena no session_state
    df = gf.load_data(uploaded_files)
    df = gf.add_h3(df)
    st.session_state.df = df

    # Exibe o sumário e a amostra dos dados
    st.subheader("Sumário dos Dados:")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("**Quantidade IDs Únicos:**", value=df['registrationID'].unique().size)
    #col2.metric("**Tamanho do Dataset:**", value=f'{locale.format_string("%d", len(df), grouping=True)} linhas')
    col2.metric("**Tamanho do Dataset:**", value=f'{len(df)} linhas')
    col3.metric("**Data Inicial:**", value=df['timestamp'].min().strftime('%d-%m-%Y'))
    col4.metric("**Data Final:**", value=df['timestamp'].max().strftime('%d-%m-%Y'))
    st.divider()
    st.subheader("Amostra dos Dados:")
    st.dataframe(df.head(50))  # Exibe apenas as 50 primeiras linhas

elif 'df' in st.session_state:
    # Se os dados já estiverem no session_state, apenas exibe os sumários
    df = st.session_state.df
    st.subheader("Sumário dos Dados:")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("**Quantidade IDs Únicos:**", value=df['registrationID'].unique().size)
    #col2.metric("**Tamanho do Dataset:**", value=f'{locale.format_string("%d", len(df), grouping=True)} linhas')
    col2.metric("**Tamanho do Dataset:**", value=f'{len(df)} linhas')
    col3.metric("**Data Inicial:**", value=df['timestamp'].min().strftime('%d-%m-%Y'))
    col4.metric("**Data Final:**", value=df['timestamp'].max().strftime('%d-%m-%Y'))
    st.divider()
    st.subheader("Amostra dos Dados:")
    st.dataframe(df.head(50))  # Exibe apenas as 50 primeiras linhas


else:
    st.stop()  # Se não houver dados nem no session_state nem no upload, pare a execução

st.divider()
st.subheader("Exportar Dados:")
# Check-box para ativar a exportação
export_option = st.button("Exportar")

if export_option:
    # Exibe a mensagem de "Aguarde" enquanto os dados estão sendo processados
    with st.spinner("Aguarde, preparando os dados..."):
        # Gera os arquivos CSV e KML em cache
        csv_data = gf.export_csv(df)
        kml_data = gf.export_kml(df)

    # Exibe os botões para download após o processamento
    st.subheader("Exportar dados como CSV ou KML")
    col1, col2, col3 = st.columns([1,1,4])
    # Botão para exportar como CSV
    col1.download_button(
        label="Baixar CSV",
        data=csv_data,
        file_name="dados.csv",
        mime="text/csv"
    )

    # Botão para exportar como KML
    col2.download_button(
        label="Baixar KML",
        data=kml_data,
        file_name="dados.kml",
        mime="application/vnd.google-earth.kml+xml"
    )