#!/usr/bin/env bash
# claude-sync-push.sh — Copia memórias Claude locais para o repositório.
# Executado pelo hook pre-commit.
set -euo pipefail

PROJECT_PATH="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_HASH="$(printf '%s' "$PROJECT_PATH" | tr '/_' '--')"
CLAUDE_MEMORY_DIR="$HOME/.claude/projects/$CLAUDE_HASH/memory"
REPO_MEMORY_DIR="$PROJECT_PATH/.claude/memory"

mkdir -p "$REPO_MEMORY_DIR"

COPIED=0
if [[ -d "$CLAUDE_MEMORY_DIR" ]]; then
    while IFS= read -r -d '' file; do
        cp "$file" "$REPO_MEMORY_DIR/"
        COPIED=$((COPIED + 1))
    done < <(find "$CLAUDE_MEMORY_DIR" -maxdepth 1 -type f -name '*.md' -print0)
fi

echo "✅ claude-sync-push: $COPIED arquivo(s) copiado(s) para o repositório"
