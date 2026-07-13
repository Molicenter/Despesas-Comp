import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import io
import os
import streamlit.components.v1 as components
from supabase import create_client, Client

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS E CSS
# =========================================================
st.set_page_config(
    page_title="Despesas Complementares - Molicenter",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONEXÃO SUPABASE ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🚨 Credenciais do Supabase não encontradas no secrets.toml!")
    st.stop()

st.markdown("""
    <style>
    [data-testid="collapsedControl"] {display: none;}
    
    /* Oculta as tabelas espelho no ecrã normal (só aparecem na impressão) */
    .print-only-table { display: none; }
    
    /* ESTILOS DA NOSSA NOVA TABELA NATIVA (Para o Ecrã) */
    .custom-table table {
        width: 100%;
        border-collapse: collapse;
        color: #22303C;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .custom-table th, .custom-table td {
        border-bottom: 1px solid #D5E0EA;
        padding: 8px 10px;
        text-align: left;
    }
    .custom-table th {
        color: #0B3D63;
        font-weight: 600;
    }

    /* ESTILOS DA TABELA DE RESUMO (Centro e Menos Larga) */
    .resumo-table table {
        width: 85%;
        margin: 0 auto; /* Centraliza a tabela no container */
        border-collapse: collapse;
        color: #22303C;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .resumo-table th, .resumo-table td {
        border-bottom: 1px solid #D5E0EA;
        padding: 8px 10px;
        text-align: center !important; /* Centraliza os textos */
    }
    .resumo-table th {
        color: #0B3D63;
        font-weight: 600;
    }

    /* ======================================================= */
    /* --- REGRAS ESPECÍFICAS PARA A IMPRESSORA --- */
    /* ======================================================= */
    @media print {
        @page { size: A4 landscape; margin: 8mm; }

        /* 1. CORRECAO PRINCIPAL: forca os containers do Streamlit a caber na folha.
              Sem isto, o app mantem a largura do monitor e o navegador CORTA
              tudo o que passa da margem direita (cards, colunas e assinaturas). */
        html, body, #root, .stApp, main,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="block-container"],
        .block-container {
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            height: auto !important;
            overflow: visible !important;
            background-color: #FFFFFF !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* 2. Esconde o que nao faz sentido no papel */
        button, iframe, header, footer, [data-testid="stToolbar"], [data-testid="stManageApp"],
        [data-testid="stDataEditor"], [data-testid="stDataFrame"], [data-testid="stTable"], .no-print {
            display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; position: absolute !important;
        }
        .element-container:has([data-testid="stDataEditor"]), .element-container:has([data-testid="stDataFrame"]),
        .element-container:has([data-testid="stTable"]), .element-container:has([data-testid="stButton"]),
        .element-container:has([data-testid="stDownloadButton"]), .element-container:has(iframe), .element-container:has(.no-print) {
            display: none !important; position: absolute !important; height: 0 !important; width: 0 !important; margin: 0 !important; padding: 0 !important;
        }

        /* 3. Blocos e colunas nunca podem estourar a largura da folha */
        [data-testid="stVerticalBlock"] {
            display: block !important; width: 100% !important; max-width: 100% !important;
            gap: 0 !important; padding: 0 !important; margin: 0 !important;
        }
        .element-container {
            display: block !important; position: relative !important;
            width: 100% !important; max-width: 100% !important;
            margin-bottom: 6px !important; padding: 0 !important;
        }
        [data-testid="stHorizontalBlock"] {
            display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
            width: 100% !important; max-width: 100% !important;
            align-items: stretch !important; gap: 8px !important;
            margin-top: 8px !important; margin-bottom: 12px !important;
            page-break-inside: avoid !important;
        }
        [data-testid="column"] {
            display: block !important;
            min-width: 0 !important;
            max-width: 100% !important;
            overflow: hidden !important;
            padding: 0 !important;
        }

        /* 3b. CINTO DE SEGURANCA: o Streamlit grava larguras em PIXELS inline
              nos elementos (ex.: style="width: 1583px", medido no monitor).
              Estilo inline vence a folha de estilo, entao capamos TUDO com
              max-width para nada passar da largura da folha. */
        [data-testid="stAppViewContainer"] div,
        [data-testid="stAppViewContainer"] table {
            max-width: 100% !important;
            min-width: 0 !important;
        }
        [data-testid="stMarkdown"], [data-testid="stMarkdownContainer"],
        .stMarkdown, .stMarkdownContainer, .stElementContainer {
            width: 100% !important; max-width: 100% !important;
        }

        /* 4. Titulos e separadores: some com as linhas atravessando os titulos */
        h1, h2, h3, h4, h5 { color: #000000 !important; margin: 14px 0 6px 0 !important; padding: 0 !important; page-break-after: avoid !important; line-height: 1.3 !important; }
        h2 { font-size: 18px !important; } h3 { font-size: 15px !important; } h4 { font-size: 13px !important; }
        hr { display: none !important; }
        /* Avisos de tela (st.info / st.success) nao saem no papel */
        [data-testid="stAlert"],
        .element-container:has([data-testid="stAlert"]) {
            display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; position: absolute !important;
        }

        /* 5. Cards de metrica (os 4 agora cabem na largura) */
        .print-card {
            background: #FFFFFF !important; border: 1px solid #000000 !important; box-shadow: none !important;
            margin: 0 !important; padding: 5px !important;
            box-sizing: border-box !important; width: 100% !important;
        }
        .print-card * { color: #000000 !important; margin: 0 !important; line-height: 1.2 !important; }
        .print-card h3 { font-size: 16px !important; margin: 3px 0 !important; }
        .print-card p { font-size: 11px !important; font-weight: bold; }

        /* 6. TABELAS: largura travada em 100% e quebra de linha nas observacoes */
        .print-only-table { display: block !important; margin-bottom: 8px !important; }
        .custom-table, .resumo-table { width: 100% !important; max-width: 100% !important; overflow: visible !important; }
        .custom-table table {
            table-layout: fixed !important;   /* trava a tabela na largura da folha */
            width: 100% !important; max-width: 100% !important;
            border-collapse: collapse !important; margin-bottom: 5px !important;
        }
        .custom-table th, .custom-table td {
            color: #000000 !important; background-color: #FFFFFF !important;
            border-bottom: 1px solid #999999 !important;
            font-size: 9.5px !important; padding: 3px 4px !important; line-height: 1.25 !important;
            white-space: normal !important; word-break: break-word !important; overflow-wrap: anywhere !important;
            vertical-align: top !important;
        }
        .custom-table th { font-weight: bold !important; border-bottom: 1.5px solid #000000 !important; }

        /* Larguras por coluna da tabela de historico:
           Loja | Nome | Motivo | Observacoes | Departamento | Data | Valor | Status */
        .hist-table table th:nth-child(1), .hist-table table td:nth-child(1) { width:  4% !important; }
        .hist-table table th:nth-child(2), .hist-table table td:nth-child(2) { width: 14% !important; }
        .hist-table table th:nth-child(3), .hist-table table td:nth-child(3) { width: 11% !important; }
        .hist-table table th:nth-child(4), .hist-table table td:nth-child(4) { width: 33% !important; }
        .hist-table table th:nth-child(5), .hist-table table td:nth-child(5) { width: 11% !important; }
        .hist-table table th:nth-child(6), .hist-table table td:nth-child(6) { width:  9% !important; text-align: center !important; }
        .hist-table table th:nth-child(7), .hist-table table td:nth-child(7) { width:  8% !important; text-align: right !important; }
        .hist-table table th:nth-child(8), .hist-table table td:nth-child(8) { width: 10% !important; text-align: center !important; }
        .resumo-table table {
            table-layout: fixed !important;
            width: 100% !important; max-width: 100% !important;
            margin: 0 auto 5px auto !important; border-collapse: collapse !important;
        }
        .resumo-table th, .resumo-table td {
            color: #000000 !important; background-color: #FFFFFF !important;
            border-bottom: 1px solid #999999 !important;
            font-size: 10px !important; padding: 4px 5px !important; text-align: center !important;
        }
        .resumo-table th { font-weight: bold !important; border-bottom: 1.5px solid #000000 !important; }

        /* 7. Quebras de pagina inteligentes */
        table { page-break-inside: auto !important; }
        tr { page-break-inside: avoid !important; page-break-after: auto !important; }
        thead { display: table-header-group !important; }

        /* 8. Assinaturas: as DUAS aparecem, lado a lado */
        /* 8a. O bloco final (assinaturas + resumo por loja) nunca se parte no
              meio: se couber no espaco que sobrou da tabela, imprime ali;
              se nao couber, desce INTEIRO para a pagina seguinte. */
        [data-testid="stHorizontalBlock"]:has(.resumo-table) {
            page-break-inside: avoid !important;
            break-inside: avoid-page !important;
            margin-top: 6mm !important;
            align-items: flex-start !important;
        }
        [data-testid="stHorizontalBlock"]:has(.resumo-table) [data-testid="stImage"] {
            margin-top: 18mm !important;   /* desce as assinaturas para a altura da tabela */
        }
        .resumo-table { margin-top: 4mm !important; }

        [data-testid="stImage"] { display: block !important; height: auto !important; margin: 0 !important; padding: 0 !important; }
        [data-testid="stImage"] img { max-height: 70px !important; max-width: 100% !important; width: auto !important; margin: 0 auto !important; display: block !important; position: relative !important; }

        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
    }
    </style>
""", unsafe_allow_html=True)

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
        div.stButton > button,
        [data-testid="stFormSubmitButton"] button {
            background-color: #2e7d32 !important; color: white !important; font-weight: bold;
        }
        div.stButton > button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
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
                st.markdown(
                    "<h1 style='margin:0; font-size: 24px;'>Despesas Complementares</h1>", unsafe_allow_html=True)
                st.markdown(
                    "<p style='color:#64748b; margin:0;'>Molicenter</p>", unsafe_allow_html=True)

            with col_logo:
                if os.path.exists("passaro_logo.png"):
                    st.image("passaro_logo.png", width=60)

            st.divider()

            lista_usuarios = ["Selecione..."] + list(USUARIOS_DB.keys())

            with st.form("form_login", clear_on_submit=False):
                user_input = st.selectbox(
                    "👤 Usuário de acesso:", lista_usuarios)
                pass_input = st.text_input(
                    "🔑 Senha de acesso:", type="password", placeholder="••••••••", autocomplete="off")
                entrar = st.form_submit_button(
                    "Entrar no Sistema", use_container_width=True)

            if entrar:
                if user_input != "Selecione...":
                    user_clean = user_input.strip().lower()
                    if user_clean in USUARIOS_DB and USUARIOS_DB[user_clean]["senha"] == pass_input.strip():
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
# 3. FUNÇÕES DE DADOS (SUPABASE) E CABEÇALHO SUPERIOR
# =========================================================


def formata_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor


@st.cache_data(ttl=5)
def carregar_dados():
    try:
        response = supabase.table("despesas_comp").select("*").execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            # Renomear as colunas do banco para os nomes usados no painel
            renames = {
                "created_at": "Carimbo de Data/Hora",
                "loja": "Loja",
                "nome_completo": "Nome Completo",
                "motivo": "Motivo",
                "observacoes": "Observações",
                "departamento": "Departamento",
                "data_trabalhada": "Data Trabalhada",
                "valor": "Valor",
                "autorizacao_supervisor": "Autorização Supervisor"
            }
            df.rename(columns=renames, inplace=True)

            if 'Data Trabalhada' in df.columns:
                df['Data Trabalhada'] = pd.to_datetime(
                    df['Data Trabalhada'], errors='coerce').dt.strftime('%d/%m/%Y')
                df['Data Trabalhada'] = df['Data Trabalhada'].fillna("-")

            if 'Carimbo de Data/Hora' in df.columns:
                dt_series = pd.to_datetime(
                    df['Carimbo de Data/Hora'], errors='coerce')
                # Ajusta para fuso do Brasil
                dt_series = dt_series - pd.Timedelta(hours=3)
                df['Carimbo de Data/Hora'] = dt_series.dt.strftime(
                    '%d/%m/%Y %H:%M')
                df['Carimbo de Data/Hora'] = df['Carimbo de Data/Hora'].fillna(
                    "-")

        return df
    except Exception as e:
        st.error(f"Erro ao conectar com o Supabase: {e}")
        return pd.DataFrame()


df_base = carregar_dados()

perfil = st.session_state["perfil"]
loja_fixa = st.session_state["loja_fixa"]

# CABEÇALHO SUPERIOR
col_title, col_info, col_btn = st.columns([0.65, 0.25, 0.1])
with col_title:
    st.markdown("<h2 style='margin:0; padding:0;'>💸 Despesas Complementares</h2>",
                unsafe_allow_html=True)
with col_info:
    st.markdown(
        f"<div style='text-align: right; margin-top: 5px; color: #22303C; font-size: 14px;'><b>Usuário:</b> {st.session_state['usuario']}<br><b>Nível:</b> {perfil.upper()}</div>", unsafe_allow_html=True)
with col_btn:
    st.markdown("<div style='margin-top: 5px;' class='no-print'>",
                unsafe_allow_html=True)
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px;'>",
            unsafe_allow_html=True)

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
            valor = st.number_input(
                "Valor (R$) *", min_value=0.0, step=10.0, format="%.2f", value=None)
            obs = st.text_area(
                "Observações", placeholder="Justificativa ou transferência...")

        submit = st.form_submit_button(
            "💾 Registrar Despesas", type="primary", use_container_width=True)

        if submit:
            if not nome.strip():
                st.error("⚠️ O campo Nome é obrigatório.")
            elif valor is None or valor <= 0:
                st.error(
                    "⚠️ O campo Valor deve ser preenchido com um valor maior que zero.")
            else:
                with st.spinner("⏳ Enviando dados para o banco..."):
                    # PREPARA OS DADOS PARA O SUPABASE
                    payload = {
                        "loja": str(loja_fixa),
                        "nome_completo": nome.upper().strip(),
                        "motivo": motivo,
                        "observacoes": obs.strip() if obs else "-",
                        "departamento": depto,
                        # Supabase pede data assim YYYY-MM-DD
                        "data_trabalhada": data_trab.strftime("%Y-%m-%d"),
                        "valor": float(valor),
                        "autorizacao_supervisor": "Pendente"
                    }

                    try:
                        supabase.table("despesas_comp").insert(
                            payload).execute()
                        st.success("✅ Despesa registrada com sucesso!")
                        st.cache_data.clear()
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro de conexão ao salvar os dados: {e}")

    st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

    col_tabela, col_delete = st.columns([0.7, 0.3])

    with col_tabela:
        st.markdown("### 📋 Seus Registros Recentes")

    if not df_base.empty and 'Loja' in df_base.columns:
        df_loja = df_base[df_base['Loja'].astype(str) == str(loja_fixa)].copy()

        if not df_loja.empty:
            df_loja = df_loja.iloc[::-1].reset_index(drop=True)

            with col_tabela:
                # Mostrar o DataFrame ocultando a coluna 'id' do Supabase
                st.dataframe(df_loja.drop(
                    columns=['id'], errors='ignore'), use_container_width=True, hide_index=True)

                df_loja_print = df_loja.drop(
                    columns=['id'], errors='ignore').copy()
                if 'Valor' in df_loja_print.columns:
                    df_loja_print['Valor'] = df_loja_print['Valor'].apply(
                        formata_br)

                try:
                    html_loja = df_loja_print.style.hide(
                        axis="index").to_html()
                except:
                    html_loja = df_loja_print.style.hide_index().to_html()
                st.markdown(
                    f'<div class="print-only-table custom-table">{html_loja}</div>', unsafe_allow_html=True)

            with col_delete:
                with st.container(border=True):
                    st.markdown("#### 🗑️ Cancelar Lançamento")
                    st.markdown(
                        "<span style='font-size:13px; color:#475569;'>Lançou errado? Selecione abaixo e exclua.</span>", unsafe_allow_html=True)

                    # Usa um dicionário para linkar a Label visual com o 'id' real do banco
                    opcoes_delete = {}
                    for idx, row in df_loja.iterrows():
                        if row.get("Autorização Supervisor") == "Pendente":
                            data_str = str(row.get("Data Trabalhada", ""))
                            nome_str = str(row.get("Nome Completo", ""))
                            valor_str = str(row.get("Valor", 0))
                            label = f"{data_str} | {nome_str} | R$ {valor_str}"
                            opcoes_delete[label] = row['id']

                    if not opcoes_delete:
                        st.info("Não há registros pendentes para exclusão.")
                    else:
                        registro_selecionado = st.selectbox("Selecione o registro:", [
                                                            "- Selecione -"] + list(opcoes_delete.keys()), label_visibility="collapsed")

                        if st.button("Confirmar Exclusão", type="primary", use_container_width=True):
                            if registro_selecionado != "- Selecione -":
                                id_para_deletar = opcoes_delete[registro_selecionado]

                                with st.spinner("Apagando..."):
                                    try:
                                        # Deleta diretamente usando o ID
                                        supabase.table("despesas_comp").delete().eq(
                                            "id", id_para_deletar).execute()
                                        st.success(
                                            "Registro excluído com sucesso!")
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(
                                            f"Erro de conexão ao tentar excluir: {e}")
                            else:
                                st.warning(
                                    "Por favor, selecione um registro na lista.")
        else:
            with col_tabela:
                st.info("Nenhum registro encontrado para a sua loja até o momento.")
    else:
        st.info("O banco de dados ainda está vazio.")

