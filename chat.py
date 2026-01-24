#!/usr/bin/env python3
"""
Ollama Local Chat Application
A simple chat interface using Ollama for local LLM inference.
"""

import sys
import ollama
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()


class ChatBot:
    def __init__(self, model_name: str):
        """Initialize the chatbot with a model name."""
        self.model_name = model_name
        self.conversation_history = []

    def verify_ollama(self):
        """Verify Ollama is running and model is available."""
        console.print(f"[yellow]Checking Ollama connection and model {self.model_name}...[/yellow]")
        try:
            ollama.list()
            console.print("[green]Connected to Ollama successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error connecting to Ollama: {e}[/red]")
            console.print("[yellow]Make sure Ollama is running: ollama serve[/yellow]")
            sys.exit(1)

    def generate_response(self, user_input: str) -> str:
        """Generate a response from the model."""
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history
            )

            assistant_message = response['message']['content']
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return assistant_message
        except Exception as e:
            return f"Error generating response: {e}"

    def chat(self):
        """Run the interactive chat loop."""
        console.print(Panel.fit(
            "[bold cyan]Ollama Local Chat[/bold cyan]\n"
            f"Model: {self.model_name}\n"
            "Type 'quit', 'exit', or 'q' to end the conversation\n"
            "Type 'clear' to clear conversation history",
            border_style="cyan"
        ))

        while True:
            try:
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    console.print("[yellow]Conversation history cleared.[/yellow]")
                    continue

                if not user_input.strip():
                    continue

                response = self.generate_response(user_input)
                console.print(f"\n[bold cyan]Assistant[/bold cyan]: {response}")

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ollama Local Chat Application")
    parser.add_argument(
        "--model",
        type=str,
        default="nemotron-3-nano:latest",
        help="Ollama model name (default: nemotron-3-nano:latest)"
    )

    args = parser.parse_args()

    chatbot = ChatBot(args.model)
    chatbot.verify_ollama()
    chatbot.chat()


if __name__ == "__main__":
    main()
