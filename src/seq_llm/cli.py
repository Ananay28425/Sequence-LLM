#!/usr/bin/env python3
"""CLI entry point: interactive Sequence-LLM shell for managing local LLMs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.spinner import Spinner
from rich.live import Live

from seq_llm.config import Config, ensure_default_config, get_default_config_path
from seq_llm.core.server_manager import ServerManager
from seq_llm.core.api_client import APIClient
from seq_llm.core.command_builder import build_llama_server_command

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

        # Stop existing server if running
        if self.manager:
            with Live(Spinner("dots", text="Stopping server..."), console=console):
                self.manager.stop()
            self.manager = None
            self.active_profile = None

        # Build command from profile config
        try:
            cmd = build_llama_server_command(
                self.config.llama_server,
                profile,
                self.config.defaults,
            )
        except Exception as e:
            console.print(f"[red]Error building command: {e}")
            return False

        self.manager = ServerManager()

        self.manager.start(
            model_path=profile.endpoint,
            port=profile.port,
            args=profile.to_command_args()
        )


        # Start the server and wait for readiness
        # First startup can take longer as model needs to load
        console.print(f"[cyan]Starting {profile.name}...")
        console.print(f"[dim]Loading model from {profile.endpoint}")
        try:
            self.manager.start()
        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}")
            return False

        # Extended timeout for first startup (model loading can take time)
        startup_timeout = 120 if not self.active_profile else 60
        console.print(f"[dim]Waiting for server ready (timeout: {startup_timeout}s)...")
        ready = self.manager.wait_for_ready(timeout=startup_timeout)

        if not ready:
            console.print(
                f"[red]Error: {profile.name} failed to start within {startup_timeout}s\n"
                f"[yellow]Make sure:\n"
                f"  1. Model file exists: {profile.endpoint}\n"
                f"  2. Port {profile.port} is not in use\n"
                f"  3. System has enough RAM/resources"
            )
            self.manager.stop()
            self.manager = None
            return False

        self.active_profile = profile_name
        console.print(f"[green]✓ {profile.name} started on port {self.manager.get_port()}")
        return True

    def show_status(self):
        """Display active server status."""
        if not self.active_profile or not self.manager:
            console.print("[yellow]No model running")
            return

        profile = self.config.get_model(self.active_profile)
        if not profile:
            return

        status_text = f"Active: {profile.name}\n"
        status_text += f"Port: {self.manager.get_port()}\n"
        status_text += f"Health: {'✓ Ready' if self.manager.is_ready() else '✗ Not ready'}"

        console.print(
            Panel(status_text, title="[bold]Server Status", border_style="green")
        )


state = CLIState()


# --- Main interactive loop --------------------------------------------------
def main():
    """Main interactive REPL."""
    # Load config (create default if missing)
    console.print("[cyan]Sequence-LLM v0.1")
    if not state.load_config():
        console.print("[red]Failed to load configuration")
        raise typer.Exit(1)

    # Auto-start brain profile
    if state.config.get_model("brain"):
        console.print("[cyan]Attempting to start 'brain' profile...")
        if not state.start_profile("brain"):
            console.print("[yellow]Warning: 'brain' profile failed to start")
    else:
        console.print("[yellow]Warning: 'brain' profile not found in config")

    # Interactive loop
    console.print(
        "[cyan]Ready for input. Commands: /brain, /coder, /status, /clear, /quit, /exit"
    )

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

            # Send to model (mock for now)
            profile = state.config.get_model(state.active_profile)
            user_input = input(f"{profile.name}> ")

            # In real implementation, would use APIClient to stream chat
            # For now just echo (placeholder)
            console.print(f"(echo) {user_input}")


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

