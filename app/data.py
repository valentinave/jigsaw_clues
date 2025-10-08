from __future__ import annotations

from collections.abc import Iterable
from typing import Dict, List

from .models.game import Game


def _game(game_id: str, label: str, room: str, video: str, targets: Iterable[str]):
    return Game(id=game_id, label=label, room=room, video=video, default_targets=list(targets))


ROOM_GROUPS: Dict[str, dict] = {
    "boilerroom": {
        "label": "Boiler Room",
        "targets": ["boilerroom"],
        "games": [
            _game("ALL_BOILER", "All — Boiler Intro", "Boiler Room", "ALL_BOILER.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_DEGETE", "All — Fingers", "Boiler Room", "ALL_DEGETE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_HAPPY", "All — Happy", "Boiler Room", "ALL_HAPPY.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("BR_CARABINA", "Carabina", "Boiler Room", "BR_CARABINA.mp4", ["boilerroom"]),
            _game("BR_DEBUG", "Debug", "Boiler Room", "BR_DEBUG.mp4", ["boilerroom"]),
            _game("BR_LUMINA", "Lumina", "Boiler Room", "BR_LUMINA.mp4", ["boilerroom"]),
            _game("BR_PATRATELE", "Pătrățele", "Boiler Room", "BR_PATRATELE.mp4", ["boilerroom"]),
            _game("BR_POARTA", "Poartă", "Boiler Room", "BR_POARTA.mp4", ["boilerroom"]),
            _game("BR_X", "X", "Boiler Room", "BR_X.mp4", ["boilerroom"]),
        ],
    },
    "smallroom": {
        "label": "Small Room",
        "targets": ["boilerroom"],
        "games": [
            _game("SR_BIDEU", "Bideu", "Small Room", "SR_BIDEU.mp4", ["boilerroom"]),
            _game("SR_IMBUS", "Imbus", "Small Room", "SR_IMBUS.mp4", ["boilerroom"]),
            _game("SR_LUMINA", "Lumina", "Small Room", "SR_LUMINA.mp4", ["boilerroom"]),
            _game("SR_PUZZLE", "Puzzle", "Small Room", "SR_PUZZLE.mp4", ["boilerroom"]),
            _game("SR_SAW", "Saw", "Small Room", "SR_SAW.mp4", ["boilerroom"]),
        ],
    },
    "hallroom": {
        "label": "Hall Room",
        "targets": ["holintrare"],
        "games": [
            _game("ALL_BUCATARIE", "All — Bucătărie", "Hall Room", "ALL_BUCATARIE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_INTALNIRE", "All — Întâlnire", "Hall Room", "ALL_INTALNIRE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("HR_CARABINA", "Carabina", "Hall Room", "HR_CARABINA.mp4", ["holintrare"]),
            _game("HR_JAWS", "Jaws", "Hall Room", "HR_JAWS.mp4", ["holintrare"]),
            _game("HR_KEY_DOOR", "Key Door", "Hall Room", "HR_KEY_DOOR.mp4", ["holintrare"]),
            _game("HR_LUMINA", "Lumina", "Hall Room", "HR_LUMINA.mp4", ["holintrare"]),
        ],
    },
    "holintrare": {
        "label": "Hol Intrare",
        "targets": ["holintrare"],
        "games": [
            _game("ALL_BUTOANE", "All — Butoane", "Hol Intrare", "ALL_BUTOANE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_CHEIE_BULINA", "All — Cheie Bulina", "Hol Intrare", "ALL_CHEIE_BULINA.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_DECODOR", "All — Decodor", "Hol Intrare", "ALL_DECODOR.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_LEMN", "All — Lemn", "Hol Intrare", "ALL_LEMN.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_SFORI", "All — Sfori", "Hol Intrare", "ALL_SFORI.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_VIDEOPLAYER", "All — Videoplayer", "Hol Intrare", "ALL_VIDEOPLAYER.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_ZAVOR", "All — Zăvor", "Hol Intrare", "ALL_ZAVOR.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("HI_LOCO", "LoCo", "Hol Intrare", "HI_LOCO.mp4", ["holintrare"]),
            _game("HI_LUMINA", "Lumina", "Hol Intrare", "HI_LUMINA.mp4", ["holintrare"]),
            _game("HI_SAGETI", "Săgeți", "Hol Intrare", "HI_SAGETI.mp4", ["holintrare"]),
        ],
    },
    "jigsawroom": {
        "label": "Jigsaw Room",
        "targets": ["lastroom"],
        "games": [
            _game("ALL_ANTIDOT", "All — Antidot", "Jigsaw Room", "ALL_ANTIDOT.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_DIRECTII", "All — Direcții", "Jigsaw Room", "ALL_DIRECTII.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_FEAR", "All — Fear", "Jigsaw Room", "ALL_FEAR.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_HELP", "All — Help", "Jigsaw Room", "ALL_HELP.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_LACAT_GALBEN", "All — Lacăt Galben", "Jigsaw Room", "ALL_LACAT_GALBEN.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_LACAT_VERDE", "All — Lacăt Verde", "Jigsaw Room", "ALL_LACAT_VERDE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_LEMNE_JIGSAW", "All — Lemne", "Jigsaw Room", "ALL_LEMNE_JIGSAW.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_ORGANE", "All — Organe", "Jigsaw Room", "ALL_ORGANE.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_SEIF", "All — Seif", "Jigsaw Room", "ALL_SEIF.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_TEAVA", "All — Țeavă", "Jigsaw Room", "ALL_TEAVA.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_UV", "All — UV", "Jigsaw Room", "ALL_UV.mp4", ["boilerroom", "lastroom", "holintrare"]),
        ],
    },
    "lastroom": {
        "label": "Last Room",
        "targets": ["lastroom"],
        "games": [
            _game("ALL_CUTIE_BILA", "All — Cutie Bilă", "Last Room", "ALL_CUTIE_BILA.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_FEED", "All — Feed", "Last Room", "ALL_FEED.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_LILIAC", "All — Liliac", "Last Room", "ALL_LILIAC.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("ALL_TREFLA", "All — Trefla", "Last Room", "ALL_TREFLA.mp4", ["boilerroom", "lastroom", "holintrare"]),
            _game("LR_38", "38", "Last Room", "LR_38.mp4", ["lastroom"]),
            _game("LR_ABCDE", "ABCDE", "Last Room", "LR_ABCDE.mp4", ["lastroom"]),
            _game("LR_ARROWS", "Arrows", "Last Room", "LR_ARROWS.mp4", ["lastroom"]),
            _game("LR_CARABINA", "Carabina", "Last Room", "LR_CARABINA.mp4", ["lastroom"]),
            _game("LR_CODE", "Code", "Last Room", "LR_CODE.mp4", ["lastroom"]),
            _game("LR_GRAVITY", "Gravity", "Last Room", "LR_GRAVITY.mp4", ["lastroom"]),
            _game("LR_LUMINA", "Lumina", "Last Room", "LR_LUMINA.mp4", ["lastroom"]),
        ],
    },
}


def all_games() -> List[Game]:
    games: List[Game] = []
    for group in ROOM_GROUPS.values():
        games.extend(group["games"])
    return games
