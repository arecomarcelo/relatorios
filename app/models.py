"""
Modelos Django para SGR — fonte única de verdade.
Todos os modelos existem no banco de dados e NÃO devem gerar migrações (managed=False).
"""

from django.db import models


# ---------------------------------------------------------------------------
# PessoaTipos
# ---------------------------------------------------------------------------
class PessoaTipos(models.Model):
    """Tipos de pessoa (PF / PJ)"""

    nome = models.CharField(max_length=100)

    class Meta:
        db_table = '"compartilhado"."PessoaTipos"'
        managed = False
        verbose_name = "Tipo de Pessoa"
        verbose_name_plural = "Tipos de Pessoa"

    def __str__(self):
        return self.nome


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------
class Clientes(models.Model):
    TIPO_PESSOA_CHOICES = [
        ("PF", "Física"),
        ("PJ", "Jurídica"),
    ]

    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
    ]

    class Meta:
        db_table = '"compartilhado"."Clientes"'
        managed = False
        ordering = ["RazaoSocial"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    id = models.AutoField(primary_key=True)
    ID_Gestao = models.CharField(max_length=10)
    TipoPessoa = models.CharField(
        max_length=2, choices=TIPO_PESSOA_CHOICES, default="PF"
    )
    PessoaTipo = models.ForeignKey(
        PessoaTipos,
        on_delete=models.CASCADE,
        related_name="tipopessoa_cliente",
        verbose_name="Pessoa Tipo",
        null=True,
    )
    Nome = models.CharField(max_length=100, blank=True, null=True)
    RazaoSocial = models.CharField(max_length=100, blank=True, null=True)
    CNPJ = models.CharField(max_length=30, blank=True, null=True)
    InscricaoEstadual = models.CharField(max_length=30, blank=True, null=True)
    InscricaoMunicipal = models.CharField(max_length=30, blank=True, null=True)
    Responsavel = models.CharField(max_length=100, blank=True, null=True)
    CPF = models.CharField(max_length=30, blank=True, null=True)
    RG = models.CharField(max_length=30, blank=True, null=True)
    DataNascimento = models.DateField(
        verbose_name="Data Nascimento", blank=True, null=True
    )
    Sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default="M")
    Email = models.CharField(max_length=100, blank=True, null=True)
    Ativo = models.BooleanField(blank=True, null=True)
    NomeVendedor = models.CharField(max_length=100, blank=True, null=True)
    DataCadastro = models.DateField(verbose_name="Data Cadastro", blank=True, null=True)

    def __str__(self):
        return f"{self.RazaoSocial} - {self.CNPJ}"


# ---------------------------------------------------------------------------
# Bancos
# ---------------------------------------------------------------------------
class Bancos(models.Model):
    class Meta:
        db_table = '"financeiro"."Bancos"'
        managed = False
        ordering = ["descricao"]
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"

    descricao = models.CharField(max_length=255)
    codigo_instituicao = models.CharField(max_length=20)

    def __str__(self):
        return self.descricao


# ---------------------------------------------------------------------------
# CentroCustos
# ---------------------------------------------------------------------------
class CentroCustos(models.Model):
    class Meta:
        db_table = '"financeiro"."CentroCustos"'
        managed = False
        ordering = ["descricao"]
        verbose_name = "Centro de Custo"
        verbose_name_plural = "Centros de Custo"

    descricao = models.CharField(max_length=255)

    def __str__(self):
        return self.descricao


# ---------------------------------------------------------------------------
# Empresas
# ---------------------------------------------------------------------------
class Empresas(models.Model):
    class Meta:
        db_table = '"financeiro"."Empresas"'
        managed = False
        ordering = ["nome"]
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    nome = models.CharField(max_length=250)
    cnpj = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} - {self.cnpj}"


