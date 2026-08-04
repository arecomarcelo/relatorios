#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.text import Text

# Configurações
console = Console()
ROOT_DIR = Path(".")


def run_command(command: str, success_msg: str, error_msg: str) -> bool:
    """Executa um comando e exibe o resultado formatado."""
    console.print(f"\n[bold]Executando:[/bold] [cyan]{command}[/cyan]")

    with Progress(transient=True) as progress:
        task = progress.add_task("[yellow]Processando...", total=1)
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=ROOT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            progress.update(task, completed=1)
            console.print(
                Panel.fit(
                    Text.from_ansi(result.stdout),
                    title=f"[green]✓ {success_msg}",
                    border_style="green",
                )
            )
            return True
        except subprocess.CalledProcessError as e:
            progress.update(task, completed=1)
            console.print(
                Panel.fit(
                    Text.from_ansi(e.stderr),
                    title=f"[red]✗ {error_msg}",
                    border_style="red",
                )
            )
            return False


def check_dependencies():
    """Verifica se as dependências estão instaladas corretamente"""
    console.print("\n[yellow]🔍 Verificando dependências...[/yellow]")

    try:
        import black

        console.print("[green]✅ Black instalado[/green]")
        black_ok = True
    except ImportError:
        console.print("[red]❌ Black não encontrado[/red]")
        black_ok = False

    try:
        import mypy

        console.print("[green]✅ Mypy instalado[/green]")
        mypy_ok = True
    except ImportError:
        console.print("[red]❌ Mypy não encontrado[/red]")
        mypy_ok = False

    if not (black_ok and mypy_ok):
        console.print(
            f"\n[yellow]⚠️  Execute primeiro: {sys.executable} fix_formatters.py[/yellow]"
        )
        return False

    return True


def main():
    console.print(
        Panel.fit(
            "[bold]🔧 Formatador de Código[/bold]",  # Adicionado símbolo de registro
            subtitle="HauxTech®",  # Adicionado emoji de engrenagem
            border_style="blue",
        )
    )

    # Verificar dependências primeiro
    if not check_dependencies():
        sys.exit(1)

    # Formatação com verificações mais robustas
    black_success = run_command(
        f"{sys.executable} -m black . --line-length=88 --skip-string-normalization",
        "Black: Formatação concluída com sucesso!",
        "Black: Erro na formatação!",
    )

    isort_success = run_command(
        f"{sys.executable} -m isort . --profile black",
        "Isort: Imports organizados com sucesso!",
        "Isort: Erro ao organizar imports!",
    )

    # Verificação de tipos usando configuração do mypy.ini
    console.print(
        "\n[yellow]⚙️  Executando Mypy com configuração do projeto...[/yellow]"
    )
    mypy_success = run_command(
        f"{sys.executable} -m mypy . --config-file=mypy.ini",
        "Mypy: Verificação de tipos concluída sem erros!",
        "Mypy: Erros de tipo encontrados!",
    )

    console.print("\n[bold]📊 Resumo:[/bold]")
    console.print(
        f"• Black: {'[green]Sucesso[/green]' if black_success else '[red]Falha[/red]'}"
    )
    console.print(
        f"• Isort: {'[green]Sucesso[/green]' if isort_success else '[red]Falha[/red]'}"
    )
    console.print(
        f"• Mypy: {'[green]Sucesso[/green]' if mypy_success else '[red]Falha[/red]'}"
    )

    if not (black_success and isort_success and mypy_success):
        sys.exit(1)


if __name__ == "__main__":
    main()
