import argparse
import sys
from pathlib import Path
from typing import Optional

from seq_llm.config import Config
from seq_llm.core.server_manager import ServerManager


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="seq-llm",
        description="Sequence-LLM: Unified interface for managing LLM servers",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start an LLM server")
    start_parser.add_argument(
        "model",
        help="Model name to start",
    )
    start_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file (default: seq_llm.yaml)",
    )
    start_parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Override the port from config",
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop an LLM server")
    stop_parser.add_argument(
        "model",
        help="Model name to stop",
    )
    stop_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file (default: seq_llm.yaml)",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show server status")
    status_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file (default: seq_llm.yaml)",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    list_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file (default: seq_llm.yaml)",
    )

    return parser


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file."""
    if config_path is None:
        config_path = Path("seq_llm.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    return Config.from_file(config_path)


def cmd_start(args: argparse.Namespace) -> int:
    """Handle the start command."""
    try:
        config = load_config(args.config)
        model_config = config.get_model(args.model)

        if model_config is None:
            print(
                f"Error: Model '{args.model}' not found in configuration",
                file=sys.stderr,
            )
            return 1

        port = args.port or model_config.port
        manager = ServerManager(model_config, port)

        print(f"Starting model: {args.model}")
        manager.start()
        print(f"Model '{args.model}' started successfully on port {port}")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error starting model: {e}", file=sys.stderr)
        return 1


def cmd_stop(args: argparse.Namespace) -> int:
    """Handle the stop command."""
    try:
        config = load_config(args.config)
        model_config = config.get_model(args.model)

        if model_config is None:
            print(
                f"Error: Model '{args.model}' not found in configuration",
                file=sys.stderr,
            )
            return 1

        manager = ServerManager(model_config, model_config.port)

        print(f"Stopping model: {args.model}")
        manager.stop()
        print(f"Model '{args.model}' stopped successfully")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error stopping model: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Handle the status command."""
    try:
        config = load_config(args.config)

        print("Server Status:")
        print("-" * 50)

        for model_name, model_config in config.models.items():
            manager = ServerManager(model_config, model_config.port)
            is_running = manager.is_running()
            status = "✓ Running" if is_running else "✗ Stopped"
            print(f"{model_name:20} {status:20} (port: {model_config.port})")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error checking status: {e}", file=sys.stderr)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the list command."""
    try:
        config = load_config(args.config)

        print("Available Models:")
        print("-" * 50)

        if not config.models:
            print("No models configured")
            return 0

        for model_name, model_config in config.models.items():
            print(f"{model_name:20} (port: {model_config.port})")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error listing models: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "start":
        return cmd_start(args)
    elif args.command == "stop":
        return cmd_stop(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "list":
        return cmd_list(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
