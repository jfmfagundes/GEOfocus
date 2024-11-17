import streamlit as st

pg = st.navigation([
    st.Page("content/0_Home.py", icon=":material/home:", default=True),
    st.Page("content/1_Upload_de_Dados.py", url_path='upload', icon=":material/upload_file:"),
    st.Page("content/2_Sumário_Estatístico.py", url_path='statistics', icon=":material/analytics:"),
    st.Page("content/3_Mapa_Rápido.py", url_path='quickmap', icon=":material/map:"),
    st.Page("content/4_Mapa_de_Calor.py", url_path='heatmap', icon=":material/mode_heat:")])
    #st.Page("pages/5_Mapa_Interativo.py", icon=":material/globe:"),
    #st.Page("pages/6_Análise_de_Clusters.py",url_path='cluster', icon=":material/workspaces:"),
    #st.Page("pages/7_Análise_de_Provedores_Internet.py",url_path='isp', icon=":material/language:")  ])
pg.run()