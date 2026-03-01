#!/usr/bin/env python3
"""CLI entry point: interactive Sequence-LLM shell for managing local LLMs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from seq_llm.config import Config, ensure_default_config, save_first_run_setup
from seq_llm.core.api_client import APIClient
from seq_llm.core.command_builder import build_llama_server_command
from seq_llm.core.server_manager import ServerManager
from seq_llm.models.scanner import discover_models
from seq_llm.safety.token_guard import ensure_within_ctx

console = Console()
app = typer.Typer(help="Sequence-LLM: CLI for managing local LLMs (llama-server)")


# --- State management -------------------------------------------------------
class CLIState:
    """Transient state during a CLI session."""

    def __init__(self):
        self.config: Config | None = None
        self.config_path: Optional[Path] = None
        self.manager: ServerManager | None = None
        self.active_profile: str | None = None
        self.conversation: List[dict] = []  # Chat history

    def load_config(self, path: Optional[Path] = None) -> bool:
        """Load config from file or create default."""
        try:
            if path is None:
                config_path = ensure_default_config()
            else:
                config_path = Path(path)
                if not config_path.exists():
                    console.print(f"[red]Error: config file not found: {config_path}")
                    return False
            self.config = Config.from_yaml(config_path)
            self.config_path = config_path
            return True
        except Exception as e:
            console.print(f"[red]Error loading config: {e}")
            return False

    def start_profile(self, profile_name: str) -> bool:
        """Start a profile (stop any existing server first)."""
        if not self.config:
            console.print("[red]Error: config not loaded")
            return False

        profile = self.config.get_model(profile_name)
        if not profile:
            console.print(f"[red]Error: profile '{profile_name}' not found")
            return False

        # Validate llama_server path is configured
        if not self.config.llama_server:
            console.print("[red]Error: llama_server path not configured")
            return False

        # Validate llama_server executable exists
        if not Path(self.config.llama_server).exists():
            console.print(
                f"[red]Error: llama_server not found at {self.config.llama_server}\n"
                f"[yellow]Please update config at {self.config_path} with correct path"
            )
            return False

        # Validate model file exists
        if not Path(profile.endpoint).exists():
            console.print(
                f"[red]Error: model file not found at {profile.endpoint}\n"
                f"[yellow]Please verify model_path in config"
            )
            return False

        had_active_profile = self.active_profile is not None

        # Stop existing server if running
        if self.manager:
            with Live(Spinner("dots", text="Stopping server..."), console=console):
                self.manager.stop()
            self.manager = None
            self.active_profile = None

        # Build command args from profile config
        try:
            cmd = build_llama_server_command(
                self.config.llama_server,
                profile,
                self.config.defaults,
            )
        except Exception as e:
            console.print(f"[red]Error building command: {e}")
            return False

        self.manager = ServerManager(llama_server_bin=self.config.llama_server)

        # Start the server and wait for readiness
        console.print(f"[cyan]Starting {profile.name}...")
        console.print(f"[dim]Loading model from {profile.endpoint}")
        try:
            startup_timeout = 300 if not had_active_profile else 120
            self.manager.start_cmd(
                cmd=cmd,
                port=profile.port,
                startup_timeout=startup_timeout,
            )
        except (FileNotFoundError, TimeoutError) as e:
            console.print(f"[red]Error: {e}")
            self.manager.stop()
            self.manager = None
            return False

        self.active_profile = profile_name
        console.print(f"[green]✓ {profile.name} started on port {profile.port}")
        return True

    def show_status(self):
        """Display active server status."""
        if not self.active_profile or not self.manager:
            console.print("[yellow]No model running")
            return

        profile = self.config.get_model(self.active_profile)
        if not profile:
            return

        client = APIClient(base_url=f"http://127.0.0.1:{profile.port}")
        is_healthy = client.health_check()
        client.close()

        status_text = f"Active: {profile.name}\n"
        status_text += f"Port: {profile.port}\n"
        status_text += f"Health: {'✓ Ready' if is_healthy else '✗ Not ready'}"

        console.print(Panel(status_text, title="[bold]Server Status", border_style="green"))


state = CLIState()


def _is_first_run_needed(config: Config) -> bool:
    """Return True when required startup fields are missing."""
    if not config.llama_server:
        return True
    return config.get_model("brain") is None or config.get_model("coder") is None


def run_first_time_setup() -> bool:
    """Interactive first-run setup for llama_server and required profiles."""
    if not state.config_path:
        return False

    console.print("[yellow]First-time setup required.[/yellow]")

    llama_server = console.input("[blue]Path to llama-server executable[/blue]> ").strip()
    if not llama_server:
        console.print("[red]Error: llama-server path is required for first-run setup")
        return False

    console.print("[cyan]Scanning for model files...[/cyan]")
    candidates = discover_models()
    if not candidates:
        console.print("[red]No candidate model files were discovered")
        return False

    table = Table(title="Discovered Models")
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Path", style="green")
    table.add_column("Size (GB)", style="magenta", justify="right")
    for idx, model in enumerate(candidates, start=1):
        table.add_row(str(idx), str(model.get("path", "")), str(model.get("size_gb", "?")))
    console.print(table)

    assignments: dict[str, str] = {}
    for profile_name in ("brain", "coder"):
        choice = console.input(f"[blue]Select model # for '{profile_name}'[/blue]> ").strip()
        try:
            selected_index = int(choice) - 1
        except ValueError:
            console.print(f"[red]Invalid selection for '{profile_name}': {choice}")
            return False

        if selected_index < 0 or selected_index >= len(candidates):
            console.print(f"[red]Selection out of range for '{profile_name}': {choice}")
            return False
        assignments[profile_name] = str(candidates[selected_index]["path"])

    save_first_run_setup(
        path=state.config_path,
        llama_server=llama_server,
        assignments=assignments,
    )
    console.print(f"[green]✓ Saved first-run config to {state.config_path}")

    # Reload updated config then continue normal startup.
    return state.load_config(state.config_path)


# --- Main interactive loop --------------------------------------------------
def main():
    """Main interactive REPL."""
    # Load config (create default if missing)
    console.print("[cyan]Sequence-LLM v0.2")
    if not state.load_config():
        console.print("[red]Failed to load configuration")
        raise typer.Exit(1)

    if _is_first_run_needed(state.config):
        if not run_first_time_setup():
            console.print("[red]Failed first-time setup")
            raise typer.Exit(1)

    # Auto-start brain profile
    if state.config.get_model("brain"):
        console.print("[cyan]Attempting to start 'brain' profile...")
        if not state.start_profile("brain"):
            console.print("[yellow]Warning: 'brain' profile failed to start")
    else:
        console.print("[yellow]Warning: 'brain' profile not found in config")

    # Interactive loop
    console.print("[cyan]Ready for input. Commands: /brain, /coder, /status, /clear, /quit, /exit")

    while True:
        try:
            user_input = console.input("[blue]You[/blue]> ").strip()
        except EOFError:
            break

        if not user_input:
            continue

        # Command dispatch
        if user_input.startswith("/"):
            cmd = user_input[1:].lower()

            if cmd == "brain":
                state.start_profile("brain")
            elif cmd == "coder":
                state.start_profile("coder")
            elif cmd == "status":
                state.show_status()
            elif cmd == "clear":
                state.conversation = []
                console.print("[cyan]Conversation history cleared")
            elif cmd in ("quit", "exit"):
                console.print("[cyan]Goodbye!")
                break
            else:
                console.print(f"[yellow]Unknown command: /{cmd}")
        else:
            # Chat message: send to active model
            if not state.active_profile or not state.manager:
                console.print("[red]ERROR: No model running. Use /brain or /coder first.")
                continue

            # Add user message to history
            state.conversation.append({"role": "user", "content": user_input})

            # Send conversation to active model endpoint
            profile = state.config.get_model(state.active_profile)
            if not profile:
                console.print("[red]ERROR: Active profile not found in configuration")
                continue

            assistant_response = ""
            # ---- Token safety guard ----
            trimmed_messages, fits = ensure_within_ctx(
                state.conversation,
                profile.ctx_size if hasattr(profile, "ctx_size") else 4096,
            )

            if not fits:
                console.print("[yellow]Warning: conversation trimmed to fit context window")

            try:
                with APIClient(base_url=f"http://127.0.0.1:{profile.port}") as client:
                    for token in client.stream_chat(trimmed_messages, model=profile.name):
                        console.print(token, end="")
                        assistant_response += token
                    console.print("")
            except Exception as e:
                console.print(f"[red]ERROR: Failed to stream chat: {e}")
                continue

            if assistant_response:
                state.conversation = trimmed_messages
                state.conversation.append({"role": "assistant", "content": assistant_response})


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[cyan]Interrupted by user")
        if state.manager:
            state.manager.stop()
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}")
        if state.manager:
            state.manager.stop()
        sys.exit(1)
