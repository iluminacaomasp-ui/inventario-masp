import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

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
            return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# --- TOPO COM LOGO E TÍTULO ---
c_logo, c_tit = st.columns([1, 4]) 
with c_logo:
    st.image("https://masp.org.br", width=120)
with c_tit:
    st.title("Gestão de Iluminação MASP - Lina")
    st.markdown("*Sistema de Monitoramento em Nuvem*")

# Menu lateral
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    abas_disponiveis = list(dict_abas.keys())
    aba_sel = st.sidebar.radio("Selecione a Tabela:", abas_disponiveis)
    df = dict_abas[aba_sel].copy()

    # 1. Limpeza de nomes de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # 2. Tratamento de células mescladas (ffill seguro)
    col_cat_nome = [c for c in df.columns if 'Categoria' in c]
    if col_cat_nome:
        # Preenche a coluna categoria para que os filtros funcionem
        df[col_cat_nome[0]] = df[col_cat_nome[0]].ffill()

    # 3. Identifica colunas numéricas
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    
    # Barra de Busca e Botão de Download
    col_busca, col_btn = st.columns([3, 1])
    
    with col_busca:
        busca = st.text_input("🔍 Pesquisar Item (Indiferente a maiúsculas/minúsculas):", placeholder="Ex: PAR, Elipso, Lâmpada...")
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    with col_btn:
        st.write(" ") # Alinhamento
        output = BytesIO()
        # Necessário instalar xlsxwriter no requirements.txt
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name=aba_sel)
        st.download_button(
            label="📥 Baixar Excel",
            data=output.getvalue(),
            file_name=f"Inventario_MASP_{aba_sel}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Configuração de larguras (Mapeia Item com e sem acento por segurança)
    config_colunas = {
        "Ítem": st.column_config.TextColumn("Ítem", width="large"),
        "Item": st.column_config.TextColumn("Item", width="large"),
        "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
    }
    for cn in col_nums:
        config_colunas[cn] = st.column_config.NumberColumn(cn, width="small", format="%d")

    # Identifica coluna de cor
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    # EXIBIÇÃO FINAL
    st.dataframe(
        df.style.map(destacar_estoque, subset=col_cor).format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True,
        height=600,
        column_config=config_colunas
    )

else:
    st.info("💡 Conectando à nuvem... Verifique se a planilha está publicada como Excel.")
