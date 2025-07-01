# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, MonthLocator
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import seaborn as sns
import os
import glob
from pyecharts.charts import Pie
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts

LOGO_PATH = 'LogoCSN_Azul.png'
FAVICON_PATH = 'favicon.png'
caminho_excel = 'https://zkzgsynxomretgrzvokk.supabase.co/storage/v1/object/sign/excel-arquivo/dados_resumidos_gerado.xlsx?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9hZGU3OGY1My02MTY0LTQwMTctODZiNC04YmZiOTdiOWZmODEiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJleGNlbC1hcnF1aXZvL2RhZG9zX3Jlc3VtaWRvc19nZXJhZG8ueGxzeCIsImlhdCI6MTc1MTI5NTUyMywiZXhwIjoxNzgyODMxNTIzfQ.hqSF4rmaJ8W-CWWRGhnq6aY6qV27Ruaw5e1_bqONQF8'

st.set_page_config(
    page_title="Solda | Visualização",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon=FAVICON_PATH
)
st.image(LOGO_PATH, width=200)
st.title("Dashboard de Sensores")

data_hora_brasilia = datetime.now(ZoneInfo('America/Sao_Paulo'))

@st.cache_data
def carregar_dados():
    df_semanal = pd.read_excel(caminho_excel, sheet_name='Médias Semanais')
    df_mensal = pd.read_excel(caminho_excel, sheet_name='Médias Mensais')
    df_anual = pd.read_excel(caminho_excel, sheet_name='Médias Anuais')

    df_semanal['SEMANA'] = pd.to_datetime(df_semanal['SEMANA'].astype(str).str[:10], errors='coerce').dt.tz_localize(None)
    df_mensal['MES'] = pd.to_datetime(df_mensal['MES'], errors='coerce')
    df_anual['ANO'] = pd.to_datetime(df_anual['ANO'], format='%Y', errors='coerce')

    df_semanal['VELOCIDADE'] = df_semanal['VELOCIDADE'].astype(int) / 100
    df_mensal['VELOCIDADE'] = df_mensal['VELOCIDADE'].astype(int) / 100
    df_anual['VELOCIDADE'] = df_anual['VELOCIDADE'].astype(int) / 100

    df_semanal['CORRENTE'] = df_semanal['CORRENTE'].astype(int) / 10
    df_mensal['CORRENTE'] = df_mensal['CORRENTE'].astype(int) / 10
    df_anual['CORRENTE'] = df_anual['CORRENTE'].astype(int) / 10

    df_semanal['PRESSAO_SOLDA'] = df_semanal['PRESSAO_SOLDA'].astype(int) / 10
    df_mensal['PRESSAO_SOLDA'] = df_mensal['PRESSAO_SOLDA'].astype(int) / 10
    df_anual['PRESSAO_SOLDA'] = df_anual['PRESSAO_SOLDA'].astype(int) / 10

    df_semanal['TEMPERATURA'] = (df_semanal['TEMPERATURA'].astype(int) / 10).round().astype(int)
    df_mensal['TEMPERATURA'] = (df_mensal['TEMPERATURA'].astype(int) / 10).round().astype(int)
    df_anual['TEMPERATURA'] = (df_anual['TEMPERATURA'].astype(int) / 10).round().astype(int)

    df_semanal['PRESSAO_MARTELADOR'] = df_semanal['PRESSAO_MARTELADOR'].astype(int) / 10
    df_mensal['PRESSAO_MARTELADOR'] = df_mensal['PRESSAO_MARTELADOR'].astype(int) / 10
    df_anual['PRESSAO_MARTELADOR'] = df_anual['PRESSAO_MARTELADOR'].astype(int) / 10

    return df_semanal, df_mensal, df_anual

df_semanal, df_mensal, df_anual = carregar_dados()

cores = {
    'VELOCIDADE': "blue",
    'CORRENTE': "green",
    'PRESSAO_SOLDA': "orange",
    'PRESSAO_MARTELADOR': "purple",
    'TEMPERATURA': "gray"
}

nomes = {
    'VELOCIDADE': 'VELOCIDADE (m/min)',
    'CORRENTE': 'CORRENTE (KA)',
    'PRESSAO_SOLDA': 'PRESSAO DA SOLDA (KN)',
    'PRESSAO_MARTELADOR': 'PRESSAO DO MARTELADOR (KN)',
    'TEMPERATURA': 'TEMPERATURA (ºC)'
}

st.sidebar.header("Filtros e Chat")
historico = st.sidebar.empty()

if 'historico' not in st.session_state:
    st.session_state['historico'] = []

user_input = st.sidebar.text_input("Digite seu comando:")

