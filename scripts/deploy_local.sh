#!/bin/bash

################################################################################
# Script de Deploy — SGR (Multi-Aplicação SGA)
#
# Descrição: Push para GitHub + build/push da imagem + deploy Docker Swarm
#            na VPS Hostinger.
# Uso: bash scripts/deploy_local.sh
#
# Sequência completa de deploy:
#   1. Ajustes no código + testes locais
#   2. bash scripts/predeploy.sh     → validação local
#   3. Anotar em Historico.md
#   4. git commit
#   5. bash scripts/deploy_local.sh  → este script
#
# Pré-requisitos (uma vez):
#   - docker login ghcr.io -u arecomarcelo
#   - /home/deploy/apps/sgr já clonado na VPS (git clone git@github.com:
#     arecomarcelo/sgr.git /home/deploy/apps/sgr)
#   - .env real em /home/deploy/apps/sgr/.env (DB_HOST=host-postgres,
#     DB_NAME=sga, DB_USER/DB_PASSWORD reais, SECRET_KEY)
#   - DNS relatorios.oficialsport.com.br → 195.200.1.244 (Traefik só roteia depois
#     disso propagar; até lá dá pra validar via porta publicada/curl --resolve)
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

VPS_HOST="195.200.1.244"
VPS_USER="root"
VPS_APP_DIR="/home/deploy/apps/sgr"
APP_URL="https://relatorios.oficialsport.com.br"

clear
echo -e "${BOLD}${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          SGR — Multi-Aplicação SGA (Oficial Sport)           ║
║                                                               ║
║                DEPLOY → VPS HOSTINGER                        ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}ℹ️  Data/Hora: $(TZ='America/Sao_Paulo' date '+%d/%m/%Y %H:%M:%S')${NC}"
echo -e "${BLUE}ℹ️  VPS: ${VPS_HOST} | App: ${APP_URL}${NC}"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# ─── 1. Verificar mudanças não commitadas ────────────────────────────────────
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${RED}❌ Existem mudanças não commitadas. Faça o commit antes do deploy.${NC}"
    echo ""
    git status --short
    echo ""
    exit 1
fi

LAST_COMMIT=$(git log --oneline -1)
echo -e "${CYAN}▶ Último commit:${NC} $LAST_COMMIT"
echo ""

# ─── 2. Push para GitHub ─────────────────────────────────────────────────────
echo -e "${CYAN}▶ [1/4] Enviando para GitHub (origin/main)...${NC}"
if git push origin main; then
    echo -e "${GREEN}✅ Push realizado com sucesso!${NC}"
else
    echo -e "${RED}❌ Erro no push. Verifique sua conexão e permissões.${NC}"
    exit 1
fi
echo ""

# ─── 3. Build + push da imagem para o GHCR ───────────────────────────────────
# Pré-requisito (uma vez por máquina): docker login ghcr.io -u arecomarcelo
echo -e "${CYAN}▶ [2/4] Build e push da imagem para o GHCR...${NC}"
IMAGE="ghcr.io/arecomarcelo/sgr:latest"
if docker build -t "$IMAGE" . && docker push "$IMAGE"; then
    echo -e "${GREEN}✅ Imagem publicada: ${IMAGE}${NC}"
else
    echo -e "${RED}❌ Erro no build/push da imagem. Verifique 'docker login ghcr.io'.${NC}"
    exit 1
fi
echo ""

# ─── 4. Deploy na VPS via Docker Swarm ────────────────────────────────────────
echo -e "${CYAN}▶ [3/4] Conectando à VPS e atualizando a stack...${NC}"
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "
    cd ${VPS_APP_DIR} &&
    echo '  → git pull...' &&
    git pull origin main &&
    echo '  → docker stack deploy...' &&
    docker stack deploy -c stack.yml sgr --with-registry-auth
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deploy na VPS concluído!${NC}"
else
    echo -e "${RED}❌ Erro durante deploy na VPS. Verifique os logs:${NC}"
    echo -e "${YELLOW}   ssh ${VPS_USER}@${VPS_HOST} 'docker service logs sgr_web --tail 30'${NC}"
    exit 1
fi
echo ""

# ─── 5. Verificar status ─────────────────────────────────────────────────────
echo -e "${CYAN}▶ [4/4] Status das réplicas na VPS...${NC}"
ssh -o StrictHostKeyChecking=no ${VPS_USER}@${VPS_HOST} "docker service ls | grep sgr"
echo ""

echo -e "${GREEN}${BOLD}✅ DEPLOY CONCLUÍDO!${NC}"
echo ""
echo -e "${CYAN}Acesse:${NC}"
echo -e "  🌐 App: ${APP_URL} (depende do DNS já ter sido provisionado)"
echo -e "  🐳 VPS: ssh ${VPS_USER}@${VPS_HOST}"
echo ""

read -p "Pressione ENTER para fechar..."