# ---------------------------------------------------------------------------
# Extratos
# ---------------------------------------------------------------------------
class Extratos(models.Model):
    class Meta:
        db_table = '"financeiro"."Extratos"'
        managed = False
        ordering = ["banco", "-data"]
        verbose_name = "Extrato"
        verbose_name_plural = "Extratos"

    banco = models.ForeignKey(Bancos, on_delete=models.CASCADE)
    agencia = models.CharField(max_length=255)
    conta_corrente = models.CharField(max_length=255)
    data = models.DateField(null=True, blank=True)
    agencia_origem = models.CharField(max_length=255)
    lote = models.CharField(max_length=255)
    documento = models.CharField(max_length=255)
    historico_codigo = models.CharField(max_length=255)
    historico_descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    debito_credito = models.CharField(max_length=1, null=True, blank=True)
    descricao = models.CharField(max_length=255)
    centrocusto = models.ForeignKey(
        CentroCustos,
        on_delete=models.PROTECT,
        related_name="extratos",
        verbose_name="Centro Custo",
        null=True,
        blank=True,
        default=0,
    )
    empresa = models.ForeignKey(
        Empresas,
        on_delete=models.PROTECT,
        verbose_name="Empresa",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.banco} - {self.data} - {self.historico_descricao} - {self.valor}"


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
class Produtos(models.Model):
    class Meta:
        db_table = '"compartilhado"."Produtos"'
        managed = False
        ordering = ["Nome"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    ID_Gestao = models.CharField(max_length=100, blank=False, null=False)
    ID_Loja = models.CharField(max_length=10)
    Nome = models.CharField(max_length=200, blank=False, null=False)
    Descricao = models.CharField(max_length=200, blank=False, null=False)
    CodigoInterno = models.CharField(max_length=100, blank=True, null=True)
    CodigoBarra = models.CharField(max_length=100, blank=True, null=True)
    PossuiVariacao = models.BooleanField(blank=True, null=True)
    PossuiComposicao = models.BooleanField(blank=True, null=True)
    MovimentaEstoque = models.BooleanField(blank=True, null=True)
    Peso = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    Largura = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True
    )
    Altura = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    Comprimento = models.DecimalField(
        max_digits=10, decimal_places=4, blank=True, null=True
    )
    Ativo = models.BooleanField(default=True)
    ID_Grupo = models.CharField(max_length=10, blank=True, null=True)
    NomeGrupo = models.CharField(max_length=100, blank=True, null=True)
    Estoque = models.IntegerField(blank=True, null=True)
    ValorCusto = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    ValorVenda = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    LucroUtilizado = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    CodigoExpedicao = models.CharField(max_length=100, blank=True, null=True)
    EstoqueGalpao = models.IntegerField(default=0)
    EstoqueSeparado = models.IntegerField(default=0)
    EstoqueMovimentado = models.IntegerField(default=0)
    Localizacao = models.CharField(max_length=20, blank=True, null=True)
    QrCode = models.BooleanField(
        verbose_name="QR Code Gerado", default=False, null=True, blank=True
    )
    URL = models.CharField(max_length=500, blank=True, null=True)
    Exibir = models.BooleanField(blank=True, null=True)

    @property
    def EstoqueDisponivel(self):
        """
        Calcula o estoque disponível:
        EstoqueGalpao - (EstoqueSeparado + EstoqueMovimentado)
        """
        try:
            estoque_galpao = int(self.EstoqueGalpao) if self.EstoqueGalpao else 0
            estoque_separado = int(self.EstoqueSeparado) if self.EstoqueSeparado else 0
            estoque_movimentado = (
                int(self.EstoqueMovimentado) if self.EstoqueMovimentado else 0
            )
            disponivel = estoque_galpao - (estoque_separado + estoque_movimentado)
            return max(disponivel, 0)
        except (ValueError, TypeError):
            return 0

    def __str__(self):
        return self.Nome


# ---------------------------------------------------------------------------
# BoletosEnviados
# ---------------------------------------------------------------------------
class BoletosEnviados(models.Model):
    STATUS_CHOICES = [
        ("Enviado", "Enviado"),
        ("Errado", "Errado"),
        ("Sem Contato", "Sem Contato"),
    ]

    STATUS_MAPPING = {
        "1": {"label": "Enviado", "class": "text-success"},
        "2": {"label": "Errado", "class": "text-danger"},
        "3": {"label": "Sem Contato", "class": "text-secondary"},
    }

    class Meta:
        db_table = '"cobranca"."BoletosEnviados"'
        managed = False
        ordering = ["-DataHoraEnvio"]
        verbose_name = "Boleto Enviado"
        verbose_name_plural = "Boletos Enviados"

    id = models.AutoField(primary_key=True)
    Nome = models.CharField(max_length=250)
    Boleto = models.CharField(max_length=250)
    Vencimento = models.DateField(verbose_name="Data Vencimento")
    Importacao = models.DateField(null=True, blank=True, verbose_name="Data Importação")
    DataHoraEnvio = models.DateTimeField(verbose_name="Data Hora Envio")
    Status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Status"
    )

    def get_status_class(self):
        for key, value in self.STATUS_MAPPING.items():
            if value["label"] == self.Status:
                return value["class"]
        return ""

    def __str__(self):
        return f"{self.Boleto} - {self.Vencimento}"


