import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Sistema MASP - Lina", layout="wide")

# Link de exportação direta
URL_FINAL = "https://docs.google.com"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

@st.cache_data(ttl=30)
def carregar_dados_seguro(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            # sheet_name=None carrega TODAS as abas
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        else:
            st.error(f"Erro do Google: Status {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Botão de atualização na lateral
if st.sidebar.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

# --- CARREGAMENTO ---
dados_abas = carregar_dados_seguro(URL_FINAL)

if dados_abas is None:
    st.warning("⚠️ Aguardando resposta da planilha online... Verifique se ela está compartilhada corretamente.")
else:
    # Menu para escolher as abas encontradas
    opcoes_abas = list(dados_abas.keys())
    aba = st.sidebar.selectbox("Escolha a Tabela:", opcoes_abas)
    
    df = dados_abas[aba].copy()

    # Se a aba estiver vazia, avisa
    if df.empty:
        st.info(f"A aba '{aba}' parece não conter dados.")
    else:
        # Limpeza de nomes
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        
        # Preenche apenas a categoria
        if 'Categoria' in df.columns:
            df['Categoria'] = df['Categoria'].ffill()

        # Identifica colunas de números por palavras-chave
        palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
        col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
        
        for col in col_nums:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Filtro de Categoria
        if 'Categoria' in df.columns:
            st.sidebar.markdown("---")
            lista_cats = ["Todas"] + sorted(df['Categoria'].dropna().unique().tolist())
            cat_sel = st.sidebar.selectbox("Filtrar Categoria:", lista_cats)
            if cat_sel != "Todas":
                df = df[df['Categoria'] == cat_sel]

        # Barra de Busca
        busca = st.text_input("🔍 Pesquisar por Item ou Marca:", "")
        if busca:
            df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

        # Coluna de cor
        col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

        # EXIBIÇÃO
        st.dataframe(
            df.style.applymap(destacar_estoque, subset=col_cor)
                    .format({c: "{:.0f}" for c in col_nums}),
            use_container_width=True,
            height=600
        )
