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

# --- FUNÇÕES DE ESTILO ---
def gerar_estilo_dinamico(df, aba_atual):
    aba_upper = aba_atual.upper()
    # ATUALIZADO: Incluído RESUMÃO na lógica de cores pastéis
    if any(x in aba_upper for x in ["UTILIZADO", "SIMULADOR", "RESUMÃO"]):
        if 'Local' in df.columns:
            locais_unicos = df['Local'].unique()
            mapeamento = {local: PALETA_PASTEL_LOCAIS[i % len(PALETA_PASTEL_LOCAIS)] for i, local in enumerate(locais_unicos)}
            return df.style.apply(lambda row: [f"background-color: {mapeamento.get(row['Local'], 'white')}; color: black;" for _ in row], axis=1)
        # Se for Resumão e não tiver 'Local', aplica fundo neutro scannable
        return df.style.set_properties(**{'background-color': 'white', 'color': 'black'})
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

# --- LÓGICA DE ESTADO ---
if 'cesta' not in st.session_state: st.session_state.cesta = []
if 'visualizando' not in st.session_state: st.session_state.visualizando = False

# --- MENU LATERAL ---
st.sidebar.title("🏛️ Menu Principal")

# Botão Instruções (Home)
if st.sidebar.button("📖 Instruções de Uso"):
    st.session_state.visualizando = False
    st.rerun()

edificio_opt = st.sidebar.selectbox("Selecione o Edifício para Consultar:", ["--- Selecione ---", "Lina Bo Bardi", "Pietro"])

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
    st.info("⚠️ **Nota:** Este aplicativo destina-se exclusivamente à **consulta** e **simulação** de dados.")
    st.markdown("""
    Este sistema foi desenvolvido para facilitar a gestão de iluminação do **MASP**. Aqui você pode consultar o estoque e planejar as exposições.
    
    ### Como usar o sistema:
    1. **Selecione a Unidade:** No menu à esquerda, escolha qual edifício deseja consultar.
    2. **Aba Simulador:** Consulte o planejamento confirmado na planilha e use a "Calculadora de Projeto" no topo para simular montagens acumuladas sem alterar os dados oficiais.
    3. **Aba Estoque:** Verifique a quantidade real de material disponível na sala de estoque hoje.
    4. **Aba Utilizado:** Veja a distribuição atual dos equipamentos por galeria e andar.
    5. **Busca Rápida:** Use a lupa acima de cada tabela para filtrar itens específicos.
    ---
    """)
    st.markdown("<p style='font-style: italic; color: #888; font-size: 0.9em; text-align: right;'>Desenvolvido por: Marcel Alani Gilber</p>", unsafe_allow_html=True)

# --- EXIBIÇÃO DAS TABELAS ---
elif st.session_state.visualizando:
    dict_abas = carregar_dados(url_atual)
    if dict_abas:
        # ATUALIZADO: Incluído RESUMÃO na detecção de abas
        abas_v = [a for a in dict_abas.keys() if any(x in a.upper() for x in ["ESTOQUE", "UTILIZADO", "SIMULADOR", "RESUMÃO"])]
        aba_sel = st.sidebar.radio("Navegação:", abas_v)
        
        df = dict_abas[aba_sel].copy()
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        df = df[[c for c in df.columns if "CHAVE" not in c.upper() and "UNNAMED" not in c.upper()]]
        for cp in [c for c in df.columns if any(p in c.lower() for p in ['local', 'categoria'])]: df[cp] = df[cp].ffill()
        
        col_nums = [c for c in df.columns if any(p in c.lower() for p in ['saldo', 'quant', 'total', 'uso', 'manut', 'necessária'])]
        for col in col_nums: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # ATUALIZADO: Título específico para o Resumão
        if "RESUMÃO" in aba_sel.upper():
            st.title(f"📊 Visão Gerencial (Resumão) - {edificio_opt}")
        elif "SIMULADOR" in aba_sel.upper():
            st.title(f"🚀 Simulador de Projeto - {edificio_opt}")
            df_est = dict_abas['Estoque'].copy()
            df_est.columns = [str(c).strip() for c in df_est.columns]
            col_qtd_planilha = next((c for c in df.columns if 'QUANT' in c.upper()), None)

            st.markdown("**Como simular:** Adicione itens no formulário abaixo.")

            with st.expander("🛠️ ADICIONAR AO PROJETO", expanded=True):
                c1, c2, c3 = st.columns([1.5, 2, 1])
                local_simu = c1.selectbox("Local:", df['Local'].unique() if 'Local' in df.columns else ["Geral"])
                item_simu = c2.selectbox("Equipamento:", df_est['Item'].unique())
                qtd_simu = c3.number_input("Qtd:", min_value=1, step=1)
                if st.button("➕ Adicionar"):
                    st.session_state.cesta.append({"Local": local_simu, "Item": item_simu, "Qtd": qtd_simu})
                    st.rerun()

            if st.session_state.cesta:
                st.subheader("📋 Resumo Acumulado")
                for i, item_cesta in enumerate(st.session_state.cesta):
                    col_item, col_status, col_lixo = st.columns([2, 3, 0.5])
                    item_nome = item_cesta['Item']
                    total_simu = sum(x['Qtd'] for x in st.session_state.cesta if x['Item'] == item_nome)
                    total_planilha = df[df['Item'] == item_nome][col_qtd_planilha].sum() if col_qtd_planilha else 0
                    s_ref = df_est[(df_est['Item'] == item_nome) & (df_est['Categoria'] == 'Refletor')]['Saldo'].sum()
                    s_lam = df_est[(df_est['Item'] == item_nome) & (df_est['Categoria'] == 'Lâmpada')]['Saldo'].sum()
                    
                    status_txt = ""
                    if s_ref > 0:
                        status_txt += f"Ref: {'✅ OK' if total_simu <= (s_ref - total_planilha) else '⚠️ Falta'} "
                    if s_lam > 0:
                        status_txt += f"Lâm: {'✅ OK' if total_simu <= (s_lam - total_planilha) else '⚠️ Falta'}"

                    col_item.write(f"**{item_cesta['Local']}**: {item_cesta['Qtd']}x {item_nome}")
                    col_status.write(status_txt)
                    if col_lixo.button("🗑️", key=f"del_{i}"):
                        st.session_state.cesta.pop(i)
                        st.rerun()
            st.markdown("---")
            st.subheader("📌 Reservas Confirmadas")
        else:
            st.title(f"🏛️ {edificio_opt} - {aba_sel}")

        busca = st.text_input(f"🔍 Pesquisar em {aba_sel}:")
        if busca:
            df = df[df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)]

        st.dataframe(gerar_estilo_dinamico(df, aba_sel).map(destacar_alertas).format({c: "{:d}" for c in col_nums if c in df.columns}), 
                     use_container_width=True, height=500, hide_index=True)
