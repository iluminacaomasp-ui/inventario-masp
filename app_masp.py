import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

# --- FUNÇÃO DE CORES POR LOCAL ---
def colorir_locais(valor):
    cores = {
        "1º ANDAR": "background-color: #e8f4f8; color: black; font-weight: bold;", 
        "MEZANINO": "background-color: #fef9e7; color: black; font-weight: bold;", 
        "AQUÁRIO": "background-color: #eafaf1; color: black; font-weight: bold;", 
        "2º SUB-SOLO (VARAS)": "background-color: #f4ecf7; color: black; font-weight: bold;", 
        "2º SUB-SOLO (INFERIOR)": "background-color: #fdf2e9; color: black; font-weight: bold;" 
    }
    v_upper = str(valor).upper()
    for local, estilo in cores.items():
        if local == v_upper: # Comparação exata para evitar pintar o item
            return estilo
    return ""

def destacar_dados(valor):
    v_str = str(valor)
    # 1. Alerta para falta explícita ou erro
    if "Falta" in v_str or "❌" in v_str:
        return 'background-color: #ff4b4b; color: white; font-weight: bold;'
    # 2. Confirmação de OK
    if "✅" in v_str:
        return 'background-color: #2ecc71; color: white; font-weight: bold;'
    
    # 3. Lógica para Números Negativos Reais (Déficit)
    try:
        # Só tenta converter se não for o nome do item (evita o erro do traço no PAR 30 - 9W)
        if v_str.strip().startswith('-') and any(char.isdigit() for char in v_str):
            num = float(v_str.replace(' ', ''))
            if num < 0:
                return 'background-color: #ff4b4b; color: white;'
    except:
        pass

    # 4. Estética para zeros
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
    for cp in cols_fill: 
        df[cp] = df[cp].ffill()

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Item": st.column_config.TextColumn("Item", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left"),
    }

    # APLICAÇÃO SEGURA DOS ESTILOS
    estilo_df = df.style.map(destacar_dados)
    
    # Aplica cores de local apenas na coluna 'Local'
    col_local = [c for c in df.columns if 'LOCAL' in c.upper()]
    if col_local:
        estilo_df = estilo_df.map(colorir_locais, subset=col_local)

    st.dataframe(estilo_df, use_container_width=True, height=600, column_config=config)
else:
    st.info("💡 Sincronizando dados...")
