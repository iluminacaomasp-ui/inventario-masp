import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Inventário MASP - Lina", layout="wide")

# LINK DE PUBLICAÇÃO (Mais estável para o Streamlit Cloud)
# Ele usa o seu ID de planilha com o comando de publicação direta
URL_PUB = "https://docs.google.com"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

@st.cache_data(ttl=20) # Atualiza a cada 20 segundos
def carregar_dados_blindado(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            # Lê todas as abas (Estoque, Utilizado, etc)
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Botão de atualização na lateral
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

# --- CARREGAMENTO ---
dict_abas = carregar_dados_blindado(URL_PUB)

if dict_abas:
    # Menu para escolher as abas
    aba = st.sidebar.selectbox("Selecione a Visualização:", list(dict_abas.keys()))
    df = dict_abas[aba].copy()

    # 1. LIMPEZA DE CABEÇALHOS (Resolve Ítem com acento e espaços)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # 2. TRATAMENTO DE CÉLULAS MESCLADAS
    # Identifica onde está a Categoria (mesmo sendo a 2ª coluna agora)
    col_cat = [c for c in df.columns if 'Categoria' in c]
    if col_cat:
        df[col_cat[0]] = df[col_cat[0]].ffill()

    # 3. IDENTIFICA COLUNAS NUMÉRICAS
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # 4. FILTRO DE CATEGORIA NA LATERAL
    if col_cat:
        st.sidebar.markdown("---")
        lista_cats = ["Todas"] + sorted(df[col_cat[0]].dropna().unique().tolist())
        cat_sel = st.sidebar.selectbox("Filtrar por Categoria:", lista_cats)
        if cat_sel != "Todas":
            df = df[df[col_cat[0]] == cat_sel]

    # 5. BARRA DE BUSCA (Busca em qualquer coluna: Item, Marca, etc)
    busca = st.text_input("🔍 Digite o que procura (Item ou Marca):", "")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # 6. CORES NO SALDO
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    # EXIBIÇÃO DA TABELA
    st.dataframe(
        df.style.applymap(destar_estoque, subset=col_cor)
                .format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True,
        height=600
    )
else:
    st.info("💡 Conectando ao Google Sheets... Se o erro de 'zip file' persistir, clique no botão 'Sincronizar' na lateral.")
