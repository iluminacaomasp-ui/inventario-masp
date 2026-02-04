import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- DICIONÁRIOS DE CORES PASTÉIS ---
CORES_LOCAIS = {
    "1º ANDAR": "#D6EAF8", "MEZANINO": "#FCF3CF", 
    "AQUÁRIO": "#D4EFDF", "VARAS": "#EBDEF0", "INFERIOR": "#FAD7A0"
}

CORES_FAMILIAS = {
    "PAR 30": "#E8F4F8", "AR 111": "#FFF9E6", 
    "ELIPSO": "#F5EEF8", "BARN": "#EBEDEF"
}

# --- FUNÇÃO DE ESTILO DE LINHA (BASE) ---
def aplicar_estilo_linha(row, aba_atual):
    item = str(row.get('Ítem', row.get('Item', ''))).upper()
    local = str(row.get('Local', '')).upper()
    bg_color = "#FFFFFF" # Fundo padrão branco

    # Regra para abas de Localização (Utilizado e Solicitado)
    if any(x in aba_atual.upper() for x in ["UTILIZADO", "SOLICITADO"]):
        for chave, cor in CORES_LOCAIS.items():
            if chave in local:
                bg_color = cor
                break
    # Regra para aba de Estoque
    else:
        for chave, cor in CORES_FAMILIAS.items():
            if chave in item:
                bg_color = cor
                break
    
    # Texto sempre PRETO para leitura clara em fundos coloridos
    return [f"background-color: {bg_color}; color: black;" for _ in row]

# --- FUNÇÃO DE ALERTAS (SOBREPOSIÇÃO) ---
def destacar_alertas(valor):
    v_str = str(valor)
    # 1. Vermelho para FALTA ou NEGATIVOS
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'background-color: #E74C3C !important; color: white !important; font-weight: bold;'
    # 2. Verde para OK
    if "✅" in v_str:
        return 'background-color: #27AE60 !important; color: white !important; font-weight: bold;'
    # 3. Zeros ficam em cinza discreto para não poluir
    if v_str in ["0", "0.0"]:
        return 'color: #AAB7B8 !important;'
    return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza de nomes
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill)
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # Tratamento Numérico (Inteiros sem .0)
    palavras_chave_num = ['saldo', 'quant', 'total', 'uso', 'manut', 'observação']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave_num)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # --- APLICAÇÃO DOS ESTILOS ---
    # Primeiro aplicamos a cor de fundo da linha (Local ou Família)
    estilo_df = df.style.apply(aplicar_estilo_linha, aba_atual=aba_sel, axis=1)
    
    # Depois aplicamos os alertas (OK / Falta) que vão "vencer" a cor de fundo
    estilo_df = estilo_df.map(destacar_alertas)

    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    # Exibição Final - Formatando para INTEIRO puro
    st.dataframe(
        estilo_df.format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config
    )
else:
    st.info("💡 Sincronizando dados...")
