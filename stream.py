import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, MonthLocator
from streamlit_autorefresh import st_autorefresh
import seaborn as sns
import time
import os

st_autorefresh(interval=100000, key="refresh")

# Caminho para o Excel - Supabase
caminho_excel = 'https://wefwxrpcpwcfbbdqgpan.supabase.co/storage/v1/object/sign/excel-dados/planilhas/dados_resumidos.xlsx?token=eyJraWQiOiJzdG9yYWdlLXVybC1zaWduaW5nLWtleV9mNmMyYmMxNS1mMDQ4LTQyYjktYTg1ZS0xNWMyYzVlN2VlYmMiLCJhbGciOiJIUzI1NiJ9.eyJ1cmwiOiJleGNlbC1kYWRvcy9wbGFuaWxoYXMvZGFkb3NfcmVzdW1pZG9zLnhsc3giLCJpYXQiOjE3NTA4Njg2ODAsImV4cCI6MzMyNzY2ODY4MH0.Cj7qh0S1uAF9_UoH8ZyJnGBT2yZMPignsqbdkatO90I'
LOGO_PATH = 'LogoCSN_Azul.png'
FAVICON_PATH = 'favicon.png'

# Carregar dados
df_semanal = pd.read_excel(caminho_excel, sheet_name='Médias Semanais')
df_mensal = pd.read_excel(caminho_excel, sheet_name='Médias Mensais')
df_anual = pd.read_excel(caminho_excel, sheet_name='Médias Anuais')

# Corrigir timezone e converter datas
df_semanal['SEMANA'] = pd.to_datetime(df_semanal['SEMANA'].astype(str).str[:10], errors='coerce').dt.tz_localize(None)
df_mensal['MES'] = pd.to_datetime(df_mensal['MES'], errors='coerce')
df_anual['ANO'] = pd.to_datetime(df_anual['ANO'], errors='coerce')

# Cores exclusivas
cores = {
    'VELOCIDADE': 'blue',
    'CORRENTE': 'green',
    'PRESSAO_SOLDA': 'orange',
    'PRESSAO_MARTELADOR': 'purple',
    'TEMPERATURA': 'gray'
}

# Nomes ajustados
nomes = {
    'VELOCIDADE': 'VELOCIDADE (cm/min)',
    'CORRENTE': 'CORRENTE (KA/10)',
    'PRESSAO_SOLDA': 'PRESSAO DA SOLDA (KN/10)',
    'PRESSAO_MARTELADOR': 'PRESSAO DO MARTELADOR (KN/10)',
    'TEMPERATURA': 'TEMPERATURA (ºC*10)'
}

# Configuração da página
st.set_page_config(page_title="Sensores - Visualização Total", layout="wide", page_icon=FAVICON_PATH)
st.image(LOGO_PATH, width=200)
st.title("Dashboard de Sensores")
st.subheader("Médias Semanais e Mensais com Tendência Realista")

def plot_linha_com_media_movel(dados, eixo_x, eixo_y, titulo, cor, tamanho=(8, 4)):
    fig, ax = plt.subplots(figsize=tamanho)
    ax.plot(dados[eixo_x], dados[eixo_y], marker='o', color=cor, linewidth=1.5, label='Média')
    dados['TENDENCIA'] = dados[eixo_y].rolling(window=400, min_periods=1).mean()
    ax.plot(dados[eixo_x], dados['TENDENCIA'], "r--", label='Tendência (Média Móvel)')
    ax.set_title(titulo)
    ax.set_xlabel("Tempo")
    ax.set_ylabel(nomes[eixo_y])
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.tick_params(axis='x', rotation=30)
    if 'MES' in eixo_x:
        ax.xaxis.set_major_locator(MonthLocator(bymonthday=1))
    else:
        ax.xaxis.set_major_locator(AutoDateLocator())
    ax.legend()
    return fig

def plot_mapa_calor_semanal(dados, eixo_tempo, eixo_valor, titulo):
    dados['Ano'] = dados[eixo_tempo].dt.year
    dados['Semana'] = dados[eixo_tempo].dt.isocalendar().week
    pivot = dados.pivot_table(index='Semana', columns='Ano', values=eixo_valor, aggfunc='mean')
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt=".0f", ax=ax, cbar_kws={'label': nomes[eixo_valor]}, annot_kws={"size": 5})
    ax.set_title(titulo)
    return fig

def plot_mapa_calor_mensal(dados, eixo_tempo, eixo_valor, titulo):
    dados['Ano'] = dados[eixo_tempo].dt.year
    dados['Mes'] = dados[eixo_tempo].dt.month
    pivot = dados.pivot_table(index='Mes', columns='Ano', values=eixo_valor, aggfunc='mean')
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot, cmap='coolwarm', annot=True, fmt=".0f", ax=ax, cbar_kws={'label': nomes[eixo_valor]})
    ax.set_title(titulo)
    return fig

