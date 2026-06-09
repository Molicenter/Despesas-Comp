import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import os
import time

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS
# =========================================================
st.set_page_config(page_title="Despesas Complementares - Molicenter", layout="wide")

# COLE AQUI A URL GERADA NO GOOGLE APPS SCRIPT
URL_API_DESPESAS = "https://script.google.com/macros/s/AKfycbwbOdR--mh46XzwbUId8P4OsxQ8-T8ItbE4JwErh10qwMLWWt1S1vYUIFkK1mnzkxArYw/exec" 

# Banco de Usuários (Você pode ajustar conforme as lojas reais)
USUARIOS_DB = {
    "admin@molicenter.com.br": {"senha": "123", "perfil": "admin", "loja_fixa": None},
    "supervisor@molicenter.com.br": {"senha": "123", "perfil": "supervisor", "loja_fixa": None},
    "loja01@molicenter.com.br": {"senha": "123", "perfil": "loja", "loja_fixa": 1},
    "loja02@molicenter.com.br": {"senha": "123", "perfil": "loja", "loja_fixa": 2},
    "loja03@molicenter.com.br": {"senha": "123", "perfil": "loja", "loja_fixa": 3},
    "loja04@molicenter.com.br": {"senha": "123", "perfil": "loja", "loja_fixa": 4},
    "loja08@molicenter.com.br": {"senha": "123", "perfil": "loja", "loja_fixa": 8},
}

# Opções atualizadas conforme as imagens enviadas
OPCOES_MOTIVO = [
    "Ajuste Modular", 
    "Despesas (Justificar)", 
    "Em Efetivação", 
    "Falta Funcionário (dia)", 
    "Falta Qlp", 
    "Folga Domingo", 
    "Folga Feriado", 
    "Folga Férias", 
    "Limpeza", 
    "Venda Sazonal"
]

OPCOES_DEPTO = [
    "Açougue", 
    "Confeitaria", 
    "Cozinha", 
    "Depósito", 
    "Empacotador", 
    "Frente Caixa", 
    "Frios", 
    "Hortifruti", 
    "Loja (reposição)", 
    "Motorista", 
    "Outros", 
    "Padaria", 
    "Segurança"
]

if "logado_despesas" not in st.session_state:
    st.session_state["logado_despesas"] = False
    st.session_state["usuario"] = ""
    st.session_state["perfil"] = ""
    st.session_state["loja_fixa"] = None

# =========================================================
# 2. TELA DE LOGIN
# =========================================================
if not st.session_state["logado_despesas"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1.2, 1])
    
    with col_centro:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #0ea5e9;'>Molicenter</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #64748b; margin-top: -15px;'>Portal de Despesas Complementares</h4>", unsafe_allow_html=True)
            st.divider()
            
            lista_usuarios = ["Selecione o usuário..."] + list(USUARIOS_DB.keys())
            user_input = st.selectbox("Usuário de acesso:", lista_usuarios)
            pass_input = st.text_input("Senha de acesso:", type="password")
            
            if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
                if user_input != "Selecione o usuário...":
                    user_clean = user_input.strip().lower()
                    if user_clean in USUARIOS_DB and USUARIOS_DB[user_clean]["senha"] == pass_input:
                        st.session_state["logado_despesas"] = True
                        st.session_state["usuario"] = user_clean
                        st.session_state["perfil"] = USUARIOS_DB[user_clean]["perfil"]
                        st.session_state["loja_fixa"] = USUARIOS_DB[user_clean]["loja_fixa"]
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.warning("Selecione um usuário válido.")
    st.stop()

# =========================================================
# 3. FUNÇÕES DE DADOS
# =========================================================
@st.cache_data(ttl=10)
def carregar_dados():
    if URL_API_DESPESAS == "COLE_SUA_URL_AQUI":
        return pd.DataFrame()
    try:
        res = requests.get(URL_API_DESPESAS)
        if res.status_code == 200:
            return pd.DataFrame(res.json())
    except Exception as e:
        st.error("Erro ao conectar com a planilha.")
    return pd.DataFrame()

df_base = carregar_dados()

# =========================================================
# 4. INTERFACE PRINCIPAL
# =========================================================
perfil = st.session_state["perfil"]
loja_fixa = st.session_state["loja_fixa"]

st.sidebar.markdown(f"**Usuário:** `{st.session_state['usuario']}`")
st.sidebar.markdown(f"**Nível:** `{perfil.upper()}`")
if st.sidebar.button("🚪 Sair"):
    st.session_state["logado_despesas"] = False
    st.rerun()

st.title("💸 Despesas Complementares")

# --- VISÃO DA LOJA (DIGITAÇÃO) ---
if perfil == "loja":
    st.info(f"📍 Lançamentos - Loja {loja_fixa:02d}")
    
    with st.form("form_despesa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo do Colaborador *")
            motivo = st.selectbox("Motivo *", OPCOES_MOTIVO)
            depto = st.selectbox("Departamento *", OPCOES_DEPTO)
        with col2:
            data_trab = st.date_input("Data Trabalhada *", format="DD/MM/YYYY")
            valor = st.number_input("Valor (R$) *", min_value=0.0, step=10.0, format="%.2f")
            obs = st.text_area("Observações", placeholder="Justificativa ou transferência...")
            
        submit = st.form_submit_button("Registrar Despesa", type="primary", use_container_width=True)
        
        if submit:
            if not nome:
                st.error("O campo Nome é obrigatório.")
            else:
                with st.spinner("Enviando dados..."):
                    payload = {
                        "Loja": loja_fixa,
                        "Nome": nome.upper(),
                        "Motivo": motivo,
                        "Observacoes": obs,
                        "Departamento": depto,
                        "DataTrabalhada": data_trab.strftime("%d/%m/%Y"),
                        "Valor": valor,
                        "Autorizacao": "Pendente"
                    }
                    try:
                        requests.post(URL_API_DESPESAS, json=payload)
                        st.success("✅ Despesa registrada com sucesso!")
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Erro ao salvar os dados.")

    st.markdown("---")
    st.subheader("Seus Registros Recentes")
    if not df_base.empty:
        df_loja = df_base[df_base['Loja'] == loja_fixa]
        st.dataframe(df_loja, use_container_width=True, hide_index=True)

# --- VISÃO GERENCIAL / SUPERVISOR ---
elif perfil in ["admin", "supervisor"]:
    st.success("🌐 Visão Consolidada - Todas as Lojas")
    
    if df_base.empty:
        st.warning("Nenhum dado encontrado ou API não configurada.")
    else:
        # Formatação de exibição
        df_exibicao = df_base.copy()
        if 'Valor' in df_exibicao.columns:
            df_exibicao['Valor'] = pd.to_numeric(df_exibicao['Valor'], errors='coerce').fillna(0)
            
        col_m1, col_m2 = st.columns(2)
        total_despesas = df_exibicao['Valor'].sum()
        total_registros = len(df_exibicao)
        
        col_m1.metric("Total de Registros", total_registros)
        col_m2.metric("Valor Total Acumulado", f"R$ {total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("### Detalhamento Geral")
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
