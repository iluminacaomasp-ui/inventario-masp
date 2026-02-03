import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Sistema MASP - Lina", layout="wide")

# --- SEU LINK DE PUBLICAÇÃO CORRETO INSERIDO AQUI ---
URL_FINAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

# 2. Função de cores
def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

# 3. Função de carregamento (Documento Inteiro)
@st.cache_data(ttl=30)
def carregar_dados_seguro(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            # Carrega todas as abas: Estoque, Utilizado, Solicitado
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return f"Erro Google: {response.status_code}"
    except Exception as e:
        return str(e)

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Menu lateral para atualização manual
if st.sidebar.button("🔄 Atualizar Dados Agora"):
    st.cache_data.clear()
    st.rerun()

try:
    dados_abas = carregar_dados_seguro(URL_FINAL)
    
    if isinstance(dados_abas, dict):
        # Menu lateral para navegar entre as abas
        aba_selecionada = st.sidebar.selectbox("Escolha a Tabela:", list(dados_abas.keys()))
        df = dados_abas[aba_selecionada].copy()

        # --- TRATAMENTO DOS DADOS ---
        # Limpa nomes de colunas
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        
        # Preenchimento de categorias mescladas (ffill na coluna Categoria)
        if 'Categoria' in df.columns:
            df['Categoria'] = df['Categoria'].ffill()

        # Identifica colunas numéricas (Saldo, Total, Manut, Uso, Qtd)
        palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
        col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
        
        for col in col_nums:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # --- BUSCA INTELIGENTE (Indiferente a Maiúsculas/Minúsculas) ---
        st.markdown(f"### 🔍 Pesquisar em {aba_selecionada}")
        busca = st.text_input("Pesquisar por Ítem, Marca ou Categoria:", placeholder="Ex: Par 64, Elipso, Lâmpada...")

        if busca:
            # case=False garante que ignore maiúsculas/minúsculas
            mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
            df = df[mask]

        # Identifica a coluna para as cores (Saldo ou Disponível)
        col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

        # Exibição da Tabela
        st.dataframe(
            df.style.applymap(destacar_estoque, subset=col_cor)
                    .format({c: "{:.0f}" for c in col_nums}),
            use_container_width=True,
            height=600
        )
    else:
        st.error(f"Erro na conexão: {dados_abas}")

except Exception as e:
    st.error(f"Ocorreu um erro: {e}")
