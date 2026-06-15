import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import time
import io
import os
import streamlit.components.v1 as components

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS E CSS
# =========================================================
st.set_page_config(
    page_title="Despesas Complementares - Molicenter", 
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    
    /* Oculta as tabelas espelho no ecrã normal (só aparecem na impressão) */
    .print-only-table { display: none; }
    
    /* ESTILOS DA NOSSA NOVA TABELA NATIVA (Para o Ecrã) */
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

    /* ESTILOS DA TABELA DE RESUMO (Centro e Menos Larga) */
    .resumo-table table {
        width: 85%;
        margin: 0 auto; /* Centraliza a tabela no container */
        border-collapse: collapse;
        color: #f8fafc;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .resumo-table th, .resumo-table td {
        border-bottom: 1px solid #334155;
        padding: 8px 10px;
        text-align: center !important; /* Centraliza os textos */
    }
    .resumo-table th {
        color: #94a3b8;
        font-weight: 600;
    }

    /* ======================================================= */
    /* --- REGRAS ESPECÍFICAS PARA A IMPRESSORA (VISIBILIDADE IDEAL) --- */
    /* ======================================================= */
    @media print {
        @page {
            size: landscape;
            margin: 10mm; /* Margem segura para não cortar nas bordas da impressora */
        }

        /* 1. RESET ESTRUTURAL */
        html, body, #root, .stApp, main, 
        [data-testid="stAppViewContainer"], 
        [data-testid="block-container"] {
            display: block !important; 
            height: auto !important;
            background-color: #FFFFFF !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: visible !important;
        }

        /* Ocultação de botões e ferramentas nativas da interface */
        button, iframe, header, footer, 
        [data-testid="stToolbar"], 
        [data-testid="stManageApp"],
        [data-testid="stDataEditor"], 
        [data-testid="stDataFrame"], 
        [data-testid="stTable"],
        .no-print { 
            display: none !important; 
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            position: absolute !important;
        }

        /* 2. ZERAR ESPAÇAMENTOS FANTASMAS MAS MANTER RESPIRO */
        .element-container:has([data-testid="stDataEditor"]),
        .element-container:has([data-testid="stDataFrame"]),
        .element-container:has([data-testid="stTable"]),
        .element-container:has([data-testid="stButton"]),
        .element-container:has([data-testid="stDownloadButton"]),
        .element-container:has(iframe),
        .element-container:has(.no-print) {
            display: none !important;
            position: absolute !important;
            height: 0 !important;
            width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        [data-testid="stVerticalBlock"] {
            display: block !important;
            gap: 0 !important; 
            padding: 0 !important;
            margin: 0 !important;
        }
        
        .element-container {
            display: block !important;
            position: relative !important;
            margin-bottom: 6px !important; 
            padding: 0 !important;
        }

        /* 3. TÍTULOS E LINHAS (Legíveis) */
        h1, h2, h3, h4, h5 {
            color: #000000 !important;
            margin: 10px 0 4px 0 !important;
            padding: 0 !important;
            page-break-after: avoid !important;
            line-height: 1.2 !important;
        }
        
        h2 { font-size: 20px !important; }
        h3 { font-size: 16px !important; }
        h4 { font-size: 14px !important; }
        
        hr {
            margin: 8px 0 !important;
            border-top: 1px solid #ccc !important;
        }

        /* Caixas de Alerta (Azul/Verde) */
        [data-testid="stAlert"] {
            display: block !important;
            margin: 4px 0 8px 0 !important;
            padding: 6px 10px !important;
            min-height: 0 !important;
        }
        [data-testid="stAlert"] * {
            font-size: 12px !important;
            margin: 0 !important;
        }

        /* 4. BLOCOS LATERAIS (Assinaturas e Resumo) */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 15px !important;
            margin-top: 10px !important;
            margin-bottom: 5px !important;
            page-break-inside: avoid !important;
        }
        [data-testid="column"] {
            display: block !important;
            flex: 1 1 0% !important; 
            padding: 0 !important;
        }

        /* 5. CARTÕES DE NÚMEROS */
        .print-card {
            background: #FFFFFF !important;
            border: 1px solid #000000 !important;
            box-shadow: none !important;
            margin: 0 !important;
            padding: 6px !important;
        }
        .print-card * {
            color: #000000 !important;
            margin: 0 !important;
            line-height: 1.2 !important;
        }
        .print-card h3 { font-size: 18px !important; margin: 4px 0 !important; }
        .print-card p { font-size: 12px !important; font-weight: bold; }

        /* 6. TABELAS (Mais fáceis de ler e fundo forçado branco na impressão) */
        .print-only-table { 
            display: block !important; 
            margin-bottom: 10px !important; 
        }
        .custom-table table {
            margin-bottom: 5px !important;
            width: 100% !important;
            border-collapse: collapse !important;
        }
        .custom-table th, .custom-table td {
            color: #000000 !important;
            background-color: #FFFFFF !important; /* Força fundo branco */
            border-bottom: 1px solid #999999 !important;
            font-size: 11px !important;
            padding: 4px 6px !important;
            line-height: 1.2 !important;
        }
        .resumo-table table {
            width: 100% !important;
            margin-bottom: 5px !important;
            border-collapse: collapse !important;
        }
        .resumo-table th, .resumo-table td {
            color: #000000 !important;
            background-color: #FFFFFF !important; /* Força fundo branco */
            border-bottom: 1px solid #999999 !important;
            font-size: 11px !important;
            padding: 4px 6px !important;
            text-align: center !important;
        }
        
        table { page-break-inside: auto !important; }
        tr { page-break-inside: avoid !important; page-break-after: auto !important; }
        thead { display: table-header-group !important; }

        /* 7. IMAGENS DAS ASSINATURAS */
        [data-testid="stImage"] {
            display: block !important;
            height: auto !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        [data-testid="stImage"] img {
            max-height: 85px !important;
            max-width: 100% !important;
            width: auto !important;
            margin: 0 auto !important;
            display: block !important;
            position: relative !important;
        }

        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

URL_API_DESPESAS = "https://script.google.com/macros/s/AKfycbwbOdR--mh46XzwbUId8P4OsxQ8-T8ItbE4JwErh10qwMLWWt1S1vYUIFkK1mnzkxArYw/exec"

USUARIOS_DB = {
    "administrador": {"senha": "moli0000", "perfil": "admin", "loja_fixa": None},
    "supervisor": {"senha": "moli0000", "perfil": "supervisor", "loja_fixa": None},
    "loja01": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 1},
    "loja02": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 2},
    "loja03": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 3},
    "loja04": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 4},
    "loja05": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 5},
    "loja06": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 6},
    "loja07": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 7},
    "loja08": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 8},
    "loja30": {"senha": "moli1234", "perfil": "loja", "loja_fixa": 30},
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
    _, col_centro, _ = st.columns([1, 1, 1])
    
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
            
            pass_input = st.text_input("🔑 Senha de acesso:", type="password", placeholder="••••••••", autocomplete="off")
            
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

