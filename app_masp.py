import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- FUNÇÃO DE ESTILO ESPECÍFICA ---
def aplicar_estilos_masp(df, aba_atual):
    # Criamos uma cópia do dataframe para aplicar os estilos
    styler = df.style

    # 1. Se for a aba Solicitado, pintamos as colunas D e E de Cinza Claro
    if "SOLICITADO" in aba_atual.upper():
        # Identificamos as colunas pelos nomes (Status Refletor e Status Lâmpada) ou posições
        cols_cinza = [c for c in df.columns if "STATUS" in c.upper()]
        if cols_cinza:
            styler = styler.set_properties(subset=cols_cinza, **{'background-color': '#F2F2F2', 'color': 'black'})

    # 2. FUNÇÃO DE ALERTAS (VERMELHO/VERDE)
    # Esta função "carimba" a cor por cima, independente da aba
    def destacar_alertas(valor):
        v_str = str(valor).strip()
        # Vermelho para FALTA ou NEGATIVOS
        if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
            return 'background-color: #E74C3C !important; color: white !important; font-weight: bold;'
        # Verde para OK
        if "✅" in v_str:
            return 'background-color: #27AE60 !important; color: white !important; font-weight: bold;'
        return ''

    return styler.map(destacar_alertas)

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # Filtragem de abas operacionais
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza de nomes e colunas técnicas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill)
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # Tratamento de Números (Inteiros e sem decimais)
    palavras_chave_num = ['saldo', 'quant', 'total', 'uso', 'manut', 'observação']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave_num)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Aplicação dos Estilos Simplificados
    estilo_df = aplicar_estilos_masp(df, aba_sel)

    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    # Exibição Final
    st.dataframe(
        estilo_df.format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config
    )
else:
    st.info("💡 Sincronizando dados...")
