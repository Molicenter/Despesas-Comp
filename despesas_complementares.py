import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import time

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS
# =========================================================
st.set_page_config(
    page_title="Despesas Complementares - Molicenter", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# URL GERADA NO GOOGLE APPS SCRIPT
URL_API_DESPESAS = "https://script.google.com/macros/s/AKfycbwbOdR--mh46XzwbUId8P4OsxQ8-T8ItbE4JwErh10qwMLWWt1S1vYUIFkK1mnzkxArYw/exec" 

# Banco de Usuários
USUARIOS_DB = {
    "admin@molicenter.com.br": {"senha": "moli0000", "perfil": "admin", "loja_fixa": None},
    "supervisor@molicenter.com.br": {"senha": "moli0000", "perfil": "supervisor", "loja_fixa": None},
    "loja01@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 1},
    "loja02@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 2},
    "loja03@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 3},
    "loja04@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 4},
    "loja05@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 5},
    "loja06@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 6},
    "loja07@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 7},
    "loja08@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 8},
    "loja30@molicenter.com.br": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 30},
}

OPCOES_MOTIVO = [
    "Ajuste Modular", "Despesas (Justificar)", "Em Efetivação", "Falta Funcionário (dia)", 
    "Falta Qlp", "Folga Domingo", "Folga Feriado", "Folga Férias", "Limpeza", "Venda Sazonal"
]