def plot_grafico_anual(dados, sensor):
    dados['Ano'] = dados['MES'].dt.year
    df_anual = dados.groupby('Ano')[sensor].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(df_anual['Ano'], df_anual[sensor], color=cores[sensor])
    ax.set_title(f'{nomes[sensor]} - Média Anual')
    ax.set_xlabel('Ano')
    ax.set_ylabel(nomes[sensor])
    ax.grid(True, linestyle='--', alpha=0.6)
    return fig

def analisar_tendencia(dados, eixo_y):
    if len(dados) < 8:
        return "Período selecionado muito curto para análise confiável."

    inicio = dados[eixo_y].iloc[:5].mean()
    fim = dados[eixo_y].iloc[-5:].mean()
    variacao = ((fim - inicio) / inicio) * 100 if inicio != 0 else 0

    if variacao < -1:
        return f"🔻 Dados em tendência de queda: {variacao:.2f}% de redução no período."
    elif variacao > 1:
        return f"🔺 Dados em tendência de alta: {variacao:.2f}% de aumento no período."
    else:
        return f"➖ Dados estáveis: variação de {variacao:.2f}% no período."

# Leitura do sinalizador
def ler_sinal():
    if os.path.exists('atualizacao_sinal.txt'):
        with open('atualizacao_sinal.txt', 'r') as f:
            return f.read().strip()
    return ""

# Filtros
st.sidebar.header("Filtros de Datas")

st.sidebar.subheader("Período Semanal")
data_inicio_semana = st.sidebar.date_input("Data Inicial (Semanal)", value=pd.to_datetime(df_semanal['SEMANA'].min()))
data_fim_semana = st.sidebar.date_input("Data Final (Semanal)", value=pd.to_datetime(df_semanal['SEMANA'].max()))

st.sidebar.subheader("Período Mensal")
data_inicio_mes = st.sidebar.date_input("Data Inicial (Mensal)", value=pd.to_datetime(df_mensal['MES'].min()))
data_fim_mes = st.sidebar.date_input("Data Final (Mensal)", value=pd.to_datetime(df_mensal['MES'].max()))

# Aplicar filtros
df_semanal_filtrado = df_semanal[(df_semanal['SEMANA'] >= pd.to_datetime(data_inicio_semana)) & (df_semanal['SEMANA'] <= pd.to_datetime(data_fim_semana))]
df_mensal_filtrado = df_mensal[(df_mensal['MES'] >= pd.to_datetime(data_inicio_mes)) & (df_mensal['MES'] <= pd.to_datetime(data_fim_mes))]

# Layout dos gráficos semanais
col1, col2 = st.columns(2)
with col1:
    st.subheader("VELOCIDADE - Semanal")
    fig = plot_linha_com_media_movel(df_semanal_filtrado.copy(), 'SEMANA', 'VELOCIDADE', 'Velocidade Média por Semana', cores['VELOCIDADE'])
    plt.close(fig)
    st.pyplot(fig)
    st.write(analisar_tendencia(df_semanal_filtrado, 'VELOCIDADE'))

with col2:
    st.subheader("CORRENTE - Semanal")
    fig = plot_linha_com_media_movel(df_semanal_filtrado.copy(), 'SEMANA', 'CORRENTE', 'Corrente Média por Semana', cores['CORRENTE'])
    plt.close(fig)
    st.pyplot(fig)
    st.write(analisar_tendencia(df_semanal_filtrado, 'CORRENTE'))

col3, col4 = st.columns(2)
with col3:
    st.subheader("PRESSAO DA SOLDA - Semanal")
    fig = plot_linha_com_media_movel(df_semanal_filtrado.copy(), 'SEMANA', 'PRESSAO_SOLDA', 'Pressão da Solda - Semanal', cores['PRESSAO_SOLDA'])
    plt.close(fig)
    st.pyplot(fig)
    st.write(analisar_tendencia(df_semanal_filtrado, 'PRESSAO_SOLDA'))

with col4:
    st.subheader("PRESSAO DO MARTELADOR - Semanal")
    fig = plot_linha_com_media_movel(df_semanal_filtrado.copy(), 'SEMANA', 'PRESSAO_MARTELADOR', 'Pressão do Martelador - Semanal', cores['PRESSAO_MARTELADOR'])
    plt.close(fig)
    st.pyplot(fig)
    st.write(analisar_tendencia(df_semanal_filtrado, 'PRESSAO_MARTELADOR'))

