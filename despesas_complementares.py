import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import time
import io
import os
import streamlit.components.v1 as components

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS E CSS
# =========================================================
st.set_page_config(
    page_title="Despesas Complementares - Molicenter", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    
    /* ESTILOS DA NOSSA NOVA TABELA NATIVA (Para a Tela) */
    .custom-table table {
        width: 100%;
        border-collapse: collapse;
        color: #f8fafc; 
        font-size: 14px;
        margin-bottom: 20px;
    }
    .custom-table th, .custom-table td {
        border-bottom: 1px solid #334155;
        padding: 8px 10px;
        text-align: left;
    }
    .custom-table th {
        color: #94a3b8;
        font-weight: 600;
    }

    /* --- REGRAS ESPECÍFICAS PARA A IMPRESSORA --- */
    @media print {
        @page {
            size: landscape;
            margin: 10mm;
        }
        
        /* Esconde menus e botões */
        header, footer, [data-testid="stToolbar"], [data-testid="stManageApp"], button, iframe { 
            display: none !important; 
        }
        
        /* Destrava absolutamente todos os contêineres do Streamlit */
        html, body, .stApp, main, [data-testid="stAppViewContainer"], [data-testid="block-container"] {
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            overflow: visible !important;
            background-color: #FFFFFF !important;
        }
        
        /* Garante que nada fique preso em blocos */
        .element-container, [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] {
            height: auto !important;
            overflow: visible !important;
            page-break-inside: auto !important;
        }

        /* Mantém elementos como os cards lado a lado de forma segura */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            page-break-inside: avoid !important;
            margin-bottom: 10px !important;
        }

        /* Cores em preto puro para contraste */
        p, h1, h2, h3, h4, h5, h6, span, label { color: #000000 !important; }
        
        /* Estiliza os cards para impressão (branco com borda preta) */
        .print-card {
            background-color: #FFFFFF !important; 
            border: 1px solid #000000 !important;
            box-shadow: none !important;
        }
        .print-card p, .print-card h2 { color: #000000 !important; }

        /* Ajusta o título para nunca se separar da tabela */
        h3 {
            page-break-after: avoid !important;
            margin-top: 15px !important;
            margin-bottom: 5px !important;
            padding: 0 !important;
        }

        hr {
            margin: 10px 0 !important;
            border-top: 1px solid #ccc !important;
        }

        /* MÁGICA DA TABELA HTML: Imprime perfeitamente e quebra nas linhas certas */
        .custom-table table, .custom-table th, .custom-table td {
            color: #000000 !important;
            border-bottom: 1px solid #999999 !important;
            font-size: 11px !important;
        }
        table { 
            page-break-inside: auto !important; 
        }
        tr { 
            page-break-inside: avoid !important; 
            page-break-after: auto !important; 
        }
        thead { display: table-header-group !important; }
        tfoot { display: table-footer-group !important; }

        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

URL_API_DESPESAS = "https://script.google.com/macros/s/AKfycbwbOdR--mh46XzwbUId8P4OsxQ8-T8ItbE4JwErh10qwMLWWt1S1vYUIFkK1mnzkxArYw/exec"

USUARIOS_DB = {
    "administrador@molicenter.com.br": {"senha": "moli0000", "perfil": "admin", "loja_fixa": None},
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
# 2. TELA DE LOGIN (PADRONIZADA)
# =========================================================
if not st.session_state["logado_despesas"]:
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #2e7d32 !important; 
            color: white !important; 
            font-weight: bold;
        }
        div.stButton > button:hover {
            background-color: #1b5e20 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1.5, 1])
    
    with col_centro:
        with st.container(border=True):
            col_titulo, col_logo = st.columns([3, 1])
            
            with col_titulo:
                st.markdown("<h1 style='margin:0; font-size: 24px;'>Despesas Complementares</h1>", unsafe_allow_html=True)
                st.markdown("<p style='color:#64748b; margin:0;'>Molicenter</p>", unsafe_allow_html=True)
            
            with col_logo:
                if os.path.exists("passaro_logo.png"):
                    st.image("passaro_logo.png", width=60)
            
            st.divider()
            
            lista_usuarios = ["Selecione..."] + list(USUARIOS_DB.keys())
            user_input = st.selectbox("👤 Usuário de acesso:", lista_usuarios)
            pass_input = st.text_input("🔑 Senha de acesso:", type="password", placeholder="••••••••", autocomplete="current-password")
            
            if st.button("Entrar no Sistema", use_container_width=True):
                if user_input != "Selecione...":
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
                    st.warning("Selecione um usuário.")
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

# CABEÇALHO SUPERIOR
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
        df_aprovados = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Aprovado'].copy()
        df_reprovados = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Reprovado'].copy()
            
        col1, col2, col3, col4 = st.columns(4)
        
        def card_metrica(coluna, titulo, qtd, valor, cor_valor):
            coluna.markdown(f"""
            <div class='print-card' style='background-color:#1e293b; padding:15px; border-radius:8px; border:1px solid #334155; text-align:center;'>
                <p style='margin:0; font-size:12px; color:#cbd5e1;'>{titulo}</p>
                <h2 style='margin:0; color:#ffffff;'>{qtd}</h2>
                <p style='margin:0; font-size:14px; color:{cor_valor}; font-weight:bold;'>R$ {valor:,.2f}</p>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

        card_metrica(col1, "Pendentes", len(df_pendentes), df_pendentes['Valor'].sum(), "#fbbf24")
        card_metrica(col2, "Aprovados", len(df_aprovados), df_aprovados['Valor'].sum(), "#10b981")
        card_metrica(col3, "Reprovados", len(df_reprovados), df_reprovados['Valor'].sum(), "#ef4444")
        card_metrica(col4, "Total Geral", len(df_exibicao), df_exibicao['Valor'].sum(), "#38bdf8")

        # --- AVALIAÇÃO EM LOTE ---
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin-top:0;'>⏳ Avaliação em Lote (Lançamentos Pendentes)</h3>", unsafe_allow_html=True)
                
        if df_pendentes.empty:
            st.info("✨ Maravilha! Não há despesas pendentes de aprovação no momento.")
        else:
            st.markdown("<span style='font-size:14px; color:#cbd5e1;'>Dê <b>dois cliques</b> na coluna <b>Avaliação 📝</b> para alterar o status. Ao finalizar suas escolhas, clique no botão vermelho de salvar no final da página.</span>", unsafe_allow_html=True)
            
            df_pendentes.insert(0, 'Avaliação 📝', 'Pendente')
            df_edicao = df_pendentes.drop(columns=['Autorização Supervisor'])
            
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
            
            if st.button("💾 Salvar Alterações no Sistema", type="primary"):
                mudancas = edited_df[edited_df['Avaliação 📝'] != 'Pendente']
                
                if mudancas.empty:
                    st.warning("⚠️ Nenhuma avaliação foi alterada. Mude o status para 'Aprovado' ou 'Reprovado' na tabela antes de salvar.")
                else:
                    with st.spinner(f"⏳ Processando e salvando {len(mudancas)} avaliações de uma vez..."):
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
                            requests.post(URL_API_DESPESAS, json=payload, timeout=20)
                            sucesso_geral = True
                        except Exception as e:
                            st.error(f"Erro de conexão ao salvar: {e}")
                        
                        if sucesso_geral:
                            st.success("✅ Avaliações salvas com sucesso!")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()

        # =========================================================
        # TABELA CONSOLIDADA E HISTÓRICO - INJEÇÃO HTML DIRETA
        # =========================================================
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("<h3>📚 Despesas Complementares dessa semana</h3>", unsafe_allow_html=True)

        if df_historico.empty:
            st.info("Nenhuma despesa foi avaliada ainda.")
        else:
            df_historico = df_historico.sort_values(
                by=['Loja', 'Carimbo de Data/Hora'], ascending=[True, False]
            ).reset_index(drop=True)

            df_view = df_historico.copy()
            df_view['Valor'] = df_view['Valor'].apply(
                lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

            df_tela = df_view.copy()
            if 'Carimbo de Data/Hora' in df_tela.columns:
                df_tela = df_tela.drop(columns=['Carimbo de Data/Hora'])

            df_tela.rename(columns={'Autorização Supervisor': 'Status'}, inplace=True)

            def highlight_status(val):
                if val == 'Aprovado':
                    return 'color: #10b981; font-weight: bold;'
                elif val == 'Reprovado':
                    return 'color: #ef4444; font-weight: bold;'
                return ''

            # BURLANDO O STREAMLIT: Geramos o HTML direto do Pandas e injetamos
            try:
                html_tabela = df_tela.style.map(highlight_status, subset=['Status']).hide(axis="index").to_html()
            except:
                html_tabela = df_tela.style.map(highlight_status, subset=['Status']).hide_index().to_html()
            
            st.markdown(f'<div class="custom-table">{html_tabela}</div>', unsafe_allow_html=True)

        # =========================================================
        # BLOCO DE ASSINATURAS NO RODAPÉ E RESUMO POR LOJA
        # =========================================================
        
        col_sig1, col_space, col_sig2 = st.columns([0.7, 2.5, 0.7])
        
        # --- ASSINATURA ESQUERDA (LUCIANA) ---
        with col_sig1:
            if os.path.exists("Luciana.png"):
                st.image("Luciana.png", use_container_width=True)
            else:
                st.markdown("<br>", unsafe_allow_html=True)

        # --- MEIO: RESUMO POR LOJA ---
        with col_space:
            st.markdown("<h4 style='text-align: center; margin-top: 0;'>🏪 Resumo de Aprovados por Loja</h4>", unsafe_allow_html=True)
            
            if not df_aprovados.empty:
                resumo_lojas = df_aprovados.groupby('Loja').agg(
                    Qtde=('Valor', 'count'),
                    Total_RS=('Valor', 'sum')
                ).reset_index()
                
                resumo_lojas['Total_RS'] = resumo_lojas['Total_RS'].apply(lambda x: f"R$ {x:,.2f}")
                resumo_lojas.rename(columns={'Loja': 'Loja', 'Qtde': 'Qtde', 'Total_RS': 'R$'}, inplace=True)
                
                _, col_tabela_centro, _ = st.columns([1, 2, 1])
                
                with col_tabela_centro:
                    # Injetando o resumo como HTML puro também
                    try:
                        html_resumo = resumo_lojas.style.hide(axis="index").to_html()
                    except:
                        html_resumo = resumo_lojas.style.hide_index().to_html()
                        
                    st.markdown(f'<div class="custom-table">{html_resumo}</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhuma despesa aprovada até o momento.")

        # --- ASSINATURA DIREITA (ADRIANO) ---
        with col_sig2:
            if os.path.exists("Adriano.png"):
                st.image("Adriano.png", use_container_width=True)
            else:
                st.markdown("<br>", unsafe_allow_html=True)


        # =========================================================
        # BOTÕES DE EXPORTAR, IMPRIMIR E LIMPAR
        # =========================================================
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        
        col_export, col_print, col_clear = st.columns([1, 1, 1])

        # --- 1. Botão Exportar Excel ---
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_view.to_excel(writer, index=False, sheet_name='Histórico')

        with col_export:
            st.download_button(
                label="📊 Exportar Histórico (Excel)",
                data=buffer.getvalue(),
                file_name=f"historico_despesas_{datetime.now().strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

        # --- 2. Botão Imprimir Tela ---
        with col_print:
            components.html(
                """
                <button onclick="window.parent.print()" 
                    style="width: 100%; background-color: #475569; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-family: sans-serif; font-weight: 600; font-size: 15px; box-sizing: border-box;">
                    🖨️ Imprimir Tela
                </button>
                """,
                height=45
            )

        # --- 3. Botão Limpar Registros (somente admin) ---
        if perfil == "admin":
            @st.dialog("⚠️ Confirmar Limpeza de Registros")
            def dialog_limpar():
                st.warning(
                    "Esta ação irá **apagar TODOS os registros** da planilha de forma permanente, "
                    "preparando o sistema para uma nova semana.\n\n"
                    "**Esta operação não pode ser desfeita.**"
                )
                st.markdown("<br>", unsafe_allow_html=True)
                col_sim, col_nao = st.columns(2)

                with col_sim:
                    if st.button("✅ Sim, limpar tudo", type="primary", use_container_width=True):
                        with st.spinner("🗑️ Limpando todos os registros..."):
                            payload_clear = {"action": "clear_all"}
                            sucesso_clear = False
                            try:
                                requests.post(URL_API_DESPESAS, json=payload_clear, timeout=20)
                                sucesso_clear = True
                            except Exception as e:
                                st.error(f"Erro ao limpar: {e}")

                        if sucesso_clear:
                            st.success("✅ Todos os registros foram removidos!")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()

                with col_nao:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.rerun()

            with col_clear:
                if st.button("🗑️ Limpar Nova Semana", use_container_width=True):
                    dialog_limpar()
