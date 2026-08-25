# modules_improved_v1.py - Menu com Cards e Ícones
import streamlit as st

from utils.style_utils import apply_default_style


def menu():
    """Menu moderno com cards e ícones na sidebar"""
    apply_default_style()

    # CSS customizado para o menu com sidebar mínima
    st.markdown(
        """
    <style>
    /* Sidebar com largura mínima */
    .css-1d391kg {
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
    }

    /* Botões primários (selecionados) - azul */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] .stButton button[kind="primary"],
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #1E88E5 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 6px rgba(30, 136, 229, 0.4) !important;
        width: 100% !important;
    }

    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] .stButton button[kind="primary"]:hover,
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1976D2 !important;
        box-shadow: 0 3px 8px rgba(30, 136, 229, 0.5) !important;
    }

    /* TODOS OS BOTÕES SECONDARY - CINZA ESCURO (padrão para menus principais) */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] .stButton button[kind="secondary"],
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #5A5A5A !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        font-weight: 500 !important;
        width: 100% !important;
    }

    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #6A6A6A !important;
    }

    /* SUB-MENUS (Acessar) - BRANCO - Sobrescreve o cinza acima */
    [data-testid="stSidebar"] button[kind="secondary"][title*="Acessar"],
    [data-testid="stSidebar"] .stButton button[kind="secondary"][title*="Acessar"],
    section[data-testid="stSidebar"] button[kind="secondary"][title*="Acessar"] {
        background-color: #FFFFFF !important;
        color: #424242 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        width: 100% !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
        margin-left: 12px !important;
    }

    [data-testid="stSidebar"] button[kind="secondary"][title*="Acessar"]:hover,
    [data-testid="stSidebar"] .stButton button[kind="secondary"][title*="Acessar"]:hover,
    section[data-testid="stSidebar"] button[kind="secondary"][title*="Acessar"]:hover {
        background-color: #E3F2FD !important;
        color: #1976D2 !important;
        border: 1px solid #BBDEFB !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15) !important;
    }

    /* Reduzir espaço entre o botão de grupo e submenus */
    [data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(button[title*="Expandir"]) {
        margin-bottom: 0px !important;
    }

    /* Container dos submenus mais compacto */
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0px !important;
    }

    /* Remover outline/border dos botões */
    [data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] button {
        border: none !important;
        outline: none !important;
    }

    [data-testid="stSidebar"] button:focus,
    section[data-testid="stSidebar"] button:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(30, 136, 229, 0.3) !important;
    }

    /* Compactar ainda mais a sidebar */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
    <div style='text-align: center; margin-bottom: 25px; background: linear-gradient(135deg, #1E88E5 0%, #1976D2 100%); padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);'>
        <h3 style='color: white; margin: 0; font-size: 26px; font-weight: bold;'>🏢 Relatórios</h3>
        <p style='color: white; font-size: 11px; margin: 5px 0 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>
            Oficial Sport
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Definindo os módulos com nomes atualizados
    # Estrutura hierárquica: módulos principais e submódulos
    module_config = {
        "Estoque": {
            "permission": "view_produtos",
            "icon": "📦",
            "type": "group",
            "submenu": {
                "Produtos": {
                    "permission": "view_produtos",
                    "icon": "📦",
                    "original_name": "Estoque",
                },
            },
        },
        "Faturamento": {
            "permission": "view_boletos",
            "icon": "💰",
            "type": "group",
            "submenu": {
                "Boletos": {
                    "permission": "view_boletos",
                    "icon": "💰",
                    "original_name": "Cobrança",
                },
            },
        },
        "Financeiro": {
            "permission": "view_extratos",
            "icon": "💳",
            "type": "group",
            "submenu": {
                "Extratos": {
                    "permission": "view_extratos",
                    "icon": "💳",
                    "original_name": "Financeiro",
                },
            },
        },
        "Vendas": {
            "permission": [
                "view_venda",
                "change_venda",
                "view_pedido",
                "view_comparativo",
                "view_campanhas",
            ],
            "icon": "📊",
            "type": "group",
            "submenu": {
                "Comercial": {
                    "permission": "view_venda",
                    "icon": "📈",
                    "original_name": "Relatório de Vendas",
                },
                "Pedidos": {
                    "permission": "view_pedido",
                    "icon": "📋",
                    "original_name": "Relatório de Pedidos",
                },
                "Comparativo": {
                    "permission": "view_comparativo",
                    "icon": "🔄",
                    "original_name": "Relatório Comparativo",
                },
                "Campanhas": {
                    "permission": "view_campanhas",
                    "icon": "📣",
                    "original_name": "Dashboard de Campanhas",
                },
            },
        },
        "Recebimentos": {
            "permission": "view_recebimentos",
            "icon": "💰",
            "type": "group",
            "submenu": {
                "Relatório": {
                    "permission": "view_recebimentos",
                    "icon": "📅",
                    "original_name": "Relatório de Recebimentos",
                },
            },
        },
        "Entidades": {
            "permission": "view_clientes",
            "icon": "👥",
            "type": "group",
            "submenu": {
                "Clientes": {
                    "permission": "view_clientes",
                    "icon": "👥",
                    "original_name": "Relatório de Clientes",
                },
            },
        },
        "Comex": {
            "permission": "view_comex",
            "icon": "🌐",
            "type": "group",
            "submenu": {
                "Vendas": {
                    "permission": "view_comex",
                    "icon": "📦",
                    "original_name": "Comex Produtos",
                },
            },
        },
        "SAC": {
            "permission": "view_os",
            "icon": "🛠️",
            "type": "group",
            "submenu": {
                "Ordem de Serviço": {
                    "permission": "view_os",
                    "icon": "📋",
                    "original_name": "Ordem de Serviço",
                },
            },
        },
    }

    # Inicializar estado de expansão dos grupos
    if "menu_expanded_groups" not in st.session_state:
        st.session_state.menu_expanded_groups = {}

    # Renderizar módulos
    selected_module = None
    current_module = st.session_state.get("current_module", "")

    # ACCORDION: Identificar qual grupo deve estar expandido inicialmente
    # baseado no módulo selecionado atualmente (apenas na primeira vez)
    if not st.session_state.menu_expanded_groups:
        active_group = None
        for module, config in module_config.items():
            if config.get("type") == "group":
                for submodule, subconfig in config.get("submenu", {}).items():
                    if current_module == subconfig["original_name"]:
                        active_group = module
                        st.session_state.menu_expanded_groups[module] = True
                        break
            if active_group:
                break

    def _check_permission(permission, user_permissions, username):
        """Verifica permissão: aceita string única ou lista de permissões (OR)."""
        if username == "admin":
            return True
        if isinstance(permission, list):
            return any(p in user_permissions for p in permission)
        return permission in user_permissions

    for module, config in module_config.items():
        # Verificar permissão para o módulo principal
        has_permission = _check_permission(
            config["permission"],
            st.session_state.permissions,
            st.session_state.username,
        )

        if not has_permission:
            continue

        # Se é um grupo com submenu
        if config.get("type") == "group":
            # Inicializar estado de expansão para este grupo
            if module not in st.session_state.menu_expanded_groups:
                st.session_state.menu_expanded_groups[module] = False

            # Verificar se algum submódulo está selecionado
            any_submodule_selected = False
            for submodule, subconfig in config.get("submenu", {}).items():
                if current_module == subconfig["original_name"]:
                    any_submodule_selected = True
                    break

            # Botão do grupo (para expandir/recolher)
            is_expanded = st.session_state.menu_expanded_groups[module]
            expand_icon = "▼" if is_expanded else "▶"

            # Criar botão do grupo
            clicked = st.sidebar.button(
                f"{config['icon']} {module} {expand_icon}",
                key=f"menu_group_{module}",
                help=f"Expandir/Recolher {module}",
                use_container_width=True,
                type="primary" if any_submodule_selected else "secondary",
            )

            if clicked:
                # Comportamento accordion: ao expandir um grupo, recolher todos os outros
                new_state = not st.session_state.menu_expanded_groups[module]

                # Recolher todos os outros grupos primeiro (comportamento accordion)
                for group_name in st.session_state.menu_expanded_groups:
                    if group_name != module:
                        st.session_state.menu_expanded_groups[group_name] = False

                # Aplicar o toggle no grupo clicado
                st.session_state.menu_expanded_groups[module] = new_state
                st.rerun()

            # Renderizar submódulos se expandido
            if is_expanded:
                for submodule, subconfig in config.get("submenu", {}).items():
                    # Verificar permissão do submódulo
                    has_sub_permission = _check_permission(
                        subconfig["permission"],
                        st.session_state.permissions,
                        st.session_state.username,
                    )

                    if not has_sub_permission:
                        continue

                    # Determinar se está selecionado
                    is_selected = current_module == subconfig["original_name"]

                    # Chave única para o sub-item
                    button_key = f"submenu_{module}_{submodule}".replace(" ", "_")

                    # Criar botão do submódulo (com indentação visual)
                    # Sub-menus são secundários e ficam BRANCOS pelo CSS global
                    # Menus principais têm CSS inline que sobrescreve para cinza
                    sub_clicked = st.sidebar.button(
                        f"  {subconfig['icon']} {submodule}",
                        key=button_key,
                        help=f"Acessar {submodule}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary",
                    )

                    if sub_clicked:
                        selected_module = subconfig["original_name"]
                        st.session_state.current_module = subconfig["original_name"]
                        st.rerun()

        # Se é um item simples
        else:
            # Determinar se está selecionado
            is_selected = current_module == config["original_name"]

            # Criar botão do módulo
            clicked = st.sidebar.button(
                f"{config['icon']} {module}",
                key=f"menu_{module}",
                help=f"Acessar {module}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            )

            if clicked:
                selected_module = config["original_name"]
                st.session_state.current_module = config["original_name"]
                st.rerun()

    # Separador
    st.sidebar.markdown("---")

    # Informações do usuário (mais compactas)
    st.sidebar.markdown(
        f"""
    <div style='
        background: #F5F5F5; 
        border-radius: 8px; 
        padding: 10px; 
        text-align: center;
        margin: 15px 0;
    '>
        <div style='color: #1E88E5; font-weight: 600; font-size: 14px;'>👤 {st.session_state.username}</div>
        <div style='color: #666; font-size: 11px;'>Conectado</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Botão de logout compacto
    if st.sidebar.button(
        "🚪 Sair", key="logout", use_container_width=True, type="secondary"
    ):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.current_module = None
        st.success("Você saiu com sucesso.")
        st.rerun()

    return selected_module if selected_module else current_module
