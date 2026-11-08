"""Match-scoped quest completion derived from validator rule metadata."""
from __future__ import annotations
from dataclasses import dataclass
from model.rules.base import Rule


@dataclass(frozen=True)
class Quest:
    rule_id: str
    nazev: str
    popis: str
    xp: int


class QuestManager:
    def __init__(self, rules: tuple[Rule, ...]) -> None:
        lookup = {r.id:r for r in rules if r.quest_xp}
        order = ("capture", "castling", "en_passant", "promotion", "check", "checkmate")
        self.quests = tuple(Quest(lookup[key].id,lookup[key].nazev,lookup[key].popis,lookup[key].quest_xp) for key in order if key in lookup)
        self._awarded: set[tuple[str,str]] = set()

    def pridej_odmeny(self, rule_ids: tuple[str, ...], hrac) -> tuple[int, tuple[Quest,...]]:
        found = set(rule_ids)
        awarded: list[Quest] = []
        for quest in self.quests:
            key = (hrac.uzivatel.uzivatelske_jmeno,quest.rule_id)
            if quest.rule_id in found and key not in self._awarded:
                self._awarded.add(key)
                awarded.append(quest)
        return sum(q.xp for q in awarded),tuple(awarded)

    def dokoncil(self, username: str, rule_id: str) -> bool:
        return (username,rule_id) in self._awarded

    def reset_dokonceni(self) -> None:
        self._awarded.clear()
