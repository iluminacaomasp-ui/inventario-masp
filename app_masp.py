import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página (Trava o visual para evitar conflitos de tema)
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

# --- FUNÇÃO DE ESTILO BLINDADA (RESET TOTAL) ---
def aplicar_estilo_limpo(df, aba_atual):
    # Reset de cores para evitar o fundo preto do "Dark Mode"
    styler = df.style.set_properties(**{
        'background-color': 'white',
        'color': 'black'
    })

    # Alertas de Status (Verde e Vermelho)
    def destacar_status(valor):
        v = str(valor).strip()
        if "Falta" in v or "❌" in v or (v.startswith('-') and any(c.isdigit() for c in v)):
            return 'background-color: #ff4b4b !important; color: white !important; font-weight: bold;'
        if "✅" in v or v == "OK":
            return 'background-color: #2ecc71 !important; color: white !important; font-weight: bold;'
        if v in ["0", "0.0"]:
            return 'color: #cccccc !important;'
        return 'background-color: white; color: black;'

    # Se for Solicitado ou Utilizado, destaca a coluna de Local em cinza claro
    if any(x in aba_atual.upper() for x in ["SOLICITADO", "UTILIZADO"]):
        col_local = [c for c in df.columns if 'LOCAL' in c.upper()]
        if col_local:
            styler = styler.set_properties(subset=col_local, **{'background-color': '#f9f9f9'})

    return styler.map(destacar_status)

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")
st.markdown("*Monitoramento de Estoque e Planejamento*")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # Filtro de abas
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill)
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # Formatação de números inteiros (remove .0)
    col_nums = [c for c in df.columns if any(p in c.lower() for p in ['saldo', 'quant', 'total', 'uso', 'manut', 'observação'])]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Aplicação do Estilo e Exibição
    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    st.dataframe(
        aplicar_estilo_limpo(df, aba_sel).format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config
    )
else:
    st.info("💡 Carregando dados da nuvem...")
