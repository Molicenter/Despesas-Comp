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

# Oculta completamente a seta de abrir o menu lateral do Streamlit
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

# Opções de Seleção
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
            st.markdown("<h2 style='text-align: center; color: #0ea5e9; margin-bottom: 0;'>Molicenter</h2>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align: center; color: #64748b; margin-top: 5px;'>Portal de Despesas Complementares</h4>", unsafe_allow_html=True)
            st.divider()
            
            lista_usuarios = ["Selecione o usuário..."] + list(USUARIOS_DB.keys())
            user_input = st.selectbox("Usuário de acesso:", lista_usuarios)
            
            # Autocomplete="current-password" bloqueia a sugestão automática do navegador
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
            
            # Formata as colunas de data removendo o padrão complexo do banco
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

# CABEÇALHO SUPERIOR (Substitui o menu lateral)
col_title, col_info, col_btn = st.columns([0.65, 0.25, 0.1])
with col_title:
    st.markdown("<h2 style='margin:0; padding:0;'>💸 Despesas Complementares</h2>", unsafe_allow_html=True)
with col_info:
    st.markdown(f"<div style='text-align: right; margin-top: 5px; color: #cbd5e1; font-size: 14px;'><b>Usuário:</b> {st.session_state['usuario']}<br><b>Nível:</b> {perfil.upper()}</div>", unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='margin-top: 5px;'>", unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear() # Limpa completamente a memória do acesso
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>", unsafe_allow_html=True)

# =========================================================
# 4. INTERFACE PRINCIPAL
# =========================================================

# --- VISÃO DA LOJA (DIGITAÇÃO E EXCLUSÃO) ---
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
                with st.spinner("⏳ Enviando dados para o Google Sheets..."):
                    payload = {
                        "action": "insert",
                        "Loja": loja_fixa,
                        "Nome": nome.upper().strip(),
                        "Motivo": motivo,
                        "Observacoes": obs.strip() if obs else "-",
                        "Departamento": depto,
                        "DataTrabalhada": data_trab.strftime("%d/%m/%Y"),
                        "Valor": valor,
                        "Autorizacao": "Pendente"
                    }
                    
                    sucesso = False
                    try:
                        requests.post(URL_API_DESPESAS, json=payload, timeout=10)
                        sucesso = True
                    except Exception as e:
                        st.error(f"Erro de conexão ao salvar os dados: {e}")
                    
                if sucesso:
                    st.success("✅ Despesa registrada com sucesso!")
                    st.cache_data.clear()
                    time.sleep(1.5)
                    st.rerun()

    st.markdown("---")
    
    # DIVISÃO DA TELA: TABELA À ESQUERDA E BOTÃO DE EXCLUIR À DIREITA
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
                        if row.get("Autorização Supervisor") == "Pendente":
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
                                nome_del = partes[1].strip()
                                valor_del = partes[2].replace("R$", "").strip()
                                
                                with st.spinner("Apagando..."):
                                    payload_del = {
                                        "action": "delete",
                                        "Loja": loja_fixa,
                                        "Nome": nome_del,
                                        "Valor": float(valor_del)
                                    }
                                    
                                    sucesso_del = False
                                    try:
                                        requests.post(URL_API_DESPESAS, json=payload_del, timeout=10)
                                        sucesso_del = True
                                    except Exception as e:
                                        st.error(f"Erro de conexão ao tentar excluir: {e}")
                                
                                if sucesso_del:
                                    st.success("Registro excluído com sucesso!")
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.warning("Por favor, selecione um registro na lista.")
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
            
        df_pendentes = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Pendente'].copy()
        df_historico = df_exibicao[df_exibicao['Autorização Supervisor'] != 'Pendente'].copy()
            
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
        st.markdown("### ⏳ Avaliação em Lote (Lançamentos Pendentes)")
        
        if df_pendentes.empty:
            st.info("✨ Maravilha! Não há despesas pendentes de aprovação no momento.")
        else:
            st.markdown("<span style='font-size:14px; color:#cbd5e1;'>Dê <b>dois cliques</b> na coluna <b>Avaliação 📝</b> para alterar o status. Ao finalizar suas escolhas, clique no botão vermelho de salvar no final da página.</span>", unsafe_allow_html=True)
            
            # Insere a coluna interativa como a primeira da tabela
            df_pendentes.insert(0, 'Avaliação 📝', 'Pendente')
            
            # Remove a coluna original de aprovação para não confundir
            df_edicao = df_pendentes.drop(columns=['Autorização Supervisor'])
            
            # Tabela de Edição de Dados em Lote
            edited_df = st.data_editor(
                df_edicao,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Avaliação 📝": st.column_config.SelectboxColumn(
                        "Avaliação 📝",
                        help="Clique duas vezes para aprovar ou reprovar",
                        width="medium",
                        options=["Pendente", "Aprovado", "Reprovado"],
                        required=True,
                    ),
                    "Carimbo de Data/Hora": st.column_config.Column(disabled=True),
                    "Loja": st.column_config.Column(disabled=True),
                    "Nome Completo": st.column_config.Column(disabled=True),
                    "Motivo": st.column_config.Column(disabled=True),
                    "Observações": st.column_config.Column(disabled=True),
                    "Departamento": st.column_config.Column(disabled=True),
                    "Data Trabalhada": st.column_config.Column(disabled=True),
                    "Valor": st.column_config.NumberColumn(format="R$ %.2f", disabled=True),
                }
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Botão mestre para processar todas as avaliações feitas na tabela
            if st.button("💾 Salvar Alterações no Sistema", type="primary"):
                mudancas = edited_df[edited_df['Avaliação 📝'] != 'Pendente']
                
                if mudancas.empty:
                    st.warning("⚠️ Nenhuma avaliação foi alterada. Mude o status para 'Aprovado' ou 'Reprovado' na tabela antes de salvar.")
                else:
                    with st.spinner(f"⏳ Processando e salvando {len(mudancas)} avaliações de uma vez..."):
                        
                        # Cria uma lista/pacote com todas as alterações para enviar de uma vez só
                        lista_atualizacoes = []
                        for idx, row in mudancas.iterrows():
                            lista_atualizacoes.append({
                                "Loja": row['Loja'],
                                "Nome": row['Nome Completo'],
                                "Valor": float(row['Valor']),
                                "NovoStatus": row['Avaliação 📝']
                            })
                            
                        payload = {
                            "action": "bulk_update",
                            "updates": lista_atualizacoes
                        }
                        
                        sucesso_geral = False
                        try:
                            # Faz um único envio rápido
                            requests.post(URL_API_DESPESAS, json=payload, timeout=20)
                            sucesso_geral = True
                        except Exception as e:
                            st.error(f"Erro de conexão ao salvar: {e}")
                        
                        # Limpa e recarrega após salvar
                        if sucesso_geral:
                            st.success("✅ Avaliações salvas com sucesso!")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()

        st.markdown("<br><hr>", unsafe_allow_html=True)
        with st.expander("📚 Ver Histórico Geral de Avaliações", expanded=False):
            if df_historico.empty:
                st.info("Nenhuma despesa foi avaliada ainda.")
            else:
                df_historico = df_historico.iloc[::-1].reset_index(drop=True)
                st.dataframe(df_historico, use_container_width=True, hide_index=True)
