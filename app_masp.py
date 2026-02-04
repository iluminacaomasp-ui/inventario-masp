import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- 1. FUNÇÃO PARA COLORIR A LINHA INTEIRA (POR EQUIPAMENTO/TIPO) ---
def estilo_linha(row):
    # Cores pastéis muito suaves para o fundo da linha
    item = str(row.get('Ítem', row.get('Item', ''))).upper()
    
    # Define a cor baseada no termo encontrado no nome do item
    if "PAR 30" in item:
        color = "#f4faff" # Azul bebê
    elif "AR 111" in item:
        color = "#fff9f0" # Creme/Amarelo suave
    elif "ELIPSO" in item:
        color = "#f9f4ff" # Lavanda
    elif "BARN-DOOR" in item or "BARNDOOR" in item:
        color = "#f2f2f2" # Cinza gelo
    else:
        color = "white"
        
    return [f"background-color: {color}; color: black;" for _ in row]

# --- 2. FUNÇÃO PARA ALERTAS (VERMELHO/VERDE) - SOBREPÕE A COR DA LINHA ---
def destacar_alertas(s):
    v_str = str(s)
    # Alerta de Falta ou Erro
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'background-color: #ff4b4b !important; color: white !important; font-weight: bold;'
    # Confirmação de OK
    if "✅" in v_str:
        return 'background-color: #2ecc71 !important; color: white !important; font-weight: bold;'
    # Estética para zeros
    if v_str == "0":
        return 'color: #ccc;'
    return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    lista_abas_total = list(dict_abas.keys())
    termos_ocultos = ["ENTRADA", "SAÍDA", "AUX", "CONFIG"]
    lista_visivel = [a for a in lista_abas_total if not any(t in a.upper() for t in termos_ocultos)]
    
    aba_sel = st.sidebar.radio("Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # --- APLICAÇÃO DOS ESTILOS ---
    # 1. Primeiro aplica a cor na linha toda
    estilo_df = df.style.apply(estilo_linha, axis=1)
    
    # 2. Depois aplica os alertas (o !important no CSS garante que o vermelho vença o pastel)
    estilo_df = estilo_df.map(destacar_alertas)

    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left"),
    }

    st.dataframe(estilo_df, use_container_width=True, height=600, column_config=config)
else:
    st.info("💡 Sincronizando...")
