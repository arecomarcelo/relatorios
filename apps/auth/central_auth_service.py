"""
Autenticação contra a identidade central (schema `administracao`, banco
`oficial_db`) — mesma decisão já usada pelas demais apps do ecossistema
oficial (cadastro, senha e autorização únicos), adaptada ao Relatórios
(Streamlit, sem ciclo de request/sessão Django).

Fluxo de `validate_user()` — réplica fiel de
`estoque/apps/accounts/backends.py::ContaCentralizadaBackend.authenticate()`,
só que devolvendo o resultado direto para `st.session_state` em vez de
sincronizar um usuário-espelho Django local (não há `request.user`/`perms.xxx`
de template a alimentar aqui):
1. Usuário existe em `administracao.auth_user`? Senão -> nega.
2. Está ativo e a senha bate (`check_password`, mesmo hasher já usado hoje)?
   Senão -> nega.
3. Superusuário central -> acesso total automático (bypass), sem checar
   `AcessoApp`.
4. Usuário comum -> precisa de `AcessoApp` para o slug "relatorios". Sem ele
   -> nega.
5. `AcessoModuloMenu`: nenhuma linha gravada para o `AcessoApp` = sem
   restrição, vê todos os módulos (regra do model, preservada). Havendo
   pelo menos uma linha, só os módulos ali listados ficam visíveis.

Mapeamento chave (ModuloMenu) -> codename replica 1:1 os 12 itens de
`apps/auth/modules.py::module_config` (ver plano de 27/08/2026). `change_venda`
não é um módulo de visibilidade — é global, ligado a `AcessoApp.pode_editar`,
mesmo papel de `pode_editar` nas outras apps (sempre global, nunca por
módulo).
"""

from typing import List, Tuple

from django.contrib.auth.hashers import check_password

from apps.auth.central_repository import CentralAuthRepository

APP_SLUG = "relatorios"

_MODULO_PARA_CODENAME = {
    "produtos": "view_produtos",
    "boletos": "view_boletos",
    "extratos": "view_extratos",
    "comercial": "view_venda",
    "pedidos": "view_pedido",
    "comparativo": "view_comparativo",
    "campanha_adwords": "view_campanhas",
    "campanha_meta": "view_campanha_meta",
    "recebimentos": "view_recebimentos",
    "clientes": "view_clientes",
    "comex": "view_comex",
    "ordem_servico": "view_os",
}
_CODENAMES_VISUALIZACAO = list(_MODULO_PARA_CODENAME.values())


class CentralAuthService:
    def __init__(self, repository: CentralAuthRepository = None):
        self.repository = repository or CentralAuthRepository()

    def validate_user(
        self, username: str, password: str
    ) -> Tuple[bool, bool, List[str]]:
        """Retorna (is_valid, is_superuser, permissions) — `permissions` é a
        lista de codenames que `apps/auth/modules.py::_check_permission` já
        sabe comparar, sem nenhuma mudança nesse arquivo além do bypass de
        superusuário."""
        central = self.repository.get_central_user(username)
        if central is None:
            return False, False, []

        user_id, password_hash, is_active, is_superuser = central
        if not is_active or not check_password(password, password_hash):
            return False, False, []

        if is_superuser:
            return True, True, list(_CODENAMES_VISUALIZACAO) + ["change_venda"]

        acesso = self.repository.get_acesso_app(APP_SLUG, user_id)
        if acesso is None:
            return False, False, []

        (
            acesso_app_id,
            pode_visualizar,
            _pode_incluir,
            pode_editar,
            _pode_excluir,
        ) = acesso
        if not pode_visualizar:
            return True, False, []

        permissions = list(self._codenames_visualizacao(acesso_app_id))
        if pode_editar:
            permissions.append("change_venda")
        return True, False, permissions

    def _codenames_visualizacao(self, acesso_app_id: int) -> List[str]:
        chaves_visiveis = self.repository.get_chaves_modulos_visiveis(acesso_app_id)
        if not chaves_visiveis:
            # Sem nenhuma linha gravada = sem restrição, vê tudo.
            return _CODENAMES_VISUALIZACAO
        return [
            _MODULO_PARA_CODENAME[chave]
            for chave in chaves_visiveis
            if chave in _MODULO_PARA_CODENAME
        ]