if user_input:
    st.session_state['historico'].append(user_input)
    historico.write("\n".join(st.session_state['historico']))

st.sidebar.mardown("---")

anos_disponiveis = sorted(df_semanal['SEMANA'].dt.year.unique())
anos_selecionados = st.sidebar.multiselect("Selecione o(s) ano(s):", anos_disponiveis, default=[max(anos_disponiveis)])

df_filtrado_ano = df_semanal[df_semanal['SEMANA'].dt.year.isin(anos_selecionados)]
df_filtrado_ano['SEMANA_NUM'] = df_filtrado_ano['SEMANA'].dt.isocalendar().week

semanas_disponiveis = sorted(df_filtrado_ano['SEMANA_NUM'].unique())

if len(semanas_disponiveis) == 0:
    st.sidebar.warning("Nenhuma semana disponível para os anos selecionados.")
    st.stop()

if 'semanas_selecionadas' not in st.session_state:
    st.session_state['semanas_selecionadas'] = [min(semanas_disponiveis)]

st.sidebar.write("### Selecione as semanas:")

botao1, botao2 = st.sidebar.columns(2)

with botao1:
    if st.button("Selecionar Tudo"):
        st.session_state['semanas_selecionadas'] = semanas_disponiveis
        st.rerun()

with botao2:
    if st.button("Limpar Seleção"):
        st.session_state['semanas_selecionadas'] = []
        st.rerun()

colunas = st.sidebar.columns(5)

for idx, semana in enumerate(semanas_disponiveis):
    is_selected = semana in st.session_state['semanas_selecionadas']
    icon = "🟢" if is_selected else "⚪"
    button_label = f"{icon} {semana:02}"

    with colunas[idx % 5]:
        if st.button(button_label, key=f"btn_{semana}"):
            if is_selected:
                st.session_state['semanas_selecionadas'].remove(semana)
            else:
                st.session_state['semanas_selecionadas'].append(semana)
            st.rerun()

if not st.session_state['semanas_selecionadas']:
    st.session_state['semanas_selecionadas'] = [min(semanas_disponiveis)]

semanas_selecionadas = st.session_state['semanas_selecionadas']
df_semanal_filtrado = df_filtrado_ano[df_filtrado_ano['SEMANA_NUM'].isin(semanas_selecionadas)]

st.sidebar.mardown("---")

data_inicio_mes = st.sidebar.date_input("Data Inicial (Mensal)", value=pd.to_datetime(df_mensal['MES'].min()))
data_fim_mes = st.sidebar.date_input("Data Final (Mensal)", value=pd.to_datetime(df_mensal['MES'].max()))

df_mensal_filtrado = df_mensal[(df_mensal['MES'] >= pd.to_datetime(data_inicio_mes)) & (df_mensal['MES'] <= pd.to_datetime(data_fim_mes))]

def layout_sensor(sensor):
    st.subheader(sensor)

    col_linha, col_direita = st.columns([4, 3])

    with col_linha:
        st.write("Gráfico de Linha")
        st.line_chart(df_mensal_filtrado.set_index('MES')[sensor])

        if sensor == "TEMPERATURA":
            st.write("Mapa de Calor da Temperatura")
            heatmap_df = df_mensal_filtrado[['MES', sensor]].set_index('MES')
            st.dataframe(
                heatmap_df.style.background_gradient(cmap='coolwarm'),
                use_container_width=True
            )

    with col_direita:
        st.write("Gráfico de Barra")
        st.bar_chart(df_mensal_filtrado.set_index('MES')[sensor],
                     height=200 if sensor != "TEMPERATURA" else 350,
                     use_container_width=True
                     )

        st.write("Gráfico de Área")
        st.area_chart(
            df_mensal_filtrado.set_index('MES')[sensor],
            color="#1f77b4AA",
            height=100 if sensor != "TEMPERATURA" else 350,
            use_container_width=True
        )

def analisar_tendencia(dados, eixo_y):
    if len(dados) < 8:
        return "Período selecionado muito curto para análise confiável."

    inicio = dados[eixo_y].iloc[:3].mean()
    fim = dados[eixo_y].iloc[-3:].mean()
    variacao = ((fim - inicio) / inicio) * 100 if inicio != 0 else 0

    if variacao < -1:
        return f"🔻 Dados em tendência de queda: {variacao:.2f}% de redução no período."
    elif variacao > 1:
        return f"🔺 Dados em tendência de alta: {variacao:.2f}% de aumento no período."
    else:
        return f"➖ Dados estáveis: variação de {variacao:.2f}% no período."

aba_semana, aba_mes, aba_ano, aba_pizza = st.tabs(["Semana", "Mês", "Ano", "Falhas"])