col5, col6 = st.columns(2)
with col5:
    st.subheader("TEMPERATURA - Semanal (Linha)")
    fig = plot_linha_com_media_movel(df_semanal_filtrado.copy(), 'SEMANA', 'TEMPERATURA', 'Temperatura Média por Semana', cores['TEMPERATURA'], tamanho=(8, 4))
    plt.close(fig)
    st.pyplot(fig)
    st.write(analisar_tendencia(df_semanal_filtrado, 'TEMPERATURA'))

with col6:
    st.subheader("TEMPERATURA - Semanal (Mapa de Calor)")
    fig = plot_mapa_calor_semanal(df_semanal_filtrado.copy(), 'SEMANA', 'TEMPERATURA', 'Mapa de Calor - Temperatura Semanal')
    plt.close(fig)
    st.pyplot(fig)

st.markdown("---")
st.subheader("Gráficos Mensais (Linha e Mapa de Calor)")

for sensor in ['VELOCIDADE', 'CORRENTE', 'PRESSAO_SOLDA', 'PRESSAO_MARTELADOR']:
    col_linha, col_barra = st.columns(2)
    with col_linha:
        st.subheader(f"{sensor} - Linha (Mensal)")
        fig = plot_linha_com_media_movel(df_mensal_filtrado.copy(), 'MES', sensor, f'{sensor} - Linha', cores[sensor])
        plt.close(fig)
        st.pyplot(fig)
    with col_barra:
        st.subheader(f"{sensor} - Barra (Mensal)")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df_mensal_filtrado['MES'], df_mensal_filtrado[sensor], color=cores[sensor], width=25)
        ax.set_title(f'{sensor} - Barra')
        ax.set_xlabel('Mês')
        ax.set_ylabel(nomes[sensor])
        if sensor == 'VELOCIDADE':
            ax.set_ylim([600, 1000])
        elif sensor == 'CORRENTE':
            ax.set_ylim([60, 160])
        elif sensor == 'PRESSAO_SOLDA':
            ax.set_ylim([0, 250])
        elif sensor == 'PRESSAO_MARTELADOR':
            ax.set_ylim([100, 500])
        ax.tick_params(axis='x', rotation=20)
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.close(fig)
        st.pyplot(fig)

col_temp_linha, col_temp_mapa = st.columns(2)
with col_temp_linha:
    st.subheader("TEMPERATURA - Linha (Mensal)")
    fig = plot_linha_com_media_movel(df_mensal_filtrado.copy(), 'MES', 'TEMPERATURA', 'Temperatura - Linha', cores['TEMPERATURA'])
    plt.close(fig)
    st.pyplot(fig)
with col_temp_mapa:
    st.subheader("TEMPERATURA - Mapa de Calor (Mensal)")
    fig = plot_mapa_calor_mensal(df_mensal_filtrado.copy(), 'MES', 'TEMPERATURA', 'Mapa de Calor - Temperatura Mensal')
    plt.close(fig)
    st.pyplot(fig)

st.markdown("---")
st.subheader("Análise Anual por Sensor")

for sensor in ['VELOCIDADE', 'CORRENTE', 'PRESSAO_SOLDA', 'PRESSAO_MARTELADOR', 'TEMPERATURA']:
    fig = plot_grafico_anual(df_mensal_filtrado.copy(), sensor)

cols = st.columns(5)

for idx, sensor in enumerate(['VELOCIDADE', 'CORRENTE', 'PRESSAO_SOLDA', 'PRESSAO_MARTELADOR', 'TEMPERATURA']):
    with cols[idx]:
        st.markdown(f"{sensor} - Anual")
        fig = plot_grafico_anual(df_mensal_filtrado.copy(), sensor)
        plt.close(fig)
        st.pyplot(fig)
        st.write(analisar_tendencia(df_mensal_filtrado, sensor))


st.markdown("---")
st.caption("Desenvolvido por Luis Ignacio - 2025")


ultimo_sinal = st.session_state.get('ultimo_sinal', '')
# Lê sinal atual
sinal_atual = ler_sinal()
# Se houver mudança, recarregar a página
if sinal_atual != ultimo_sinal and ultimo_sinal != '':
    st.rerun()
st.session_state['ultimo_sinal'] = sinal_atual

if sinal_atual:
    try:
        # Se sinal_atual for um número
        timestamp = float(sinal_atual)
        data_formatada = datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M')
        st.write("Última atualização detectada:", data_formatada)
    except:
        # Caso não seja um timestamp numérico
        st.write("Última atualização detectada:", sinal_atual)
else:
    st.write("Última atualização detectada:", sinal_atual)
