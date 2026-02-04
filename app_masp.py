import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- DICIONÁRIO DE CORES PASTÉIS PARA OS LOCAIS ---
CORES_LOCAIS = {
    "1º ANDAR": "#E8F4F8", # Azul Bebê
    "MEZANINO": "#FFF9E6", # Amarelo Creme
    "AQUÁRIO": "#EAFAF1", # Verde Menta
    "2º SUB-SOLO (VARAS)": "#F5EEF8", # Lavanda
    "2º SUB-SOLO (INFERIOR)": "#FDF2E9" # Pêssego
}

# --- FUNÇÃO DE ESTILO PARA A LINHA INTEIRA (ABA SOLICITADO) ---
def estilo_setorizado(row, aba_atual):
    if "SOLICITADO" in aba_atual.upper():
        local = str(row.get('Local', '')).upper()
        bg_color = "white"
        for chave, cor in CORES_LOCAIS.items():
            if chave in local:
                bg_color = cor
                break
        return [f"background-color: {bg_color}; color: black;" for _ in row]
    return ["" for _ in row]

# --- FUNÇÃO DE DESTAQUE DE TEXTO (STATUS/SALDO) ---
def destacar_alertas(valor):
    v_str = str(valor)
    # Se houver "Falta", "❌" ou número negativo, texto fica Vermelho e Negrito
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'color: #ff4b4b; font-weight: bold;'
    # Se houver "✅", texto fica Verde e Negrito
    if "✅" in v_str:
        return 'color: #2ecc71; font-weight: bold;'
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
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()

    # 1. Limpeza de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['categoria', 'local'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # 2. Tratamento Numérico
    palavras_chave_num = ['saldo', 'quant', 'total', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave_num)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # --- 3. APLICAÇÃO DOS ESTILOS ---
    # Primeiro a cor da linha (Fundo)
    estilo_df = df.style.apply(estilo_setorizado, aba_atual=aba_sel, axis=1)
    # Depois a cor do texto (Alertas)
    estilo_df = estilo_df.map(destacar_alertas)

    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left"),
    }

    st.dataframe(
        estilo_df.format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config,
        hide_index=True
    )
else:
    st.info("💡 Sincronizando dados...")
