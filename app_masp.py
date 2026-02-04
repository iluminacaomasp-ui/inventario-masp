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

def gerar_estilo_dinamico(df, aba_atual):
    aba_upper = aba_atual.upper()
    if any(x in aba_upper for x in ["UTILIZADO", "SIMULADOR"]):
        if 'Local' in df.columns:
            locais_unicos = df['Local'].unique()
            mapeamento = {local: PALETA_PASTEL_LOCAIS[i % len(PALETA_PASTEL_LOCAIS)] for i, local in enumerate(locais_unicos)}
            return df.style.apply(lambda row: [f"background-color: {mapeamento.get(row['Local'], 'white')}; color: black;" for _ in row], axis=1)
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
    if "Falta" in v_str or "❌" in v_str or (v_str.startswith('-') and any(c.isdigit() for c in v_str)):
        return 'color: #ff4b4b; font-weight: bold;'
    if "✅" in v_str:
        return 'color: #2ecc71; font-weight: bold;'
    return ''

@st.cache_data(ttl=20)
def carregar_dados(url):
    try:
        response = requests.get(url, timeout=30)
        return pd.read_excel(BytesIO(response.content), sheet_name=None, engine='openpyxl')
    except: return None

# --- INICIALIZAÇÃO DA CESTA DE SIMULAÇÃO ---
if 'cesta' not in st.session_state:
    st.session_state.cesta = []
if 'visualizando' not in st.session_state:
    st.session_state.visualizando = False

# --- MENU LATERAL ---
st.sidebar.title("🏛️ Menu Principal")
if st.sidebar.button("📖 Instruções de Uso"):
    st.session_state.visualizando = False

edificio_opt = st.sidebar.selectbox("Selecione o Edifício:", ["--- Selecione ---", "Lina Bo Bardi", "Pietro"])

if edificio_opt != "--- Selecione ---":
    st.session_state.visualizando = True
    url_atual = URL_LINA if edificio_opt == "Lina Bo Bardi" else URL_PIETRO
    if st.sidebar.button("🔄 Sincronizar Dados"):
        st.cache_data.clear()
        st.rerun()
else:
    st.session_state.visualizando = False

# --- TELA DE BOAS-VINDAS ---
if not st.session_state.visualizando:
    st.markdown("<h1>Bem-vindo ao Inventário do <span style='color: #E30613;'>MASP</span></h1>", unsafe_allow_html=True)
    st.info("⚠️ **Nota:** Este aplicativo destina-se exclusivamente à **consulta** de dados.")
    st.markdown("### Como usar o sistema:\n1. Selecione a Unidade no menu lateral.\n2. Use o **Simulador** para planejar montagens acumuladas.")
    st.markdown("<p style='text-align: right; font-style: italic; color: #888;'>Desenvolvido por: Marcel Alani Gilber</p>", unsafe_allow_html=True)

# --- EXIBIÇÃO DAS TABELAS ---
elif st.session_state.visualizando:
    dict_abas = carregar_dados(url_atual)
    if dict_abas:
        abas_v = [a for a in dict_abas.keys() if any(x in a.upper() for x in ["ESTOQUE", "UTILIZADO", "SIMULADOR"])]
        aba_sel = st.sidebar.radio("Navegação:", abas_v)
        df = dict_abas[aba_sel].copy()
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
        for cp in [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]: df[cp] = df[cp].ffill()
        
        # --- LÓGICA DO SIMULADOR ACUMULADO ---
        if "SIMULADOR" in aba_sel.upper():
            st.title(f"🚀 Planejamento Semanal - {edificio_opt}")
            df_est = dict_abas['Estoque'].copy()
            df_est.columns = [str(c).strip() for c in df_est.columns]
            
            with st.expander("🛠️ ADICIONAR AO PROJETO ATUAL", expanded=True):
                c1, c2, c3 = st.columns([1.5, 2, 1])
                local_simu = c1.selectbox("Local da Montagem:", df['Local'].unique())
                item_simu = c2.selectbox("Equipamento:", df_est['Item'].unique())
                qtd_simu = c3.number_input("Qtd:", min_value=1, step=1)
                
                if st.button("➕ Adicionar à Cesta"):
                    st.session_state.cesta.append({"Local": local_simu, "Item": item_simu, "Qtd": qtd_simu})
            
            if st.session_state.cesta:
                st.subheader("📋 Resumo do Projeto (Acumulado)")
                df_cesta = pd.DataFrame(st.session_state.cesta)
                
                # Cálculo de disponibilidade real
                def calcular_status(row):
                    item = row['Item']
                    total_pedido = df_cesta[df_cesta['Item'] == item]['Qtd'].sum()
                    s_ref = df_est[(df_est['Item'] == item) & (df_est['Categoria'] == 'Refletor')]['Saldo'].sum()
                    s_lam = df_est[(df_est['Item'] == item) & (df_est['Categoria'] == 'Lâmpada')]['Saldo'].sum()
                    
                    res = []
                    if s_ref > 0:
                        if total_pedido <= s_ref: res.append(f"✅ Refletor OK ({int(s_ref)})")
                        else: res.append(f"⚠️ Falta Refletor ({int(total_pedido - s_ref)})")
                    if s_lam > 0:
                        if total_pedido <= s_lam: res.append(f"✅ Lâmpada OK ({int(s_lam)})")
                        else: res.append(f"⚠️ Falta Lâmpada ({int(total_pedido - s_lam)})")
                    return " | ".join(res)

                df_cesta['Status Acumulado'] = df_cesta.apply(calcular_status, axis=1)
                st.dataframe(df_cesta.style.map(destacar_alertas), use_container_width=True, hide_index=True)
                
                if st.button("🗑️ Limpar Projeto"):
                    st.session_state.cesta = []
                    st.rerun()

        st.markdown("---")
        busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
        if busca:
            df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

        st.dataframe(gerar_estilo_dinamico(df, aba_sel).map(destacar_alertas), use_container_width=True, height=500, hide_index=True)
