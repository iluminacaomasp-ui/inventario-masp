import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
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
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return f"Erro na resposta do Google: {response.status_code}"
    except Exception as e:
        return str(e)

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Botão de atualização na lateral
if st.sidebar.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

try:
    dados_abas = carregar_dados_seguro(URL_FINAL)
    
    if isinstance(dados_abas, dict):
        aba = st.sidebar.selectbox("Escolha a Tabela:", list(dados_abas.keys()))
        df = dados_abas[aba].copy()

        # Limpeza de nomes e tratamento de células mescladas
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        
        # Inteligência: Só aplica o ffill (preencher células mescladas) na coluna 'Categoria' 
        # Não importa se ela é a primeira ou a segunda coluna.
        if 'Categoria' in df.columns:
            df['Categoria'] = df['Categoria'].ffill()

        # Identifica colunas numéricas
        palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
        col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
        
        for col in col_nums:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # --- FILTRO POR CATEGORIA (Opcional na Sidebar) ---
        if 'Categoria' in df.columns:
            st.sidebar.markdown("---")
            lista_cats = ["Todas"] + sorted(df['Categoria'].dropna().unique().tolist())
            cat_selecionada = st.sidebar.selectbox("Filtrar Categoria:", lista_cats)
            if cat_selecionada != "Todas":
                df = df[df['Categoria'] == cat_selecionada]

        # Barra de Busca focada no Item
        busca = st.text_input("🔍 Pesquisar por Nome do Item ou Marca:", "")
        if busca:
            df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

        # Aplica cores no Saldo
        col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

        # Exibição da Tabela com a primeira coluna fixada (Item)
        st.dataframe(
            df.style.applymap(destacar_estoque, subset=col_cor)
                    .format({c: "{:.0f}" for c in col_nums}),
            use_container_width=True,
            height=600
        )

except Exception as e:
    st.error(f"Erro inesperado: {e}")
