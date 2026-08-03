# login.py
import streamlit as st

from core.logging_config import get_logger

logger = get_logger(__name__)


def login_screen(user_service):
    """
    Tela de login do aplicativo
    """
    # CSS para login moderno conforme imagem
    login_style = """
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    header {visibility: hidden;} 
    .stDeployButton {visibility: hidden;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    
    /* Container principal */
    .stApp {
        background: #2c2c2c;
    }
    
    [data-testid="stAppViewContainer"] {
        max-width: 800px;
        margin: auto;
        padding: 20px;
        background: #2c2c2c;
    }
    
    /* Estilo do cabeçalho Login */
    .login-header {
        background: #1976D2;
        color: white;
        text-align: center;
        padding: 20px;
        border-radius: 10px 10px 0 0;
        margin-bottom: 0;
        font-size: 24px;
        font-weight: 600;
    }
    
    /* Container do formulário */
    .login-container {
        background: #3c3c3c;
        padding: 30px;
        border-radius: 0 0 10px 10px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
    
    /* Labels */
    .stTextInput > label {
        color: #e0e0e0 !important;
        font-weight: 500 !important;
        margin-bottom: 8px !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #4a4a4a !important;
        color: white !important;
        border: 1px solid #555 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #aaa !important;
    }
    
    /* Botão Entrar */
    .stButton > button {
        background: #1976D2 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 0 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        width: 100% !important;
        margin-top: 20px !important;
    }
    
    .stButton > button:hover {
        background: #1565C0 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4) !important;
    }
    </style>
    """

    # Aplicar o CSS
    st.markdown(login_style, unsafe_allow_html=True)

    # Header do login
    st.markdown(
        """
    <div class="login-header">
        Login
    </div>
    <div class="login-container">
    """,
        unsafe_allow_html=True,
    )

    # Usar form para capturar Enter
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Usuário", placeholder="Digite seu usuário", key="login_username"
        )
        password = st.text_input(
            "Senha",
            type="password",
            placeholder="Digite sua senha",
            key="login_password",
        )

        # Submit button - será ativado ao pressionar Enter
        login_submitted = st.form_submit_button("🔐 Entrar", use_container_width=True)

    # Fechar container
    st.markdown("</div>", unsafe_allow_html=True)

    # Processar login fora do form para evitar problemas de estado
    if login_submitted:
        if username and password:
            # Captura as permissões ao validar o usuário
            try:
                is_valid, permissions = user_service.validate_user(username, password)
            except Exception as e:
                logger.error(
                    f"Falha ao validar usuário '{username}': {e}", exc_info=True
                )
                st.error(
                    "⚠ Não foi possível conectar ao banco de dados no momento. "
                    "Tente novamente em instantes."
                )
                return
            if is_valid:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.permissions = (
                    permissions  # Armazenar permissões na sessão
                )
                st.success("Login bem-sucedido!")
                st.rerun()  # Recarrega a página para atualizar o estado
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.error("Por favor, preencha todos os campos.")
