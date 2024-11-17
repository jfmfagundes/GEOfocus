import streamlit as st

st.set_page_config(layout="wide")

# Customize page title
st.title("Análises de Dados Geoespaciais")

st.markdown(
    """
    Este aplicativo web permite realizar análises com base em dados geoespaciais do _Infinity Tracker_.   
    Trata-se de projeto experimental, sujeito a eventuais _bugs_ e incorreções.
    """
)

st.header("Instruções")

markdown = """
1. Para iniciar você precisará do(s) arquivo(s) exportado(s) pelo _Tracker_.   
2. No Menu de Navegação à esquerda, procure a página de [Upload]() e envie o(s) arquivo(s) de interesse.
3. Após fazer o _upload_ dos dados, basta navegar pelas diferentes opções de análises.
4. As análises podem ser realizadas em qualquer ordem, bastando inicial fazer o _upload_ do arquivo a se estudado.
"""

st.markdown(markdown)