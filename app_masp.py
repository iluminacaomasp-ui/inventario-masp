import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP", layout="wide", page_icon="🏛️")

# --- URLs DE PUBLICAÇÃO (Ajuste o link do Pietro quando tiver) ---
URL_LINA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"
URL_PIETRO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBLmJrDLvDMoz91hpFNLgrJ3pgl_LoenIGP_ptZxxrch3cK9FCIaLkUx4ecD0EMFtWWBcsax7asJDc/pub?output=xlsx"


# --- PALETA DE CORES PASTÉIS PARA LOCAIS ---
PALETA_PASTEL_LOCAIS = ["#E8F4F8", "#FFF9E6", "#EAFAF1", "#F5EEF8", "#FDF2E9", "#EBF5FB", "#F4F6F7", "#FEF9E7"]

# --- DICIONÁRIO DE CORES PARA FAMÍLIAS DE ITENS (ESTOQUE) ---
CORES_ITENS = {
    "PAR 30": "#E8F4F8", # Azul
    "AR 111": "#FFF9E6", # Amarelo
    "ELIPSO": "#F5EEF8", # Roxo
    "LENTE": "#EAF2F8",  # Azul claro (Pietro)
    "BARN": "#EBEDEF",   # Cinza suave
    "REFLETOR": "#F4F6F7" # Cinza neutro
}

def gerar_estilo_dinamico(df, aba_atual):
    aba_upper = aba_atual.upper()
    
    # 1. Regra para abas de Localização (UTILIZADO e SOLICITADO)
    if any(x in aba_upper for x in ["UTILIZADO", "SOLICITADO"]):
        if 'Local' in df.columns:
            locais_unicos = df['Local'].unique()
            mapeamento = {local: PALETA_PASTEL_LOCAIS[i % len(PALETA_PASTEL_LOCAIS)] for i, local in enumerate(locais_unicos)}
            return df.style.apply(lambda row: [f"background-color: {mapeamento.get(row['Local'], 'white')}; color: black;" for _ in row], axis=1)
    
    # 2. Regra para aba de ESTOQUE (Referência: Item/Família)
    elif "ESTOQUE" in aba_upper:
        def cor_estoque(row):
            item = str(row.get('Ítem', row.get('Item', ''))).upper()
            bg = "white"
            for chave, cor in CORES_ITENS.items():
                if chave in item: bg = cor; break
            return [f"background-color: {bg}; color: black;" for _ in row]
        return df.style.apply(cor_estoque, axis=1)
    
    return df.style.set_properties(**{'background-color': 'white', 'color': 'black'})

def destacar_alertas(valor):
    v_str = str(valor)
    # Vermelho para Falta, Erro ou Negativos
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'color: #ff4b4b; font-weight: bold;'
    # Verde para OK
    if "✅" in v_str:
        return 'color: #2ecc71; font-weight: bold;'
    return ''

@st.cache_data(ttl=20)
def carregar_dados(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

# --- INTERFACE LATERAL ---
st.sidebar.title("Edifício")
edificio = st.sidebar.radio("Escolha a Unidade:", ["Lina Bo Bardi", "Pietro"])
url_atual = URL_LINA if edificio == "Lina Bo Bardi" else URL_PIETRO

if st.sidebar.button("🔄 Sincronizar"):
    st.cache_data.clear()
    st.rerun()

dict_abas = carregar_dados(url_atual)

if dict_abas:
    # Filtro de abas visíveis (esconde Entrada/Saída, AUX, etc)
    abas_v = [a for a in dict_abas.keys() if not any(t in a.upper() for t in ["ENTRADA", "SAÍDA", "AUX", "CONFIG"])]
    aba_sel = st.sidebar.radio("Tabela:", abas_v)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza e Formatação de colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill) para Local/Categoria
    for cp in [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]: 
        df[cp] = df[cp].ffill()
    
    # Tratamento de colunas numéricas (Inteiros)
    col_nums = [c for c in df.columns if any(p in c.lower() for p in ['saldo', 'quant', 'total', 'uso', 'manut'])]
    for col in col_nums: 
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.title(f"🏛️ Inventário - {edificio}")
    
    # Barra de busca dinâmica
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Aplicação dos Estilos (Cores de fundo + Cor do texto para alertas)
    estilo_final = gerar_estilo_dinamico(df, aba_sel).map(destacar_alertas)

    # Exibição do Dataframe
    st.dataframe(
        estilo_final.format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, height=600, hide_index=True,
        column_config={
            "Ítem": st.column_config.TextColumn("Ítem", pinned="left"), 
            "Item": st.column_config.TextColumn("Item", pinned="left"),
            "Local": st.column_config.TextColumn("Local", pinned="left")
        }
    )
else:
    st.info(f"💡 Sincronizando dados do edifício {edificio}...")
