import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide")

# --- DIRETRIZ: URL CONFERIDA CARACTERE POR CARACTERE ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: 
            return 'background-color: #ff4b4b; color: white;' # Vermelho
        elif num < 5: 
            return 'background-color: #f1c40f; color: black;' # Amarelo
        return ''
    except:
        return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            # Carrega todas as abas usando o motor openpyxl (xlsx)
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Menu lateral para atualização
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

# --- CARREGAMENTO ---
dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # Menu para escolher as abas
    aba_selecionada = st.sidebar.radio("Selecione a Tabela:", list(dict_abas.keys()))
    df = dict_abas[aba_selecionada].copy()

    # 1. Limpeza de nomes de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # 2. Tratamento de células mescladas (ffill na coluna Categoria)
    col_cat = [c for c in df.columns if 'Categoria' in c]
    if col_cat:
        df[col_cat[0]] = df[col_cat[0]].ffill()

    # 3. Identifica colunas numéricas (Saldo, Total, Manut, Uso, Qtd)
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # --- 4. BUSCA INTELIGENTE (Indiferente a Maiúsculas/Minúsculas) ---
    st.markdown(f"### 🔍 Pesquisar em {aba_selecionada}")
    busca = st.text_input("Digite o nome do equipamento ou marca:", placeholder="Ex: Par 64, Elipso, Lâmpada...")

    if busca:
        # Filtra em qualquer coluna, ignorando case (maiúsculo/minúsculo)
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    # 5. Identifica coluna de cor (Saldo ou Disponível)
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    # 6. Exibição da Tabela
    # Corrigido: 'applymap' para versões mais antigas do pandas ou 'map' para novas
    # O Streamlit lida melhor com .style.map para destacar células individuais
    st.dataframe(
        df.style.map(destacar_estoque, subset=col_cor)
                .format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True,
        height=600
    )
else:
    st.info("💡 Conectando ao Google Sheets... Verifique se a planilha está publicada como Excel (.xlsx).")
