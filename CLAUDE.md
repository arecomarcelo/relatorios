# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## Visão Geral do Projeto

Relatórios (antigo SGR - Sistema de Gestão de Recursos, renomeado em 03/08/2026) é uma aplicação de gestão empresarial construída com:
- **Frontend**: Streamlit (framework web Python)
- **Backend**: Django (ORM e configurações)
- **Banco de Dados**: PostgreSQL (hospedado em 195.200.1.244)
- **Arquitetura**: Padrão Service-Repository com estrutura modular

## Estrutura Principal da Aplicação

### Componentes Principais
- `app.py` - Ponto de entrada principal da aplicação Streamlit com roteamento de módulos
- `service.py` - Camada de lógica de negócio (DataService, UserService)
- `repository.py` - Camada de acesso a dados com conexões de banco
- `modules.py` - Sistema de menu de navegação
- `login.py` - Tela de autenticação
- Arquivos de módulos: `vendas.py`, `clientes.py`, `boletos.py`, `extratos.py`, `estoque.py`

### Integração Django
- Django é usado principalmente para modelos ORM e configuração de banco de dados
- Configurações em `app/settings.py` (configuração básica Django com SQLite padrão)
- Autenticação usa sistema auth do Django com hash de senhas

### Configuração do Banco de Dados
A aplicação conecta a um banco PostgreSQL via variáveis de ambiente (`.env`):
```python
DB_CONFIG = {
    'dbname': os.environ.get("DB_NAME"),
    'user': os.environ.get("DB_USER"),
    'password': os.environ.get("DB_PASSWORD"),
    'host': os.environ.get("DB_HOST"),
    'port': os.environ.get("DB_PORT"),
}
```
As credenciais ficam no arquivo `.env` (não versionado). Use `.env.example` como referência.

## Comandos Comuns de Desenvolvimento

### Configuração do Ambiente
```bash
# Ativar ambiente virtual (Linux)
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Executando a Aplicação
```bash
# Iniciar aplicação Streamlit
streamlit run app.py

# Comandos de gerenciamento Django (se necessário)
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

### Ferramentas de Qualidade de Código (da documentação)
```bash
# Organizar imports
isort .

# Formatar código
blue .

# Verificar estilo
flake8
```

### Gerenciamento de Dependências
```bash
# Atualizar requirements.txt
pip freeze > requirements.txt
```

## Padrões de Arquitetura

### Padrão Service-Repository
- **Camada Repository**: Acesso direto ao banco de dados (`repository.py`)
- **Camada Service**: Lógica de negócio (`service.py`)
- **Camada Presentation**: Módulos Streamlit (vendas, clientes, etc.)

### Estrutura dos Módulos
Cada módulo de negócio segue este padrão:
```python
def main(key="nome_modulo"):
    # Interface Streamlit específica do módulo
    # Usa DataService para operações de dados
```

### Acesso ao Banco de Dados
- Usa tanto SQLAlchemy quanto psycopg2 para diferentes operações
- Classes Repository lidam com operações específicas de entidades
- DataService orquestra interações entre repositories

## Dependências Principais
- `streamlit` - Framework web
- `django` - ORM e autenticação
- `pandas` - Manipulação de dados
- `plotly` - Visualização de dados
- `psycopg2-binary` - Adaptador PostgreSQL
- `sqlalchemy` - Toolkit de banco de dados

## Notas de Desenvolvimento

### Segurança do Banco de Dados
As credenciais do banco estão atualmente hardcoded na camada de serviço. Considere usar variáveis de ambiente para deployments de produção.

### Configuração Streamlit
Configuração de página definida em `app.py` com:
- Título da página: "Relatórios - Oficial Sport"
- Layout amplo
- Sidebar expandida

### Fluxo de Autenticação
1. Tela de login valida contra tabela auth_user do Django
2. Permissões do usuário buscadas do sistema auth Django
3. Estado da sessão gerencia status de login

