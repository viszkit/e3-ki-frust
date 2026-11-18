"""Fixed study material and shared experiment rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Condition = Literal["keine_hilfe", "statische_hilfe", "ki_chat"]

CONDITIONS: tuple[Condition, ...] = ("keine_hilfe", "statische_hilfe", "ki_chat")
CONDITION_LABELS: dict[Condition, str] = {
    "keine_hilfe": "Keine Hilfe",
    "statische_hilfe": "Statische Hilfe",
    "ki_chat": "KI-Chat",
}


@dataclass(frozen=True)
class Riddle:
    number: int
    title: str
    prompt: str
    entities: tuple[str, str, str, str]
    targets: tuple[str, str, str, str]
    solution: tuple[tuple[str, str], tuple[str, str], tuple[str, str], tuple[str, str]]
    options: tuple[str, str, str, str]
    correct_option: int
    hints: tuple[str, str, str]


# Each item contains exactly four objects and four target values. The third hint
# gives the complete, declared mapping so that it is auditable and reproducible.
RIDDLES: tuple[Riddle, ...] = (
    Riddle(
        1,
        "Die Sitzreihe",
        "Anna, Ben, Cem und Daria sitzen auf vier Plätzen von links nach rechts. "
        "Daria sitzt ganz rechts. Ben sitzt nicht außen. Cem sitzt unmittelbar rechts von Anna. "
        "Wer sitzt ganz links?",
        ("Anna", "Ben", "Cem", "Daria"),
        ("Platz 1", "Platz 2", "Platz 3", "Platz 4"),
        (("Anna", "Platz 1"), ("Cem", "Platz 2"), ("Ben", "Platz 3"), ("Daria", "Platz 4")),
        ("Anna", "Ben", "Cem", "Daria"),
        0,
        (
            "Zeichne vier Plätze und trage zuerst Daria auf Platz 4 ein.",
            "Anna und Cem bilden ein Paar: Cem sitzt direkt rechts von Anna.",
            "Lösung: Anna - Cem - Ben - Daria. Anna sitzt ganz links.",
        ),
    ),
    Riddle(
        2,
        "Die Vorträge",
        "Vier Vorträge finden nacheinander statt: Klima, Robotik, Sprache und Medizin. "
        "Sprache findet unmittelbar vor Medizin statt. Robotik findet nach Klima statt, aber nicht zuletzt. "
        "Klima findet vor Sprache statt. Welcher Vortrag findet an zweiter Stelle statt?",
        ("Klima", "Robotik", "Sprache", "Medizin"),
        ("Slot 1", "Slot 2", "Slot 3", "Slot 4"),
        (("Klima", "Slot 1"), ("Robotik", "Slot 2"), ("Sprache", "Slot 3"), ("Medizin", "Slot 4")),
        ("Klima", "Robotik", "Sprache", "Medizin"),
        1,
        (
            "Behandle Sprache und Medizin als festes Zweierpaar.",
            "Robotik darf nicht zuletzt stattfinden und muss nach Klima liegen.",
            "Lösung: Klima - Robotik - Sprache - Medizin. Robotik ist an zweiter Stelle.",
        ),
    ),
    Riddle(
        3,
        "Die Taschen",
        "Lea, Malik, Nora und Omar haben jeweils eine Tasche in Rot, Blau, Grün oder Gelb. "
        "Malik hat Blau, Omar hat Gelb, Nora hat weder Grün noch Gelb und Lea hat nicht Rot. "
        "Welche Farbe hat Leas Tasche?",
        ("Lea", "Malik", "Nora", "Omar"),
        ("Rot", "Blau", "Grün", "Gelb"),
        (("Lea", "Grün"), ("Malik", "Blau"), ("Nora", "Rot"), ("Omar", "Gelb")),
        ("Rot", "Blau", "Grün", "Gelb"),
        2,
        (
            "Streiche zuerst die bereits fest vergebenen Farben Blau und Gelb.",
            "Für Lea und Nora bleiben Rot und Grün; Lea darf nicht Rot haben.",
            "Lösung: Lea Grün, Malik Blau, Nora Rot und Omar Gelb.",
        ),
    ),
    Riddle(
        4,
        "Der vierstellige Code",
        "Ein Code besteht aus den Ziffern 1, 2, 3 und 4, jede genau einmal. "
        "Die 1 steht unmittelbar rechts von der 4. Die 2 steht unmittelbar links von der 3. "
        "Die 4 steht links von der 2. Wie lautet der Code?",
        ("1", "2", "3", "4"),
        ("Position 1", "Position 2", "Position 3", "Position 4"),
        (("4", "Position 1"), ("1", "Position 2"), ("2", "Position 3"), ("3", "Position 4")),
        ("4123", "2341", "4213", "2134"),
        0,
        (
            "Die Regeln bilden zwei feste Paare: 4-1 und 2-3.",
            "Die 4 muss links vom Paar 2-3 stehen.",
            "Lösung: 4123. Die Reihenfolge ist 4 - 1 - 2 - 3.",
        ),
    ),
    Riddle(
        5,
        "Die Pflanzen",
        "Basilikum, Farn, Kaktus und Orchidee stehen in dieser Reihenfolge in einem Regal mit vier Plätzen. "
        "Basilikum steht unmittelbar links vom Kaktus. Orchidee steht unmittelbar links vom Farn. "
        "Der Kaktus steht links von der Orchidee. Welche Pflanze steht auf Platz 2?",
        ("Basilikum", "Farn", "Kaktus", "Orchidee"),
        ("Platz 1", "Platz 2", "Platz 3", "Platz 4"),
        (("Basilikum", "Platz 1"), ("Kaktus", "Platz 2"), ("Orchidee", "Platz 3"), ("Farn", "Platz 4")),
        ("Basilikum", "Farn", "Kaktus", "Orchidee"),
        2,
        (
            "Basilikum-Kaktus und Orchidee-Farn sind jeweils feste Nachbarpaare.",
            "Das Paar Basilikum-Kaktus muss vor dem Paar Orchidee-Farn stehen.",
            "Lösung: Basilikum - Kaktus - Orchidee - Farn. Der Kaktus steht auf Platz 2.",
        ),
    ),
    Riddle(
        6,
        "Die Zugtickets",
        "Eva, Finn, Gina und Hugo fahren an vier verschiedenen Tagen: Montag bis Donnerstag. "
        "Gina fährt am Mittwoch. Eva fährt vor Finn, und Finn fährt vor Hugo. Hugo fährt nicht am Dienstag. "
        "An welchem Tag fährt Eva?",
        ("Eva", "Finn", "Gina", "Hugo"),
        ("Montag", "Dienstag", "Mittwoch", "Donnerstag"),
        (("Eva", "Montag"), ("Finn", "Dienstag"), ("Gina", "Mittwoch"), ("Hugo", "Donnerstag")),
        ("Montag", "Dienstag", "Mittwoch", "Donnerstag"),
        0,
        (
            "Gina belegt bereits den Mittwoch.",
            "Eva, Finn und Hugo müssen in dieser Reihenfolge auf die übrigen Tage verteilt werden.",
            "Lösung: Eva Montag, Finn Dienstag, Gina Mittwoch und Hugo Donnerstag.",
        ),
    ),
    Riddle(
        7,
        "Die Poster",
        "Vier Poster hängen untereinander: Musik, Sport, Technik und Kunst. "
        "Technik hängt unmittelbar über Kunst. Musik hängt über Sport. Sport hängt nicht ganz unten. "
        "Welches Poster hängt ganz oben?",
        ("Musik", "Sport", "Technik", "Kunst"),
        ("Position 1", "Position 2", "Position 3", "Position 4"),
        (("Musik", "Position 1"), ("Sport", "Position 2"), ("Technik", "Position 3"), ("Kunst", "Position 4")),
        ("Musik", "Sport", "Technik", "Kunst"),
        0,
        (
            "Technik und Kunst bilden ein festes Zweierpaar.",
            "Musik muss über Sport hängen; Sport darf nicht die letzte Position haben.",
            "Lösung: Musik - Sport - Technik - Kunst. Musik hängt ganz oben.",
        ),
    ),
    Riddle(
        8,
        "Die Schließfächer",
        "In vier Schließfächern A, B, C und D liegen ein Schlüssel, eine Karte, ein Stift und eine Münze. "
        "Die Karte liegt in D. Der Schlüssel liegt links vom Stift. Der Stift liegt nicht in C. "
        "Die Münze liegt nicht in A. Was liegt in Fach A?",
        ("Schlüssel", "Karte", "Stift", "Münze"),
        ("Fach A", "Fach B", "Fach C", "Fach D"),
        (("Schlüssel", "Fach A"), ("Stift", "Fach B"), ("Münze", "Fach C"), ("Karte", "Fach D")),
        ("Schlüssel", "Karte", "Stift", "Münze"),
        0,
        (
            "Karte und Münze können nicht in Fach A liegen.",
            "Der Stift kann weder in C noch in D liegen; der Schlüssel muss links von ihm sein.",
            "Lösung: Schlüssel A, Stift B, Münze C und Karte D. In A liegt der Schlüssel.",
        ),
    ),
)


def aid_is_available(condition: Condition, riddle_number: int) -> bool:
    return condition != "keine_hilfe" and riddle_number <= 4


def is_correct(riddle: Riddle, selected_option: int | None) -> bool:
    return selected_option == riddle.correct_option
