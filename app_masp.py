import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP - Lina", layout="wide", page_icon="🏛️")

# --- DIRETRIZ: URL FIXA E CONFERIDA ---
URL_PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"


# --- FUNÇÃO DE ESTILO REVISADA (SEM CONFLITOS) ---
def formatar_tabela_masp(df, aba_atual):
    # Criamos o objeto de estilo
    styler = df.style

    # 1. FORÇAMOS TODAS AS CÉLULAS A TEREM FUNDO BRANCO E TEXTO PRETO (RESET TOTAL)
    styler = styler.set_properties(**{
        'background-color': 'white',
        'color': 'black',
        'border-color': '#f0f0f0'
    })

    # 2. SE FOR A ABA SOLICITADO, PINTAMOS AS COLUNAS D E E DE CINZA CLARO
    if "SOLICITADO" in aba_atual.upper():
        # Tentamos identificar as colunas Status Refletor e Status Lâmpada
        cols_status = [c for c in df.columns if "STATUS" in c.upper()]
        if cols_status:
            styler = styler.set_properties(subset=cols_status, **{
                'background-color': '#f8f8f8',
                'color': 'black'
            })

    # 3. FUNÇÃO DE ALERTAS (VERMELHO E VERDE)
    def aplicar_alertas(valor):
        v = str(valor).strip()
        # VERMELHO: Se contiver "Falta", "❌" ou for um número negativo
        if "Falta" in v or "❌" in v or (v.startswith('-') and any(c.isdigit() for c in v)):
            return 'background-color: #ff4b4b !important; color: white !important; font-weight: bold;'
        # VERDE: Se contiver "✅" ou "OK"
        if "✅" in v or v == "OK":
            return 'background-color: #2ecc71 !important; color: white !important; font-weight: bold;'
        return ''

    return styler.map(aplicar_alertas)

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
    aba_sel = st.sidebar.radio("Selecione a Tabela:", lista_visivel)
    df = dict_abas[aba_sel].copy()
    
    # Limpeza de nomes e colunas
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
    
    # Preenchimento automático (ffill)
    cols_fill = [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]
    for cp in cols_fill: df[cp] = df[cp].ffill()

    # Tratamento de Números para Inteiros
    palavras_chave_num = ['saldo', 'quant', 'total', 'uso', 'manut', 'observação']
    col_nums = [c for c in df.columns if any(p in c.lower() for p in palavras_chave_num)]
    for col in col_nums:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    st.markdown("---")
    busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
    if busca:
        df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

    # Aplicação do Estilo Blindado
    estilo_final = formatar_tabela_masp(df, aba_sel)

    # Configuração de Colunas
    config = {
        "Ítem": st.column_config.TextColumn("Ítem", pinned="left"),
        "Local": st.column_config.TextColumn("Local", pinned="left")
    }

    # Exibição com formatação de inteiro para colunas numéricas
    st.dataframe(
        estilo_final.format({c: "{:d}" for c in col_nums if c in df.columns}), 
        use_container_width=True, 
        height=600, 
        column_config=config
    )
else:
    st.info("💡 Sincronizando dados...")