### Navegação entre Módulos
A aplicação principal roteia para diferentes módulos baseado na seleção da sidebar:
- Estoque
- Cobrança
- Financeiro
- Vendas
- Relatório de Clientes
- SAC (Serviço de Atendimento ao Cliente)
- Comex (Comércio Exterior)

## Sistema de Logging

### Visão Geral
O Relatórios utiliza um sistema de logging centralizado (`core/logging_config.py`) com as seguintes características:
- **Rotação automática** de arquivos (10MB por arquivo, mantém 5 backups)
- **Múltiplos níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Duplo destino**: Console (simplificado) e arquivos (detalhado)
- **Filtros inteligentes**: Evita logs repetitivos no console
- **Formatação padronizada**: Timestamps, níveis, módulos e funções

### Arquivos de Log
- `logs/relatorios.log` - Log principal com todas as mensagens
- `logs/relatorios_errors.log` - Apenas erros (ERROR e CRITICAL)
- Rotação automática com backups numerados (.1, .2, .3, etc)

### Como Usar

```python
# Importar logger
from core.logging_config import get_logger

# Obter logger para o módulo atual
logger = get_logger(__name__)

# Registrar mensagens
logger.debug("Informação de debug detalhada")
logger.info("✓ Operação concluída com sucesso")
logger.warning("⚠ Atenção: configuração não encontrada")
logger.error("✗ Erro ao processar dados", exc_info=True)
logger.critical("🚨 Erro crítico no sistema")
```

### Context Manager para Operações

```python
from core.logging_config import get_logger, log_operation

logger = get_logger(__name__)

with log_operation(logger, "Buscar vendas", "Período: 01/12 a 31/12"):
    # Tempo de execução será logado automaticamente
    vendas = buscar_vendas()
```

### Formatação de Logs

**Console (simplificado):**
```
09:15:23 | INFO     | ✓ VendasService inicializado com 4 repositórios
```

**Arquivo (detalhado):**
```
2025-12-17 09:15:23 | INFO     | core.container_vendas | get_vendas_service | ✓ VendasService inicializado
```

### Boas Práticas

**✅ FAZER:**
- Usar logger ao invés de print() em código de produção
- Incluir contexto relevante nas mensagens
- Usar exc_info=True para incluir stack traces em erros
- Usar emojis para facilitar visualização (✓, ✗, ⚠, 📊, 🔍, etc)

**❌ NÃO FAZER:**
- Logar em loops que podem gerar milhares de mensagens
- Incluir informações sensíveis (senhas, tokens, etc)
- Usar mensagens vagas como "ok" ou "erro"
- Usar print() ao invés do sistema de logging

### Documentação Completa
Consulte `documentacao/LOGGING.md` para informações detalhadas sobre:
- Configuração avançada
- Monitoramento e análise de logs
- Troubleshooting
- Performance

## Diretrizes de Codificação

- **Princípios Fundamentais**:
  01) Sempre revise suas alterações de modo a não alterar ou prejudicar a execução já implementada
  02) Sempre responder em Português do Brasil
  03) Sempre retornar o código completo, jamais abrevie o código
  04) Sempre Listar o nomes dos arquivos alterado
  05) Sempre finalize suas resposta com uma linha em Branco *** FINALIZADO ***
  06) Ao finalizar uma Interação, armazene no arquivo Historico.md (crie se não existir):
    1) Dia (somente na primeira interação do Dia) e a cada nova interação Hora da Tarefa
    2) O que foi pedido
    3) Detalhamento da Solução ou Implementação
    4) Lista de Arquivos Alterados ou Criados
    5) Utilize emojis para tornar clara a compreensão
    6) Utilize UTF-8 e o Fuso Horário Local
 07) **MODELOS**: Os modelos já existem no banco de dados e NÃO devem gerar migrações
 08) **NOVOS MODELOS**: Quando um modelo não existir, será informado como "Novo Modelo" na descrição
