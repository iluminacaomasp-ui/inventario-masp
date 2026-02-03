import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# URL FIXA E CONFERIDA
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;'
        elif num < 5: return 'background-color: #f1c40f; color: black;'
        return ''
    except: return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")
st.markdown("*Sistema de Monitoramento Online - Espaço Lina Bo Bardi*")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    lista_abas = list(dict_abas.keys())
    aba_padrao = 0
    for i, nome in enumerate(lista_abas):
        if "Entrada" in nome or "Saída" in nome:
            aba_padrao = i
            break

    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_abas, index=aba_padrao)
    df = dict_abas[aba_sel].copy()
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    cols_para_preencher = [c for c in df.columns if any(p in c.lower() for p in ['categoria', 'local'])]
    for cp in cols_para_preencher:
        df[cp] = df[cp].ffill()

    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:", placeholder="Digite o que procura...")
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=aba_sel)
    st.download_button(label=f"📥 Baixar {aba_sel} (Excel)", data=output.getvalue(), file_name=f"Inventario_MASP_{aba_sel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    config_colunas = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Item": st.column_config.TextColumn("Item", pinned="left"),
    }
    for cn in col_nums:
        config_colunas[cn] = st.column_config.NumberColumn(cn, format="%d")

    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    st.dataframe(df.style.map(destacar_estoque, subset=col_cor).format({c: "{:.0f}" for c in col_nums}), use_container_width=True, height=600, column_config=config_colunas)
else:
    st.info("💡 Sincronizando com a nuvem...")
