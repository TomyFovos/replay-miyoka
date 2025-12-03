from itertools import combinations

characters = [
    "luke",
    "jamie",
    "manon",
    "kimberly",
    "marisa",
    "lily",
    "jp",
    "juri",
    "deejay",
    "cammy",
    "ryu",
    "honda",
    "blanka",
    "guile",
    "ken",
    "chunli",
    "zangief",
    "dhalsim",
    "rashid",
    "aki",
    "ed",
    "akuma",
    "bison",
    "terry",
]

replay_select_character_position = {
    "luke": (1, 0),
    "jamie": (2, 0),
    "manon": (3, 0),
    "kimberly": (0, 1),
    "marisa": (1, 1),
    "lily": (2, 1),
    "jp": (3, 1),
    "juri": (0, 2),
    "deejay": (1, 2),
    "cammy": (2, 2),
    "ryu": (3, 2),
    "honda": (0, 3),
    "blanka": (1, 3),
    "guile": (2, 3),
    "ken": (3, 3),
    "chunli": (0, 4),
    "zangief": (1, 4),
    "dhalsim": (2, 4),
    "rashid": (3, 4),
    "aki": (0, 5),
    "ed": (1, 5),
    "akuma": (2, 5),
    "bison": (3, 5),
    "terry": (4, 5),
}


def get_all_character_combinations() -> list[set]:
    comb = list(combinations(characters, 2))
    for c in characters:
        comb.append((c, c))
    return comb


def get_nth_character_combination(n):
    comb = get_all_character_combinations()
    n = n % len(comb)
    return comb[n]
