import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Sistema MASP - Lina", layout="wide")

# --- O SEU LINK DE PUBLICAÇÃO INSERIDO AQUI ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

@st.cache_data(ttl=30)
def carregar_dados_online(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            # Lê todas as abas: Estoque, Utilizado, Solicitado
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return None
    except Exception as e:
        return str(e)

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

st.title("🏛️ Gestão de Iluminação MASP - Lina")

# Botão de atualização manual
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

try:
    # Busca o dicionário de abas
    dicionario_abas = carregar_dados_online(URL_PUB)
    
    if isinstance(dicionario_abas, dict):
        # Menu lateral com as abas: Estoque, Utilizado, Solicitado
        aba_escolhida = st.sidebar.radio("Selecione a Tabela:", list(dicionario_abas.keys()))
        df = dicionario_abas[aba_escolhida].copy()

        # Limpeza e preenchimento
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        df = df.ffill()

        # Identifica colunas numéricas (Saldo, Total, Manut, Uso, Qtd)
        palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
        col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
        
        for col in col_nums:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # Barra de Busca
        busca = st.text_input(f"🔍 Pesquisar em {aba_escolhida}:", "")
        if busca:
            df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

        # Coluna de cor (Saldo)
        col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

        # Exibição da Tabela
        st.dataframe(
            df.style.applymap(destacar_estoque, subset=col_cor)
                    .format({c: "{:.0f}" for c in col_nums}),
            use_container_width=True,
            height=450
        )

        # Cards de Resumo Dinâmicos (Aparecem na aba Estoque)
        if "estoque" in aba_escolhida.lower():
            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            def somar(termo):
                col = [c for c in df.columns if termo in c.lower()]
                return int(df[col].sum().sum()) if col else 0

            c1.metric("Patrimônio", somar('patrimônio'))
            c2.metric("Manutenção", somar('manut'))
            c3.metric("Em Uso", somar('uso'))
            c4.metric("Saldo", somar('saldo'))
            
    else:
        st.error(f"Erro ao acessar planilha: {dicionario_abas}")

except Exception as e:
    st.error(f"Erro inesperado: {e}")