# --- VISÃO GERENCIAL / SUPERVISOR ---
elif perfil in ["admin", "supervisor"]:
    st.success("🌐 Visão Consolidada - Painel de Aprovação")

    if df_base.empty:
        st.warning("Nenhum dado encontrado no banco de dados.")
    else:
        df_exibicao = df_base.copy()

        if 'Valor' in df_exibicao.columns:
            df_exibicao['Valor'] = pd.to_numeric(
                df_exibicao['Valor'], errors='coerce').fillna(0)

        df_pendentes = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Pendente'].copy(
        )
        df_historico = df_exibicao[df_exibicao['Autorização Supervisor'] != 'Pendente'].copy(
        )
        df_aprovados = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Aprovado'].copy(
        )
        df_reprovados = df_exibicao[df_exibicao['Autorização Supervisor'] == 'Reprovado'].copy(
        )

        col1, col2, col3, col4 = st.columns(4)

        def card_metrica(coluna, titulo, qtd, valor, cor_valor):
            coluna.markdown(f"""
            <div class='print-card' style='background-color:#0B3D63; border-radius:6px; border:1px solid #2A6693; text-align:center;'>
                <p style='margin:0; font-size:14px; color:#cbd5e1; line-height:1.2;'>{titulo}</p>
                <h3 style='margin:2px 0; color:#ffffff; line-height:1.2;'>{qtd}</h3>
                <p style='margin:0; font-size:18px; color:{cor_valor}; font-weight:bold; line-height:1.2;'>R$ {valor:,.2f}</p>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

        card_metrica(col1, "Pendentes", len(df_pendentes),
                     df_pendentes['Valor'].sum(), "#fbbf24")
        card_metrica(col2, "Aprovados", len(df_aprovados),
                     df_aprovados['Valor'].sum(), "#10b981")
        card_metrica(col3, "Reprovados", len(df_reprovados),
                     df_reprovados['Valor'].sum(), "#ef4444")
        card_metrica(col4, "Total Geral", len(df_exibicao),
                     df_exibicao['Valor'].sum(), "#38bdf8")

        # --- AVALIAÇÃO EM LOTE ---
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        st.markdown(
            "<h3 class='no-print'>⏳ Avaliação em Lote (Lançamentos Pendentes)</h3>", unsafe_allow_html=True)

        if df_pendentes.empty:
            st.info("✨ Maravilha! Não há despesas pendentes de aprovação no momento.")
        else:
            st.markdown("<span class='no-print' style='font-size:14px; color:#475569;'>Dê <b>dois cliques</b> na coluna <b>Avaliação 📝</b> para alterar o status. Ao finalizar, clique em salvar.</span>", unsafe_allow_html=True)

            if "status_lote_padrao" not in st.session_state:
                st.session_state["status_lote_padrao"] = "🟡 Pendente"

            col_all1, col_all2, col_all3, espaco_vazio = st.columns(
                [1.2, 1.2, 1.2, 6])

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

            df_pendentes.insert(
                0, 'Avaliação 📝', st.session_state["status_lote_padrao"])
            df_edicao = df_pendentes.drop(columns=['Autorização Supervisor'])

            chave_editor = f"editor_lote_{st.session_state['status_lote_padrao']}"

            edited_df = st.data_editor(
                df_edicao,
                key=chave_editor,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": None,  # Oculta a coluna ID do banco
                    "Avaliação 📝": st.column_config.SelectboxColumn(
                        "Avaliação 📝",
                        help="Clique duas vezes para aprovar ou reprovar",
                        width="medium",
                        options=["🟡 Pendente", "🟢 Aprovado", "🔴 Reprovado"],
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

            # --- TABELA FANTASMA PARA IMPRESSÃO (Pendentes) ---
            df_edicao_print = df_edicao.drop(
                columns=['id'], errors='ignore').copy()
            if 'Valor' in df_edicao_print.columns:
                df_edicao_print['Valor'] = df_edicao_print['Valor'].apply(
                    formata_br)

            try:
                html_pendentes = df_edicao_print.style.hide(
                    axis="index").to_html()
            except:
                html_pendentes = df_edicao_print.style.hide_index().to_html()
            st.markdown(
                f'<div class="print-only-table custom-table">{html_pendentes}</div>', unsafe_allow_html=True)

            if st.button("💾 Salvar Alterações no Sistema", type="primary"):
                mudancas = edited_df[edited_df['Avaliação 📝'] != '🟡 Pendente']

                if mudancas.empty:
                    st.warning(
                        "⚠️ Nenhuma avaliação foi alterada. Mude o status na tabela antes de salvar.")
                else:
                    with st.spinner(f"⏳ Processando e salvando {len(mudancas)} avaliações..."):
                        sucesso_geral = True
                        for idx, row in mudancas.iterrows():
                            status_selecionado = row['Avaliação 📝']
                            if "Aprovado" in status_selecionado:
                                status_limpo = "Aprovado"
                            elif "Reprovado" in status_selecionado:
                                status_limpo = "Reprovado"
                            else:
                                status_limpo = "Pendente"

                            try:
                                # Usa o ID da linha para atualizar apenas aquele registro exato
                                supabase.table("despesas_comp").update(
                                    {"autorizacao_supervisor": status_limpo}).eq("id", row['id']).execute()
                            except Exception as e:
                                st.error(
                                    f"Erro ao atualizar ID {row['id']}: {e}")
                                sucesso_geral = False

                        if sucesso_geral:
                            st.success("✅ Avaliações salvas com sucesso!")
                            st.cache_data.clear()
                            st.session_state["status_lote_padrao"] = "🟡 Pendente"
                            time.sleep(1.5)
                            st.rerun()

        # =========================================================
        # TABELA CONSOLIDADA E HISTÓRICO - INJEÇÃO HTML DIRETA
        # =========================================================
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        st.markdown("<h3>📚 Despesas Complementares dessa semana</h3>",
                    unsafe_allow_html=True)

        if df_historico.empty:
            st.info("Nenhuma despesa foi avaliada ainda.")
        else:
            df_historico = df_historico.sort_values(
                by=['Loja', 'Carimbo de Data/Hora'], ascending=[True, False]
            ).reset_index(drop=True)

            df_view = df_historico.copy()
            df_view['Valor'] = df_view['Valor'].apply(formata_br)

            df_tela = df_view.drop(columns=['id'], errors='ignore').copy()
            if 'Carimbo de Data/Hora' in df_tela.columns:
                df_tela = df_tela.drop(columns=['Carimbo de Data/Hora'])

            df_tela.rename(
                columns={'Autorização Supervisor': 'Status'}, inplace=True)

            def highlight_status(val):
                if val == 'Aprovado':
                    return 'color: #10b981; font-weight: bold;'
                elif val == 'Reprovado':
                    return 'color: #ef4444; font-weight: bold;'
                return ''

            try:
                html_tabela = df_tela.style.map(highlight_status, subset=[
                                                'Status']).hide(axis="index").to_html()
            except:
                html_tabela = df_tela.style.map(highlight_status, subset=[
                                                'Status']).hide_index().to_html()

            st.markdown(
                f'<div class="custom-table hist-table">{html_tabela}</div>', unsafe_allow_html=True)

        # =========================================================
        # BLOCO DE ASSINATURAS NO RODAPÉ E RESUMO POR LOJA
        # =========================================================

        col_sig1, col_space, col_sig2 = st.columns([0.7, 2.5, 0.7])

        # --- ASSINATURA ESQUERDA (LUCIANA) ---
        with col_sig1:
            if os.path.exists("Luciana.png"):
                st.image("Luciana.png", use_container_width=True)

        # --- MEIO: RESUMO POR LOJA ---
        with col_space:
            st.markdown(
                "<h4 style='text-align: center; margin-top: 0;'>🏪 Resumo de Aprovados por Loja</h4>", unsafe_allow_html=True)

            if not df_aprovados.empty:
                resumo_total = df_aprovados.groupby('Loja').agg(
                    Qtde_Total=('Valor', 'count'),
                    Total_RS=('Valor', 'sum')
                ).reset_index()

                df_apenas_despesas = df_aprovados[df_aprovados['Motivo'].astype(
                    str).str.strip() == 'Despesas (Justificar)']
                resumo_despesas = df_apenas_despesas.groupby('Loja').agg(
                    Qtde_Desp=('Valor', 'count'),
                    Desp_RS=('Valor', 'sum')
                ).reset_index()

                resumo_lojas = pd.merge(
                    resumo_total, resumo_despesas, on='Loja', how='left')

                resumo_lojas['Qtde_Desp'] = resumo_lojas['Qtde_Desp'].fillna(
                    0).astype(int)
                resumo_lojas['Desp_RS'] = resumo_lojas['Desp_RS'].fillna(0.0)

                resumo_lojas['Diarias_RS'] = resumo_lojas['Total_RS'] - \
                    resumo_lojas['Desp_RS']

                total_qtde_desp = int(resumo_lojas['Qtde_Desp'].sum())
                total_desp_rs = resumo_lojas['Desp_RS'].sum()
                total_qtde_total = int(resumo_lojas['Qtde_Total'].sum())
                total_total_rs = resumo_lojas['Total_RS'].sum()
                total_diarias_rs = resumo_lojas['Diarias_RS'].sum()

                linha_total = pd.DataFrame({
                    'Loja': ['TOTAL'],
                    'Qtde_Total': [total_qtde_total],
                    'Total_RS': [total_total_rs],
                    'Qtde_Desp': [total_qtde_desp],
                    'Desp_RS': [total_desp_rs],
                    'Diarias_RS': [total_diarias_rs]
                })

                resumo_lojas = pd.concat(
                    [resumo_lojas, linha_total], ignore_index=True)

                resumo_lojas['Desp_RS'] = resumo_lojas['Desp_RS'].apply(
                    formata_br)
                resumo_lojas['Diarias_RS'] = resumo_lojas['Diarias_RS'].apply(
                    formata_br)
                resumo_lojas['Total_RS'] = resumo_lojas['Total_RS'].apply(
                    formata_br)

                resumo_lojas.rename(columns={
                    'Qtde_Desp': 'Qtde (Despesas)',
                    'Qtde_Total': 'Qtde (Total)',
                    'Desp_RS': 'R$ Despesas',
                    'Diarias_RS': 'R$ Diárias',
                    'Total_RS': 'R$ Total'
                }, inplace=True)

                resumo_lojas = resumo_lojas[[
                    'Loja', 'Qtde (Despesas)', 'Qtde (Total)', 'R$ Despesas', 'R$ Diárias', 'R$ Total']]

                def formata_linha_total(row):
                    if row['Loja'] == 'TOTAL':
                        return ['font-weight: bold; background-color: #0B3D63; color: #ffffff;'] * len(row)
                    return [''] * len(row)

                try:
                    html_resumo = resumo_lojas.style.apply(
                        formata_linha_total, axis=1).hide(axis="index").to_html()
                except:
                    html_resumo = resumo_lojas.style.apply(
                        formata_linha_total, axis=1).hide_index().to_html()

                st.markdown(
                    f'<div class="resumo-table">{html_resumo}</div>', unsafe_allow_html=True)
            else:
                st.info("Nenhuma despesa aprovada até o momento.")

        # --- ASSINATURA DIREITA (ADRIANO) ---
        with col_sig2:
            if os.path.exists("Adriano.png"):
                st.image("Adriano.png", use_container_width=True)

        # =========================================================
        # BOTÕES DE EXPORTAR, IMPRIMIR E LIMPAR
        # =========================================================
        st.markdown("<hr class='no-print custom-hr'>", unsafe_allow_html=True)

        col_export, col_print, col_clear = st.columns([1, 1, 1])

        # --- 1. Botão Exportar Excel ---
        with col_export:
            if 'df_view' in locals() and not df_view.empty:
                # Remove o ID na hora de exportar para o Excel
                df_export = df_view.drop(
                    columns=['id'], errors='ignore').copy()
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False,
                                       sheet_name='Histórico')

                data_atual_br = datetime.now() - timedelta(hours=3)

                st.download_button(
                    label="📊 Exportar Histórico (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"historico_despesas_{data_atual_br.strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.button(
                    label="📊 Exportar Histórico (Excel)",
                    disabled=True,
                    use_container_width=True,
                    help="Não há dados no histórico para exportar."
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
                    "Esta ação irá **apagar TODOS os registros** do banco de forma permanente, "
                    "preparando o sistema para uma nova semana.\n\n"
                    "**Esta operação não pode ser desfeita.**"
                )
                col_sim, col_nao = st.columns(2)

                with col_sim:
                    if st.button("✅ Sim, limpar tudo", type="primary", use_container_width=True):
                        with st.spinner("🗑️ Limpando todos os registros..."):
                            try:
                                # Deleta todas as linhas onde o ID não seja zero (ou seja, todas)
                                supabase.table("despesas_comp").delete().neq(
                                    "id", 0).execute()
                                st.success(
                                    "✅ Todos os registros foram removidos!")
                                st.cache_data.clear()
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao limpar: {e}")

                with col_nao:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.rerun()

            with col_clear:
                if st.button("🗑️ Limpar Nova Semana", use_container_width=True):
                    dialog_limpar()
