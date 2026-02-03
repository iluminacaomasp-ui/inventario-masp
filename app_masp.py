import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"

def destacar_estoque(valor):
    try:
        num = float(valor)
        if num == 0: return 'background-color: #ff4b4b; color: white;' # Vermelho
        elif num < 5: return 'background-color: #f1c40f; color: black;' # Amarelo
        return ''
    except: return ''

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        # Leitura binária direta (conforme nosso padrão de sucesso)
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

# --- CABEÇALHO ---
st.title("🏛️ Gestão de Iluminação MASP - Lina")
st.markdown("*Monitoramento Online - Estoque e Localização*")

# Menu lateral
if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # --- LÓGICA PARA ESCONDER ABA DE OPERAÇÃO INTERNA ---
    lista_abas_total = list(dict_abas.keys())
    # Remove qualquer aba que contenha 'Entrada' ou 'Saída' no nome
    lista_abas_visiveis = [a for a in lista_abas_total if "Entrada" not in a and "Saída" not in a]
    
    # Se a lista estiver vazia por algum erro de nome, mostra todas por segurança
    if not lista_abas_visiveis:
        lista_abas_visiveis = lista_abas_total

    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_abas_visiveis)
    df = dict_abas[aba_sel].copy()

    # 1. Limpeza de nomes de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    
    # 2. Tratamento de células mescladas (ffill para Categoria e Local)
    cols_para_preencher = [c for c in df.columns if any(p in c.lower() for p in ['categoria', 'local'])]
    for cp in cols_para_preencher:
        df[cp] = df[cp].ffill()

    # 3. Identifica colunas numéricas
    palavras_chave = ['saldo', 'quant', 'total', 'em ', 'patrimônio', 'uso', 'manut']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    
    # 4. Busca e Download
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:", placeholder="Digite o que procura...")
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=aba_sel)
    st.download_button(
        label=f"📥 Baixar {aba_sel} (Excel)",
        data=output.getvalue(),
        file_name=f"Inventario_MASP_{aba_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # 5. Configuração de largura (Auto-ajuste e Congelamento)
    config_colunas = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Item": st.column_config.TextColumn("Item", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left"), # Congela Local também
        "Categoria": st.column_config.TextColumn("Categoria"),
    }
    
    # Mantém colunas numéricas compactas
    for cn in col_nums:
        config_colunas[cn] = st.column_config.NumberColumn(cn, format="%d")

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
    st.info("💡 Sincronizando com a nuvem... A aba de operação interna (Entrada/Saída) está oculta por segurança.")
