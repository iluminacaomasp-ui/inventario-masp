import streamlit as st
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(page_title="Inventário MASP", layout="wide", page_icon="🏛️")

# --- URLs DE PUBLICAÇÃO (Ajuste o link do Pietro quando tiver) ---
URL_LINA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"
URL_PIETRO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBLmJrDLvDMoz91hpFNLgrJ3pgl_LoenIGP_ptZxxrch3cK9FCIaLkUx4ecD0EMFtWWBcsax7asJDc/pub?output=xlsx"


@st.cache_data(ttl=60)
def carregar_dados(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

# --- LÓGICA DE SIMULAÇÃO (CÁLCULO NO APP) ---
def processar_simulacao(df_solicitado, df_estoque):
    # Criamos colunas de Status vazias para o App calcular
    df = df_solicitado.copy()
    
    for idx, row in df.iterrows():
        item = str(row.get('Item', '')).strip()
        qtd_pedida = row.get('Quantidade', 0)
        
        if not item or qtd_pedida <= 0:
            continue
            
        # Busca estoque total do item (somando todas as marcas/estados)
        estoque_refletor = df_estoque[(df_estoque['Item'] == item) & (df_estoque['Categoria'] == 'Refletor')]['Saldo'].sum()
        estoque_lampada = df_estoque[(df_estoque['Item'] == item) & (df_estoque['Categoria'] == 'Lâmpada')]['Saldo'].sum()
        
        # Cálculo Status Refletor
        if estoque_refletor > 0 or "Refletor" in item:
            if qtd_pedida <= estoque_refletor:
                df.at[idx, 'Status Refletor'] = "✅ OK"
            else:
                df.at[idx, 'Status Refletor'] = f"⚠️ Falta {int(estoque_refletor - qtd_pedida)}"
        
        # Cálculo Status Lâmpada
        if estoque_lampada > 0 or "Lâmpada" in item:
            if qtd_pedida <= estoque_lampada:
                df.at[idx, 'Status Lâmpada'] = "✅ OK"
            else:
                df.at[idx, 'Status Lâmpada'] = f"⚠️ Falta {int(estoque_lampada - qtd_pedida)}"
    return df

# --- INTERFACE ---
if 'edificio' not in st.session_state:
    st.session_state.edificio = "--- Selecione ---"

st.sidebar.title("🏛️ Menu Principal")
edificio_opt = st.sidebar.selectbox("Selecione o Edifício:", ["--- Selecione ---", "Lina Bo Bardi", "Pietro"])

if edificio_opt == "--- Selecione ---":
    st.markdown("<h1>Bem-vindo ao Inventário do <span style='color: #E30613;'>MASP</span></h1>", unsafe_allow_html=True)
    st.info("💡 Este aplicativo é um simulador de consulta. Para planejar, selecione um edifício ao lado.")
    st.markdown("<p style='text-align: right; color: gray;'>Desenvolvido por: Marcel Alani Gilber</p>", unsafe_allow_html=True)
else:
    url = URL_LINA if edificio_opt == "Lina Bo Bardi" else URL_PIETRO
    dict_abas = carregar_dados(url)
    
    if dict_abas:
        abas_v = [a for a in dict_abas.keys() if any(x in a.upper() for x in ["ESTOQUE", "UTILIZADO", "SOLICITADO"])]
        aba_sel = st.sidebar.radio("Navegação:", abas_v)
        
        df_principal = dict_abas[aba_sel].copy()
        
        if "SOLICITADO" in aba_sel.upper():
            st.title(f"🚀 Simulador de Projeto - {edificio_opt}")
            st.write("Altere a coluna **Quantidade** para testar a disponibilidade do estoque.")
            
            # Preparamos os dados para o editor
            df_estoque = dict_abas['Estoque'].copy()
            # Garante que nomes de colunas batam
            df_estoque.columns = [str(c).strip() for c in df_estoque.columns]
            df_principal.columns = [str(c).strip() for c in df_principal.columns]
            
            # O Editor de Dados permite que o usuário digite
            df_editado = st.data_editor(
                df_principal,
                column_config={
                    "Quantidade": st.column_config.NumberColumn("Quantidade", min_value=0, step=1),
                    "Status Refletor": st.column_config.TextColumn("Status Refletor", disabled=True),
                    "Status Lâmpada": st.column_config.TextColumn("Status Lâmpada", disabled=True),
                },
                disabled=["Local", "Item"], # Travamos o que não deve ser mudado
                hide_index=True,
                use_container_width=True
            )
            
            # Recalcula os Status baseados no que o usuário digitou
            df_simulado = processar_simulacao(df_editado, df_estoque)
            st.subheader("Resultado da Simulação")
            st.dataframe(df_simulado, use_container_width=True, hide_index=True)
            
        else:
            st.title(f"🏛️ {edificio_opt} - {aba_sel}")
            st.dataframe(df_principal, use_container_width=True, hide_index=True)
