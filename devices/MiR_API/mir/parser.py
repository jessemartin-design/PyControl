"""Parse typed MiR commands and recover likely intent from typos."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Iterable, Literal

MatchKind = Literal["exact", "alias", "prefix", "fuzzy", "none"]
CatalogName = Literal["positions", "missions"]

FUZZY_MIN_RATIO = 0.55
PREFIX_MIN_LEN = 2
VALUE_CLOSE_N = 5
VALUE_CLOSE_CUTOFF = 0.55


@dataclass(frozen=True)
class CommandSpec:
    name: str
    catalog: CatalogName | None
    aliases: frozenset[str]
    needs_value: bool
    value_label: str = ""
    description: str = ""


COMMANDS: dict[str, CommandSpec] = {
    "GoToPosition": CommandSpec(
        name="GoToPosition",
        catalog="positions",
        aliases=frozenset(
            {
                "goto",
                "go",
                "gop",
                "gotopos",
                "position",
                "move",
                "moveto",
                "movetoposition",
                "drive",
                "driveto",
            }
        ),
        needs_value=True,
        value_label="position",
        description="Drive to a named map position or marker",
    ),
    "RunMission": CommandSpec(
        name="RunMission",
        catalog="missions",
        aliases=frozenset(
            {
                "run",
                "mission",
                "start",
                "startmission",
                "execute",
                "executemission",
                "queue",
                "queuemission",
            }
        ),
        needs_value=True,
        value_label="mission",
        description="Queue a mission stored on the robot",
    ),
    "ListPositions": CommandSpec(
        name="ListPositions",
        catalog="positions",
        aliases=frozenset({"listpos", "listposition", "showpositions", "positions"}),
        needs_value=False,
        description="List positions stored on the robot",
    ),
    "ListMissions": CommandSpec(
        name="ListMissions",
        catalog="missions",
        aliases=frozenset({"listmis", "listmission", "showmissions", "missions"}),
        needs_value=False,
        description="List missions stored on the robot",
    ),
    "Status": CommandSpec(
        name="Status",
        catalog=None,
        aliases=frozenset({"stat", "state", "info"}),
        needs_value=False,
        description="Show robot status",
    ),
    "Help": CommandSpec(
        name="Help",
        catalog=None,
        aliases=frozenset({"?", "h"}),
        needs_value=False,
        description="Show available commands",
    ),
    "Quit": CommandSpec(
        name="Quit",
        catalog=None,
        aliases=frozenset({"exit", "q"}),
        needs_value=False,
        description="Leave the console",
    ),
}

# Longest phrase first. These are informal spellings, so they always
# count as a correction toward the canonical verb.
PHRASES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("go", "to", "position"), "GoToPosition"),
    (("goto", "position"), "GoToPosition"),
    (("go", "position"), "GoToPosition"),
    (("move", "to"), "GoToPosition"),
    (("go", "to"), "GoToPosition"),
    (("run", "mission"), "RunMission"),
    (("start", "mission"), "RunMission"),
    (("list", "positions"), "ListPositions"),
    (("list", "position"), "ListPositions"),
    (("list", "missions"), "ListMissions"),
    (("list", "mission"), "ListMissions"),
)


@dataclass
class ParsedCommand:
    raw: str
    verb: str | None
    kind: MatchKind
    argument: str | None
    confidence: float
    alternatives: list[str] = field(default_factory=list)

    @property
    def spec(self) -> CommandSpec | None:
        if not self.verb:
            return None
        return COMMANDS[self.verb]

    @property
    def needs_correction(self) -> bool:
        return self.verb is not None and self.kind != "exact"

    @property
    def catalog(self) -> CatalogName | None:
        spec = self.spec
        return spec.catalog if spec else None


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def tokenize(line: str) -> list[str]:
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError:
        tokens = line.split()
    return [token for token in tokens if token]


def parse_line(line: str) -> ParsedCommand:
    raw = line.strip()
    if not raw:
        return ParsedCommand(raw=raw, verb=None, kind="none", argument=None, confidence=0.0)

    tokens = tokenize(raw)
    if not tokens:
        return ParsedCommand(raw=raw, verb=None, kind="none", argument=None, confidence=0.0)

    phrase_verb, consumed = _match_phrase(tokens)
    if phrase_verb:
        argument = " ".join(tokens[consumed:]) or None
        return ParsedCommand(
            raw=raw,
            verb=phrase_verb,
            kind="alias",
            argument=argument,
            confidence=0.9,
        )

    verb, kind, confidence, alternatives = infer_verb(tokens[0])
    argument = " ".join(tokens[1:]) or None
    return ParsedCommand(
        raw=raw,
        verb=verb,
        kind=kind,
        argument=argument,
        confidence=confidence,
        alternatives=alternatives,
    )


def infer_verb(token: str) -> tuple[str | None, MatchKind, float, list[str]]:
    folded = token.casefold()
    compact = normalize(token)

    for name in COMMANDS:
        if folded == name.casefold() or compact == normalize(name):
            return name, "exact", 1.0, []

    scored: list[tuple[str, MatchKind, float]] = []
    for name, spec in COMMANDS.items():
        name_compact = normalize(name)
        best_kind: MatchKind = "none"
        best = 0.0

        if compact in spec.aliases:
            best_kind, best = "alias", 0.93
        elif (
            len(compact) >= PREFIX_MIN_LEN
            and name_compact.startswith(compact)
            and compact != name_compact
        ):
            best_kind, best = "prefix", 0.88 + 0.1 * (len(compact) / len(name_compact))
        else:
            ratios = [SequenceMatcher(None, compact, name_compact).ratio()]
            ratios.extend(SequenceMatcher(None, compact, alias).ratio() for alias in spec.aliases)
            ratio = max(ratios)
            if ratio >= FUZZY_MIN_RATIO:
                best_kind, best = "fuzzy", ratio

        if best_kind != "none":
            scored.append((name, best_kind, best))

    if not scored:
        return None, "none", 0.0, []

    scored.sort(key=lambda item: item[2], reverse=True)
    top_name, top_kind, top_score = scored[0]
    close = [
        name
        for name, _, score in scored
        if top_score - score <= 0.08 and score >= FUZZY_MIN_RATIO
    ]
    # Prefixes like "list" or "go" can sit equally well on two commands.
    if len(close) > 1 and top_kind in {"prefix", "fuzzy"}:
        return None, "none", top_score, close
    return top_name, top_kind, top_score, [name for name, _, _ in scored[1:3]]


def resolve_value(
    name: str,
    choices: Iterable[str],
    *,
    n: int = VALUE_CLOSE_N,
    cutoff: float = VALUE_CLOSE_CUTOFF,
) -> tuple[str | None, list[str]]:
    """Return (exact_or_unique_match, close_suggestions)."""
    wanted = name.casefold().strip()
    catalog = list(dict.fromkeys(choices))
    if not wanted:
        return None, catalog

    exact = [item for item in catalog if item.casefold() == wanted]
    if len(exact) == 1:
        return exact[0], []
    if len(exact) > 1:
        return None, exact

    prefixes = [item for item in catalog if item.casefold().startswith(wanted)]
    if len(prefixes) == 1:
        return prefixes[0], []

    ranked = sorted(
        catalog,
        key=lambda item: SequenceMatcher(None, wanted, item.casefold()).ratio(),
        reverse=True,
    )
    close = [
        item
        for item in ranked
        if SequenceMatcher(None, wanted, item.casefold()).ratio() >= cutoff
    ][:n]
    return None, close or catalog[:n]


def help_text() -> str:
    lines = [
        "Commands:",
        "  GoToPosition <name>   Drive to a map position/marker",
        "  RunMission <name>     Queue a mission stored on the robot",
        "  ListPositions         Show positions from the robot",
        "  ListMissions          Show missions from the robot",
        "  Status                Show robot status",
        "  Help                  Show this message",
        "  Quit                  Exit",
        "",
        "Examples:",
        "  GoToPosition Station2",
        "  RunMission Charge",
        "  RunMission Station2",
        "",
        "Command names are matched even if you shorten or misspell them.",
        "Suggestions then list only the matching values from the robot",
        "(positions for GoToPosition, missions for RunMission).",
    ]
    return "\n".join(lines)


def _match_phrase(tokens: list[str]) -> tuple[str | None, int]:
    lowered = [token.casefold() for token in tokens]
    for phrase, verb in PHRASES:
        if lowered[: len(phrase)] == list(phrase):
            return verb, len(phrase)
    return None, 0