OPCOES_DEPTO = [
    "Açougue", "Confeitaria", "Cozinha", "Depósito", "Empacotador", "Frente Caixa", 
    "Frios", "Hortifruti", "Loja (reposição)", "Motorista", "Outros", "Padaria", "Segurança"
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
            st.markdown("<h2 style='text-align: center; color: #0ea5e9; margin-bottom: 0;'>Molicenter</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #64748b; margin-top: 5px;'>Portal de Despesas Complementares</h4>", unsafe_allow_html=True)
            st.divider()
            
            lista_usuarios = ["Selecione o usuário..."] + list(USUARIOS_DB.keys())
            user_input = st.selectbox("Usuário de acesso:", lista_usuarios)
            pass_input = st.text_input("Senha de acesso:", type="password", placeholder="••••••••", autocomplete="current-password")
            
            st.markdown("<br>", unsafe_allow_html=True)
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
# 3. FUNÇÕES DE DADOS E CABEÇALHO SUPERIOR
# =========================================================
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        res = requests.get(URL_API_DESPESAS, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            if 'Data Trabalhada' in df.columns:
                df['Data Trabalhada'] = pd.to_datetime(df['Data Trabalhada'], errors='coerce').dt.strftime('%d/%m/%Y')
                df['Data Trabalhada'] = df['Data Trabalhada'].fillna("-")
            if 'Carimbo de Data/Hora' in df.columns:
                df['Carimbo de Data/Hora'] = pd.to_datetime(df['Carimbo de Data/Hora'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M')
                df['Carimbo de Data/Hora'] = df['Carimbo de Data/Hora'].fillna("-")
            return df
    except Exception as e:
        st.error("Erro ao conectar com a planilha do Google.")
    return pd.DataFrame()

df_base = carregar_dados()

perfil = st.session_state["perfil"]
loja_fixa = st.session_state["loja_fixa"]

col_title, col_info, col_btn = st.columns([0.65, 0.25, 0.1])
with col_title:
    st.markdown("<h2 style='margin:0; padding:0;'>💸 Despesas Complementares</h2>", unsafe_allow_html=True)
with col_info:
    st.markdown(f"<div style='text-align: right; margin-top: 5px; color: #cbd5e1; font-size: 14px;'><b>Usuário:</b> {st.session_state['usuario']}<br><b>Nível:</b> {perfil.upper()}</div>", unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# =========================================================
# 4. INTERFACE PRINCIPAL
# =========================================================

# --- VISÃO DA LOJA (DIGITAÇÃO) ---
if perfil == "loja":
    st.info(f"📍 Módulo de Lançamentos - **Loja {loja_fixa:02d}**")
    
    with st.form("form_despesa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo do Colaborador *")
            motivo = st.selectbox("Motivo *", OPCOES_MOTIVO)
            depto = st.selectbox("Departamento *", OPCOES_DEPTO)
        with col2:
            data_trab = st.date_input("Data Trabalhada *", format="DD/MM/YYYY")
            valor = st.number_input("Valor (R$) *", min_value=0.0, step=10.0, format="%.2f", value=None)
            obs = st.text_area("Observações", placeholder="Justificativa ou transferência...")
            
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("💾 Registrar Despesa", type="primary", use_container_width=True)
        
        if submit:
            if not nome.strip():
                st.error("⚠️ O campo Nome é obrigatório.")
            elif valor is None or valor <= 0:
                st.error("⚠️ O campo Valor deve ser preenchido com um valor maior que zero.")
            else:
                with st.spinner("⏳ Enviando dados..."):
                    payload = {
                        "action": "insert", "Loja": loja_fixa, "Nome": nome.upper().strip(),
                        "Motivo": motivo, "Observacoes": obs.strip() if obs else "-", "Departamento": depto,
                        "DataTrabalhada": data_trab.strftime("%d/%m/%Y"), "Valor": valor, "Autorizacao": "Pendente"
                    }
                    sucesso = False
                    try:
                        requests.post(URL_API_DESPESAS, json=payload, timeout=10)
                        sucesso = True
                    except:
                        st.error("Erro de conexão ao salvar os dados.")
                if sucesso:
                    st.success("✅ Despesa registrada com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1.5)
                    st.rerun()

    st.markdown("---")
    col_tabela, col_delete = st.columns([0.7, 0.3])
    with col_tabela:
        st.markdown("### 📋 Seus Registros Recentes")
    
    if not df_base.empty and 'Loja' in df_base.columns:
        df_loja = df_base[df_base['Loja'].astype(str) == str(loja_fixa)].copy()
        if not df_loja.empty:
            df_loja = df_loja.iloc[::-1].reset_index(drop=True)
            with col_tabela:
                st.dataframe(df_loja, use_container_width=True, hide_index=True)
            with col_delete:
                with st.container(border=True):
                    st.markdown("#### 🗑️ Cancelar Lançamento")
                    st.markdown("<span style='font-size:13px; color:#cbd5e1;'>Lançou errado? Selecione abaixo e exclua.</span>", unsafe_allow_html=True)
                    opcoes_delete = []
                    for idx, row in df_loja.iterrows():
                        if row.get("Autorização Supervisor") == "Pendente": # Só pode deletar o que tá pendente
                            data_str = str(row.get("Data Trabalhada", ""))
                            nome_str = str(row.get("Nome Completo", ""))
                            valor_str = str(row.get("Valor", 0))
                            opcoes_delete.append(f"{data_str} | {nome_str} | R$ {valor_str}")
                    
                    if not opcoes_delete:
                        st.info("Não há registros pendentes para exclusão.")
                    else:
                        registro_selecionado = st.selectbox("Selecione o registro:", ["- Selecione -"] + opcoes_delete, label_visibility="collapsed")
                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                            if registro_selecionado != "- Selecione -":
                                partes = registro_selecionado.split(" | ")
                                nome_del, valor_del = partes[1].strip(), partes[2].replace("R$", "").strip()
                                with st.spinner("Apagando..."):
                                    payload_del = {
                                        "action": "delete", "Loja": loja_fixa, "Nome": nome_del, "Valor": float(valor_del)
                                    }
                                    sucesso_del = False
                                    try:
                                        requests.post(URL_API_DESPESAS, json=payload_del, timeout=10)
                                        sucesso_del = True
                                    except:
                                        st.error("Erro de conexão ao tentar excluir.")
                                if sucesso_del:
                                    st.success("Registro excluído!")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.warning("Por favor, selecione um registro.")
        else:
            with col_tabela:
                st.info("Nenhum registro encontrado para a sua loja até o momento.")
    else:
        st.info("O banco de dados ainda está vazio.")

# --- VISÃO GERENCIAL / SUPERVISOR ---
elif perfil in ["admin", "supervisor"]:
    st.success("🌐 Visão Consolidada - Painel de Aprovação")
    
    if df_base.empty:
        st.warning("Nenhum dado encontrado ou planilha vazia.")
    else:
        df_exibicao = df_base.copy()
        if 'Valor' in df_exibicao.columns:
            df_exibicao['Valor'] = pd.to_numeric(df_exibicao['Valor'], errors='coerce').fillna(0)
            
        # Separa os pendentes dos já avaliados
        df_pendentes = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Pendente']
        df_historico = df_exibicao[df_exibicao['Autorização Supervisor'] != 'Pendente']
            
        col_m1, col_m2 = st.columns(2)
        total_pendente_valor = df_pendentes['Valor'].sum()
        total_pendente_qtd = len(df_pendentes)
        
        with col_m1:
            st.markdown(f"""
            <div style='background-color:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; text-align:center;'>
                <p style='margin:0; font-size:14px; color:#cbd5e1;'>Aguardando Aprovação (Qtd)</p>
                <h2 style='margin:0; color:#fbbf24;'>{total_pendente_qtd}</h2>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div style='background-color:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; text-align:center;'>
                <p style='margin:0; font-size:14px; color:#cbd5e1;'>Valor Pendente</p>
                <h2 style='margin:0; color:#fbbf24;'>R$ {total_pendente_valor:,.2f}</h2>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ⏳ Fila de Lançamentos Pendentes")
        
        def atualizar_status(row_data, novo_status):
            with st.spinner(f"Marcando como {novo_status}..."):
                payload = {
                    "action": "update",
                    "Loja": row_data['Loja'],
                    "Nome": row_data['Nome Completo'],
                    "DataTrabalhada": row_data['Data Trabalhada'],
                    "Valor": float(row_data['Valor']),
                    "NovoStatus": novo_status
                }
                sucesso_upd = False
                try:
                    requests.post(URL_API_DESPESAS, json=payload, timeout=10)
                    sucesso_upd = True
                except Exception as e:
                    st.error("Erro de conexão ao salvar decisão.")
                if sucesso_upd:
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

        if df_pendentes.empty:
            st.info("✨ Maravilha! Não há despesas pendentes de aprovação no momento.")
        else:
            # Lista os pendentes um a um em formato de cards para facilitar a decisão
            for idx, row in df_pendentes.iterrows():
                with st.container(border=True):
                    col_info, col_val, col_y, col_n = st.columns([0.5, 0.2, 0.15, 0.15], vertical_alignment="center")
                    
                    with col_info:
                        st.markdown(f"**Loja {int(row['Loja']):02d}** | {row['Nome Completo']}<br><span style='font-size:13px; color:#94a3b8;'>{row['Motivo']} - {row['Departamento']} ({row['Data Trabalhada']})</span><br><span style='font-size:12px; color:#64748b;'>Obs: {row['Observações']}</span>", unsafe_allow_html=True)
                    with col_val:
                        st.markdown(f"<h3 style='margin:0; color:#e2e8f0;'>R$ {row['Valor']:.2f}</h3>", unsafe_allow_html=True)
                    with col_y:
                        if st.button("✔️ Aprovar", key=f"y_{idx}", type="primary", use_container_width=True):
                            atualizar_status(row, "Aprovado")
                    with col_n:
                        if st.button("❌ Reprovar", key=f"n_{idx}", use_container_width=True):
                            atualizar_status(row, "Reprovado")

        st.markdown("<br><hr>", unsafe_allow_html=True)
        with st.expander("📚 Ver Histórico de Avaliações", expanded=False):
            if df_historico.empty:
                st.info("Nenhuma despesa foi avaliada ainda.")
            else:
                df_historico = df_historico.iloc[::-1].reset_index(drop=True)
                st.dataframe(df_historico, use_container_width=True, hide_index=True)
