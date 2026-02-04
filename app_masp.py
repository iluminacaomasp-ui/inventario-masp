import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

# --- 1. CORES DAS LINHAS (POR FAMÍLIA DE ITEM) ---
def estilo_linha(row):
    item = str(row.get('Ítem', row.get('Item', ''))).upper()
    # Cores pastéis bem leves para fundo de linha
    if "PAR 30" in item: color = "#E8F4F8"   # Azul claro
    elif "AR 111" in item: color = "#FFF9E6" # Amarelo claro
    elif "ELIPSO" in item: color = "#F5EEF8" # Roxo claro
    elif "BARN" in item: color = "#EBEDEF"   # Cinza claro
    else: color = "#FFFFFF"                  # Branco
    return [f"background-color: {color}; color: black;" for _ in row]

# --- 2. CORES DOS LOCAIS (DENTRO DA CÉLULA) ---
def colorir_locais(valor):
    cores = {
        "1º ANDAR": "#D6EAF8", "MEZANINO": "#FCF3CF", 
        "AQUÁRIO": "#D4EFDF", "VARAS": "#EBDEF0", "INFERIOR": "#FAD7A0"
    }
    v_upper = str(valor).upper()
    for local, cor in cores.items():
        if local in v_upper:
            return f"background-color: {cor}; color: black; font-weight: bold;"
    return ""

# --- 3. ALERTAS (VERMELHO/VERDE) - PRIORIDADE MÁXIMA ---
def destacar_alertas(valor):
    v_str = str(valor)
    # Vermelho para Falta ou Números Negativos
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'background-color: #E74C3C !important; color: white !important; font-weight: bold;'
    # Verde para OK
    if "✅" in v_str:
        return 'background-color: #27AE60 !important; color: white !important; font-weight: bold;'
    # Cinza para Zeros
    if v_str == "0" or v_str == "0.0":
        return 'color: #BDC3C7;'
    return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except:
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # Filtragem de abas
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza básica
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill)
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # --- APLICAÇÃO DE ESTILOS ---
    # Passo 1: Cor da linha inteira (Família)
    estilo_df = df.style.apply(estilo_linha, axis=1)
    
    # Passo 2: Cor da célula de Local
    col_local = [c for c in df.columns if 'LOCAL' in c.upper()]
    if col_local:
        estilo_df = estilo_df.map(colorir_locais, subset=col_local)
        
    # Passo 3: Alertas (Vencem as outras cores)
    estilo_df = estilo_df.map(destacar_alertas)

    # Configuração de colunas
    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    st.dataframe(estilo_df, use_container_width=True, height=600, column_config=config)
else:
    st.info("💡 Sincronizando dados...")
