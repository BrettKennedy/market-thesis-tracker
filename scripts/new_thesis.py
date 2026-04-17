"""Create a new thesis draft from an interactive interview."""

from __future__ import annotations

import json
import re
from pathlib import Path

import typer
import yaml
from rich.console import Console
from thesis_ai import normalize_interview_with_openai, normalized_draft_to_thesis
from thesis_models import Thesis, ThesisStatus

app = typer.Typer(add_completion=False)
console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


def make_thesis_id(title: str) -> str:
    """Create a stable thesis_id from a title."""
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not slug:
        raise ValueError("Thesis title must contain letters or numbers.")
    if slug[0].isdigit():
        slug = f"thesis_{slug}"
    return slug


def _prompt_required_text(message: str) -> str:
    while True:
        value = typer.prompt(message, prompt_suffix=": ").strip()
        if value:
            return value
        console.print("[yellow]This field is required.[/yellow]")


def _prompt_optional_text(message: str, default: str = "") -> str:
    return typer.prompt(message, default=default, prompt_suffix=": ").strip()


def _prompt_list(message: str, item_label: str = "item") -> list[str]:
    console.print(f"[cyan]{message}[/cyan]")
    console.print(
        f"[dim]Enter one {item_label} per line. Press Enter on a blank line to finish.[/dim]"
    )
    values: list[str] = []
    while True:
        value = input("> ").strip()
        if not value:
            break
        values.append(value)
    return values


def _normalize_ticker_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        ticker = value.strip().upper()
        if not ticker:
            continue
        normalized.append(ticker)
    return normalized


def _merge_bucket_members(
    *,
    benchmark: list[str],
    core: list[str],
    torque: list[str],
    canary: list[str],
    remove: list[str],
) -> list[dict[str, object]]:
    benchmark_set = set(_normalize_ticker_list(benchmark))
    role_sets = {
        "core": set(_normalize_ticker_list(core)),
        "torque": set(_normalize_ticker_list(torque)),
        "canary": set(_normalize_ticker_list(canary)),
        "remove": set(_normalize_ticker_list(remove)),
    }

    for role_name in ("core", "torque", "canary"):
        if role_sets["remove"] & role_sets[role_name]:
            overlap = ", ".join(sorted(role_sets["remove"] & role_sets[role_name]))
            raise ValueError(f"Remove tickers cannot also appear in {role_name}: {overlap}")
    if role_sets["remove"] & benchmark_set:
        overlap = ", ".join(sorted(role_sets["remove"] & benchmark_set))
        raise ValueError(f"Remove tickers cannot also appear in benchmark: {overlap}")

    conflicting_roles: list[str] = []
    role_pairs = [("core", "torque"), ("core", "canary"), ("torque", "canary")]
    for left, right in role_pairs:
        overlap = role_sets[left] & role_sets[right]
        if overlap:
            tickers = ", ".join(sorted(overlap))
            conflicting_roles.append(f"{left} vs {right}: {tickers}")
    if conflicting_roles:
        joined = "; ".join(conflicting_roles)
        raise ValueError(f"Tickers may only have one non-benchmark role: {joined}")

    members: list[dict[str, object]] = []
    seen: set[str] = set()

    def add_member(ticker: str, role: str, *, is_benchmark: bool = False) -> None:
        if ticker in seen:
            return
        seen.add(ticker)
        members.append({"ticker": ticker, "role": role, "is_benchmark": is_benchmark})

    for role_name in ("core", "torque", "canary"):
        for ticker in sorted(role_sets[role_name]):
            add_member(ticker, role_name, is_benchmark=ticker in benchmark_set)

    for ticker in sorted(role_sets["remove"]):
        add_member(ticker, "remove")

    benchmark_only = benchmark_set - seen
    for ticker in sorted(benchmark_only):
        add_member(ticker, "benchmark")

    return members


def conduct_thesis_interview() -> dict[str, object]:
    """Collect rough thesis inputs from the operator."""
    console.print("[bold]New Thesis Interview[/bold]")
    console.print(
        "[dim]Capture the rough idea first. AI normalization can sharpen it afterward.[/dim]"
    )

    title = _prompt_required_text("Working thesis title")
    rough_idea = _prompt_required_text("Rough thesis statement")
    why_this_matters = _prompt_optional_text("Why does this matter?", default="")
    mechanism = _prompt_optional_text("What is the economic mechanism?", default="")
    time_horizon = _prompt_optional_text("Time horizon", default="4 to 6 quarters")
    confirmation_signals = _prompt_list("Possible confirming signals", item_label="signal")
    disconfirming_signals = _prompt_list("Possible disconfirming signals", item_label="signal")
    counter_narrative = _prompt_optional_text("Strongest counter-narrative", default="")
    benchmark = _prompt_list("Benchmark tickers", item_label="ticker")
    core = _prompt_list("Core tickers", item_label="ticker")
    torque = _prompt_list("Torque tickers", item_label="ticker")
    canary = _prompt_list("Canary tickers", item_label="ticker")
    remove = _prompt_list("Remove tickers", item_label="ticker")
    research_gaps = _prompt_list("Research gaps or open questions", item_label="question")
    tags = _prompt_list("Optional tags", item_label="tag")

    return {
        "title": title,
        "rough_idea": rough_idea,
        "why_this_matters": why_this_matters,
        "mechanism": mechanism,
        "time_horizon": time_horizon,
        "confirmation_signals": confirmation_signals,
        "disconfirming_signals": disconfirming_signals,
        "counter_narrative": counter_narrative,
        "benchmark": benchmark,
        "core": core,
        "torque": torque,
        "canary": canary,
        "remove": remove,
        "research_gaps": research_gaps,
        "tags": tags,
    }