with aba_semana:
    st.subheader("Gráficos Semanais")
    
    sensores = list(cores.keys())
    
    # Cria as duas colunas para os quatro primeiros gráficos
    col1, col2 = st.columns(2)

    # Exibe os dois primeiros gráficos na primeira coluna
    with col1:
        for sensor in sensores[:2]:
            st.write(f"## {nomes[sensor]}")
            st.line_chart(df_semanal_filtrado.set_index('SEMANA_NUM')[sensor])
            st.caption(analisar_tendencia(df_semanal_filtrado, sensor))

    # Exibe os dois gráficos seguintes na segunda coluna
    with col2:
        for sensor in sensores[2:4]:
            st.write(f"## {nomes[sensor]}")
            st.line_chart(df_semanal_filtrado.set_index('SEMANA_NUM')[sensor])
            st.caption(analisar_tendencia(df_semanal_filtrado, sensor))

    # Exibe o último gráfico ocupando toda a largura
    st.write(f"## {nomes[sensores[4]]}")
    st.line_chart(df_semanal_filtrado.set_index('SEMANA_NUM')[sensores[4]])
    st.caption(analisar_tendencia(df_semanal_filtrado, sensores[4]))


with aba_mes:
    st.subheader("Gráficos Mensais")
    for sensor in cores.keys():
        layout_sensor(sensor)
        st.caption(analisar_tendencia(df_mensal_filtrado, sensor))

with aba_ano:
    st.subheader("Gráficos Anuais")
    for sensor in cores.keys():
        st.write(f"## {sensor}")
        df_anual_plot = df_anual.groupby(df_anual['ANO'].dt.year)[sensor].mean().reset_index()
        st.bar_chart(df_anual_plot.set_index('ANO')[sensor])
        st.caption(analisar_tendencia(df_anual_plot, sensor))

with aba_pizza:
    st.subheader("Falhas por Componente")
    arquivo = "https://zkzgsynxomretgrzvokk.supabase.co/storage/v1/object/sign/excel-arquivo/Copiar%20de%20Lista%20de%20paradas%20LZC%20d7905c9b.xlsx?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9hZGU3OGY1My02MTY0LTQwMTctODZiNC04YmZiOTdiOWZmODEiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJleGNlbC1hcnF1aXZvL0NvcGlhciBkZSBMaXN0YSBkZSBwYXJhZGFzIExaQyBkNzkwNWM5Yi54bHN4IiwiaWF0IjoxNzUxMzg1ODkzLCJleHAiOjE3ODI5MjE4OTN9.GVqSO1mDGbmSP4tJvJe8N7jMnAAfagPxIHp4k63f90U"

    if arquivo:
        try:
            df_componentes = pd.read_excel(arquivo)
            df_componentes['Componente (PE)'] = df_componentes['Componente (PE)'].astype(str)
            df_componentes['Componente_Num'] = df_componentes['Componente (PE)'].str.extract(r'(\d{3})')[0]
            df_pizza = df_componentes[df_componentes['Componente_Num'].notna()]
            df_pizza['Componente_Num'] = df_pizza['Componente_Num'].astype(int)
            df_pizza = df_pizza[df_pizza['Componente_Num'].between(73, 85)]

            if not df_pizza.empty:
                pizza_count = df_pizza['Componente (PE)'].value_counts().reset_index()
                pizza_count.columns = ['Componentes', 'Quantidade']

                st.subheader("Gráfico de Falhas por Componente")

                modo_escuro = st.get_option('theme.base') == 'dark'
                cor_label = "#fff" if modo_escuro else "#000"

                pie = Pie()
                pie.height = "700px"

                pie.add(
                    "",
                    [list(z) for z in zip(pizza_count['Componentes'].astype(str), pizza_count['Quantidade'])],
                    radius=["40%", "85%"],
                    center=["50%", "45%"],
                    itemstyle_opts={"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
                    rosetype="radius",
                    label_opts=opts.LabelOpts(
                        position="outside",
                        formatter="{b}: {c} ({d}%)",
                        font_size=12,
                        color=cor_label
                    )
                )

                pie.set_global_opts(legend_opts=opts.LegendOpts(is_show=False), graphic_opts=[])

                st_pyecharts(pie)

                st.write("### Últimas falhas registradas")
                ultimas_falhas = df_pizza.sort_values(by='Dt. Início (PE)', ascending=False).head(5)
                st.dataframe(ultimas_falhas, use_container_width=True)

            else:
                st.warning("Nenhum componente válido encontrado entre 073 e 085.")

        except Exception as e:
            st.error(f"Erro ao processar arquivo de paradas: {str(e)}")

st.markdown("---")
st.caption("Desenvolvido por Luis Ignacio - 2025")
st.caption("Versão 1.0.4")
