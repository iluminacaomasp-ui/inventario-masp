import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Configuração da página - Reset visual
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- FUNÇÃO DE ESTILO BLINDADA CONTRA PRETO E DECIMAIS ---
def aplicar_estilo_final(df):
    # 1. Reset total: Força fundo branco e texto preto em TUDO
    # Isso mata o erro do "preto" na raiz, independente da fórmula
    styler = df.style.set_properties(**{
        'background-color': 'white',
        'color': 'black',
        'border-color': '#e6e6e6'
    })

    # 2. Lógica de Alerta para as células com as fórmulas (OK / Falta)
    def destacar_status(valor):
        v = str(valor).strip()
        # Se contiver os seus termos das fórmulas ou números negativos
        if "Falta" in v or "❌" in v or "-" in v:
            return 'background-color: #ff4b4b !important; color: white !important; font-weight: bold;'
        if "✅" in v or "OK" in v:
            return 'background-color: #2ecc71 !important; color: white !important; font-weight: bold;'
        # Se for zero, deixa um cinza bem clarinho (limpeza visual)
        if v in ["0", "0.0"]:
            return 'color: #d1d1d1 !important;'
        return ''

    return styler.map(destacar_status)

@st.cache_data(ttl=20)
def carregar_dados_seguro(url):
    try:
        response = requests.get(url, timeout=30)
        # Importante: convert_float=True ajuda a tratar o erro dos decimais na leitura
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except:
        return None

st.title("🏛️ Gestão de Iluminação MASP - Lina")

if st.sidebar.button("🔄 Sincronizar Agora"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados_seguro(URL_PUB)

if dict_abas:
    # Filtro de abas (Esconde as internas)
    lista_visivel = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza de colunas técnicas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill) para Local/Categoria
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # --- TRATAMENTO AGRESSIVO DE NÚMEROS (FIM DOS DECIMAIS) ---
    palavras_chave_num = ['saldo', 'quant', 'total', 'uso', 'manut', 'observação']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave_num)]
    for col in col_nums:
        # Convertemos para numérico e forçamos INTEIRO para sumir o .0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:", placeholder="Digite para filtrar...")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Configuração de Colunas Fixas
    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    # EXIBIÇÃO FINAL - Com formatador de inteiro rígido
    st.dataframe(
        aplicar_estilo_final(df).format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config
    )
else:
    st.info("💡 Sincronizando dados...")