def formata_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

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
                dt_series = pd.to_datetime(df['Carimbo de Data/Hora'], errors='coerce')
                dt_series = dt_series - pd.Timedelta(hours=3) # Subtrai 3 horas
                
                df['Carimbo de Data/Hora'] = dt_series.dt.strftime('%d/%m/%Y %H:%M')
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
    st.markdown("<div style='margin-top: 5px;' class='no-print'>", unsafe_allow_html=True)
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

    st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
    
    col_tabela, col_delete = st.columns([0.7, 0.3])
    
    with col_tabela:
        st.markdown("### 📋 Seus Registros Recentes")
    
    if not df_base.empty and 'Loja' in df_base.columns:
        df_loja = df_base[df_base['Loja'].astype(str) == str(loja_fixa)].copy()
        
        if not df_loja.empty:
            df_loja = df_loja.iloc[::-1].reset_index(drop=True)
            
            with col_tabela:
                st.dataframe(df_loja, use_container_width=True, hide_index=True)
                
                df_loja_print = df_loja.copy()
                if 'Valor' in df_loja_print.columns:
                    df_loja_print['Valor'] = df_loja_print['Valor'].apply(formata_br)
                
                try:
                    html_loja = df_loja_print.style.hide(axis="index").to_html()
                except:
                    html_loja = df_loja_print.style.hide_index().to_html()
                st.markdown(f'<div class="print-only-table custom-table">{html_loja}</div>', unsafe_allow_html=True)
            
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
            <div class='print-card' style='background-color:#1e293b; border-radius:6px; border:1px solid #334155; text-align:center;'>
                <p style='margin:0; font-size:14px; color:#cbd5e1; line-height:1.2;'>{titulo}</p>
                <h3 style='margin:2px 0; color:#ffffff; line-height:1.2;'>{qtd}</h3>
                <p style='margin:0; font-size:18px; color:{cor_valor}; font-weight:bold; line-height:1.2;'>R$ {valor:,.2f}</p>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

        card_metrica(col1, "Pendentes", len(df_pendentes), df_pendentes['Valor'].sum(), "#fbbf24")
        card_metrica(col2, "Aprovados", len(df_aprovados), df_aprovados['Valor'].sum(), "#10b981")
        card_metrica(col3, "Reprovados", len(df_reprovados), df_reprovados['Valor'].sum(), "#ef4444")
        card_metrica(col4, "Total Geral", len(df_exibicao), df_exibicao['Valor'].sum(), "#38bdf8")

        # --- AVALIAÇÃO EM LOTE ---
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        st.markdown("<h3>⏳ Avaliação em Lote (Lançamentos Pendentes)</h3>", unsafe_allow_html=True)
                
        if df_pendentes.empty:
            st.info("✨ Maravilha! Não há despesas pendentes de aprovação no momento.")
        else:
            st.markdown("<span class='no-print' style='font-size:14px; color:#cbd5e1;'>Dê <b>dois cliques</b> na coluna <b>Avaliação 📝</b> para alterar o status. Ao finalizar, clique em salvar.</span>", unsafe_allow_html=True)
            
            if "status_lote_padrao" not in st.session_state:
                st.session_state["status_lote_padrao"] = "🟡 Pendente"
            
            col_all1, col_all2, col_all3, espaco_vazio = st.columns([1.2, 1.2, 1.2, 6])
            
            with col_all1:
                if st.button("🟢 Aprovar Todos", use_container_width=True):
                    st.session_state["status_lote_padrao"] = "🟢 Aprovado"
                    st.rerun()
            with col_all2:
                if st.button("🔴 Reprovar Todos", use_container_width=True):
                    st.session_state["status_lote_padrao"] = "🔴 Reprovado"
                    st.rerun()
            with col_all3:
                if st.button("🔄 Pendentes", use_container_width=True):
                    st.session_state["status_lote_padrao"] = "🟡 Pendente"
                    st.rerun()

            df_pendentes.insert(0, 'Avaliação 📝', st.session_state["status_lote_padrao"])
            df_edicao = df_pendentes.drop(columns
