#!/usr/bin/env bash
# claude-sync-pull.sh — Copia memórias Claude do repositório para o ambiente local.
# Executado pelo hook post-merge e também pelo sincronizador de ambientes.
set -euo pipefail

PROJECT_PATH="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_HASH="$(printf '%s' "$PROJECT_PATH" | tr '/_' '--')"
CLAUDE_MEMORY_DIR="$HOME/.claude/projects/$CLAUDE_HASH/memory"
REPO_MEMORY_DIR="$PROJECT_PATH/.claude/memory"

mkdir -p "$CLAUDE_MEMORY_DIR"

COPIED=0
if [[ -d "$REPO_MEMORY_DIR" ]]; then
    while IFS= read -r -d '' file; do
        cp "$file" "$CLAUDE_MEMORY_DIR/"
        COPIED=$((COPIED + 1))
    done < <(find "$REPO_MEMORY_DIR" -maxdepth 1 -type f -name '*.md' -print0)
fi

echo "✅ claude-sync-pull: $COPIED arquivo(s) restaurado(s) para ~/.claude/"
