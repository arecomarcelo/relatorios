"""Regra SQL de "venda de vendedor cadastrado" — única para todo o relatorios.

Comparação pelo `vendedor_id` do Gestão Click (estável quando o vendedor é
renomeado lá; a API devolve sempre o nome atual). Pelo nome, com TRIM, quando
falta o ID em um dos lados: cadastro recém incluído pela tela Gerenciar do
dashboard (o rpa preenche o ID na importação seguinte) ou venda importada antes
do rpa gravar o ID. Mesma regra do app Vendas (`filtrar_por_vendedores`,
filtro "Cadastrados"). Decisão do usuário, 14/10/2026.
"""


def sql_vendedor_cadastrado(alias: str = "") -> str:
    """Condição SQL (sem AND inicial) para vendas de vendedores cadastrados.

    `alias` é o apelido da tabela vendas."Vendas" na consulta (ex.: "v").
    """
    p = f"{alias}." if alias else ""
    return (
        "("
        f'{p}"VendedorID" IN (SELECT "VendedorID" FROM vendas."Vendedores" '
        'WHERE "VendedorID" IS NOT NULL) '
        f'OR TRIM({p}"VendedorNome") IN (SELECT "Nome" FROM vendas."Vendedores" '
        'WHERE "VendedorID" IS NULL) '
        f'OR ({p}"VendedorID" IS NULL AND TRIM({p}"VendedorNome") IN '
        '(SELECT "Nome" FROM vendas."Vendedores"))'
        ")"
    )
