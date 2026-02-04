import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da página
st.set_page_config(page_title="Inventário MASP", layout="wide", page_icon="🏛️")

# --- URLs DE PUBLICAÇÃO (Ajuste o link do Pietro quando tiver) ---
URL_LINA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5xDC_D1MLVhmm03puk-5goOFTelsYp9eT7gyUzscAnkXAvho4noxsbBoeCscTsJC8JfWfxZ5wdnRW/pub?output=xlsx"
URL_PIETRO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBLmJrDLvDMoz91hpFNLgrJ3pgl_LoenIGP_ptZxxrch3cK9FCIaLkUx4ecD0EMFtWWBcsax7asJDc/pub?output=xlsx"

# --- PALETA DE CORES ---
PALETA_PASTEL_LOCAIS = ["#E8F4F8", "#FFF9E6", "#EAFAF1", "#F5EEF8", "#FDF2E9", "#EBF5FB", "#F4F6F7", "#FEF9E7"]
CORES_ITENS = {"PAR 30": "#E8F4F8", "AR 111": "#FFF9E6", "ELIPSO": "#F5EEF8", "LENTE": "#EAF2F8", "BARN": "#EBEDEF", "REFLETOR": "#F4F6F7"}

def destacar_alertas(valor):
    v_str = str(valor)
    if "Falta" in v_str or "❌" in v_str or "-" in v_str: return 'color: #ff4b4b; font-weight: bold;'
    if "✅" in v_str: return 'color: #2ecc71; font-weight: bold;'
    return ''

@st.cache_data(ttl=10)
def carregar_dados(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

# --- INTERFACE ---
st.sidebar.title("🏛️ Menu Principal")
edificio_opt = st.sidebar.selectbox("Selecione o Edifício:", ["--- Selecione ---", "Lina Bo Bardi", "Pietro"])

if edificio_opt == "--- Selecione ---":
    st.markdown("<h1>Bem-vindo ao Inventário do <span style='color: #E30613;'>MASP</span></h1>", unsafe_allow_html=True)
    st.info("⚠️ Este aplicativo é para consulta. Selecione um edifício para começar.")
    st.markdown("<p style='text-align: right; color: gray;'>Desenvolvido por: Marcel Alani Gilber</p>", unsafe_allow_html=True)
else:
    url = URL_LINA if edificio_opt == "Lina Bo Bardi" else URL_PIETRO
    dict_abas = carregar_dados(url)
    
    if dict_abas:
        abas_v = [a for a in dict_abas.keys() if any(x in a.upper() for x in ["ESTOQUE", "UTILIZADO", "SOLICITADO"])]
        aba_sel = st.sidebar.radio("Navegação:", abas_v)
        
        if "SOLICITADO" in aba_sel.upper():
            st.title(f"🚀 Simulador de Projeto - {edificio_opt}")
            
            # --- LÓGICA DO SIMULADOR ---
            df_est = dict_abas['Estoque'].copy()
            df_est.columns = [str(c).strip() for c in df_est.columns]
            
            with st.expander("🔍 Abrir Calculadora de Simulação", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    item_simu = st.selectbox("Selecione o Equipamento:", df_est['Item'].unique())
                with col2:
                    qtd_simu = st.number_input("Quantidade Necessária:", min_value=0, step=1)
                
                # Busca o saldo no estoque real da planilha
                saldo_refletor = df_est[(df_est['Item'] == item_simu) & (df_est['Categoria'] == 'Refletor')]['Saldo'].sum()
                saldo_lampada = df_est[(df_est['Item'] == item_simu) & (df_est['Categoria'] == 'Lâmpada')]['Saldo'].sum()
                
                if qtd_simu > 0:
                    c1, c2 = st.columns(2)
                    # Resultado Refletor
                    if saldo_refletor >= qtd_simu:
                        c1.success(f"Refletor: ✅ Disponível (Saldo: {saldo_refletor})")
                    else:
                        c1.error(f"Refletor: ⚠️ Falta {int(qtd_simu - saldo_refletor)} unidades")
                    
                    # Resultado Lâmpada (Se houver categoria lâmpada para o item)
                    if saldo_lampada > 0:
                        if saldo_lampada >= qtd_simu:
                            c2.success(f"Lâmpada: ✅ Disponível (Saldo: {saldo_lampada})")
                        else:
                            c2.error(f"Lâmpada: ⚠️ Falta {int(qtd_simu - saldo_lampada)} unidades")
            
            st.markdown("---")
            st.subheader("Tabela de Planejamento (Planilha)")
            st.dataframe(dict_abas[aba_sel], use_container_width=True, hide_index=True)

        else:
            st.title(f"🏛️ {edificio_opt} - {aba_sel}")
            st.dataframe(dict_abas[aba_sel], use_container_width=True, hide_index=True)
