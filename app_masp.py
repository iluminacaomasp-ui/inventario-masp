import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com"

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
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# --- CABEÇALHO ---
st.title("🏛️ Gestão de Iluminação MASP - Lina")
st.markdown("*Sistema de Monitoramento Online - Espaço Lina Bo Bardi*")

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
    
    # 2. Tratamento de células mescladas
    col_cat_nome = [c for c in df.columns if 'Categoria' in c]
    if col_cat_nome:
        df[col_cat_nome] = df[col_cat_nome].ffill()

    # 3. Identifica colunas numéricas
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    
    # Barra de Busca
    busca = st.text_input("🔍 Pesquisar por Ítem (Maiúsculo/Minúsculo):", placeholder="Ex: Par 64, Elipso, Lâmpada...")
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    # Botão de Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=aba_sel)
    st.download_button(
        label="📥 Baixar Tabela Atual (Excel)",
        data=output.getvalue(),
        file_name=f"Inventario_MASP_{aba_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- 4. CONFIGURAÇÃO DE LARGURA (AUTO-AJUSTE) ---
    # Removi os tamanhos fixos ('large', 'medium') para o Streamlit calcular o menor espaço possível
    config_colunas = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned=True),
        "Item": st.column_config.TextColumn("Item", pinned=True),
        "Categoria": st.column_config.TextColumn("Categoria"),
        "Marca": st.column_config.TextColumn("Marca"),
    }
    
    # Colunas numéricas continuam pequenas para otimizar espaço
    for cn in col_nums:
        config_colunas[cn] = st.column_config.NumberColumn(cn, format="%d")

    # Identifica coluna de cor
    col_cor = [c for c in df.columns if any(x in c.lower() for x in ['saldo', 'disponível'])]

    # EXIBIÇÃO FINAL
    # Ao não definir larguras fixas, o Streamlit tenta comprimir as colunas ao tamanho do texto
    st.dataframe(
        df.style.map(destacar_estoque, subset=col_cor).format({c: "{:.0f}" for c in col_nums}),
        use_container_width=True, 
        height=600, 
        column_config=config_colunas
    )

else:
    st.info("💡 Sincronizando com a nuvem... Clique em 'Sincronizar Agora' se a tabela não carregar.")