# ---------------------------------------------------------------------------
# OS (Ordens de Serviço)
# ---------------------------------------------------------------------------
class OS(models.Model):
    """Modelo para gerenciar OS's do Gestão."""

    class Meta:
        db_table = '"vendas"."OS"'
        managed = False
        ordering = ["ID_Gestao"]
        verbose_name = "OS"
        verbose_name_plural = "OS"

    ID_Gestao = models.CharField(max_length=100)
    OS_Codigo = models.CharField(max_length=100)
    Data = models.DateField(verbose_name="Data Entrada")
    ClienteNome = models.CharField(max_length=100, verbose_name="Nome Cliente")
    SituacaoNome = models.CharField(max_length=100, verbose_name="Situação OS")
    Referencia = models.TextField(null=True, blank=True, verbose_name="Referência OS")

    def __str__(self):
        return f"OS {self.ID_Gestao} - {self.ClienteNome}"


# ---------------------------------------------------------------------------
# OS_Produtos (Produtos das OS's)
# ---------------------------------------------------------------------------
class OS_Produtos(models.Model):
    """Modelo para gerenciar Produtos das OS's do Gestão."""

    class Meta:
        db_table = '"vendas"."OS_Produtos"'
        managed = False
        ordering = ["OS"]
        verbose_name = "OS Produto"
        verbose_name_plural = "OS Produtos"

    OS = models.ForeignKey(OS, on_delete=models.CASCADE, verbose_name="OS")
    Nome = models.CharField(max_length=100, verbose_name="Nome Produto")
    SiglaUnidade = models.CharField(max_length=10, verbose_name="Sigla da Unidade")
    Quantidade = models.IntegerField()
    ValorVenda = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Venda"
    )
    TipoDesconto = models.CharField(max_length=10, verbose_name="Tipo Desconto")
    Desconto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Desconto",
        blank=True,
        null=True,
    )
    DescontoPorcentagem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Percentual Desconto",
        blank=True,
        null=True,
    )
    ValorTotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Valor Total OS"
    )

    def __str__(self):
        return f"{self.Nome} - OS {self.OS.ID_Gestao}"


# ---------------------------------------------------------------------------
# Vendas
# ---------------------------------------------------------------------------
class Venda(models.Model):
    class Meta:
        db_table = '"vendas"."Vendas"'
        managed = False
        ordering = [
            "ID_Gestao",
        ]
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"

    ID_Gestao = models.CharField(max_length=100)
    Codigo = models.CharField(max_length=100)
    ClienteNome = models.CharField(max_length=100)
    VendedorNome = models.CharField(max_length=100)
    Data = models.CharField(max_length=100)
    PrazoEntrega = models.CharField(max_length=100, null=True, blank=True)
    SituacaoNome = models.CharField(max_length=100)
    NomeCanalVenda = models.CharField(max_length=100)
    CondicaoPagamento = models.CharField(max_length=100)
    ValorCusto = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorProdutos = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorDesconto = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorTotal = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    Origem = models.CharField(max_length=100, null=True, blank=True)


class VendaPagamento(models.Model):
    class Meta:
        db_table = '"vendas"."VendaPagamentos"'
        managed = False
        ordering = [
            "Venda_ID",
        ]
        verbose_name = "Venda Pagamento"
        verbose_name_plural = "Venda Pagamentos"

    Venda_ID = models.CharField(max_length=100)
    DataVencimento = models.DateField(null=True, blank=True)
    Valor = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    NomeFormaPagamento = models.CharField(max_length=100)
    Observacao = models.TextField(null=True, blank=True)


class VendaProduto(models.Model):
    class Meta:
        db_table = '"vendas"."VendaProdutos"'
        managed = False
        ordering = [
            "Venda_ID",
        ]
        verbose_name = "Venda Produto"
        verbose_name_plural = "Venda Produtos"

    Venda_ID = models.CharField(max_length=100)
    Nome = models.TextField()
    Detalhes = models.TextField(null=True, blank=True)
    Quantidade = models.IntegerField(null=True, blank=True)
    ValorCusto = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorVenda = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorDesconto = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    ValorTotal = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    CodigoExpedicao = models.CharField(max_length=100, blank=True, null=True)
