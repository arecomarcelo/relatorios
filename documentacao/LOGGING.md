# 📋 Sistema de Logging do Relatórios

## Visão Geral

O Relatórios utiliza um sistema de logging centralizado, inteligente e configurável que fornece rastreabilidade completa das operações do sistema.

## Características Principais

### ✅ Rotação Automática de Arquivos
- Arquivo principal: `logs/relatorios.log` (máximo 10MB)
- Arquivo de erros: `logs/relatorios_errors.log` (apenas ERROR e CRITICAL)
- Mantém 5 backups de cada arquivo
- Rotação automática quando atingir o limite

### 📊 Múltiplos Níveis de Log
- **DEBUG**: Informações detalhadas para diagnóstico
- **INFO**: Informações gerais sobre operações
- **WARNING**: Avisos sobre situações incomuns
- **ERROR**: Erros que não impedem a execução
- **CRITICAL**: Erros críticos que podem parar o sistema

### 🎯 Filtros Inteligentes
- Evita logs repetitivos no console
- Mantém logs completos nos arquivos
- Filtragem configurável de mensagens específicas

### 📝 Formatação Padronizada
- **Arquivo**: `2025-12-17 09:15:23 | INFO     | core.container_vendas | get_vendas_service | ✓ VendasService inicializado`
- **Console**: `09:15:23 | INFO     | ✓ VendasService inicializado`

## Como Usar

### Uso Básico

```python
from core.logging_config import get_logger

# Obter logger para o módulo atual
logger = get_logger(__name__)

# Registrar diferentes níveis de log
logger.debug("Informação de debug detalhada")
logger.info("Operação concluída com sucesso")
logger.warning("Atenção: configuração não encontrada")
logger.error("Erro ao processar dados")
logger.critical("Erro crítico no sistema")
```

### Logging com Contexto de Exceções

```python
try:
    # Código que pode falhar
    processar_dados()
except Exception as e:
    # exc_info=True inclui o stack trace completo
    logger.error(f"Erro ao processar: {e}", exc_info=True)
```

### Decorator para Logging de Funções

```python
from core.logging_config import get_logger, log_function_call

logger = get_logger(__name__)

@log_function_call(logger)
def buscar_vendas(data_inicio, data_fim):
    """Esta função terá entrada e saída logadas automaticamente"""
    return vendas
```

### Context Manager para Operações

```python
from core.logging_config import get_logger, log_operation

logger = get_logger(__name__)

with log_operation(logger, "Importar vendas", "Arquivo: vendas.csv"):
    # O tempo de execução será logado automaticamente
    importar_vendas_do_arquivo()
```

## Exemplos de Saída

### Console (Simplificado)
```
09:15:23 | INFO     | ✓ VendasService inicializado com 4 repositórios
09:15:24 | INFO     | ▶ Iniciando: Buscar vendas (Período: 01/12 a 31/12)
09:15:26 | INFO     | ✓ Concluído: Buscar vendas | Duração: 2.31s
09:15:27 | WARNING  | Cliente não encontrado: ID 12345
```

### Arquivo (Detalhado)
```
2025-12-17 09:15:23 | INFO     | core.container_vendas          | get_vendas_service   | ✓ VendasService inicializado com 4 repositórios
2025-12-17 09:15:24 | INFO     | apps.vendas.views              | buscar_vendas        | ▶ Iniciando: Buscar vendas (Período: 01/12 a 31/12)
2025-12-17 09:15:26 | INFO     | apps.vendas.views              | buscar_vendas        | ✓ Concluído: Buscar vendas | Duração: 2.31s
2025-12-17 09:15:27 | WARNING  | domain.services.cliente_service| get_cliente         | Cliente não encontrado: ID 12345
```

## Configuração Avançada

### Alterar Nível de Log Globalmente

```python
import logging
from core.logging_config import SGRLogger

# Configurar para DEBUG (mostra tudo)
SGRLogger.setup(level=logging.DEBUG)

# Ou apenas para módulo específico
logger = get_logger(__name__, level=logging.DEBUG)
```

### Adicionar Mensagens Filtradas

