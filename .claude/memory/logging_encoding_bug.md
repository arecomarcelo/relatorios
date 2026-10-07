---
name: logging-encoding-bug
description: "UnicodeEncodeError real em produção (25/08/2026) no console_handler de core/logging_config.py — sys.stderr reportava ascii em threads do Streamlit mesmo com PYTHONIOENCODING=utf-8; corrigido com reconfigure()"
metadata:
  node_type: memory
  type: project
  originSessionId: cec14d61-c34f-4540-aef6-154ee5849b63
  modified: 2026-08-25T19:27:20.320Z
---

`core/logging_config.py` (`RelatoriosLogger.setup()`) cria um `console_handler = logging.StreamHandler()` sem argumento — isso captura `sys.stderr` **uma única vez**, no momento da criação. Em produção (container Docker, imagem `python:3.12-slim`), mesmo com `PYTHONIOENCODING=utf-8` corretamente definido no `Dockerfile` e confirmado presente no processo real (`/proc/1/environ`), esse `sys.stderr` capturado já foi visto reportando encoding `ascii` **dentro de threads de execução do Streamlit** (`_run_script_thread`) — todo log com emoji (convenção deste projeto: `✓`, `📊`, `⚠` etc.) estourava `UnicodeEncodeError` na hora do `stream.write()`. O `logging` engole esse erro internamente (não derruba a app — o site seguia respondendo HTTP 200), mas suja os logs com um traceback a cada chamada e esconde a mensagem real.

**Causa raiz não 100% isolada** (não valia o custo de instrumentar a thread do Streamlit em produção para confirmar o mecanismo exato) — a correção aplicada é robusta independente da causa.

**Correção (`core/logging_config.py`):** antes de criar o `console_handler`, reconfigurar explicitamente o stream:
```python
console_stream = sys.stderr
try:
    console_stream.reconfigure(encoding='utf-8', errors='backslashreplace')
except (AttributeError, ValueError):
    pass
console_handler = logging.StreamHandler(console_stream)
```
`errors='backslashreplace'` é o que realmente elimina a classe de bug: mesmo se o ambiente voltar a reportar um encoding incompatível no futuro, o pior caso vira um caractere escapado no log, nunca mais uma exceção. Precisa de `# type: ignore[union-attr]` na linha do `reconfigure()` — o stub `TextIO` do mypy não declara esse método (só existe no `TextIOWrapper` real).

**Validado** simulando o cenário exato: substituir `sys.stderr` por um `io.TextIOWrapper(buffer, encoding='ascii', errors='strict')` antes de importar `core.logging_config` — log com emoji gravado corretamente, sem exceção, com a correção.

**Why:** projeto usa emoji em log extensivamente por convenção (regra 11 do CLAUDE.md — "usar emojis para facilitar visualização"), então esse bug se manifestava em praticamente toda operação de log em produção.

**How to apply:** se aparecer `UnicodeEncodeError` de novo em qualquer log deste projeto (ou de outro projeto Django/Streamlit com a mesma convenção de emoji em logs), verificar primeiro se o `StreamHandler` do logger está reconfigurando o encoding do stream explicitamente — não basta setar `PYTHONIOENCODING` no Dockerfile/ambiente, threads podem herdar um stream já capturado com encoding diferente.

**Atualização 06/10/2026 (Note_Oficial via Claude Code) — causa raiz real, a correção de 25/08 não resolvia:** o `reconfigure()` atua no stderr, mas o erro vinha de outro handler. `app.py` roda `django.setup()` a cada rerun do Streamlit, o que reaplica `settings.LOGGING` com um `FileHandler` sem `encoding`; e o fallback `locale.setlocale(LC_ALL, "C")` (o container não tem `pt_BR`) deixava o processo em ASCII. Corrigido nos commits `fbbf2c43` (`encoding: utf-8` no handler + fallback `C.UTF-8` em estoque/boletos/clientes/extratos + teste `tests/test_logging_encoding.py`) e `72f029c9` (keep-alive desativado no Docker). Zero ocorrências após o deploy. Se o erro voltar, olhar primeiro handlers recriados pelo `django.setup()` e o locale, não o stderr.
