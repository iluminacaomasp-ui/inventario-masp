import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide")

# --- LINK CORRIGIDO E COMPLETO ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"
def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

@st.cache_data(ttl=20)
def carregar_dados_blindado(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_blindado(URL_PUB)

if dict_abas:
    aba = st.sidebar.selectbox("Selecione a Visualização:", list(dict_abas.keys()))
    df = dict_abas[aba].copy()

    # 1. LIMPEZA DE CABEÇALHOS
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # 2. TRATAMENTO DE CÉLULAS MESCLADAS
    col_cat = [c for c in df.columns if 'Categoria' in c]
    if col_cat:
        df[col_cat] = df[col_cat].ffill()

    # 3. IDENTIFICA COLUNAS NUMÉRICAS
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # 4. FILTRO DE CATEGORIA NA LATERAL
    if col_cat:
        st.sidebar.markdown("---")
        # Pega a primeira coluna que contém 'Categoria' no nome
        nome_col_cat = col_cat[0]
        lista_cats = ["Todas"] + sorted(df[nome_col_cat].dropna().unique().tolist())
        cat_sel = st.sidebar.selectbox("Filtrar por Categoria:", lista_cats)
        if cat_sel != "Todas":
            df = df[df[nome_col_cat] == cat_sel]

    # --- 5. BUSCA INTELIGENTE (Ignora Maiúsculas/Minúsculas) ---
    st.markdown("### 🔍 Pesquisar por Ítem")
    busca = st.text_input("Digite o nome do equipamento:", placeholder="Ex: Par 64, Elipso, Lâmpada...")

    if busca:
        # Busca em todas as colunas de texto, case=False ignora maiúsculas/minúsculas
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    # 6. CORES NO SALDO
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    # EXIBIÇÃO DA TABELA
    st.dataframe(
        df.style.applymap(destacar_estoque, subset=col_cor)
                .format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True,
        height=600
    )
else:
    st.info("💡 Conectando ao Google Sheets... Aguarde um momento.")