def build_ai_prompt(interview: dict[str, object], target_status: ThesisStatus) -> str:
    """Render the raw interview into an AI normalization prompt."""
    return json.dumps(
        {
            "operator_interview": interview,
            "instructions": {
                "target_status": target_status,
                "do_not_invent_tickers": True,
                "keep_uncertain_fields_empty": True,
                "preserve_research_gaps": True,
            },
        },
        indent=2,
        sort_keys=True,
    )


def build_manual_thesis(interview: dict[str, object], target_status: ThesisStatus) -> Thesis:
    """Convert the raw interview directly into a thesis draft."""
    title = str(interview["title"]).strip()
    thesis_id = make_thesis_id(title)
    source_notes = [
        "Generated from the thesis intake interview without AI normalization.",
        f"Original rough idea: {str(interview['rough_idea']).strip()}",
    ]

    return Thesis.model_validate(
        {
            "schema_version": 1,
            "thesis_id": thesis_id,
            "title": title,
            "status": target_status,
            "content": {
                "thesis_statement": str(interview["rough_idea"]).strip(),
                "why_this_matters": str(interview["why_this_matters"]).strip(),
                "mechanism": str(interview["mechanism"]).strip(),
                "time_horizon": str(interview["time_horizon"]).strip(),
            },
            "evidence": {
                "confirmation_signals": interview["confirmation_signals"],
                "disconfirming_signals": interview["disconfirming_signals"],
                "counter_narrative": str(interview["counter_narrative"]).strip(),
            },
            "basket": {
                "members": _merge_bucket_members(
                    benchmark=interview["benchmark"],
                    core=interview["core"],
                    torque=interview["torque"],
                    canary=interview["canary"],
                    remove=interview["remove"],
                )
            },
            "working_notes": {
                "research_gaps": interview["research_gaps"],
                "source_notes": source_notes,
                "tags": interview["tags"],
            },
        }
    )


def build_ai_thesis(interview: dict[str, object], target_status: ThesisStatus) -> Thesis:
    """Normalize the raw interview with AI into a thesis draft."""
    prompt_text = build_ai_prompt(interview, target_status)
    normalized = normalize_interview_with_openai(
        prompt_text=prompt_text,
        target_status=target_status,
    )
    thesis_id = make_thesis_id(normalized.title)
    thesis = normalized_draft_to_thesis(
        normalized=normalized,
        thesis_id=thesis_id,
        target_status=target_status,
    )

    source_notes = list(thesis.working_notes.source_notes)
    source_notes.extend(
        [
            "AI-normalized from the thesis intake interview. Review before activation.",
            f"Original rough idea: {str(interview['rough_idea']).strip()}",
        ]
    )
    thesis.working_notes.source_notes = source_notes
    return thesis


def write_thesis_file(thesis: Thesis, output_path: Path) -> None:
    """Persist a thesis YAML file."""
    payload = thesis.model_dump(exclude_none=True)
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def render_thesis_preview(thesis: Thesis) -> str:
    """Render a YAML preview of the thesis file."""
    return yaml.safe_dump(thesis.model_dump(exclude_none=True), sort_keys=False)


@app.command()
def main(
    use_ai: bool = typer.Option(
        True,
        "--use-ai/--no-use-ai",
        help="Use OpenAI to normalize the interview into a structured thesis draft.",
    ),
    target_status: ThesisStatus = typer.Option(
        "draft",
        "--target-status",
        help="Target thesis status for the saved file.",
    ),
    output_dir: Path = typer.Option(
        None,
        help="Optional output directory. Defaults to theses/ under repo root.",
    ),
    overwrite: bool = typer.Option(False, help="Overwrite an existing thesis file if present."),
    yes: bool = typer.Option(False, "--yes", help="Skip the final save confirmation."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview the file without writing it."),
) -> None:
    """Create theses/<thesis_id>.yaml from an interactive interview."""
    interview = conduct_thesis_interview()
    try:
        thesis = build_ai_thesis(interview, target_status) if use_ai else build_manual_thesis(
            interview, target_status
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to build thesis draft:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    resolved_output_dir = output_dir or (BASE_DIR / "theses")
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = resolved_output_dir / f"{thesis.thesis_id}.yaml"

    console.print("[bold]Thesis preview[/bold]")
    console.print(render_thesis_preview(thesis))

    if dry_run:
        console.print(f"[cyan]Dry run:[/cyan] did not write {output_path}")
        return

    if output_path.exists() and not overwrite:
        console.print(f"[red]File already exists:[/red] {output_path}")
        raise typer.Exit(code=1)

    if not yes and not typer.confirm(f"Save thesis draft to {output_path}?", default=True):
        console.print("[yellow]Canceled before writing thesis file.[/yellow]")
        raise typer.Exit(code=1)

    write_thesis_file(thesis, output_path)
    mode = "AI-normalized" if use_ai else "manual"
    console.print(f"[green]Created thesis draft:[/green] {output_path}")
    console.print(f"[cyan]Mode:[/cyan] {mode}")
    if use_ai:
        console.print(
            "[cyan]Reminder:[/cyan] API keys must stay in local environment variables only."
        )


if __name__ == "__main__":
    app()