```python
from core.logging_config import SGRLogger

# Adicionar mensagens que não devem aparecer no console
SGRLogger.FILTERED_MESSAGES.append("Mensagem repetitiva")
```

## Boas Práticas

### ✅ FAZER

```python
# Usar nível apropriado
logger.info("Operação bem-sucedida")  # Informação
logger.error("Erro ao conectar", exc_info=True)  # Erro com stack trace

# Mensagens descritivas
logger.info(f"✓ {total_vendas} vendas processadas em {tempo:.2f}s")

# Incluir contexto relevante
logger.warning(f"Valor alto detectado: R$ {valor:,.2f} para venda {venda_id}")
```

### ❌ NÃO FAZER

```python
# Logs sem informação útil
logger.info("ok")  # Muito vago

# Logs repetitivos em loops
for item in items:
    logger.info(f"Processando {item}")  # Vai gerar milhares de logs

# Logs com informações sensíveis
logger.info(f"Senha do usuário: {senha}")  # NUNCA!
```

## Estrutura de Arquivos de Log

```
logs/
├── relatorios.log              # Log principal (todos os níveis)
├── relatorios.log.1            # Backup 1 (rotação)
├── relatorios.log.2            # Backup 2
├── relatorios.log.3            # Backup 3
├── relatorios.log.4            # Backup 4
├── relatorios.log.5            # Backup 5 (mais antigo)
├── relatorios_errors.log       # Apenas erros
├── relatorios_errors.log.1     # Backup de erros 1
└── ...
```

## Monitoramento e Análise

### Buscar Erros Recentes

```bash
# Últimos 50 erros
tail -50 logs/relatorios_errors.log

# Erros de hoje
grep "2025-12-17" logs/relatorios_errors.log

# Contar erros por tipo
grep "ERROR" logs/relatorios.log | cut -d"|" -f3 | sort | uniq -c
```

### Acompanhar Logs em Tempo Real

```bash
# Seguir log principal
tail -f logs/relatorios.log

# Apenas erros em tempo real
tail -f logs/relatorios_errors.log

# Filtrar mensagens específicas
tail -f logs/relatorios.log | grep "VendasService"
```

## Integração com Módulos Existentes

O sistema de logging foi integrado aos seguintes módulos:

- ✅ `core/container_vendas.py` - Container DI de vendas
- ✅ `infrastructure/database/repositories_*.py` - Repositórios
- ✅ `domain/services/*.py` - Serviços de domínio
- ✅ `apps/*/views.py` - Views dos módulos

### Migração de Código Antigo

Se você encontrar código usando o sistema antigo de logging:

```python
# ❌ Sistema antigo
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# ... configuração manual de handlers

# ✅ Sistema novo
from core.logging_config import get_logger
logger = get_logger(__name__)
```

## Troubleshooting

### Problema: Logs não aparecem

**Solução**: Verificar se o nível de log é apropriado
```python
import logging
from core.logging_config import get_logger

logger = get_logger(__name__, level=logging.DEBUG)
```

### Problema: Muitos logs repetitivos

**Solução**: Adicionar mensagem ao filtro
```python
from core.logging_config import SGRLogger
SGRLogger.FILTERED_MESSAGES.append("Mensagem repetitiva")
```

### Problema: Arquivos de log muito grandes

**Solução**: Ajustar configuração de rotação
```python
from core.logging_config import SGRLogger

# Reduzir tamanho máximo para 5MB
SGRLogger.MAX_BYTES = 5 * 1024 * 1024

# Manter apenas 3 backups
SGRLogger.BACKUP_COUNT = 3

# Reconfigurar
SGRLogger._initialized = False
SGRLogger.setup()
```

## Performance

O sistema de logging foi projetado para ter impacto mínimo na performance:

- Logs DEBUG são descartados antes de formatação quando não habilitados
- Rotação de arquivos é assíncrona
- Filtros são aplicados antes da formatação completa
- Console usa formato simplificado para menor overhead

## Suporte

Para problemas ou dúvidas sobre o sistema de logging, consulte:
- Código fonte: `core/logging_config.py`
- Exemplos: Este documento
- Histórico de alterações: `Historico.md`
