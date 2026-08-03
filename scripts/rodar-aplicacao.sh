#!/usr/bin/env bash
# Sobe o ambiente local do SGR (Streamlit + Django ORM) para testes

set -euo pipefail

PROJETO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORTA=8001
URL="http://localhost:${PORTA}"

cd "$PROJETO_DIR"

clear

# ─── Cores ────────────────────────────────────────────────────────────────────
VERDE="\033[0;32m"
AMARELO="\033[1;33m"
VERMELHO="\033[0;31m"
CIANO="\033[0;36m"
RESET="\033[0m"

ok()   { echo -e "${VERDE}  ✔ ${1}${RESET}"; }
info() { echo -e "${CIANO}  → ${1}${RESET}"; }
warn() { echo -e "${AMARELO}  ⚠ ${1}${RESET}"; }
erro() { echo -e "${VERMELHO}  ✘ ${1}${RESET}"; exit 1; }

echo ""
echo -e "${CIANO}╔══════════════════════════════════════════╗${RESET}"
echo -e "${CIANO}║   SGR — Iniciar Ambiente Local            ║${RESET}"
echo -e "${CIANO}╚══════════════════════════════════════════╝${RESET}"
echo ""

# ─── 1. Verificar venv ─────────────────────────────────────────────────────────
info "Verificando ambiente virtual..."
STREAMLIT="${PROJETO_DIR}/venv/bin/streamlit"
if [[ ! -x "$STREAMLIT" ]]; then
    erro "venv não encontrado em ${PROJETO_DIR}/venv — rode 'python3 -m venv venv && venv/bin/pip install -r requirements.txt'."
fi
ok "venv encontrado"

# ─── 2. Verificar .env ─────────────────────────────────────────────────────────
info "Verificando .env..."
[[ -f "${PROJETO_DIR}/.env" ]] || erro ".env não encontrado — copie .env.example e preencha as credenciais."
ok ".env presente"

# Sem Docker/Redis/migrations aqui: diferente das apps Multi-Aplicação (admini
# stracao/financeiro/estoque), o SGR é sistema legado (Streamlit + Django ORM)
# que conecta direto no banco `sga` já existente — sem banco local espelhado,
# sem Celery/Redis, e todos os modelos são managed=False (sem migrations).

# ─── 3. Subir Streamlit ────────────────────────────────────────────────────────
echo ""
echo -e "${VERDE}╔══════════════════════════════════════════╗${RESET}"
echo -e "${VERDE}║  ✔  Ambiente pronto                       ║${RESET}"
echo -e "${VERDE}║     ${URL}                      ║${RESET}"
echo -e "${VERDE}╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  Parar depois:  ${CIANO}Ctrl+C${RESET}"
echo ""

# Abre o browser após o Streamlit inicializar (comando bloqueia, então abre em background)
(sleep 3 && xdg-open "$URL" > /dev/null 2>&1) &

"$STREAMLIT" run app.py --server.port "$PORTA"
