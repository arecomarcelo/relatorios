#!/bin/bash

################################################################################
# Script de Pré-Deploy — SGR (Multi-Aplicação SGA)
#
# Descrição: Valida o sistema antes do deploy Docker na VPS Hostinger.
# Uso: bash scripts/predeploy.sh
#
# Sequência completa de deploy:
#   1. Ajustes no código + testes locais
#   2. bash scripts/predeploy.sh   → validação local (este script)
#   3. Anotar em Historico.md
#   4. git commit
#   5. bash scripts/deploy_local.sh
#
# Diferente de administracao/comex/estoque/financeiro: o SGR é sistema legado
# (ver memória projeto-natureza) — sem migrações Django (modelos já existem no
# banco), sem % Desenvolvido/Score de Implantação, sem Celery/Redis.
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

ERRORS=0
WARNINGS=0

print_header() {
    echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}
print_step()    { echo -e "${CYAN}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error()   { echo -e "${RED}❌ $1${NC}"; ((ERRORS++)); }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; ((WARNINGS++)); }
print_info()    { echo -e "${BLUE}ℹ️  $1${NC}"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

clear
echo -e "${BOLD}${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          SGR — Multi-Aplicação SGA (Oficial Sport)           ║
║                                                               ║
║           SCRIPT DE PRÉ-DEPLOY — VALIDAÇÃO                   ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

print_info "Iniciando verificações de pré-deploy..."
print_info "Data/Hora: $(TZ='America/Sao_Paulo' date '+%d/%m/%Y %H:%M:%S')"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# ============================================================================
# 1. AMBIENTE
# ============================================================================
print_header "1. VERIFICAÇÃO DO AMBIENTE"

print_step "Verificando Python..."
if command_exists python3; then
    print_success "Python encontrado: $(python3 --version 2>&1)"
else
    print_error "Python3 não encontrado!"
fi

print_step "Verificando Git..."
if command_exists git; then
    print_success "Git encontrado: $(git --version 2>&1)"
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        print_warning "Existem mudanças não commitadas"
    else
        print_success "Repositório limpo"
    fi
else
    print_error "Git não encontrado!"
fi

print_step "Verificando virtual environment..."
if [ -d "venv" ]; then
    print_success "Virtual environment encontrado: ./venv"
else
    print_error "Virtual environment não encontrado em ./venv"
fi

print_step "Verificando Docker..."
if command_exists docker; then
    print_success "Docker encontrado: $(docker --version 2>&1)"
else
    print_error "Docker não encontrado — necessário para build/push da imagem"
fi

# ============================================================================
# 2. QUALIDADE DE CÓDIGO
# ============================================================================
print_header "2. QUALIDADE DE CÓDIGO"

PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
PIP_BIN="$PROJECT_DIR/venv/bin/pip"

print_step "Executando formata.py (black + isort + flake8)..."
if [ -f "formata.py" ]; then
    if "$PYTHON_BIN" formata.py; then
        print_success "Formatação e linting concluídos"
    else
        print_error "formata.py encontrou problemas — corrija antes de prosseguir"
    fi
else
    print_warning "formata.py não encontrado — pulando formatação"
fi

print_step "Verificando erros de sintaxe Python..."
SYNTAX_ERRORS=0
while IFS= read -r -d '' file; do
    if ! "$PYTHON_BIN" -m py_compile "$file" 2>/dev/null; then
        print_error "Erro de sintaxe em: $file"
        ((SYNTAX_ERRORS++))
    fi
done < <(find . -name "*.py" -not -path "./venv/*" -print0)
[ $SYNTAX_ERRORS -eq 0 ] && print_success "Nenhum erro de sintaxe encontrado"

# ============================================================================
# 3. DEPENDÊNCIAS
# ============================================================================
print_header "3. DEPENDÊNCIAS"

print_step "Verificando dependências críticas..."
CRITICAL_DEPS=("Django" "streamlit" "psycopg2-binary" "SQLAlchemy" "pandas")
for dep in "${CRITICAL_DEPS[@]}"; do
    if "$PIP_BIN" show "$dep" >/dev/null 2>&1; then
        VERSION=$("$PIP_BIN" show "$dep" | grep "Version:" | cut -d' ' -f2)
        print_success "$dep instalado (v$VERSION)"
    else
        print_error "$dep não está instalado!"
    fi
done

# ============================================================================
# 4. VERIFICAÇÕES DJANGO
# ============================================================================
print_header "4. VERIFICAÇÕES DO DJANGO"

print_step "Executando django check..."
if "$PYTHON_BIN" manage.py check --no-color 2>&1 | grep -q "System check identified no issues"; then
    print_success "django check passou sem problemas"
else
    print_error "django check encontrou problemas"
    "$PYTHON_BIN" manage.py check --no-color 2>&1
fi

print_step "Confirmando ausência de migrações pendentes de criação (modelos já existem no banco)..."
if "$PYTHON_BIN" manage.py makemigrations --dry-run --check >/dev/null 2>&1; then
    print_success "Nenhuma migração nova seria gerada"
else
    print_warning "makemigrations detectaria mudanças de model — lembrar que o SGR NÃO deve gerar migrações (modelos já existem no banco)"
fi

# ============================================================================
# 5. SEGURANÇA
# ============================================================================
print_header "5. SEGURANÇA"

print_step "Verificando arquivos sensíveis no repositório..."
FOUND_SENSITIVE=0
for pattern in ".env" "*.key" "*.pem" "*credentials*" "*secrets*"; do
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            if git check-ignore -q "$file" 2>/dev/null; then
                print_success "Arquivo sensível $file está no .gitignore"
            else
                print_error "Arquivo sensível $file NÃO está no .gitignore!"
                ((FOUND_SENSITIVE++))
            fi
        fi
    done < <(find . -name "$pattern" -not -path "./venv/*")
done
[ $FOUND_SENSITIVE -eq 0 ] && print_success "Nenhum arquivo sensível exposto"

print_step "Verificando Dockerfile/entrypoint.sh..."
[ -f "Dockerfile" ] && print_success "Dockerfile presente" || print_error "Dockerfile não encontrado"
if [ -f "entrypoint.sh" ]; then
    [ -x "entrypoint.sh" ] && print_success "entrypoint.sh presente e executável" || print_warning "entrypoint.sh presente mas sem permissão de execução local (o Dockerfile já ajusta isso no build)"
else
    print_error "entrypoint.sh não encontrado"
fi

# ============================================================================
# RESUMO
# ============================================================================
print_header "RESUMO DA VALIDAÇÃO"

echo -e "${BOLD}Estatísticas:${NC}"
echo -e "  ${RED}Erros:   $ERRORS${NC}"
echo -e "  ${YELLOW}Avisos:  $WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ SISTEMA APROVADO PARA DEPLOY!${NC}"
    echo ""
    echo -e "${CYAN}Próximos passos:${NC}"
    echo -e "  1. Anotar em Historico.md"
    echo -e "  2. git commit"
    echo -e "  3. bash scripts/deploy_local.sh"
    echo ""
else
    echo -e "${RED}${BOLD}❌ CORRIJA OS $ERRORS ERRO(S) ANTES DE PROSSEGUIR!${NC}"
    echo ""
fi

[ $ERRORS -eq 0 ] && exit 0 || exit 1
