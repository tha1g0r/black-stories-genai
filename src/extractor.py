"""Classify the minimum discoveries of each mystery card with Gemini."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from google.genai import types


DEFAULT_INPUT_DIR = Path("content/cartas-enigma/run-extractor")
DEFAULT_OUTPUT_DIR = Path("content/cartas-enigma")
DEFAULT_PROMPT = Path("prompts/classificar-descobertas.md")
DEFAULT_MODEL = "gemini-2.5-flash-lite"
DIFFICULTY_PATTERN = re.compile(
    r"\*\*Nível de dificuldade:\*\*\s*(Fácil|Médio|Difícil)",
    re.IGNORECASE,
)
REQUIRED_HEADINGS = (
    "### Descobertas mínimas",
    "### Detalhes não obrigatórios",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classifica as descobertas mínimas das cartas-enigma."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument(
        "--model",
        default=None,
        help="Modelo Gemini a utilizar.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Intervalo, em segundos, entre chamadas à API.",
    )
    return parser.parse_args()


def difficulty_for(card: str, path: Path) -> str:
    match = DIFFICULTY_PATTERN.search(card)
    if not match:
        raise ValueError(f"Nível de dificuldade ausente ou inválido: {path}")

    return {
        "fácil": "facil",
        "médio": "medio",
        "difícil": "dificil",
    }[match.group(1).lower()]


def validate_classification(classification: str, path: Path) -> None:
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in classification]
    if missing:
        headings = ", ".join(missing)
        raise ValueError(f"Resposta inválida para {path}: faltam {headings}.")


def classify_card(
    client: genai.Client,
    model: str,
    prompt: str,
    card: str,
    path: Path,
) -> str:
    response = client.models.generate_content(
        model=model,
        contents=card,
        config=types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.2,
        ),
    )
    classification = response.text.strip() if response.text else ""
    validate_classification(classification, path)
    return classification


def write_processed_card(
    output_dir: Path,
    difficulty: str,
    source_path: Path,
    card: str,
    classification: str,
) -> Path:
    destination_dir = output_dir / difficulty
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source_path.name
    processed = (
        f"{card.rstrip()}\n\n"
        "## Classificação gerada pelo extractor\n\n"
        f"{classification.rstrip()}\n"
    )
    destination.write_text(processed, encoding="utf-8")
    return destination


def run(args: argparse.Namespace) -> int:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY não está configurada no arquivo .env.", file=sys.stderr)
        return 2
    if args.delay < 0:
        print("--delay não pode ser negativo.", file=sys.stderr)
        return 2
    if not args.input_dir.is_dir():
        print(f"Diretório de entrada não encontrado: {args.input_dir}", file=sys.stderr)
        return 2
    if not args.prompt.is_file():
        print(f"Prompt não encontrado: {args.prompt}", file=sys.stderr)
        return 2

    prompt = args.prompt.read_text(encoding="utf-8")
    cards = sorted(args.input_dir.glob("*.md"))
    if not cards:
        print(f"Nenhuma carta Markdown encontrada em {args.input_dir}.", file=sys.stderr)
        return 2

    client = genai.Client(api_key=api_key)
    model = args.model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    failures = 0

    for index, card_path in enumerate(cards):
        try:
            card = card_path.read_text(encoding="utf-8")
            difficulty = difficulty_for(card, card_path)
            classification = classify_card(client, model, prompt, card, card_path)
            destination = write_processed_card(
                args.output_dir,
                difficulty,
                card_path,
                card,
                classification,
            )
            print(f"[OK] {card_path} -> {destination}")
        except (OSError, ValueError, errors.APIError) as error:
            failures += 1
            print(f"[ERRO] {card_path}: {error}", file=sys.stderr)

        if index < len(cards) - 1 and args.delay:
            time.sleep(args.delay)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
