import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Inventário MASP - Lina", layout="wide")

# --- LINK PUBLICADO COMO .ODS (Suporta todas as abas e fórmulas) ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=ods"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

@st.cache_data(ttl=20)
def carregar_tudo(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Odfpy lê o arquivo .ods com todas as abas e fórmulas calculadas
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='odf')
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_tudo(URL_PUB)

if dict_abas:
    # Menu lateral com todas as abas originais
    aba = st.sidebar.selectbox("Selecione a Tabela:", list(dict_abas.keys()))
    df = dict_abas[aba].copy()

    # Limpeza e tratamento
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # Preenche categoria (ffill cirúrgico)
    col_cat = [c for c in df.columns if 'Categoria' in c]
    if col_cat:
        df[col_cat[0]] = df[col_cat[0]].ffill()

    # Números sem decimais
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Busca Inteligente (Ignora maiúsculas/minúsculas)
    st.markdown(f"### 🔍 Pesquisar em {aba}")
    busca = st.text_input("Digite o nome do equipamento:", placeholder="Ex: Par 64, Elipso...")

    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Cores
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    st.dataframe(
        df.style.applymap(destacar_estoque, subset=col_cor)
                .format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True,
        height=600
    )
else:
    st.info("💡 Sincronizando com o Google Sheets... Verifique se a publicação como .ods está ativa.")
