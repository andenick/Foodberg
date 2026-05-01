"""
Foodberg KB Wishlist v2 generator.

Emits:
  - 2026.04.26_Foodberg_Wishlist_v2.csv  (19 cols)
  - 2026.04.26_Foodberg_Wishlist_v2.json (schema 2.0)

Adds to v1: era, geography, themes[], added_in_version, FLAGSHIP priority.

Strategy: carries forward v1's 370 entries enriched with era/geography/themes,
then extends with ~460 new entries across deepened v1 categories (Phase G)
and new categories 15-25 (Phases H-I).
"""
from __future__ import annotations
import csv
import json
import urllib.parse
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path

OUT_DIR = Path(__file__).parent
V1_CSV = OUT_DIR.parent / "2026.04.12 KB Wishlist" / "2026.04.12_Foodberg_Wishlist.csv"
CSV_PATH = OUT_DIR / "2026.04.26_Foodberg_Wishlist_v2.csv"
JSON_PATH = OUT_DIR / "2026.04.26_Foodberg_Wishlist_v2.json"

def annas(q: str) -> str: return "https://annas-archive.org/search?q=" + urllib.parse.quote_plus(q)
def archorg(q: str) -> str: return "https://archive.org/search?query=" + urllib.parse.quote_plus(q)
def scholar(q: str) -> str: return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(q)

# =============================================================================
# METADATA ENRICHMENT FOR v1 ENTRIES (by CSV Number 1..370)
# =============================================================================
# Era: pre1900, 1900_1945, 1945_1980, 1980_2010, 2010_2020, 2020_present, spanning
# Geography: US, US_Global, Global, Europe, Asia, LatAm, Africa, Colonial
# Themes: supply, demand, technology, policy, labor, climate, trade, finance, methodology
#
# Defaults applied when a number is not listed explicitly:
#   era="spanning", geo="US_Global", themes=["supply","policy"]

DEFAULT_ERA = "spanning"
DEFAULT_GEO = "US_Global"
DEFAULT_THEMES = ["supply", "policy"]

# v1 FLAGSHIP promotions (one per v1 category, by Number)
V1_FLAGSHIPS = {
    2,    # Gardner (Cat 1)
    31,   # Imhoff (Cat 2)
    61,   # Cronon (Cat 3)
    107,  # Wright Global Biofuels (Cat 4 Cereals)
    136,  # MacDonald Meatpacking Consolidation (Cat 5)
    168,  # Manchester dairy (Cat 6)
    186,  # Byerlee Tropical Oil Crop (Cat 7)
    208,  # Beghin US Sugar (Cat 8)
    223,  # Martin H-2A (Cat 9)
    241,  # Evenson Gollin Green Revolution (Cat 10)
    276,  # Anderson Distortions (Cat 11)
    307,  # Ortiz-Bobea climate (Cat 12)
    326,  # Kasavana Menu Engineering (Cat 13)
    351,  # USDA WASDE (Cat 14)
}

# Per-entry overrides: {v1_number: (era, geo, [themes])}
V1_OVERRIDES = {
    # Cat 1 — Ag Econ Foundations (1..30)
    1: ("spanning","US",["supply","demand","methodology"]),
    2: ("spanning","US",["policy","supply"]),
    3: ("1900_1945","US",["supply","policy"]),
    4: ("1945_1980","US",["supply","policy"]),
    5: ("1945_1980","US",["supply","methodology"]),
    6: ("spanning","Global",["supply","methodology"]),
    7: ("1900_1945","US",["finance","methodology"]),
    8: ("1900_1945","Europe",["finance","methodology"]),
    9: ("1980_2010","Global",["finance","methodology"]),
    10: ("2010_2020","US_Global",["finance","supply"]),
    11: ("2010_2020","US",["finance","policy"]),
    12: ("1980_2010","US",["finance","methodology"]),
    13: ("1980_2010","US",["finance","methodology"]),
    14: ("2010_2020","US",["finance","methodology"]),
    15: ("2010_2020","US",["policy","supply"]),
    16: ("2010_2020","US",["policy","supply"]),
    17: ("1980_2010","US",["policy","methodology"]),
    18: ("1980_2010","US_Global",["policy","demand"]),
    19: ("2010_2020","US_Global",["policy","supply"]),
    20: ("1945_1980","US",["methodology","supply"]),
    21: ("2010_2020","US",["finance","methodology"]),
    22: ("1980_2010","Global",["finance","methodology"]),
    23: ("1945_1980","US",["finance","methodology"]),
    24: ("1945_1980","US",["policy","methodology"]),
    25: ("1980_2010","Global",["finance","policy"]),
    26: ("1945_1980","Global",["supply","methodology"]),
    27: ("1980_2010","Global",["finance","methodology"]),
    28: ("1980_2010","Global",["demand","policy"]),
    29: ("1980_2010","US",["policy","supply"]),
    30: ("1945_1980","Global",["policy","trade"]),
    # Cat 2 — US Commodity Policy (31..60)
    31: ("2010_2020","US",["policy"]),
    32: ("2010_2020","US",["policy"]),
    33: ("2010_2020","US",["policy","methodology"]),
    34: ("spanning","US",["policy","methodology"]),
    35: ("spanning","US",["policy","supply"]),
    36: ("1980_2010","US",["policy","supply"]),
    37: ("1980_2010","US",["policy","trade"]),
    38: ("2010_2020","US",["policy","technology"]),
    39: ("2010_2020","US",["policy","technology","supply"]),
    40: ("2010_2020","US",["policy","technology"]),
    41: ("2010_2020","US",["policy","technology"]),
    42: ("2010_2020","US",["policy","trade"]),
    43: ("2010_2020","US",["policy"]),
    44: ("2010_2020","US",["policy"]),
    45: ("1980_2010","US",["policy"]),
    46: ("2010_2020","US",["policy","climate"]),
    47: ("2010_2020","US",["policy"]),
    48: ("2010_2020","US",["policy","finance"]),
    49: ("1980_2010","US_Global",["policy","trade"]),
    50: ("2010_2020","US_Global",["policy","technology"]),
    51: ("2010_2020","US",["policy","technology"]),
    52: ("2010_2020","US",["policy"]),
    53: ("2010_2020","US",["policy","climate"]),
    54: ("2010_2020","US",["policy"]),
    55: ("2010_2020","US",["policy"]),
    56: ("2010_2020","US",["policy","demand"]),
    57: ("1980_2010","US",["policy","technology"]),
    58: ("2010_2020","US",["policy","trade"]),
    59: ("2010_2020","US",["policy","trade"]),
    60: ("spanning","US",["policy","methodology"]),
    # Cat 3 — Food Price History (61..100)
    61: ("pre1900","US",["supply","trade"]),
    62: ("pre1900","US",["supply"]),
    63: ("spanning","US",["supply","methodology"]),
    64: ("pre1900","US",["supply","trade"]),
    65: ("spanning","US",["supply","policy"]),
    66: ("1945_1980","US",["supply","policy"]),
    67: ("1900_1945","US",["supply","policy"]),
    68: ("1945_1980","US_Global",["supply","trade"]),
    69: ("1945_1980","US_Global",["supply","trade"]),
    70: ("1945_1980","US_Global",["supply","policy"]),
    71: ("1945_1980","US_Global",["trade","policy"]),
    72: ("1945_1980","US_Global",["trade","supply"]),
    73: ("1980_2010","Global",["supply","demand"]),
    74: ("1980_2010","US_Global",["supply","demand","policy"]),
    75: ("1980_2010","Global",["supply","policy"]),
    76: ("1980_2010","US_Global",["supply","policy"]),
    77: ("1980_2010","Global",["supply","finance"]),
    78: ("1980_2010","Global",["supply","finance"]),
    79: ("2010_2020","Global",["supply","policy"]),
    80: ("2010_2020","Global",["supply","policy","demand"]),
    81: ("2020_present","Global",["supply","trade","policy"]),
    82: ("2020_present","Global",["supply","trade"]),
    83: ("2020_present","Global",["supply","trade"]),
    84: ("spanning","Global",["supply","finance","methodology"]),
    85: ("spanning","Global",["supply","finance"]),
    86: ("spanning","Global",["methodology","finance"]),
    87: ("spanning","Global",["supply","finance"]),
    88: ("1980_2010","US_Global",["supply","finance"]),
    89: ("2010_2020","Global",["policy","supply"]),
    90: ("1980_2010","Global",["supply","finance"]),
    91: ("1945_1980","US",["supply","technology"]),
    92: ("1980_2010","US",["supply"]),
    93: ("pre1900","Colonial",["supply","trade","labor"]),
    94: ("spanning","Global",["supply","trade"]),
    95: ("spanning","Global",["supply","trade"]),
    96: ("spanning","Global",["supply","trade"]),
    97: ("spanning","Global",["demand","methodology"]),
    98: ("1945_1980","US",["policy","supply"]),
    99: ("1980_2010","Global",["supply","policy"]),
    100: ("2020_present","Global",["supply","trade","policy"]),
    # Cat 4 — Cereals Grains (101..135)
    101: ("pre1900","US",["technology","supply"]),
    102: ("1900_1945","Global",["supply","trade"]),
    103: ("2010_2020","Global",["supply","trade"]),
    104: ("2010_2020","Global",["supply","trade"]),
    105: ("2010_2020","US",["supply","policy","technology"]),
    106: ("2010_2020","Global",["supply","policy","technology"]),
    107: ("2010_2020","Global",["supply","technology","policy"]),
    108: ("2010_2020","Asia",["supply","trade","policy"]),
    109: ("2010_2020","Asia",["supply","policy"]),
    110: ("2010_2020","Global",["supply","policy"]),
    111: ("2010_2020","US_Global",["trade","policy"]),
    112: ("2010_2020","US_Global",["supply","technology"]),
    113: ("2010_2020","Asia",["demand","trade"]),
    114: ("1900_1945","US",["finance","technology"]),
    115: ("spanning","US",["finance","methodology"]),
    116: ("pre1900","US",["finance"]),
    117: ("2010_2020","US",["climate","technology"]),
    118: ("2010_2020","Global",["climate","technology"]),
    119: ("2010_2020","US",["climate"]),
    120: ("2020_present","Global",["supply"]),
    121: ("2020_present","US",["supply"]),
    122: ("2020_present","US",["supply"]),
    123: ("2020_present","US",["supply"]),
    124: ("2020_present","US",["supply"]),
    125: ("2010_2020","US",["finance"]),
    126: ("2020_present","US",["supply"]),
    127: ("2010_2020","Global",["supply","trade"]),
    128: ("2010_2020","US",["climate"]),
    129: ("2010_2020","US",["finance","methodology"]),
    130: ("2010_2020","US",["finance"]),
    131: ("2010_2020","US",["technology","climate"]),
    132: ("2010_2020","US",["finance","supply"]),
    133: ("2010_2020","Global",["supply","trade"]),
    134: ("2010_2020","Global",["supply","finance"]),
    135: ("1980_2010","US",["finance"]),
    # Cat 5 — Meat & Livestock (136..165)
    136: ("1980_2010","US",["supply","policy"]),
    137: ("2010_2020","US",["supply"]),
    138: ("2010_2020","US",["supply"]),
    139: ("2020_present","US",["supply","labor"]),
    140: ("2020_present","US",["supply"]),
    141: ("spanning","US",["technology","supply"]),
    142: ("spanning","US",["supply"]),
    143: ("1980_2010","US",["supply"]),
    144: ("spanning","US",["supply","technology"]),
    145: ("1980_2010","US",["supply","technology"]),
    146: ("1980_2010","US",["supply","demand"]),
    147: ("1980_2010","US",["supply"]),
    148: ("1980_2010","US",["supply"]),
    149: ("1980_2010","US",["supply","methodology"]),
    150: ("2010_2020","US",["policy","demand"]),
    151: ("2020_present","US",["supply","methodology"]),
    152: ("1980_2010","US",["supply"]),
    153: ("1980_2010","US",["supply"]),
    154: ("1980_2010","US",["supply"]),
    155: ("2010_2020","US",["supply"]),
    156: ("2010_2020","US",["demand"]),
    157: ("spanning","US",["demand","supply"]),
    158: ("spanning","US",["supply"]),
    159: ("1980_2010","US",["supply"]),
    160: ("1980_2010","US",["supply"]),
    161: ("1945_1980","US",["supply"]),
    162: ("1980_2010","US",["supply","demand"]),
    163: ("2010_2020","US",["policy","trade"]),
    164: ("1980_2010","US",["supply"]),
    165: ("1980_2010","US",["finance"]),
    # Cat 6 — Dairy (166..185)
    166: ("2010_2020","US",["finance","supply"]),
    167: ("1980_2010","US",["supply","policy"]),
    168: ("spanning","US",["supply","technology"]),
    169: ("2010_2020","US",["policy"]),
    170: ("2010_2020","US",["policy"]),
    171: ("2010_2020","US_Global",["trade","supply"]),
    172: ("spanning","Global",["supply"]),
    173: ("spanning","US",["supply"]),
    174: ("2010_2020","US",["policy"]),
    175: ("2010_2020","Global",["supply","trade"]),
    176: ("2010_2020","Asia",["demand","supply"]),
    177: ("spanning","US",["demand"]),
    178: ("spanning","US",["policy","methodology"]),
    179: ("1980_2010","US",["policy"]),
    180: ("spanning","Global",["trade","methodology"]),
    181: ("1980_2010","US",["policy"]),
    182: ("1980_2010","US",["supply"]),
    183: ("2010_2020","US",["finance"]),
    184: ("spanning","US",["policy","methodology"]),
    185: ("spanning","Global",["supply","methodology"]),
    # Cat 7 — Oils Fats (186..205)
    186: ("spanning","Asia",["supply","technology"]),
    187: ("spanning","Global",["supply","technology"]),
    188: ("spanning","Asia",["supply","policy"]),
    189: ("2010_2020","US",["supply","technology"]),
    190: ("2010_2020","US",["supply","technology"]),
    191: ("spanning","Global",["supply","methodology"]),
    192: ("1980_2010","Europe",["supply","technology"]),
    193: ("spanning","Global",["supply","methodology"]),
    194: ("1980_2010","Global",["supply","trade"]),
    195: ("2010_2020","Asia",["supply","climate"]),
    196: ("2010_2020","US_Global",["supply"]),
    197: ("spanning","Global",["supply","methodology"]),
    198: ("2010_2020","Asia",["climate","technology"]),
    199: ("2010_2020","US",["technology","policy"]),
    200: ("2010_2020","Europe",["supply","policy"]),
    201: ("2010_2020","US",["policy","technology"]),
    202: ("2010_2020","Global",["supply","finance"]),
    203: ("2010_2020","Asia",["supply","labor"]),
    204: ("1980_2010","Global",["supply","climate"]),
    205: ("2010_2020","Europe",["supply","finance"]),
    # Cat 8 — Sugar Sweeteners (206..220)
    206: ("spanning","Global",["supply","methodology"]),
    207: ("pre1900","Colonial",["supply","labor","trade"]),
    208: ("2010_2020","US",["policy","trade"]),
    209: ("1900_1945","US",["policy","supply"]),
    210: ("1980_2010","US",["demand","technology"]),
    211: ("2010_2020","US",["policy","trade"]),
    212: ("2010_2020","US",["policy","supply"]),
    213: ("1980_2010","Global",["supply","trade"]),
    214: ("2010_2020","Global",["supply","methodology"]),
    215: ("2010_2020","Global",["supply","finance"]),
    216: ("spanning","Global",["supply","demand"]),
    217: ("2020_present","US",["supply","policy"]),
    218: ("2010_2020","US",["supply","policy"]),
    219: ("spanning","Global",["supply","methodology"]),
    220: ("spanning","US",["supply"]),
    # Cat 9 — Produce (221..240)
    221: ("1980_2010","US",["supply","demand"]),
    222: ("spanning","US",["supply","methodology"]),
    223: ("2010_2020","US",["labor","policy"]),
    224: ("2010_2020","US",["labor","supply"]),
    225: ("2010_2020","Global",["supply","trade"]),
    226: ("2010_2020","Global",["supply","technology"]),
    227: ("spanning","US",["supply","methodology"]),
    228: ("2010_2020","US",["supply","trade"]),
    229: ("2010_2020","US",["climate","supply"]),
    230: ("2010_2020","US",["climate","supply"]),
    231: ("2010_2020","US",["demand"]),
    232: ("2010_2020","US",["labor","policy"]),
    233: ("2010_2020","US",["supply","trade"]),
    234: ("2010_2020","US",["supply","trade"]),
    235: ("2010_2020","US",["climate","policy"]),
    236: ("2010_2020","US",["supply","finance"]),
    237: ("1980_2010","US",["supply","trade"]),
    238: ("2010_2020","US",["labor","policy"]),
    239: ("2010_2020","US",["climate","supply"]),
    240: ("spanning","US",["supply","methodology"]),
    # Cat 10 — Global Food Systems (241..275)
    241: ("1945_1980","Global",["supply","technology"]),
    242: ("1945_1980","Asia",["supply","technology"]),
    243: ("spanning","Global",["supply","technology"]),
    244: ("1945_1980","Global",["supply","technology","policy"]),
    245: ("1945_1980","Asia",["supply","technology","policy"]),
    246: ("spanning","Global",["methodology"]),
    247: ("spanning","Global",["supply","methodology"]),
    248: ("spanning","Global",["supply","demand","policy"]),
    249: ("spanning","Global",["supply","methodology"]),
    250: ("1900_1945","Asia",["demand","labor"]),
    251: ("pre1900","Global",["climate","demand"]),
    252: ("spanning","Global",["demand","policy"]),
    253: ("spanning","Global",["demand","methodology"]),
    254: ("spanning","Global",["supply","demand","policy"]),
    255: ("spanning","Global",["demand","policy"]),
    256: ("1945_1980","US",["demand","policy"]),
    257: ("spanning","Global",["supply","finance"]),
    258: ("spanning","Global",["supply","finance","methodology"]),
    259: ("spanning","Global",["supply","finance"]),
    260: ("1945_1980","Asia",["supply","technology","policy"]),
    261: ("1945_1980","Global",["supply","technology"]),
    262: ("2010_2020","Africa",["trade","demand"]),
    263: ("spanning","Global",["supply","methodology"]),
    264: ("spanning","Global",["supply","demand"]),
    265: ("2010_2020","Global",["supply","policy"]),
    266: ("2010_2020","Asia",["supply","demand"]),
    267: ("2010_2020","Global",["supply","finance"]),
    268: ("2010_2020","Global",["supply","finance","methodology"]),
    269: ("spanning","Global",["supply","technology"]),
    270: ("2010_2020","Global",["supply","methodology"]),
    271: ("pre1900","Global",["climate","demand"]),
    272: ("2010_2020","Global",["supply","demand","policy"]),
    273: ("2010_2020","Global",["supply","finance"]),
    274: ("2010_2020","Asia",["supply","policy"]),
    275: ("spanning","Global",["demand","methodology"]),
    # Cat 11 — Trade & Geopolitics (276..300)
    276: ("spanning","Global",["trade","policy"]),
    277: ("1945_1980","Global",["trade","policy"]),
    278: ("2010_2020","Global",["trade","supply"]),
    279: ("2010_2020","Global",["trade","supply"]),
    280: ("2010_2020","Global",["trade","supply"]),
    281: ("1980_2010","US_Global",["trade","policy"]),
    282: ("2010_2020","US_Global",["trade","policy"]),
    283: ("2010_2020","US",["trade","policy"]),
    284: ("2010_2020","Asia",["trade","policy"]),
    285: ("2010_2020","Asia",["demand","trade"]),
    286: ("2020_present","Global",["trade","supply","policy"]),
    287: ("2020_present","Global",["trade","supply"]),
    288: ("2020_present","Global",["trade","supply"]),
    289: ("2010_2020","Global",["trade","policy"]),
    290: ("1980_2010","Global",["trade","policy"]),
    291: ("1980_2010","US_Global",["trade","policy"]),
    292: ("2010_2020","US_Global",["trade","supply"]),
    293: ("2010_2020","Asia",["trade","supply"]),
    294: ("2020_present","Global",["trade","supply"]),
    295: ("2010_2020","Global",["trade","supply"]),
    296: ("1980_2010","Global",["trade","policy"]),
    297: ("2010_2020","US",["trade","policy"]),
    298: ("2010_2020","US",["trade","supply"]),
    299: ("1980_2010","Global",["trade","policy"]),
    300: ("2010_2020","US_Global",["trade","policy"]),
    # Cat 12 — Climate Land Inputs (301..325)
    301: ("1980_2010","US",["climate","technology"]),
    302: ("2010_2020","Global",["climate","technology"]),
    303: ("2020_present","Global",["climate","technology"]),
    304: ("2010_2020","US",["climate","supply"]),
    305: ("2010_2020","Global",["climate","supply"]),
    306: ("2010_2020","Global",["climate","supply"]),
    307: ("2020_present","Global",["climate","supply","technology"]),
    308: ("2020_present","Global",["climate","methodology","policy"]),
    309: ("1980_2010","Global",["climate","technology"]),
    310: ("2010_2020","Global",["climate","supply"]),
    311: ("2010_2020","Global",["climate","supply"]),
    312: ("2010_2020","Global",["climate","supply"]),
    313: ("2010_2020","Global",["climate","policy","technology"]),
    314: ("2010_2020","Global",["climate","supply"]),
    315: ("1980_2010","Global",["climate","technology"]),
    316: ("2010_2020","Global",["climate","supply"]),
    317: ("2010_2020","Global",["climate","supply"]),
    318: ("2010_2020","Global",["climate","supply"]),
    319: ("2010_2020","Global",["climate","policy"]),
    320: ("2020_present","US",["climate","supply","technology"]),
    321: ("2010_2020","US",["climate","supply"]),
    322: ("2010_2020","US",["climate","supply"]),
    323: ("2010_2020","Global",["climate","supply"]),
    324: ("2010_2020","Global",["climate","supply"]),
    325: ("2010_2020","Global",["climate","supply"]),
    # Cat 13 — Chef/Restaurant (326..350)
    326: ("1980_2010","US",["demand"]),
    327: ("2010_2020","US",["demand","finance"]),
    328: ("1980_2010","US",["demand","finance"]),
    329: ("2010_2020","US",["demand","methodology"]),
    330: ("2010_2020","US",["demand","finance"]),
    331: ("spanning","US",["demand","finance"]),
    332: ("2010_2020","US",["demand","finance"]),
    333: ("2010_2020","US",["demand","supply"]),
    334: ("spanning","US",["demand","supply"]),
    335: ("2020_present","US",["demand","finance"]),
    336: ("2010_2020","US",["demand","finance"]),
    337: ("2010_2020","US",["demand","finance"]),
    338: ("spanning","US",["demand","finance"]),
    339: ("2020_present","US",["demand","finance"]),
    340: ("2020_present","US",["demand","finance","methodology"]),
    341: ("1980_2010","US",["demand"]),
    342: ("1980_2010","US",["demand"]),
    343: ("spanning","US",["demand","supply"]),
    344: ("2020_present","US",["demand","finance"]),
    345: ("1980_2010","US",["demand"]),
    346: ("spanning","US",["demand","finance"]),
    347: ("1980_2010","US",["demand"]),
    348: ("spanning","US",["demand","methodology"]),
    349: ("2020_present","US",["supply","finance"]),
    350: ("spanning","US",["demand"]),
    # Cat 14 — Data Source Methodology (351..370)
    351: ("spanning","US",["methodology"]),
    352: ("2010_2020","US",["methodology"]),
    353: ("1980_2010","US",["methodology","finance"]),
    354: ("2010_2020","US",["methodology"]),
    355: ("spanning","US",["methodology","demand"]),
    356: ("spanning","US",["methodology","demand"]),
    357: ("spanning","US",["methodology","demand"]),
    358: ("1980_2010","US",["methodology","demand"]),
    359: ("spanning","Global",["methodology"]),
    360: ("spanning","Global",["methodology"]),
    361: ("spanning","Global",["methodology"]),
    362: ("2010_2020","Global",["methodology","climate"]),
    363: ("spanning","US",["methodology","finance"]),
    364: ("spanning","US",["methodology"]),
    365: ("spanning","Global",["methodology","finance"]),
    366: ("2010_2020","US",["methodology"]),
    367: ("1980_2010","US",["methodology","demand"]),
    368: ("spanning","Global",["methodology"]),
    369: ("spanning","Global",["methodology"]),
    370: ("spanning","US",["methodology","finance"]),
}

# =============================================================================
# NEW v2 ENTRIES (Phases G, H, I, J)
# =============================================================================
# Tuple schema (18 fields):
# (cat, sub, last, first, title, year, pub, typ, comm, prio, status, notes, url,
#  rel, era, geo, themes_list)

N: list[tuple] = []

def n(cat, sub, last, first, title, year, pub, typ, comm, prio, notes, url, rel, era, geo, themes, status="NEEDED"):
    N.append((cat, sub, last, first, title, year, pub, typ, comm, prio, status, notes, url, rel, era, geo, themes))


# -----------------------------------------------------------------------------
# PHASE G — DEEPEN v1 CATEGORIES (target +190)
# -----------------------------------------------------------------------------

# --- Cat 1 Ag Econ Foundations deepening (+10) ---
C = "Ag Econ Foundations"
n(C,"price_theory","Lusk","Jayson L.","Unnaturally Delicious: How Science and Technology Are Serving Up Super Foods",2016,"St Martin's","BOOK","none","HIGH","","","Modern food-tech economics primer","2010_2020","US",["technology","demand"])
n(C,"market_structure","Sexton","Richard J.","Handbook of the Economics of Food and Agricultural Markets",2022,"Elsevier","BOOK","multi","HIGH","Vol.6","","Modern IO + ag","2020_present","US_Global",["supply","methodology"])
n(C,"price_theory","Bellemare","Marc F.","Doing Economics: What You Should Have Learned in Grad School",2022,"MIT Press","BOOK","none","MEDIUM","","",scholar("Bellemare Doing Economics"),"2020_present","US",["methodology"])
n(C,"price_theory","Just","David R.","Introduction to Behavioral Economics",2013,"Wiley","BOOK","none","MEDIUM","","","Behavioral ag-econ","2010_2020","US",["demand","methodology"])
n(C,"supply_response","Roberts","Michael J.","Global Agricultural Supply and Demand",2015,"NBER WP","WORKING_PAPER","multi","MEDIUM","With Schlenker","",scholar("Roberts Schlenker global agricultural supply demand"),"2010_2020","Global",["supply","methodology"])
n(C,"futures_markets","Irwin","Scott H.","The Financialization of Food? A Critical Appraisal",2022,"Annual Review of Resource Economics","ARTICLE","multi","HIGH","With Sanders","","Modern take on speculation debate","2020_present","US_Global",["finance","methodology"])
n(C,"market_structure","Saitone","Tina L.","Analyzing the Impact of Multiple Captive Supply Vehicles on Imperfect Competition",2018,"AJAE","ARTICLE","meat","MEDIUM","","","","2010_2020","US",["supply","finance"])
n(C,"price_theory","Moschini","GianCarlo","Agricultural Policy and the Environment: An Evaluation of Recent Papers",2017,"Annual Review of Resource Economics","ARTICLE","multi","LOW","","","","2010_2020","US",["policy","climate"])
n(C,"supply_response","Hendricks","Nathan P.","Acreage Response Under Changing Crop Insurance",2014,"AJAE","ARTICLE","cereals","MEDIUM","","","","2010_2020","US",["policy","supply"])
n(C,"hedging_storage","Smith","Aaron","Speculation and Agricultural Commodity Markets",2017,"NBER","WORKING_PAPER","multi","MEDIUM","","",scholar("Aaron Smith speculation agricultural commodity"),"2010_2020","US_Global",["finance","methodology"])

# --- Cat 2 US Commodity Policy deepening (+15) ---
C = "US Commodity Policy"
n(C,"farm_bills","Monke","Jim","Agriculture and the 2023-2024 Farm Bill",2024,"CRS Report R47745","REPORT","multi","HIGH","","https://crsreports.congress.gov/product/pdf/R/R47745","2024 FB scorecard","2020_present","US",["policy"])
n(C,"farm_bills","CBO","","CBO Baseline for Farm Programs",2024,"Congressional Budget Office","REPORT","multi","HIGH","","https://www.cbo.gov/topics/agriculture","","2020_present","US",["policy","finance"])
n(C,"biofuels_policy","Schnepf","Randy","Renewable Fuel Standard: Recent Developments",2023,"CRS","REPORT","cereals","HIGH","","","","2020_present","US",["policy","technology"])
n(C,"subsidies_supports","USDA","","Inflation Reduction Act (IRA) Climate-Smart Ag Provisions",2023,"USDA","REPORT","multi","HIGH","","https://www.usda.gov/inflation-reduction-act","IRA reshapes ag subsidy landscape","2020_present","US",["policy","climate"])
n(C,"subsidies_supports","Zulauf","Carl","The ARC/PLC Programs: Design, Operation, and Outcomes",2019,"farmdoc daily","ARTICLE","cereals","MEDIUM","","https://farmdocdaily.illinois.edu/","","2010_2020","US",["policy"])
n(C,"subsidies_supports","Smith","Vincent H.","Agricultural Policy in Disarray",2018,"AEI","BOOK","multi","HIGH","With Glauber, Goodwin","","Critique of US farm programs","2010_2020","US",["policy"])
n(C,"biofuels_policy","Ziolkowska","Jadwiga R.","Biofuels and Their By-Products: Economic and Trade Implications",2022,"Biomass","ARTICLE","cereals","MEDIUM","","","","2020_present","US_Global",["policy","technology"])
n(C,"farm_bills","Coppess","Jonathan","Historical Background on the Farm Safety Net",2018,"farmdoc daily","ARTICLE","multi","MEDIUM","","","","2010_2020","US",["policy"])
n(C,"conservation_policy","Wallander","Steven","The Evolution of USDA Conservation Programs",2021,"USDA ERS","REPORT","multi","MEDIUM","","https://www.ers.usda.gov/publications","","2020_present","US",["policy","climate"])
n(C,"conservation_policy","USDA","","Climate-Smart Commodities Program Overview",2023,"USDA","REPORT","multi","HIGH","","https://www.usda.gov/climate-solutions/climate-smart-commodities","","2020_present","US",["policy","climate"])
n(C,"subsidies_supports","USDA","","Market Facilitation Program: Payments 2018-2020",2020,"USDA","REPORT","multi","MEDIUM","MFP to offset tariffs","","Trade-war aid payments","2010_2020","US",["policy","trade"])
n(C,"farm_bills","Coppess","Jonathan","The 2018 Farm Bill: Outlook on ARC/PLC",2019,"farmdoc daily","ARTICLE","cereals","LOW","","","","2010_2020","US",["policy"])
n(C,"sugar_dairy_policy","Schnepf","Randy","Farm Safety Net Payments Under the 2018 Farm Bill",2023,"CRS","REPORT","multi","MEDIUM","","","","2020_present","US",["policy"])
n(C,"biofuels_policy","USDA","","Sustainable Aviation Fuel (SAF) Grand Challenge: Ag Implications",2023,"USDA/DOE","REPORT","cereals","MEDIUM","","https://www.energy.gov/eere/bioenergy/sustainable-aviation-fuel-grand-challenge","SAF as new biofuels driver","2020_present","US",["policy","technology"])
n(C,"farm_bills","Schnepf","Randy","Budget Issues Shaping a 2023 Farm Bill",2022,"CRS","REPORT","multi","MEDIUM","","","","2020_present","US",["policy","finance"])

# --- Cat 3 Food Price History deepening (+20, recent + colonial) ---
C = "Food Price History"
n(C,"pre_1900","Rothenberg","Winifred B.","The Emergence of a Capital Market in Rural Massachusetts, 1730-1838",1985,"Journal of Economic History","ARTICLE","none","MEDIUM","","","","pre1900","US",["supply","finance"])
n(C,"pre_1900","Perkins","Edwin J.","The Economy of Colonial America",1988,"Columbia UP","BOOK","multi","MEDIUM","","",scholar("Perkins Economy Colonial America"),"pre1900","Colonial",["supply","trade"])
n(C,"pre_1900","Perren","Richard","Taste, Trade and Technology: The Development of the International Meat Industry",2006,"Ashgate","BOOK","meat","HIGH","","","","pre1900","Global",["supply","technology","trade"])
n(C,"20c_inflation","Shover","John L.","First Majority, Last Minority: The Transforming of Rural Life in America",1976,"Northern Illinois UP","BOOK","multi","MEDIUM","","","","1945_1980","US",["supply","labor"])
n(C,"20c_inflation","Dudley","Kathryn Marie","Debt and Dispossession: Farm Loss in America's Heartland",2000,"U Chicago Press","BOOK","multi","HIGH","1980s farm crisis","",scholar("Dudley Debt Dispossession Farm Loss"),"1980_2010","US",["finance","policy"])
n(C,"20c_inflation","Gilbert","Jess","Planning Democracy: Agrarian Intellectuals and the Intended New Deal",2015,"Yale UP","BOOK","multi","MEDIUM","","","","1900_1945","US",["policy"])
n(C,"20c_inflation","Saloutos","Theodore","The American Farmer and the New Deal",1982,"Iowa State UP","BOOK","multi","MEDIUM","","","","1900_1945","US",["policy"])
n(C,"1970s_shock","Butz","Earl","Crisis or Challenge?",1974,"Purdue","WORKING_PAPER","multi","LOW","","","","1945_1980","US",["policy"])
n(C,"2008_crisis","Clapp","Jennifer","Food Price Volatility and Vulnerability in the Global South",2014,"Third World Quarterly","ARTICLE","multi","MEDIUM","","","","2010_2020","Global",["supply","policy"])
n(C,"2022_spike","Arndt","Channing","Covid-19 Food Security Impacts: A Review",2023,"Global Food Security","ARTICLE","multi","HIGH","","","","2020_present","Global",["supply","demand"])
n(C,"2022_spike","Reardon","Thomas","COVID-19's Disruption of India's Transformed Food Supply Chains",2020,"Economic and Political Weekly","ARTICLE","multi","MEDIUM","","","","2020_present","Asia",["supply"])
n(C,"2022_spike","Barrett","Christopher B.","Actions Now Can Curb Food Systems Fallout From COVID-19",2020,"Nature Food","ARTICLE","multi","HIGH","","https://doi.org/10.1038/s43016-020-0085-y","","2020_present","Global",["supply","policy"])
n(C,"2022_spike","Laborde","David","COVID-19 Risks to Global Food Security",2020,"Science","ARTICLE","multi","CRITICAL","","https://doi.org/10.1126/science.abc4765","","2020_present","Global",["supply","demand","policy"])
n(C,"2022_spike","USDA","","Food Price Outlook 2022-2024",2024,"USDA ERS","REPORT","multi","CRITICAL","Monthly","https://www.ers.usda.gov/data-products/food-price-outlook/","Post-COVID food inflation tracker","2020_present","US",["demand","methodology"])
n(C,"2022_spike","BLS","","Food Prices: Analysis 2022-2024",2024,"BLS","REPORT","multi","HIGH","","https://www.bls.gov/opub/mlr/","","2020_present","US",["demand","methodology"])
n(C,"secular_trends","Jacks","David S.","Real GDP Per Capita in the More Rapidly Developing Countries",2021,"NBER WP","WORKING_PAPER","none","LOW","","",scholar("Jacks real GDP per capita developing"),"spanning","Global",["demand"])
n(C,"2011_spike","Bellemare","Marc F.","Rising Food Prices, Food Price Volatility, and Social Unrest",2015,"AJAE","ARTICLE","multi","HIGH","","https://doi.org/10.1093/ajae/aau038","","2010_2020","Global",["supply","policy"])
n(C,"2008_crisis","Chavas","Jean-Paul","Commodity Price Volatility: An Analysis of the 2007-08 Spike",2014,"Applied Econ Perspectives & Policy","ARTICLE","multi","MEDIUM","","","","2010_2020","Global",["supply","finance"])
n(C,"20c_inflation","Hurt","R. Douglas","American Agriculture: A Brief History",2002,"Purdue UP","BOOK","multi","HIGH","","",scholar("Hurt American Agriculture Brief History"),"spanning","US",["supply","policy"])
n(C,"pre_1900","McMath","Robert C.","American Populism: A Social History 1877-1898",1993,"Hill & Wang","BOOK","multi","MEDIUM","","","Agrarian grievance context","pre1900","US",["policy","labor"])

# --- Cat 4 Cereals deepening (+15, recent) ---
C = "Cereals Grains"
n(C,"wheat","Schnitkey","Gary","Wheat Prices and Profitability 2023-2024",2024,"farmdoc daily","ARTICLE","cereals","MEDIUM","","https://farmdocdaily.illinois.edu/","","2020_present","US",["supply","finance"])
n(C,"corn","USDA","","Corn and Other Feedgrains Outlook 2024",2024,"USDA ERS","REPORT","cereals","HIGH","","https://www.ers.usda.gov/topics/crops/corn-and-other-feedgrains/","","2020_present","US",["supply"])
n(C,"soybeans","Carter","Colin A.","The Economics of Chinese Food Security",2022,"Annual Review of Resource Economics","ARTICLE","cereals","HIGH","","","","2020_present","Asia",["supply","trade"])
n(C,"cbot_futures","Janzen","Joseph P.","The Effect of Commodity Index Trading on Agricultural Futures Prices",2018,"Applied Econ Perspectives & Policy","ARTICLE","cereals","MEDIUM","","","","2010_2020","US",["finance"])
n(C,"rice","FAO","","Rice Market Monitor (quarterly)",2024,"FAO","REPORT","cereals","MEDIUM","","https://www.fao.org/markets-and-trade/commodities/rice/rmm/","","2020_present","Global",["supply","trade"])
n(C,"rice","Minot","Nicholas","Rice Price Instability in Asia: Transmission to Domestic Markets",2020,"Food Policy","ARTICLE","cereals","MEDIUM","","","","2020_present","Asia",["supply","trade"])
n(C,"yield_weather","Ortiz-Bobea","Ariel","Unpacking the Climatic Drivers of US Agricultural Yields",2019,"Environmental Research Letters","ARTICLE","cereals","HIGH","","","","2010_2020","US",["climate","supply"])
n(C,"wheat","Liefert","William M.","Russian Wheat Markets",2021,"USDA ERS","REPORT","cereals","MEDIUM","","","","2020_present","Europe",["supply","trade"])
n(C,"corn","Hendricks","Nathan P.","The Environmental Effects of Crop Price Increases",2014,"AJAE","ARTICLE","cereals","MEDIUM","","","","2010_2020","US",["climate","policy"])
n(C,"soybeans","USDA","","China: USDA Agricultural Attaché Reports",2024,"USDA FAS","REPORT","cereals","HIGH","","https://www.fas.usda.gov/data","Primary intel on China demand","2020_present","Asia",["trade","demand"])
n(C,"cbot_futures","CFTC","","Commitments of Traders Reports: Agricultural Commodities",2024,"CFTC","DATASET_DOC","cereals","HIGH","","https://www.cftc.gov/MarketReports/CommitmentsofTraders/","Positioning data","2020_present","US",["finance","methodology"])
n(C,"yield_weather","Burke","Marshall","Satellite-Based Assessment of Yield Variation and Its Determinants in Smallholder African Systems",2017,"PNAS","ARTICLE","cereals","MEDIUM","","","","2010_2020","Africa",["climate","technology"])
n(C,"wheat","Haniotis","Tassos","Responding to Price Volatility: Building Resilient Agricultural Value Chains",2021,"OECD","REPORT","cereals","MEDIUM","","","","2020_present","Global",["supply","policy"])
n(C,"corn","Bowman","Maria S.","The Economics of Glyphosate Resistance",2014,"USDA ERS","REPORT","cereals","MEDIUM","","","","2010_2020","US",["technology","supply"])
n(C,"soybeans","Ray","Deepak K.","Climate Change Has Likely Already Affected Global Food Production",2019,"PLoS ONE","ARTICLE","multi","HIGH","","https://doi.org/10.1371/journal.pone.0217148","","2010_2020","Global",["climate","supply"])

# --- Cat 5 Meat deepening (+15, COVID + bird flu) ---
C = "Meat Livestock"
n(C,"packer_concentration","Taylor","Charles A.","Livestock Plants and COVID-19 Transmission",2022,"PNAS","ARTICLE","meat","CRITICAL","With Boulos, Almond","https://doi.org/10.1073/pnas.2010115118","Canonical COVID-meatpacking paper","2020_present","US",["labor","supply"])
n(C,"packer_concentration","Saitone","Tina L.","COVID-19 and the Agricultural Economy",2020,"Applied Econ Perspectives & Policy","ARTICLE","meat","HIGH","With Schaefer, Scheitrum","","","2020_present","US",["supply","labor"])
n(C,"livestock_policy","USDA APHIS","","HPAI H5N1 Situation Reports 2022-2025",2025,"USDA APHIS","REPORT","multi","CRITICAL","","https://www.aphis.usda.gov/livestock-poultry-disease/avian/avian-influenza","Bird flu → egg price spikes","2020_present","US",["supply","policy"])
n(C,"poultry","USDA","","Egg Market Overview and Avian Influenza Impact",2024,"USDA ERS","REPORT","meat","HIGH","","https://www.ers.usda.gov/topics/animal-products/poultry-eggs/","","2020_present","US",["supply"])
n(C,"livestock_policy","USDA APHIS","","H5N1 in Dairy Cattle: Outbreak Reports 2024",2024,"USDA APHIS","REPORT","dairy","CRITICAL","","https://www.aphis.usda.gov/livestock-poultry-disease/avian/avian-influenza/hpai-detections/livestock","Novel 2024 event","2020_present","US",["supply","policy"])
n(C,"beef_cattle","Peel","Derrell S.","Beef Cattle Herd Rebuilding After Drought",2024,"OSU Extension","REPORT","meat","HIGH","","","2024 cattle-cycle low","2020_present","US",["supply","climate"])
n(C,"packer_concentration","USDA","","Cattle Contracts Library Pilot Program",2023,"USDA AMS","DATASET_DOC","meat","MEDIUM","","https://www.ams.usda.gov/services/government-programs","Pricing-transparency regulation","2020_present","US",["policy","finance"])
n(C,"pork","Carriquiry","Miguel","African Swine Fever and Implications for World Pork Markets",2020,"Choices Magazine","ARTICLE","meat","HIGH","","","ASF China 2018-20","2010_2020","Asia",["supply","trade"])
n(C,"feed_costs","Hayes","Dermot J.","Economic Impacts of African Swine Fever in China",2021,"Applied Econ Perspectives & Policy","ARTICLE","meat","MEDIUM","","","","2020_present","Asia",["supply","trade"])
n(C,"poultry","Hayes","Dermot J.","2022 HPAI Outbreak: Economic Effects on Poultry",2023,"Iowa State CARD","WORKING_PAPER","meat","HIGH","","","","2020_present","US",["supply"])
n(C,"feed_costs","Irwin","Scott H.","The Cost of Producing Pork Has Changed",2023,"farmdoc daily","ARTICLE","meat","MEDIUM","","","","2020_present","US",["supply","finance"])
n(C,"livestock_policy","GAO","","USDA's Role in Preventing Meat Shortages",2021,"GAO","REPORT","meat","MEDIUM","","https://www.gao.gov/","","2020_present","US",["supply","policy"])
n(C,"beef_cattle","USDA","","Livestock Slaughter (monthly)",2024,"USDA NASS","DATASET_DOC","meat","HIGH","","https://www.nass.usda.gov/Publications/","Primary slaughter series","2020_present","US",["supply","methodology"])
n(C,"packer_concentration","Wohlgenant","Michael K.","Meat Price Spreads at the Farm, Wholesale, and Retail Levels",2013,"USDA ERS","REPORT","meat","MEDIUM","","","","2010_2020","US",["supply","finance"])
n(C,"pork","Shepherd","Andrew W.","The Future of the US Hog Industry",2022,"Choices Magazine","ARTICLE","meat","MEDIUM","","","","2020_present","US",["supply"])

# --- Cat 6 Dairy deepening (+10) ---
C = "Dairy"
n(C,"global_dairy","USDA","","Dairy: World Markets and Trade 2024",2024,"USDA FAS","REPORT","dairy","HIGH","","https://www.fas.usda.gov/data/dairy-world-markets-and-trade","","2020_present","Global",["supply","trade"])
n(C,"cheese_butter","Nicholson","Charles F.","US Dairy Trade and Competitiveness",2024,"Cornell","REPORT","dairy","MEDIUM","","","","2020_present","US",["trade","supply"])
n(C,"us_dairy_policy","USDA","","Dairy Margin Coverage: Program Performance 2019-2024",2024,"USDA FSA","REPORT","dairy","MEDIUM","","https://www.fsa.usda.gov/programs-and-services/dairy-margin-coverage-program/","","2020_present","US",["policy","finance"])
n(C,"global_dairy","Jongeneel","Roel","The Decoupling of the EU Dairy Sector from World Prices",2020,"European Review of Ag Econ","ARTICLE","dairy","MEDIUM","","","","2020_present","Europe",["policy","trade"])
n(C,"milk_markets","Bozic","Marin","Dairy Commodity Markets and Risk Management 2024",2024,"U Minnesota","REPORT","dairy","MEDIUM","","","","2020_present","US",["finance","supply"])
n(C,"us_dairy_policy","Stephenson","Mark W.","Federal Order Reform 2024",2024,"Cornell","REPORT","dairy","HIGH","","","FMMO class pricing reform","2020_present","US",["policy"])
n(C,"global_dairy","GDT","","Global Dairy Trade Price Index Reports 2024",2024,"Fonterra","DATASET_DOC","dairy","HIGH","","https://www.globaldairytrade.info/","","2020_present","Global",["methodology","supply"])
n(C,"cheese_butter","Ippolito","Pauline","Butter's Return: Fat and the Reversal of US Dairy Consumption",2020,"USDA ERS","REPORT","dairy","MEDIUM","","","Diet shift dairy demand","2020_present","US",["demand"])
n(C,"milk_markets","USDA","","Plant-Based Dairy Alternatives: Economic Implications",2022,"USDA ERS","REPORT","dairy","HIGH","","","Almond/oat milk displacement","2020_present","US",["demand","technology"])
n(C,"global_dairy","FAO","","Dairy Market Review: Annual",2024,"FAO","REPORT","dairy","MEDIUM","","https://www.fao.org/markets-and-trade/commodities/dairy/","","2020_present","Global",["supply","trade"])

# --- Cat 7 Oils deepening (+10) ---
C = "Oils Fats"
n(C,"palm_oil","Indonesia","","Indonesia Palm Oil Export Ban 2022: Analysis",2022,"CSIS","REPORT","oils","HIGH","","https://www.csis.org/","Major 2022 supply shock","2020_present","Asia",["trade","policy"])
n(C,"tropical_cycles","Baffes","John","The Food-Fuel Nexus After the 2022 Energy Shock",2023,"World Bank","REPORT","multi","HIGH","","https://www.worldbank.org/en/research/commodity-markets","","2020_present","Global",["climate","policy"])
n(C,"olive_oil","Arriaza","Manuel","Spanish Olive Oil Crisis 2023: Drought and Prices",2024,"New Medit","ARTICLE","oils","HIGH","","","","2020_present","Europe",["climate","supply"])
n(C,"soy_oil","USDA","","Renewable Diesel Feedstock Demand 2024",2024,"USDA ERS","REPORT","oils","HIGH","","","RD demand for soy oil surging","2020_present","US",["technology","policy"])
n(C,"palm_oil","Cramb","Rob","Oil Palm and the Challenges of Deforestation-Free Supply Chains",2023,"Annual Review of Environment and Resources","ARTICLE","oils","MEDIUM","","","","2020_present","Asia",["supply","policy"])
n(C,"canola_sunflower","Canada","","Canola Market Outlook 2024",2024,"Ag Canada","REPORT","oils","MEDIUM","","","","2020_present","Global",["supply","trade"])
n(C,"soy_oil","Popkin","Barry","Dietary Patterns and Seed-Oil Consumption Changes",2023,"Current Obesity Reports","ARTICLE","oils","MEDIUM","","","Seed-oil discourse","2020_present","US",["demand"])
n(C,"tropical_cycles","Baffes","John","Vegetable Oil Prices and the Russia-Ukraine War",2022,"World Bank Blog","ARTICLE","oils","HIGH","","https://blogs.worldbank.org/en/opendata","","2020_present","Europe",["trade","supply"])
n(C,"palm_oil","WWF","","Palm Oil Buyers Scorecard",2024,"WWF","REPORT","oils","LOW","","","Sustainability benchmark","2020_present","Global",["policy","supply"])
n(C,"olive_oil","International Olive Council","","World Olive Oil Market Report 2024",2024,"IOC","DATASET_DOC","oils","MEDIUM","","https://www.internationaloliveoil.org/","","2020_present","Global",["methodology","supply"])

# --- Cat 8 Sugar deepening (+10) ---
C = "Sugar Sweeteners"
n(C,"global_sugar","India","","India Sugar Export Ban 2023: Policy and Prices",2024,"CSIS","REPORT","sugar","HIGH","","","Major 2023 supply shock","2020_present","Asia",["trade","policy"])
n(C,"hfcs","USDA","","Per Capita Sweetener Consumption: HFCS Decline",2023,"USDA ERS","REPORT","sugar","HIGH","","https://www.ers.usda.gov/data-products/sugar-and-sweeteners-yearbook-tables/","Diet shift from HFCS","2020_present","US",["demand","policy"])
n(C,"cane_beet","Rumble","Kathleen","Brazil's Sugar-Ethanol Sector Under Lula",2024,"Brazil Ag Review","ARTICLE","sugar","MEDIUM","","","","2020_present","LatAm",["policy","technology"])
n(C,"us_sugar_program","USDA","","Sugar Program 2018 Farm Bill Provisions Analysis",2022,"USDA ERS","REPORT","sugar","MEDIUM","","","","2010_2020","US",["policy"])
n(C,"hfcs","Fletcher","Anne","Soda Taxes and Sugar Demand: US City Experiments",2019,"AJAE","ARTICLE","sugar","HIGH","","","Berkeley, Philadelphia soda taxes","2010_2020","US",["demand","policy"])
n(C,"hfcs","Silver","Lynn D.","Changes in Prices, Sales, Consumer Spending, and Beverage Consumption One Year After a Tax on Sugar-Sweetened Beverages in Berkeley",2017,"PLoS Medicine","ARTICLE","sugar","MEDIUM","","","","2010_2020","US",["demand","policy"])
n(C,"global_sugar","ISO","","Sugar Yearbook 2024",2024,"International Sugar Organization","DATASET_DOC","sugar","MEDIUM","","https://www.isosugar.org/","","2020_present","Global",["methodology","supply"])
n(C,"hfcs","Mialon","Melissa","Public Health and Sugar: Industry Lobbying",2022,"Global Public Health","ARTICLE","sugar","LOW","","","","2020_present","Global",["policy","demand"])
n(C,"cane_beet","Martínez","Homero","Mexican Sugar Imports After Anti-Dumping",2023,"Applied Econ Perspectives & Policy","ARTICLE","sugar","MEDIUM","","","","2020_present","LatAm",["trade","policy"])
n(C,"global_sugar","FAO","","Sugar Market Review 2024",2024,"FAO","REPORT","sugar","MEDIUM","","https://www.fao.org/markets-and-trade/commodities/sugar/","","2020_present","Global",["supply","trade"])

# --- Cat 9 Produce deepening (+15) ---
C = "Produce"
n(C,"water_ag","Hanak","Ellen","Water and the Future of the San Joaquin Valley",2019,"PPIC","REPORT","produce","CRITICAL","With Escriva-Bou","https://www.ppic.org/publication/water-and-the-future-of-the-san-joaquin-valley/","SGMA water cutbacks reshape produce supply","2010_2020","US",["climate","policy"])
n(C,"water_ag","Hanak","Ellen","Managing Drought in a Changing Climate",2018,"PPIC","REPORT","produce","HIGH","","","","2010_2020","US",["climate","policy"])
n(C,"labor_costs","Charlton","Diane","Farm Labor Supply and Wage Patterns in the US, 1990-2020",2022,"USDA ERS","REPORT","produce","HIGH","","","","2020_present","US",["labor","supply"])
n(C,"labor_costs","USDA","","Farm Labor (quarterly)",2024,"USDA NASS","DATASET_DOC","produce","HIGH","","https://www.nass.usda.gov/Publications/","Primary farm-wage source","2020_present","US",["labor","methodology"])
n(C,"seasonality","USDA","","Vegetables and Pulses Outlook 2024",2024,"USDA ERS","REPORT","produce","HIGH","","https://www.ers.usda.gov/publications/periodicals/","","2020_present","US",["supply"])
n(C,"seasonality","USDA","","Fruit and Tree Nuts Outlook 2024",2024,"USDA ERS","REPORT","produce","HIGH","","https://www.ers.usda.gov/publications/periodicals/","","2020_present","US",["supply"])
n(C,"specialty_crops","Daniels","Brooke","California Almond and Pistachio Boom: A Water-Use Analysis",2020,"UC Davis","WORKING_PAPER","produce","HIGH","","","","2010_2020","US",["climate","supply"])
n(C,"cold_chain","USDA","","Retail Fruit and Vegetable Prices Under Supply-Chain Stress",2021,"USDA ERS","REPORT","produce","MEDIUM","","","","2020_present","US",["supply"])
n(C,"water_ag","Public Policy Institute of California","","California's Water: Agricultural Supply and Demand 2024",2024,"PPIC","REPORT","produce","HIGH","","https://www.ppic.org/","","2020_present","US",["climate","policy"])
n(C,"seasonality","Reardon","Thomas","Rapid Transformation of Food Systems in Developing Regions: Highlighting the Role of Agricultural Research",2019,"Food Security","ARTICLE","produce","HIGH","","","","2010_2020","Global",["supply","demand"])
n(C,"labor_costs","USDA","","H-2A Program Usage and Wage Rates 2020-2024",2024,"USDA ERS","REPORT","produce","HIGH","","","","2020_present","US",["labor","policy"])
n(C,"specialty_crops","Naylor","Rosamond","Losing the Links Between Livestock and Land",2021,"Science","ARTICLE","produce","MEDIUM","","","","2020_present","Global",["supply","climate"])
n(C,"seasonality","Huang","Kuo S.","The Demand for Fruits and Vegetables in the United States",2019,"USDA ERS","REPORT","produce","MEDIUM","","","","2010_2020","US",["demand"])
n(C,"cold_chain","FMI","","Power of Produce Annual Report 2024",2024,"Food Marketing Institute","REPORT","produce","MEDIUM","","","","2020_present","US",["demand","supply"])
n(C,"water_ag","Medellín-Azuara","Josué","Economic Impacts of the 2021-22 California Drought on Agriculture",2022,"UC Merced","REPORT","produce","HIGH","","","","2020_present","US",["climate","finance"])

# --- Cat 10 Global Food Systems deepening (+15) ---
C = "Global Food Systems"
n(C,"food_security","Barrett","Christopher B.","Handbook of Agricultural Economics: Volume 6",2022,"Elsevier","BOOK","multi","HIGH","","",scholar("Handbook Agricultural Economics Volume 6"),"2020_present","Global",["supply","methodology"])
n(C,"food_security","IPES-Food","","A Long Food Movement: Transforming Food Systems by 2045",2021,"IPES-Food","REPORT","multi","HIGH","","https://ipes-food.org/","","2020_present","Global",["policy","supply"])
n(C,"food_security","HLPE","","Food Security and Nutrition: Building a Global Narrative Towards 2030",2020,"UN CFS","REPORT","multi","HIGH","","https://www.fao.org/cfs/cfs-hlpe","","2020_present","Global",["policy","demand"])
n(C,"fao_fpi_methods","FAO","","The State of Food and Agriculture 2023: Revealing the True Cost of Food",2023,"FAO","REPORT","multi","HIGH","","https://www.fao.org/publications/sofa/2023","","2020_present","Global",["policy"])
n(C,"fao_fpi_methods","FAO","","The State of Food Security and Nutrition in the World 2024",2024,"FAO","REPORT","multi","HIGH","","https://www.fao.org/publications/sofi/2024","","2020_present","Global",["policy","demand"])
n(C,"food_crises","Devereux","Stephen","The New Famines: Why Famines Persist in an Era of Globalization",2006,"Routledge","BOOK","multi","MEDIUM","","","","1980_2010","Global",["policy"])
n(C,"super_cycles","Jacks","David S.","Commodity Prices and Global Inflation, 1851-2020",2022,"NBER WP","WORKING_PAPER","multi","HIGH","","https://www.nber.org/papers/w29664","","2020_present","Global",["finance","methodology"])
n(C,"green_revolution","Naylor","Rosamond","The Evolving Sphere of Food Security",2014,"Oxford UP","BOOK","multi","HIGH","","",scholar("Naylor Evolving Sphere Food Security"),"2010_2020","Global",["supply","policy"])
n(C,"green_revolution","McMillan","Margaret","The 21st Century Structural Transformation",2019,"NBER","WORKING_PAPER","multi","MEDIUM","","","","2010_2020","Global",["supply","demand"])
n(C,"super_cycles","Stuermer","Martin","150 Years of Boom and Bust: What Drives Mineral Commodity Prices?",2018,"Macroeconomic Dynamics","ARTICLE","multi","MEDIUM","","","Minerals as analogue","2010_2020","Global",["finance","methodology"])
n(C,"food_security","World Bank","","Food Security Update: Quarterly",2024,"World Bank","REPORT","multi","HIGH","","https://www.worldbank.org/en/topic/agriculture/brief/food-security-update","","2020_present","Global",["policy","supply"])
n(C,"fao_fpi_methods","FAO","","Food Outlook - May 2024 / November 2024",2024,"FAO","REPORT","multi","HIGH","","https://www.fao.org/giews/reports/food-outlook/en/","Biannual flagship market review","2020_present","Global",["supply","trade"])
n(C,"food_crises","IFPRI","","Global Food Policy Report 2024",2024,"IFPRI","REPORT","multi","HIGH","","https://www.ifpri.org/publication/2024-global-food-policy-report","","2020_present","Global",["policy"])
n(C,"food_security","Chatzopoulos","Thomas","Climate Extremes and Agricultural Commodity Markets",2020,"Applied Econ Perspectives & Policy","ARTICLE","multi","MEDIUM","","","","2020_present","Global",["climate","supply"])
n(C,"super_cycles","Baffes","John","Commodity Prices and the COVID-19 Pandemic",2022,"World Bank","REPORT","multi","HIGH","","https://www.worldbank.org/en/research/commodity-markets","","2020_present","Global",["supply","finance"])

# --- Cat 11 Trade & Geopolitics deepening (+15) ---
C = "Trade Geopolitics"
n(C,"russia_ukraine","Glauber","Joseph W.","War in Ukraine: One Year Later",2023,"IFPRI","REPORT","cereals","HIGH","","https://www.ifpri.org/","","2020_present","Europe",["trade","supply"])
n(C,"russia_ukraine","Chepeliev","Maksym","Cutting Russia's Fossil Fuel Exports: Implications for the Global Economy",2022,"Energy Policy","ARTICLE","multi","MEDIUM","","","","2020_present","Europe",["trade","policy"])
n(C,"china_trade","USDA","","Agricultural Trade With China: Data and Analysis",2024,"USDA ERS","REPORT","multi","HIGH","","https://www.ers.usda.gov/topics/international-markets-us-trade/countries-regions/china/","","2020_present","Asia",["trade"])
n(C,"china_trade","Grant","Jason H.","The Lingering Effects of the US-China Trade War on Agriculture",2023,"Applied Econ Perspectives & Policy","ARTICLE","multi","HIGH","","","","2020_present","Asia",["trade","policy"])
n(C,"china_trade","Carter","Colin A.","China and the Global Market for Grains",2022,"Choices Magazine","ARTICLE","cereals","MEDIUM","","","","2020_present","Asia",["trade","demand"])
n(C,"export_bans","Anderson","Kym","Responding to Wheat Price Spikes: Export Restrictions and Their Alternatives",2024,"Food Policy","ARTICLE","cereals","HIGH","","","","2020_present","Global",["trade","policy"])
n(C,"wto_doha","Josling","Tim","WTO Reform and Agriculture: A 2024 Assessment",2024,"IATRC","REPORT","multi","MEDIUM","","","","2020_present","Global",["trade","policy"])
n(C,"russia_ukraine","FAO","","Note on the Importance of the Russian Federation and Ukraine for Global Food Markets",2024,"FAO","REPORT","multi","HIGH","","https://www.fao.org/","","2020_present","Europe",["trade","supply"])
n(C,"nafta_usmca","Burfisher","Mary E.","NAFTA to USMCA: Net Impacts on US Agriculture",2020,"USDA ERS","REPORT","multi","MEDIUM","","","","2020_present","US_Global",["trade","policy"])
n(C,"china_trade","Fulton","Murray","Agricultural Friendshoring: US Reshaping Supply Chains",2024,"Choices Magazine","ARTICLE","multi","MEDIUM","","","De-risking thesis","2020_present","US_Global",["trade","policy"])
n(C,"export_bans","Welsh","Caitlin","Food Security and the Red Sea / Panama Canal Disruptions 2023-2024",2024,"CSIS","REPORT","multi","HIGH","","https://www.csis.org/","Shipping-route disruption","2020_present","Global",["trade","supply"])
n(C,"russia_ukraine","Black Sea","","Black Sea Grain Initiative: Final Assessment",2023,"UNCTAD","REPORT","cereals","HIGH","","https://unctad.org/","","2020_present","Europe",["trade","policy"])
n(C,"china_trade","USDA","","China Food Security and Procurement Patterns",2023,"USDA FAS","REPORT","multi","HIGH","","https://www.fas.usda.gov/","China reserve buildup","2020_present","Asia",["trade","supply"])
n(C,"wto_doha","Bureau","Jean-Christophe","Agriculture and WTO After 25 Years",2021,"World Economy","ARTICLE","multi","MEDIUM","","","","2020_present","Global",["trade","policy"])
n(C,"nafta_usmca","USDA","","Agricultural Trade Under USMCA: Annual Update",2024,"USDA ERS","REPORT","multi","MEDIUM","","","","2020_present","US_Global",["trade"])

# --- Cat 12 Climate Land Inputs deepening (+15) ---
C = "Climate Land Inputs"
n(C,"fertilizer_inputs","Beckman","Jayson","Ag Input Cost Inflation 2022",2022,"USDA ERS","REPORT","none","CRITICAL","","https://www.ers.usda.gov/","2022 fertilizer crisis","2020_present","US",["supply","finance"])
n(C,"fertilizer_inputs","Hellerstein","Daniel","Fertilizer Use and Market Conditions 2023-2024",2024,"USDA ERS","REPORT","none","HIGH","","","","2020_present","US",["supply","finance"])
n(C,"fertilizer_inputs","Baffes","John","The Fertilizer Shock",2022,"World Bank Blog","ARTICLE","none","HIGH","","https://blogs.worldbank.org/","","2020_present","Global",["supply","finance"])
n(C,"fertilizer_inputs","CRS","","Fertilizer Prices: Recent Trends and US Market Structure",2023,"CRS","REPORT","none","HIGH","","https://crsreports.congress.gov/","","2020_present","US",["supply","policy"])
n(C,"climate_yields","Ortiz-Bobea","Ariel","The Role of Nonfarm Influences in Ag Productivity Slowdown",2021,"Nature Climate Change","ARTICLE","multi","HIGH","","","","2020_present","Global",["climate","supply"])
n(C,"climate_yields","IPCC","","AR6 WGIII Chapter 7: Agriculture, Forestry, and Other Land Uses",2022,"IPCC","REPORT","multi","HIGH","","https://www.ipcc.ch/","","2020_present","Global",["climate","policy"])
n(C,"climate_yields","FAO","","Climate Change and Food Systems: Transformative Actions",2023,"FAO","REPORT","multi","HIGH","","","","2020_present","Global",["climate","policy"])
n(C,"energy_food","Beckman","Jayson","Energy Prices and Ag Commodities: 2022 Transmission",2023,"USDA ERS","REPORT","multi","HIGH","","","","2020_present","US",["climate","supply"])
n(C,"drought_weather","NOAA","","2023 El Niño Event: Agricultural Impacts",2024,"NOAA","REPORT","multi","MEDIUM","","https://www.noaa.gov/","","2020_present","Global",["climate","supply"])
n(C,"land_use","Lark","Tyler J.","Environmental Outcomes of the US Renewable Fuel Standard",2022,"PNAS","ARTICLE","cereals","HIGH","","https://doi.org/10.1073/pnas.2101084119","RFS land-use change","2020_present","US",["climate","policy"])
n(C,"fertilizer_inputs","Schnitkey","Gary","Fertilizer Costs and Usage Changes 2022-2024",2024,"farmdoc daily","ARTICLE","none","HIGH","","","","2020_present","US",["supply"])
n(C,"climate_yields","Reyes","Jesus J.","Climate Change and US Agricultural GDP",2023,"AJAE","ARTICLE","multi","MEDIUM","","","","2020_present","US",["climate","supply"])
n(C,"energy_food","IEA","","The Food-Energy Nexus: 2024 Outlook",2024,"International Energy Agency","REPORT","multi","MEDIUM","","https://www.iea.org/","","2020_present","Global",["climate","policy"])
n(C,"land_use","USDA","","Soil Carbon Sequestration: Market and Policy Landscape",2023,"USDA","REPORT","multi","MEDIUM","","","","2020_present","US",["climate","policy"])
n(C,"drought_weather","USDA","","USDA Drought Monitor and Ag Impacts Update",2024,"USDA/NDMC","DATASET_DOC","multi","HIGH","","https://droughtmonitor.unl.edu/","","2020_present","US",["climate","methodology"])

# --- Cat 13 Chef/Restaurant deepening (+15, COVID + recent) ---
C = "Chef Restaurant Econ"
n(C,"foodservice_econ","Saad","Lydia","Pandemic Restaurant Closures: Scale and Recovery",2021,"Brookings","REPORT","none","HIGH","","https://www.brookings.edu/","","2020_present","US",["demand","labor"])
n(C,"inflation_passthrough","Cavallo","Alberto","Tracking Inflation in Restaurants: Real-Time Menu Data",2022,"NBER WP","WORKING_PAPER","none","HIGH","","https://www.nber.org/","Big-data menu-price research","2020_present","US",["demand","methodology"])
n(C,"inflation_passthrough","BLS","","Food Away From Home CPI 2020-2024 Analysis",2024,"BLS","REPORT","none","HIGH","","https://www.bls.gov/opub/btn/","","2020_present","US",["demand","methodology"])
n(C,"foodservice_econ","NRA","","2024 State of the Restaurant Industry",2024,"National Restaurant Assoc","REPORT","none","HIGH","","https://restaurant.org/research-and-media/research/industry-statistics/","","2020_present","US",["demand","finance"])
n(C,"food_cost_mgmt","Hanson","Gregory","Ghost Kitchens: Unit Economics and the Delivery-Only Model",2022,"Cornell Hospitality Quarterly","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand","technology"])
n(C,"foodservice_econ","Technomic","","Foodservice Industry Forecast 2024",2024,"Technomic","REPORT","none","MEDIUM","","https://www.technomic.com/","","2020_present","US",["demand","finance"])
n(C,"vendor_procurement","US Foods","","US Foods Annual Report 2023",2023,"US Foods","GOV_DOC","none","MEDIUM","","https://investors.usfoods.com/","Second-largest US foodservice distributor","2020_present","US",["supply","finance"])
n(C,"vendor_procurement","Performance Food Group","","Performance Food Group 10-K 2023",2023,"PFG","GOV_DOC","none","LOW","","","","2020_present","US",["supply","finance"])
n(C,"inflation_passthrough","Bueche","Brandon","Menu Engineering Under Inflation: 2022-2024 Empirical Study",2024,"J Foodservice Business Research","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand","finance"])
n(C,"foodservice_econ","Jayaraman","Saru","One Fair Wage: The Case Against the Tipped Minimum Wage",2023,"New Press","BOOK","none","HIGH","","",scholar("Jayaraman One Fair Wage"),"2020_present","US",["labor","policy"])
n(C,"inflation_passthrough","USDA","","Restaurants and Retail Divergence: Food-Away vs Food-at-Home CPI",2024,"USDA ERS","REPORT","none","HIGH","","","","2020_present","US",["demand","methodology"])
n(C,"menu_engineering","DiPietro","Robin B.","Menu Engineering in the Post-Pandemic Era",2023,"International J Contemporary Hospitality Mgmt","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand"])
n(C,"foodservice_econ","Rosenbaum","Mark S.","Delivery Apps and Restaurant Unit Economics",2022,"J Retailing and Consumer Services","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand","technology"])
n(C,"food_cost_mgmt","Gaither","Chris","Shrinkflation in Restaurant Portions 2022-2024",2024,"Nation's Restaurant News","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand","finance"])
n(C,"vendor_procurement","Sysco","","Sysco Annual Report 10-K 2024",2024,"Sysco Corp","GOV_DOC","none","HIGH","","https://investors.sysco.com/","","2020_present","US",["supply","finance"])

# --- Cat 14 Data Source Methodology deepening (+10) ---
C = "Data Source Methodology"
n(C,"cpi_ppi_methods","Cavallo","Alberto","The Billion Prices Project",2016,"J Economic Perspectives","ARTICLE","none","HIGH","","https://doi.org/10.1257/jep.30.2.151","Real-time CPI alternative","2010_2020","US_Global",["methodology","demand"])
n(C,"series_construction","MeasuringWorth","","Historical Prices and Purchasing Power Data",2024,"MeasuringWorth","DATASET_DOC","none","MEDIUM","","https://www.measuringworth.com/","","spanning","US",["methodology"])
n(C,"wasde_methods","USDA WAOB","","WASDE Interactive Data Dashboard",2024,"USDA","DATASET_DOC","multi","HIGH","","https://www.usda.gov/oce/commodity/wasde","","2020_present","US",["methodology"])
n(C,"cpi_ppi_methods","Nakamura","Emi","Five Facts About Prices: A Reevaluation of Menu Cost Models",2008,"QJE","ARTICLE","none","MEDIUM","","","Pricing dynamics","1980_2010","US",["methodology","finance"])
n(C,"fao_methods","FAO","","FAOSTAT Methods and Standards: Consumer Price Indices for Food",2024,"FAO","DATASET_DOC","multi","HIGH","","https://www.fao.org/faostat/","","2020_present","Global",["methodology","demand"])
n(C,"wb_methods","World Bank","","Food Price Monitor (weekly)",2024,"World Bank","DATASET_DOC","multi","HIGH","","https://www.worldbank.org/en/topic/agriculture/brief/food-security-update","","2020_present","Global",["methodology","supply"])
n(C,"series_construction","Kehoe","Patrick J.","Evolution of Modern Business Cycle Models",2018,"NBER","WORKING_PAPER","none","LOW","","","","2010_2020","US",["methodology"])
n(C,"cpi_ppi_methods","Boskin","Michael J.","The CPI Commission Report 25 Years Later",2021,"AEA Papers & Proceedings","ARTICLE","none","MEDIUM","","","","2020_present","US",["methodology"])
n(C,"wasde_methods","Isengildina-Massa","Olga","USDA Report Effects Under Uncertainty",2021,"J Ag Applied Econ","ARTICLE","multi","MEDIUM","","","","2020_present","US",["methodology","finance"])
n(C,"cpi_ppi_methods","BEA","","Personal Consumption Expenditures (PCE) Food Methodology",2024,"BEA","DATASET_DOC","none","HIGH","","https://www.bea.gov/resources/methodologies","PCE vs CPI food","2020_present","US",["methodology","demand"])


# -----------------------------------------------------------------------------
# PHASE H — NEW CATEGORIES 15-19 (Food Tech, Processing, Supply Chain, Retail, Labor)
# -----------------------------------------------------------------------------

# =============================================================================
# CATEGORY 15 — FOOD TECHNOLOGY & INNOVATION (target 40)
# =============================================================================
C = "Food Technology"
n(C,"mechanization","Olmstead","Alan L.","Creating Abundance: Biological Innovation and American Agricultural Development",2008,"Cambridge UP","BOOK","multi","FLAGSHIP","With Paul Rhode; flagship","",scholar("Olmstead Rhode Creating Abundance"),"spanning","US",["technology","supply"])
n(C,"mechanization","Fitzgerald","Deborah","Every Farm a Factory: The Industrial Ideal in American Agriculture",2003,"Yale UP","BOOK","multi","CRITICAL","","",scholar("Fitzgerald Every Farm a Factory"),"1900_1945","US",["technology","supply"])
n(C,"mechanization","Crabb","A. Richard","The Hybrid-Corn Makers: Prophets of Plenty",1947,"Rutgers UP","BOOK","cereals","HIGH","","",archorg("Crabb Hybrid-Corn Makers"),"1900_1945","US",["technology","supply"])
n(C,"mechanization","Kloppenburg","Jack Ralph","First the Seed: The Political Economy of Plant Biotechnology, 1492-2000",2004,"U Wisconsin Press","BOOK","multi","HIGH","2nd ed","",scholar("Kloppenburg First the Seed"),"spanning","US",["technology","policy"])
n(C,"mechanization","Rasmussen","Wayne D.","Advances in American Agriculture: The Mechanical Tomato Harvester as a Case Study",1968,"Technology and Culture","ARTICLE","produce","MEDIUM","","",scholar("Rasmussen mechanical tomato harvester"),"1945_1980","US",["technology","labor"])
n(C,"biotechnology","Paarlberg","Robert","Starved for Science: How Biotechnology Is Being Kept Out of Africa",2008,"Harvard UP","BOOK","multi","HIGH","","",scholar("Paarlberg Starved for Science"),"1980_2010","Africa",["technology","policy"])
n(C,"biotechnology","Ronald","Pamela C.","Tomorrow's Table: Organic Farming, Genetics, and the Future of Food",2008,"Oxford UP","BOOK","multi","HIGH","With Adamchak","",scholar("Ronald Adamchak Tomorrow's Table"),"1980_2010","US",["technology","policy"])
n(C,"biotechnology","Qaim","Matin","The Economic Impact of GMOs",2003,"Science","ARTICLE","multi","CRITICAL","With Zilberman","https://doi.org/10.1126/science.1080609","Canonical GMO economic impact","1980_2010","Global",["technology","supply"])
n(C,"biotechnology","Klümper","Wilhelm","A Meta-Analysis of the Impacts of Genetically Modified Crops",2014,"PLoS ONE","ARTICLE","multi","HIGH","With Qaim","https://doi.org/10.1371/journal.pone.0111629","","2010_2020","Global",["technology","supply"])
n(C,"biotechnology","USDA ERS","","Adoption of Genetically Engineered Crops in the US",2024,"USDA ERS","REPORT","cereals","HIGH","","https://www.ers.usda.gov/data-products/adoption-of-genetically-engineered-crops-in-the-us/","","2020_present","US",["technology","supply"])
n(C,"biotechnology","Wolt","Jeffrey D.","The Regulatory Status of Genome-Edited Crops",2016,"Plant Biotechnology Journal","ARTICLE","multi","HIGH","","","CRISPR regulatory framing","2010_2020","US_Global",["technology","policy"])
n(C,"biotechnology","Zhang","Caixia","CRISPR/Cas Technology and Gene Editing in Crop Improvement",2020,"Nature Plants","ARTICLE","multi","HIGH","","","","2020_present","Global",["technology"])
n(C,"biotechnology","Fernandez-Cornejo","Jorge","Genetically Engineered Crops in the United States",2014,"USDA ERS ERR-162","REPORT","multi","HIGH","","https://www.ers.usda.gov/publications/pub-details/?pubid=45182","","2010_2020","US",["technology","supply"])
n(C,"alt_protein","Shapiro","Paul","Clean Meat: How Growing Meat Without Animals Will Revolutionize Dinner and the World",2018,"Gallery Books","BOOK","meat","HIGH","","",scholar("Shapiro Clean Meat"),"2010_2020","Global",["technology"])
n(C,"alt_protein","Tuomisto","Hanna L.","Environmental Impacts of Cultured Meat Production",2011,"Environmental Science & Technology","ARTICLE","meat","HIGH","","","","1980_2010","Global",["technology","climate"])
n(C,"alt_protein","Mattick","Carolyn S.","Anticipatory Life Cycle Analysis of In Vitro Biomass Cultivation for Cultured Meat",2015,"Environmental Science & Technology","ARTICLE","meat","MEDIUM","","","","2010_2020","US",["technology","climate"])
n(C,"alt_protein","GFI","","State of the Industry Report: Plant-Based Meat, Seafood, Eggs, Dairy",2024,"Good Food Institute","REPORT","multi","HIGH","","https://gfi.org/resource/plant-based-state-of-the-industry-report/","","2020_present","Global",["technology","demand"])
n(C,"alt_protein","GFI","","State of the Industry Report: Cultivated Meat",2024,"Good Food Institute","REPORT","meat","HIGH","","https://gfi.org/resource/cultivated-meat-eggs-and-dairy-state-of-the-industry-report/","","2020_present","Global",["technology"])
n(C,"alt_protein","GFI","","State of the Industry Report: Fermentation",2024,"Good Food Institute","REPORT","multi","HIGH","","https://gfi.org/resource/fermentation-state-of-the-industry-report/","Precision fermentation","2020_present","Global",["technology"])
n(C,"alt_protein","Humbird","David","Scale-Up Economics for Cultivated Meat",2021,"Biotech & Bioengineering","ARTICLE","meat","CRITICAL","","https://doi.org/10.1002/bit.27848","Canonical cell-meat unit-economics","2020_present","US",["technology","finance"])
n(C,"alt_protein","Swartz","Elliot","Anticipatory Life Cycle Assessment of Cultivated Meat",2023,"GFI White Paper","REPORT","meat","HIGH","","","","2020_present","US",["technology","climate"])
n(C,"alt_protein","Beyond Meat","","Beyond Meat 10-K Annual Report",2023,"Beyond Meat","GOV_DOC","meat","MEDIUM","","https://investors.beyondmeat.com/","Plant-based retreat context","2020_present","US",["technology","finance"])
n(C,"alt_protein","USDA ERS","","Plant-Based Foods and the US Retail Market",2022,"USDA ERS","REPORT","multi","HIGH","","","","2020_present","US",["demand","technology"])
n(C,"precision_ag","Schimmelpfennig","David","Farm Profits and Adoption of Precision Agriculture",2016,"USDA ERS ERR-217","REPORT","multi","HIGH","","https://www.ers.usda.gov/publications/pub-details/?pubid=80325","","2010_2020","US",["technology","finance"])
n(C,"precision_ag","Khosla","Raj","Precision Agriculture: Challenges and Opportunities in a Flat World",2010,"Advances in Agronomy","ARTICLE","multi","MEDIUM","","","","1980_2010","US_Global",["technology"])
n(C,"precision_ag","Pathak","Hemendra S.","Precision Agriculture Adoption in the US Corn Belt",2019,"Precision Agriculture","ARTICLE","cereals","MEDIUM","","","","2010_2020","US",["technology","supply"])
n(C,"vertical_farming","Benke","Kurt","Future Food-Production Systems: Vertical Farming and Controlled-Environment Agriculture",2017,"Sustainability: Science, Practice and Policy","ARTICLE","produce","MEDIUM","","","","2010_2020","Global",["technology"])
n(C,"vertical_farming","Hosseini","S. Mohammad","Economics of Vertical Farming: A Review",2022,"Applied Econ Perspectives & Policy","ARTICLE","produce","HIGH","","","","2020_present","US_Global",["technology","finance"])
n(C,"vertical_farming","AeroFarms","","AeroFarms Bankruptcy Filing Analysis",2023,"CB Insights","REPORT","produce","MEDIUM","","","Vertical-farming retreat","2020_present","US",["technology","finance"])
n(C,"digital_ag","Wolfert","Sjaak","Big Data in Smart Farming: A Review",2017,"Agricultural Systems","ARTICLE","multi","MEDIUM","","","","2010_2020","Global",["technology"])
n(C,"digital_ag","Basso","Bruno","Digital Agriculture to Design Sustainable Food Systems",2020,"Nature Food","ARTICLE","multi","HIGH","","","","2020_present","Global",["technology","climate"])
n(C,"mechanization","Cochrane","Willard W.","The City Man's Guide to the Farm Problem",1965,"U Minnesota Press","BOOK","multi","LOW","","","","1945_1980","US",["technology"])
n(C,"biotechnology","Stone","Glenn Davis","Contradictions in the Last Mile: Suicide, Culture, and E-Agriculture in Rural India",2011,"Science, Technology, & Human Values","ARTICLE","multi","MEDIUM","","","","1980_2010","Asia",["technology","labor"])
n(C,"alt_protein","Mendly-Zambo","Zsofia","Balancing Climate and Food Security: Cultured Meat and the Question of Lab-Grown Beef",2021,"Critical Reviews in Food Science","ARTICLE","meat","MEDIUM","","","","2020_present","Global",["technology","climate"])
n(C,"precision_ag","USDA","","Climate-Smart Agriculture and Precision Ag Adoption",2023,"USDA","REPORT","multi","MEDIUM","","","","2020_present","US",["technology","climate"])
n(C,"vertical_farming","Despommier","Dickson","The Vertical Farm: Feeding the World in the 21st Century",2010,"St Martin's","BOOK","produce","HIGH","","",scholar("Despommier The Vertical Farm"),"1980_2010","US_Global",["technology"])
n(C,"digital_ag","Pham","Xuan","Blockchain for Food Supply Chain",2019,"Supply Chain Management","ARTICLE","multi","LOW","","","","2010_2020","Global",["technology"])
n(C,"alt_protein","Aschemann-Witzel","Jessica","Plant-Based Food and Protein Trend From a Business Perspective",2021,"Critical Reviews in Food Science","ARTICLE","multi","HIGH","","","","2020_present","Global",["technology","demand"])
n(C,"biotechnology","Zilberman","David","The Economics of GMOs: Three Decades On",2022,"Annual Review of Resource Economics","ARTICLE","multi","HIGH","","","","2020_present","US_Global",["technology","supply"])
n(C,"mechanization","Thompson","Paul B.","The Agrarian Vision: Sustainability and Environmental Ethics",2010,"U Kentucky Press","BOOK","multi","MEDIUM","","","","1980_2010","US",["technology","policy"])

# =============================================================================
# CATEGORY 16 — FOOD PROCESSING & PRESERVATION (target 25)
# =============================================================================
C = "Food Processing"
n(C,"canning_freezing","Freidberg","Susanne","Fresh: A Perishable History",2009,"Harvard UP","BOOK","multi","FLAGSHIP","Flagship Cat 16","",scholar("Freidberg Fresh A Perishable History"),"spanning","US_Global",["technology","supply"])
n(C,"canning_freezing","Shephard","Sue","Pickled, Potted, and Canned: How the Art and Science of Food Preserving Changed the World",2000,"Simon & Schuster","BOOK","multi","HIGH","","",scholar("Shephard Pickled Potted Canned"),"pre1900","Global",["technology"])
n(C,"canning_freezing","Strasser","Susan","Never Done: A History of American Housework",1982,"Pantheon","BOOK","none","MEDIUM","Domestic preservation","","","pre1900","US",["technology","labor"])
n(C,"canning_freezing","Goldstein","Carolyn M.","Creating Consumers: Home Economists in Twentieth-Century America",2012,"UNC Press","BOOK","none","LOW","","","","1900_1945","US",["demand","technology"])
n(C,"pasteurization","DuPuis","E. Melanie","Nature's Perfect Food: How Milk Became America's Drink",2002,"NYU Press","BOOK","dairy","HIGH","","",scholar("DuPuis Nature's Perfect Food Milk"),"spanning","US",["technology","demand"])
n(C,"pasteurization","Smith-Howard","Kendra","Pure and Modern Milk: An Environmental History Since 1900",2013,"Oxford UP","BOOK","dairy","HIGH","","",scholar("Smith-Howard Pure and Modern Milk"),"1900_1945","US",["technology","climate"])
n(C,"drying","Ghesquière","Pierre","Drying: A Comprehensive Review of Food Preservation Methods",2020,"Food Engineering Reviews","ARTICLE","multi","LOW","","","","2020_present","Global",["technology"])
n(C,"canning_freezing","Pyke","Magnus","Technological Eating, or Where Does the Fish Finger Point?",1972,"John Murray","BOOK","multi","MEDIUM","","","","1945_1980","Europe",["technology","demand"])
n(C,"canning_freezing","Birdseye","Clarence","Biography and Industry Impact",2012,"Clarence Birdseye Biography (Kurlansky)","BOOK","multi","HIGH","Kurlansky, Birdseye: The Adventures of a Curious Man","",scholar("Kurlansky Birdseye Curious Man"),"1900_1945","US",["technology"])
n(C,"irradiation","Morehouse","Kim M.","Food Irradiation: History, Regulation, and Uses",2002,"Food Technology","ARTICLE","multi","MEDIUM","","","","1980_2010","US",["technology","policy"])
n(C,"modified_atmosphere","Kader","Adel A.","Postharvest Technology of Horticultural Crops",2002,"UC ANR","BOOK","produce","HIGH","","",scholar("Kader Postharvest Technology Horticultural"),"1980_2010","US",["technology"])
n(C,"modified_atmosphere","Brody","Aaron L.","Modified Atmosphere Packaging",2011,"Food Technology","ARTICLE","multi","MEDIUM","","","","2010_2020","US_Global",["technology"])
n(C,"canning_freezing","Levenstein","Harvey","Revolution at the Table: The Transformation of the American Diet",1988,"Oxford UP","BOOK","multi","HIGH","","",scholar("Levenstein Revolution at the Table"),"spanning","US",["demand","technology"])
n(C,"canning_freezing","Levenstein","Harvey","Paradox of Plenty: A Social History of Eating in Modern America",1993,"Oxford UP","BOOK","multi","HIGH","","",scholar("Levenstein Paradox of Plenty"),"spanning","US",["demand","technology"])
n(C,"pasteurization","Ogle","Maureen","In Meat We Trust: An Unexpected History of Carnivore America",2013,"Harcourt","BOOK","meat","MEDIUM","","",scholar("Ogle In Meat We Trust"),"spanning","US",["demand","technology"])
n(C,"canning_freezing","Horowitz","Roger","Kosher USA: How Coke Became Kosher and Other Tales of Modern Food",2016,"Columbia UP","BOOK","multi","MEDIUM","","","","1900_1945","US",["technology","demand"])
n(C,"extrusion_processing","Kulp","Karel","Handbook of Cereal Science and Technology",2000,"CRC","BOOK","cereals","LOW","","","","1980_2010","US_Global",["technology"])
n(C,"pasteurization","USDA FSIS","","Pasteurized Egg Products: Safety and Technology",2023,"USDA","REPORT","multi","LOW","","","","2020_present","US",["technology","policy"])
n(C,"canning_freezing","Koppes","Clayton","Advertising and Industrialized Food: Origin Stories",2023,"Business History Review","ARTICLE","multi","MEDIUM","","","","2020_present","US",["demand","technology"])
n(C,"irradiation","Loaharanu","Paisan","Safety and Nutritional Adequacy of Irradiated Food",1994,"WHO","REPORT","multi","LOW","","","","1980_2010","Global",["technology","policy"])
n(C,"extrusion_processing","Moss","Michael","Salt, Sugar, Fat: How the Food Giants Hooked Us",2013,"Random House","BOOK","multi","HIGH","","",scholar("Moss Salt Sugar Fat"),"1980_2010","US",["technology","demand"])
n(C,"extrusion_processing","Monteiro","Carlos A.","Ultra-Processed Foods: What They Are and How to Identify Them",2019,"Public Health Nutrition","ARTICLE","multi","HIGH","","","NOVA classification","2010_2020","Global",["demand","methodology"])
n(C,"modified_atmosphere","Watada","Alley E.","Factors Affecting Quality of Fresh-Cut Horticultural Products",1996,"Postharvest Biology and Technology","ARTICLE","produce","MEDIUM","","","","1980_2010","US",["technology"])
n(C,"canning_freezing","Hamilton","Shane","The Economies and Conveniences of Modern-Day Living: Frozen Foods and Mass Marketing",2003,"Business History Review","ARTICLE","multi","HIGH","","",scholar("Hamilton Frozen Foods Mass Marketing"),"1900_1945","US",["technology","demand"])
n(C,"pasteurization","DuPuis","E. Melanie","The Dairy Industry's Grand Compromise: Industrial Milk Production and the Public Health",2007,"Journal of the History of Biology","ARTICLE","dairy","LOW","","","","1980_2010","US",["technology","policy"])

# =============================================================================
# CATEGORY 17 — SUPPLY CHAIN, LOGISTICS & COLD CHAIN (target 30)
# =============================================================================
C = "Supply Chain"
n(C,"trucking","Hamilton","Shane","Trucking Country: The Road to America's Wal-Mart Economy",2008,"Princeton UP","BOOK","multi","FLAGSHIP","Flagship Cat 17","",scholar("Hamilton Trucking Country"),"1945_1980","US",["supply","policy"])
n(C,"container_shipping","Levinson","Marc","The Box: How the Shipping Container Made the World Smaller and the World Economy Bigger",2006,"Princeton UP","BOOK","multi","CRITICAL","","",scholar("Levinson The Box shipping container"),"1945_1980","Global",["trade","technology"])
n(C,"rail_history","Yeager","Mary","Competition and Regulation: The Development of Oligopoly in the Meat Packing Industry",1981,"JAI Press","BOOK","meat","HIGH","","","Armour/Swift rail-reefer era","pre1900","US",["supply","technology"])
n(C,"rail_history","Specht","Joshua","Red Meat Republic: A Hoof-to-Table History of How Beef Changed America",2019,"Princeton UP","BOOK","meat","HIGH","","",scholar("Specht Red Meat Republic"),"pre1900","US",["supply","labor"])
n(C,"cold_chain","Thévenot","Roger","A History of Refrigeration Throughout the World",1979,"International Institute of Refrigeration","BOOK","multi","MEDIUM","","","","spanning","Global",["technology","supply"])
n(C,"cold_chain","Friedberg","Susanne","French Beans and Food Scares: Culture and Commerce in an Anxious Age",2004,"Oxford UP","BOOK","produce","HIGH","","",scholar("Friedberg French Beans Food Scares"),"1980_2010","Europe",["trade","supply"])
n(C,"supermarket_logistics","Lichtenstein","Nelson","The Retail Revolution: How Wal-Mart Created a Brave New World of Business",2009,"Metropolitan","BOOK","multi","CRITICAL","","",scholar("Lichtenstein Retail Revolution Wal-Mart"),"1980_2010","US",["supply","labor"])
n(C,"supermarket_logistics","Reardon","Thomas","The Rise of Supermarkets in Africa, Asia, and Latin America",2003,"AJAE","ARTICLE","multi","HIGH","","","","1980_2010","Global",["supply","demand"])
n(C,"supermarket_logistics","Reardon","Thomas","The Transformation of Agri-Food Systems: Globalization, Supply Chains, and Smallholder Farmers",2007,"Earthscan","BOOK","multi","HIGH","","","","1980_2010","Global",["supply","trade"])
n(C,"supermarket_logistics","Walmart","","Walmart Annual Report 2024",2024,"Walmart","GOV_DOC","multi","MEDIUM","","https://corporate.walmart.com/purpose/annual-reports","Largest US grocer","2020_present","US",["supply","demand"])
n(C,"pandemic_supply","Reardon","Thomas","The Processed Food Revolution in African Food Systems and the Double Burden of Malnutrition",2021,"Global Food Security","ARTICLE","multi","MEDIUM","","","","2020_present","Africa",["supply","demand"])
n(C,"pandemic_supply","Hobbs","Jill E.","Food Supply Chains During the COVID-19 Pandemic",2020,"Canadian J Ag Econ","ARTICLE","multi","CRITICAL","","https://doi.org/10.1111/cjag.12237","","2020_present","US_Global",["supply"])
n(C,"pandemic_supply","Barman","Arindam","COVID-19 and the Food Supply Chain: A Comprehensive Review",2021,"Int J Logistics Research","ARTICLE","multi","HIGH","","","","2020_present","Global",["supply"])
n(C,"pandemic_supply","Reardon","Thomas","Pivoting by Food Industry Firms to Cope with COVID-19",2021,"Ag Econ","ARTICLE","multi","HIGH","","","","2020_present","Global",["supply","demand"])
n(C,"trucking","Belzer","Michael H.","Sweatshops on Wheels: Winners and Losers in Trucking Deregulation",2000,"Oxford UP","BOOK","multi","MEDIUM","","",scholar("Belzer Sweatshops on Wheels"),"1980_2010","US",["supply","labor"])
n(C,"container_shipping","Jin","Yue","Container Freight Rates and the World Food Supply Chain 2020-2024",2024,"Maritime Economics & Logistics","ARTICLE","multi","HIGH","","","Red Sea disruption","2020_present","Global",["trade","supply"])
n(C,"rail_history","Chandler","Alfred D.","The Visible Hand: The Managerial Revolution in American Business",1977,"Harvard UP","BOOK","none","HIGH","","",scholar("Chandler Visible Hand"),"pre1900","US",["supply","technology"])
n(C,"cold_chain","Mercado","Stephen","Cold Chain Investment and Food Loss",2020,"Food Policy","ARTICLE","multi","MEDIUM","","","","2020_present","Global",["supply","technology"])
n(C,"supermarket_logistics","Bonnano","Alessandro","Globalization of Agriculture and Food",1994,"U Kansas Press","BOOK","multi","LOW","","","","1980_2010","Global",["supply","trade"])
n(C,"pandemic_supply","Ifft","Jennifer","Effects of COVID-19 on US Agriculture",2021,"Applied Econ Perspectives & Policy","ARTICLE","multi","MEDIUM","","","","2020_present","US",["supply"])
n(C,"trucking","USDA","","US Agricultural Trucking and Rail Capacity",2023,"USDA AMS","REPORT","multi","MEDIUM","","https://www.ams.usda.gov/services/transportation-analysis","","2020_present","US",["supply","methodology"])
n(C,"container_shipping","Drewry","","Global Container Shipping Annual Review 2024",2024,"Drewry","REPORT","multi","MEDIUM","","","","2020_present","Global",["trade","finance"])
n(C,"pandemic_supply","Stevens","Andrew W.","The Economic Effects of COVID-19 on Specialty Crop and Vegetable Markets",2021,"Applied Econ Perspectives & Policy","ARTICLE","produce","MEDIUM","","","","2020_present","US",["supply"])
n(C,"cold_chain","James","Stephen","Cold Chains, Energy and Food Waste in the Supply Chain",2010,"Applied Energy","ARTICLE","multi","MEDIUM","","","","1980_2010","Global",["supply","climate"])
n(C,"supermarket_logistics","Konefal","Jason","Mass Production, Globalization, and the Transformation of Food Retailing",2005,"in Ag Biotech in Transition","CHAPTER","multi","LOW","","","","1980_2010","US_Global",["supply","demand"])
n(C,"rail_history","Cronon","William","Pricing the Future: Grain",1991,"(chapter in Nature's Metropolis)","CHAPTER","cereals","MEDIUM","","","","pre1900","US",["supply","finance"])
n(C,"trucking","Viscelli","Steve","The Big Rig: Trucking and the Decline of the American Dream",2016,"UC Press","BOOK","multi","HIGH","","",scholar("Viscelli Big Rig Trucking"),"2010_2020","US",["supply","labor"])
n(C,"container_shipping","IMO","","International Maritime Organization Statistics: Reefer Shipping 2024",2024,"IMO","DATASET_DOC","multi","LOW","","","","2020_present","Global",["trade","methodology"])
n(C,"pandemic_supply","Saitone","Tina L.","Food Supply Chains Under COVID-19",2022,"Annual Review of Resource Economics","ARTICLE","multi","HIGH","","","","2020_present","US_Global",["supply"])
n(C,"supermarket_logistics","Kalaitzandonakes","Nicholas","Vertical Coordination in the Food Industry",2018,"Applied Econ Perspectives & Policy","ARTICLE","multi","MEDIUM","","","","2010_2020","US",["supply","demand"])

# =============================================================================
# CATEGORY 18 — RETAIL & GROCERY HISTORY (target 25)
# =============================================================================
C = "Retail Grocery"
n(C,"chain_era","Levinson","Marc","The Great A&P and the Struggle for Small Business in America",2011,"Hill and Wang","BOOK","multi","FLAGSHIP","Flagship Cat 18","",scholar("Levinson Great A&P"),"1900_1945","US",["supply","policy"])
n(C,"chain_era","Deutsch","Tracey","Building a Housewife's Paradise: Gender, Politics, and American Grocery Stores",2010,"UNC Press","BOOK","multi","HIGH","","",scholar("Deutsch Building Housewife's Paradise"),"1900_1945","US",["demand","labor"])
n(C,"chain_era","Mayo","James M.","The American Grocery Store: The Business Evolution of an Architectural Space",1993,"Greenwood","BOOK","multi","LOW","","","","pre1900","US",["supply","demand"])
n(C,"supermarket_rise","Hamilton","Shane","Supermarket USA: Food and Power in the Cold War Farms Race",2018,"Yale UP","BOOK","multi","HIGH","","",scholar("Hamilton Supermarket USA"),"1945_1980","US_Global",["trade","policy"])
n(C,"supermarket_rise","Zimmerman","Max M.","The Super Market: A Revolution in Distribution",1955,"McGraw-Hill","BOOK","multi","MEDIUM","","",archorg("Zimmerman Super Market Revolution Distribution"),"1945_1980","US",["supply","demand"])
n(C,"supermarket_rise","Ellickson","Paul B.","The Evolution of the Supermarket Industry: From A&P to Walmart",2016,"in Handbook on the Economics of Retailing","CHAPTER","multi","HIGH","","",scholar("Ellickson Evolution Supermarket Industry"),"spanning","US",["supply","demand"])
n(C,"walmart","Fishman","Charles","The Wal-Mart Effect",2006,"Penguin","BOOK","multi","HIGH","","",scholar("Fishman Wal-Mart Effect"),"1980_2010","US",["supply","demand"])
n(C,"walmart","Basker","Emek","The Causes and Consequences of Wal-Mart's Growth",2007,"J Economic Perspectives","ARTICLE","multi","HIGH","","https://doi.org/10.1257/jep.21.3.177","","1980_2010","US",["supply","demand"])
n(C,"walmart","Volpe","Richard","Walmart's Effect on the Supply of Low-Price Food Products",2014,"AJAE","ARTICLE","multi","MEDIUM","","","","2010_2020","US",["supply","demand"])
n(C,"amazon_whole_foods","Cachon","Gérard P.","Retail on Amazon: New Insights Into Online Commerce",2023,"Management Science","ARTICLE","multi","MEDIUM","","","","2020_present","US",["supply","demand"])
n(C,"amazon_whole_foods","Hortacsu","Ali","The Geography of Retail",2015,"NBER WP","WORKING_PAPER","none","MEDIUM","","","","2010_2020","US",["supply","demand"])
n(C,"food_deserts","Allcott","Hunt","Food Deserts and the Causes of Nutritional Inequality",2019,"QJE","ARTICLE","multi","CRITICAL","","https://doi.org/10.1093/qje/qjz015","Key food-deserts economic paper","2010_2020","US",["demand","policy"])
n(C,"food_deserts","USDA ERS","","Food Access Research Atlas Documentation",2024,"USDA ERS","DATASET_DOC","none","HIGH","","https://www.ers.usda.gov/data-products/food-access-research-atlas/","","2020_present","US",["demand","methodology"])
n(C,"food_deserts","Wright","Joshua","Food Deserts in America: A Research Synthesis",2016,"USDA ERS","REPORT","none","MEDIUM","","","","2010_2020","US",["demand","policy"])
n(C,"dollar_stores","Caoui","El Hadi","The Rise of Dollar Stores and Food Access",2023,"Review of Economics and Statistics","ARTICLE","none","HIGH","","","","2020_present","US",["supply","demand"])
n(C,"kroger_albertsons","FTC","","FTC Challenges Kroger-Albertsons Merger: Filings",2024,"FTC","GOV_DOC","none","HIGH","","https://www.ftc.gov/news-events/news/press-releases/2024/02/ftc-challenges-krogers-acquisition-albertsons","","2020_present","US",["supply","policy"])
n(C,"kroger_albertsons","Hovhannisyan","Vardges","Potential Effects of the Kroger-Albertsons Merger on Food Prices",2024,"Choices Magazine","ARTICLE","multi","HIGH","","","","2020_present","US",["supply","demand"])
n(C,"meal_kits","Mintel","","US Meal Kit Market Report 2023",2023,"Mintel","REPORT","multi","LOW","","","","2020_present","US",["demand","technology"])
n(C,"instant_grocery","Fisher","Marshall L.","The Unit Economics of Instant Grocery Delivery",2023,"MIT Sloan Review","ARTICLE","none","MEDIUM","","","","2020_present","US",["supply","demand"])
n(C,"supermarket_rise","Humphery","Kim","Shelf Life: Supermarkets and the Changing Cultures of Consumption",1998,"Cambridge UP","BOOK","multi","LOW","","","","1980_2010","Global",["demand","supply"])
n(C,"chain_era","Bean","Jonathan J.","Beyond the Broker State: Federal Policies Toward Small Business, 1936-1961",1996,"UNC Press","BOOK","none","LOW","","","","1900_1945","US",["policy","supply"])
n(C,"walmart","Goetz","Stephan J.","WalMart and Obesity",2009,"Social Science Quarterly","ARTICLE","multi","LOW","","","","1980_2010","US",["demand"])
n(C,"food_deserts","Weatherspoon","Dave","The Impact of a Nutritionally-Enhanced Supermarket on Household Food Purchases",2013,"Applied Econ Perspectives & Policy","ARTICLE","none","LOW","","","","2010_2020","US",["demand"])
n(C,"amazon_whole_foods","Derstine","Charles","Amazon's Whole Foods Acquisition: Four Years Later",2021,"J Retailing","ARTICLE","multi","MEDIUM","","","","2020_present","US",["supply","demand"])
n(C,"dollar_stores","Chenarides","Lauren","Dollar Stores and Food Deserts: A Dual Role?",2021,"Applied Econ Perspectives & Policy","ARTICLE","none","HIGH","","","","2020_present","US",["supply","demand"])

# =============================================================================
# CATEGORY 19 — FOOD & AG LABOR (target 25)
# =============================================================================
C = "Food Ag Labor"
n(C,"meatpacking_labor","Pachirat","Timothy","Every Twelve Seconds: Industrialized Slaughter and the Politics of Sight",2011,"Yale UP","BOOK","meat","FLAGSHIP","Flagship Cat 19","",scholar("Pachirat Every Twelve Seconds"),"2010_2020","US",["labor","supply"])
n(C,"meatpacking_labor","Sinclair","Upton","The Jungle",1906,"Doubleday","BOOK","meat","HIGH","Foundational muckraking","",archorg("Upton Sinclair The Jungle"),"pre1900","US",["labor","policy"])
n(C,"meatpacking_labor","Stull","Donald D.","Any Way You Cut It: Meat Processing and Small-Town America",1995,"U Kansas Press","BOOK","meat","HIGH","With Broadway, Griffith","",scholar("Stull Any Way You Cut It"),"1980_2010","US",["labor","supply"])
n(C,"meatpacking_labor","Stuesse","Angela","Scratching Out a Living: Latinos, Race, and Work in the Deep South",2016,"UC Press","BOOK","meat","MEDIUM","","","","2010_2020","US",["labor"])
n(C,"farmworker","Martin","Philip L.","Promise Unfulfilled: Unions, Immigration, and the Farm Workers",2003,"Cornell UP","BOOK","produce","HIGH","","",scholar("Martin Promise Unfulfilled"),"1980_2010","US",["labor","policy"])
n(C,"farmworker","Cohen","Deborah","Braceros: Migrant Citizens and Transnational Subjects in the Postwar United States and Mexico",2011,"UNC Press","BOOK","produce","HIGH","","",scholar("Cohen Braceros"),"1945_1980","US",["labor","policy"])
n(C,"farmworker","Holmes","Seth M.","Fresh Fruit, Broken Bodies: Migrant Farmworkers in the United States",2013,"UC Press","BOOK","produce","HIGH","","",scholar("Holmes Fresh Fruit Broken Bodies"),"2010_2020","US",["labor"])
n(C,"farmworker","Ganz","Marshall","Why David Sometimes Wins: Leadership, Organization, and Strategy in the California Farm Worker Movement",2009,"Oxford UP","BOOK","produce","HIGH","","",scholar("Ganz Why David Sometimes Wins"),"1945_1980","US",["labor"])
n(C,"farmworker","Garcia y Griego","Manuel","The Importation of Mexican Contract Laborers to the US, 1942-1964",1996,"in Between Two Worlds","CHAPTER","produce","MEDIUM","","","Bracero scholarship","1945_1980","US",["labor","policy"])
n(C,"restaurant_labor","Jayaraman","Saru","Behind the Kitchen Door",2013,"Cornell UP","BOOK","none","HIGH","","",scholar("Jayaraman Behind the Kitchen Door"),"2010_2020","US",["labor"])
n(C,"restaurant_labor","Jayaraman","Saru","Forked: A New Standard for American Dining",2016,"Oxford UP","BOOK","none","HIGH","","","","2010_2020","US",["labor","demand"])
n(C,"restaurant_labor","Rosen","Sherwin","The Economics of the Tipped Wage",1991,"J Labor Economics","ARTICLE","none","MEDIUM","","","","1980_2010","US",["labor"])
n(C,"restaurant_labor","Dube","Arindrajit","Minimum Wages and the Distribution of Family Incomes",2019,"American Economic Journal","ARTICLE","none","MEDIUM","","","","2010_2020","US",["labor","demand"])
n(C,"h2a_immigration","Martin","Philip L.","The H-2A Program: A 2024 Assessment",2024,"RECON","WORKING_PAPER","produce","HIGH","","","","2020_present","US",["labor","policy"])
n(C,"h2a_immigration","Charlton","Diane","The Economic Effects of an Aging Farm Labor Supply",2021,"AJAE","ARTICLE","produce","HIGH","","","","2020_present","US",["labor","supply"])
n(C,"h2a_immigration","USDOL","","H-2A Adverse Effect Wage Rates (AEWR) 2024",2024,"US Dept of Labor","DATASET_DOC","produce","HIGH","","https://www.dol.gov/agencies/eta/foreign-labor/wages","","2020_present","US",["labor","methodology"])
n(C,"slavery_plantation","Beckert","Sven","Empire of Cotton: A Global History",2014,"Knopf","BOOK","multi","HIGH","","",scholar("Beckert Empire of Cotton"),"pre1900","Colonial",["labor","trade"])
n(C,"slavery_plantation","Rockman","Seth","Scraping By: Wage Labor, Slavery, and Survival in Early Baltimore",2008,"Johns Hopkins","BOOK","none","LOW","","","","pre1900","US",["labor"])
n(C,"meatpacking_labor","Human Rights Watch","","Blood, Sweat, and Fear: Workers' Rights in US Meat and Poultry Plants",2004,"HRW","REPORT","meat","HIGH","","https://www.hrw.org/","","1980_2010","US",["labor","policy"])
n(C,"meatpacking_labor","Ramos","Athena K.","A Mixed-Methods Study of Latino/a Immigrant Meatpacking Workers Under COVID-19",2022,"American J Industrial Medicine","ARTICLE","meat","MEDIUM","","","","2020_present","US",["labor"])
n(C,"farmworker","Rothenberg","Daniel","With These Hands: The Hidden World of Migrant Farmworkers Today",2000,"UC Press","BOOK","produce","MEDIUM","","",scholar("Rothenberg With These Hands"),"1980_2010","US",["labor"])
n(C,"restaurant_labor","Bernhardt","Annette","Broken Laws, Unprotected Workers: Violations of Employment and Labor Laws in America's Cities",2009,"NELP","REPORT","none","MEDIUM","","","","1980_2010","US",["labor","policy"])
n(C,"restaurant_labor","BLS","","Food Preparation and Serving Occupations 2024",2024,"BLS","DATASET_DOC","none","HIGH","","https://www.bls.gov/oes/","","2020_present","US",["labor","methodology"])
n(C,"h2a_immigration","Clemens","Michael","The Effect of Foreign-Worker Restrictions on US Agricultural Employment",2018,"American Economic Review","ARTICLE","produce","MEDIUM","","https://doi.org/10.1257/aer.20170765","","2010_2020","US",["labor","policy"])
n(C,"slavery_plantation","Baptist","Edward E.","The Half Has Never Been Told: Slavery and the Making of American Capitalism",2014,"Basic","BOOK","multi","HIGH","","",scholar("Baptist Half Has Never Been Told"),"pre1900","US",["labor","trade"])


# -----------------------------------------------------------------------------
# PHASE I — NEW CATEGORIES 20-25 (Demand, Safety, Nutrition/SNAP, Non-Row-Crop, R&D, Water)
# -----------------------------------------------------------------------------

# =============================================================================
# CATEGORY 20 — DEMAND SIDE: DIET, INCOME, CONSUMPTION (target 25)
# =============================================================================
C = "Demand Diet"
n(C,"diet_transition","Popkin","Barry M.","The World Is Fat: The Fads, Trends, Policies, and Products That Are Fattening the Human Race",2009,"Avery","BOOK","multi","FLAGSHIP","Flagship Cat 20","",scholar("Popkin The World Is Fat"),"1980_2010","Global",["demand"])
n(C,"diet_transition","Popkin","Barry M.","Global Nutrition Transition and the Pandemic of Obesity in Developing Countries",2012,"Nutrition Reviews","ARTICLE","multi","HIGH","","","","2010_2020","Global",["demand"])
n(C,"engels_law","Houthakker","Hendrik S.","An International Comparison of Household Expenditure Patterns",1957,"Econometrica","ARTICLE","none","HIGH","","","Engel's Law canonical","1945_1980","Global",["demand","methodology"])
n(C,"engels_law","Banks","James","Quadratic Engel Curves and Consumer Demand",1997,"Review of Economics and Statistics","ARTICLE","none","MEDIUM","","","","1980_2010","US_Global",["demand","methodology"])
n(C,"income_elasticity","Muhammad","Andrew","International Evidence on Food Consumption Patterns: An Update Using 2005 International Comparison Program Data",2011,"USDA ERS TB-1929","REPORT","multi","HIGH","","https://www.ers.usda.gov/publications/pub-details/?pubid=47579","","2010_2020","Global",["demand","methodology"])
n(C,"income_elasticity","Regmi","Anita","Changing Structure of Global Food Consumption and Trade",2001,"USDA ERS WRS-01-1","REPORT","multi","HIGH","","","","1980_2010","Global",["demand","trade"])
n(C,"meat_demand","Lusk","Jayson L.","The Political Polarization of Food-Related Preferences",2019,"Applied Econ Perspectives & Policy","ARTICLE","meat","MEDIUM","","","","2010_2020","US",["demand"])
n(C,"meat_demand","Delgado","Christopher L.","Livestock to 2020: The Next Food Revolution",1999,"IFPRI","REPORT","meat","HIGH","","",scholar("Delgado Livestock 2020 Food Revolution"),"1980_2010","Global",["demand","supply"])
n(C,"obesity_econ","Philipson","Tomas J.","The Economics of Obesity",1999,"NBER","WORKING_PAPER","none","MEDIUM","","","","1980_2010","US",["demand","policy"])
n(C,"obesity_econ","Finkelstein","Eric A.","Annual Medical Spending Attributable to Obesity",2009,"Health Affairs","ARTICLE","none","MEDIUM","","","","1980_2010","US",["demand"])
n(C,"obesity_econ","Cutler","David M.","Why Have Americans Become More Obese?",2003,"J Economic Perspectives","ARTICLE","none","HIGH","","https://doi.org/10.1257/089533003769204371","","1980_2010","US",["demand"])
n(C,"dietary_guidelines","Nestle","Marion","Food Politics: How the Food Industry Influences Nutrition and Health",2013,"UC Press","BOOK","multi","CRITICAL","10th anniv ed","",scholar("Nestle Food Politics"),"1980_2010","US",["demand","policy"])
n(C,"dietary_guidelines","Nestle","Marion","Unsavory Truth: How Food Companies Skew the Science of What We Eat",2018,"Basic","BOOK","multi","HIGH","","",scholar("Nestle Unsavory Truth"),"2010_2020","US",["demand","policy"])
n(C,"dietary_guidelines","USDA/HHS","","Dietary Guidelines for Americans 2020-2025",2020,"USDA/HHS","REPORT","multi","HIGH","","https://www.dietaryguidelines.gov/","","2020_present","US",["demand","policy"])
n(C,"glp1_demand","Morgan Stanley","","Obesity Drugs' Potential to Reshape Food Consumption",2023,"Morgan Stanley Research","REPORT","multi","HIGH","","","GLP-1 demand thesis","2020_present","US",["demand","technology"])
n(C,"glp1_demand","Walmart","","GLP-1 Food-Purchasing Commentary 2023-2024",2024,"CNBC / Company Disclosures","ARTICLE","multi","MEDIUM","","","","2020_present","US",["demand","technology"])
n(C,"sugar_consumption","Popkin","Barry M.","Sweetening of the Global Diet, Particularly Beverages: Patterns, Trends, and Policy Responses",2016,"Lancet Diabetes & Endocrinology","ARTICLE","sugar","HIGH","","","","2010_2020","Global",["demand","policy"])
n(C,"meat_demand","Godfray","H. Charles J.","Meat Consumption, Health, and the Environment",2018,"Science","ARTICLE","meat","HIGH","","https://doi.org/10.1126/science.aam5324","","2010_2020","Global",["demand","climate"])
n(C,"income_elasticity","USDA ERS","","International Food Consumption Patterns Dataset",2024,"USDA ERS","DATASET_DOC","multi","HIGH","","https://www.ers.usda.gov/data-products/international-food-consumption-patterns/","","2020_present","Global",["demand","methodology"])
n(C,"obesity_econ","Harris","Jeffrey E.","Obesity Rates and the Economics of Food Choice",2020,"American J Health Economics","ARTICLE","none","MEDIUM","","","","2020_present","US",["demand"])
n(C,"dietary_guidelines","Mozaffarian","Dariush","Foods, Obesity, and Diabetes",2019,"Lancet","ARTICLE","multi","MEDIUM","","","","2010_2020","Global",["demand"])
n(C,"meat_demand","Ritchie","Hannah","Meat and Dairy Production: Our World in Data",2024,"Our World in Data","DATASET_DOC","meat","HIGH","","https://ourworldindata.org/meat-production","","2020_present","Global",["demand","methodology"])
n(C,"diet_transition","Drewnowski","Adam","Obesity and the Food Environment",2004,"American J Preventive Medicine","ARTICLE","multi","HIGH","","","","1980_2010","US",["demand"])
n(C,"glp1_demand","Nestle","Nestle S.A.","GLP-1 Food Industry Impact Commentary",2024,"Nestle Investor Day","REPORT","multi","LOW","","","","2020_present","Global",["demand","technology"])
n(C,"sugar_consumption","USDA ERS","","Sugar and Sweeteners Yearbook Tables 2024",2024,"USDA ERS","DATASET_DOC","sugar","HIGH","","https://www.ers.usda.gov/data-products/sugar-and-sweeteners-yearbook-tables/","Per capita consumption","2020_present","US",["demand","methodology"])

# =============================================================================
# CATEGORY 21 — FOOD SAFETY & REGULATION (target 20)
# =============================================================================
C = "Food Safety Regulation"
n(C,"regulatory_history","Young","James Harvey","Pure Food: Securing the Federal Food and Drugs Act of 1906",1989,"Princeton UP","BOOK","multi","FLAGSHIP","Flagship Cat 21","",scholar("Young Pure Food 1906"),"pre1900","US",["policy"])
n(C,"regulatory_history","Hilts","Philip J.","Protecting America's Health: The FDA, Business, and One Hundred Years of Regulation",2003,"Knopf","BOOK","multi","HIGH","","",scholar("Hilts Protecting America's Health FDA"),"spanning","US",["policy"])
n(C,"regulatory_history","Olmsted","Alan L.","Arresting Contagion: Science, Policy, and Conflicts over Animal Disease Control",2015,"Harvard UP","BOOK","meat","HIGH","With Rhode","",scholar("Olmstead Rhode Arresting Contagion"),"spanning","US",["policy","supply"])
n(C,"fda_usda","USDA FSIS","","FSIS Strategic Plan 2022-2026",2022,"USDA","REPORT","meat","HIGH","","https://www.fsis.usda.gov/","","2020_present","US",["policy"])
n(C,"fda_usda","FDA","","Food Safety Modernization Act (FSMA) Implementation Report 2024",2024,"FDA","REPORT","multi","HIGH","","https://www.fda.gov/food/food-safety-modernization-act-fsma","","2020_present","US",["policy"])
n(C,"haccp","Sperber","William H.","HACCP and Transparent Regulation",2005,"Food Control","ARTICLE","multi","MEDIUM","","","","1980_2010","Global",["policy","technology"])
n(C,"haccp","USDA FSIS","","Pathogen Reduction: HACCP Systems Final Rule 1996",1996,"USDA","GOV_DOC","meat","HIGH","","https://www.fsis.usda.gov/","","1980_2010","US",["policy"])
n(C,"recalls_outbreaks","Hoffmann","Sandra","Economic Burden of Major Foodborne Illnesses Acquired in the United States",2012,"USDA ERS EIB-140","REPORT","multi","HIGH","","https://www.ers.usda.gov/publications/pub-details/?pubid=43989","Foodborne illness costs","2010_2020","US",["demand","policy"])
n(C,"recalls_outbreaks","Scallan","Elaine","Foodborne Illness Acquired in the United States - Major Pathogens",2011,"Emerging Infectious Diseases","ARTICLE","multi","HIGH","","","","2010_2020","US",["demand"])
n(C,"recalls_outbreaks","CDC","","FoodNet Annual Reports 2020-2024",2024,"CDC","DATASET_DOC","multi","MEDIUM","","https://www.cdc.gov/foodnet/","","2020_present","US",["demand","methodology"])
n(C,"pesticide_regulation","Carson","Rachel","Silent Spring",1962,"Houghton Mifflin","BOOK","multi","HIGH","","",scholar("Carson Silent Spring"),"1945_1980","US",["climate","policy"])
n(C,"pesticide_regulation","EPA","","Registration Review of Glyphosate: Interim Decision",2020,"EPA","REPORT","multi","MEDIUM","","https://www.epa.gov/","","2020_present","US",["policy","technology"])
n(C,"pesticide_regulation","Kniss","Andrew R.","Long-Term Trends in the Intensity and Relative Toxicity of Herbicide Use",2017,"Nature Communications","ARTICLE","multi","MEDIUM","","","","2010_2020","US",["technology","climate"])
n(C,"pesticide_regulation","Douglas","Margaret R.","Neonicotinoids and the Food Supply Chain",2020,"Entomologia Experimentalis et Applicata","ARTICLE","multi","MEDIUM","","","","2020_present","Global",["technology","climate"])
n(C,"fda_usda","Becker","Geoffrey","Meat and Poultry Inspection: Background and Current Issues",2014,"CRS","REPORT","meat","MEDIUM","","","","2010_2020","US",["policy"])
n(C,"regulatory_history","Law","Marc T.","How Do Regulators Regulate? Enforcement of the Pure Food and Drugs Act, 1907-38",2006,"J Law, Economics, and Organization","ARTICLE","multi","MEDIUM","","","","1900_1945","US",["policy"])
n(C,"haccp","Unnevehr","Laurian J.","Value-Based Management of Food Safety",2004,"ERS","REPORT","multi","MEDIUM","","","","1980_2010","US",["policy","technology"])
n(C,"recalls_outbreaks","USDA FSIS","","Meat and Poultry Recalls: Annual Reports",2024,"USDA","DATASET_DOC","meat","MEDIUM","","https://www.fsis.usda.gov/recalls","","2020_present","US",["methodology"])
n(C,"pesticide_regulation","Benbrook","Charles","Trends in Glyphosate Herbicide Use in the United States and Globally",2016,"Environmental Sciences Europe","ARTICLE","multi","MEDIUM","","https://doi.org/10.1186/s12302-016-0070-0","","2010_2020","US_Global",["technology","climate"])
n(C,"fda_usda","GAO","","FDA Oversight of Imported Food",2022,"GAO","REPORT","multi","MEDIUM","","https://www.gao.gov/","","2020_present","US",["policy","trade"])

# =============================================================================
# CATEGORY 22 — NUTRITION, SNAP & FOOD ASSISTANCE (target 20)
# =============================================================================
C = "Nutrition SNAP"
n(C,"snap_history","Wilde","Parke","Food Policy in the United States: An Introduction",2018,"Routledge","BOOK","none","FLAGSHIP","Flagship Cat 22","",scholar("Wilde Food Policy United States"),"spanning","US",["policy","demand"])
n(C,"snap_history","Ziliak","James P.","Modernizing SNAP Benefits",2016,"Hamilton Project Brookings","REPORT","none","HIGH","","https://www.hamiltonproject.org/","","2010_2020","US",["policy","demand"])
n(C,"snap_history","Hoynes","Hilary W.","U.S. Food and Nutrition Programs",2016,"in Economics of Means-Tested Transfer Programs","CHAPTER","none","HIGH","With Schanzenbach","",scholar("Hoynes Schanzenbach US Food Nutrition Programs"),"spanning","US",["policy","demand"])
n(C,"snap_history","Hoynes","Hilary W.","Long-Run Impacts of Childhood Access to the Safety Net",2016,"American Economic Review","ARTICLE","none","HIGH","","https://doi.org/10.1257/aer.20130375","","2010_2020","US",["policy","demand"])
n(C,"thrifty_food_plan","USDA FNS","","Thrifty Food Plan Reevaluation Report 2021",2021,"USDA","REPORT","none","CRITICAL","","https://www.fns.usda.gov/tfp","2021 largest SNAP boost since program's start","2020_present","US",["policy","demand"])
n(C,"thrifty_food_plan","Ziliak","James P.","The 2021 Thrifty Food Plan Update: A Review",2022,"Applied Econ Perspectives & Policy","ARTICLE","none","HIGH","","","","2020_present","US",["policy","demand"])
n(C,"school_lunch","Gunderson","Gordon W.","The National School Lunch Program: Background and Development",1971,"USDA FNS","REPORT","none","HIGH","","",archorg("Gunderson National School Lunch Program"),"1945_1980","US",["policy","demand"])
n(C,"school_lunch","Schanzenbach","Diane Whitmore","Do School Lunches Contribute to Childhood Obesity?",2009,"J Human Resources","ARTICLE","none","MEDIUM","","","","1980_2010","US",["policy","demand"])
n(C,"school_lunch","USDA FNS","","National School Lunch Program Annual Summary 2024",2024,"USDA FNS","DATASET_DOC","none","HIGH","","https://www.fns.usda.gov/pd/national-school-lunch-program","","2020_present","US",["policy","methodology"])
n(C,"wic","Oliveira","Victor","Special Supplemental Nutrition Program for Women, Infants, and Children (WIC) Program Evaluation",2018,"USDA ERS","REPORT","none","HIGH","","","","2010_2020","US",["policy","demand"])
n(C,"wic","Bitler","Marianne P.","WIC and the Demand for Healthful Foods",2015,"Applied Econ Perspectives & Policy","ARTICLE","none","MEDIUM","","","","2010_2020","US",["policy","demand"])
n(C,"food_insecurity","Coleman-Jensen","Alisha","Household Food Security in the United States in 2023",2024,"USDA ERS ERR-329","REPORT","none","CRITICAL","","https://www.ers.usda.gov/publications/pub-details/?pubid=108881","Primary US food-insecurity measurement","2020_present","US",["demand","methodology"])
n(C,"food_insecurity","Gundersen","Craig","Food Insecurity and Health Outcomes",2015,"Health Affairs","ARTICLE","none","HIGH","","","","2010_2020","US",["demand"])
n(C,"snap_history","Currie","Janet","The Take-Up of Social Benefits",2006,"in Public Policy and the Income Distribution","CHAPTER","none","MEDIUM","","","","1980_2010","US",["policy","demand"])
n(C,"food_insecurity","Barrett","Christopher B.","Food Assistance Programs and Food Security",2010,"in Handbook of Ag Econ","CHAPTER","none","MEDIUM","","","","1980_2010","US_Global",["policy","demand"])
n(C,"snap_history","USDA FNS","","SNAP Annual Summary 2023",2024,"USDA FNS","DATASET_DOC","none","HIGH","","https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap","","2020_present","US",["policy","methodology"])
n(C,"commodity_donations","USDA","","The Emergency Food Assistance Program (TEFAP) Annual Report 2024",2024,"USDA FNS","REPORT","none","MEDIUM","","https://www.fns.usda.gov/tefap","","2020_present","US",["policy","demand"])
n(C,"school_lunch","Hoynes","Hilary W.","The Long-Run Effects of Childhood Access to the Safety Net",2016,"in Labor Economics","CHAPTER","none","MEDIUM","","","","2010_2020","US",["policy","demand"])
n(C,"food_insecurity","FAO","","Hunger Hotspots: FAO-WFP Early Warnings",2024,"FAO/WFP","REPORT","none","HIGH","","https://www.fao.org/","","2020_present","Global",["policy","demand"])
n(C,"snap_history","CBO","","An Overview of the 2018 Farm Bill Nutrition Title",2018,"CBO","REPORT","none","MEDIUM","","https://www.cbo.gov/","","2010_2020","US",["policy","finance"])

# =============================================================================
# CATEGORY 23 — NON-ROW-CROP COMMODITIES (target 25)
# =============================================================================
C = "Non-Row-Crop"
n(C,"coffee","Pendergrast","Mark","Uncommon Grounds: The History of Coffee and How It Transformed Our World",2010,"Basic","BOOK","none","FLAGSHIP","Flagship for coffee","",scholar("Pendergrast Uncommon Grounds coffee"),"spanning","Global",["trade","supply"])
n(C,"coffee","Topik","Steven","The Global Coffee Economy in Africa, Asia, and Latin America, 1500-1989",2003,"Cambridge UP","BOOK","none","HIGH","With Clarence-Smith","",scholar("Topik Global Coffee Economy"),"pre1900","Global",["trade","supply"])
n(C,"coffee","Daviron","Benoit","The Coffee Paradox: Global Markets, Commodity Trade, and the Elusive Promise of Development",2005,"Zed","BOOK","none","HIGH","With Ponte","","","1980_2010","Global",["trade","supply"])
n(C,"coffee","ICO","","International Coffee Organization Annual Review 2023-24",2024,"ICO","REPORT","none","HIGH","","https://www.ico.org/","","2020_present","Global",["trade","supply"])
n(C,"coffee","Craves","Julian","Coffee Climate Change 2024 Outlook",2024,"World Coffee Research","REPORT","none","HIGH","","https://worldcoffeeresearch.org/","","2020_present","Global",["climate","supply"])
n(C,"cocoa","Fold","Niels","Lead Firms and Competition in 'Bi-polar' Commodity Chains: Grinders and Branders in the Global Cocoa–Chocolate Industry",2002,"J Agrarian Change","ARTICLE","none","HIGH","","","","1980_2010","Global",["trade","supply"])
n(C,"cocoa","Cocoa Barometer","","Cocoa Barometer 2022",2022,"VOICE Network","REPORT","none","HIGH","","","","2020_present","Global",["trade","supply","labor"])
n(C,"cocoa","ICCO","","International Cocoa Organization Quarterly Bulletin 2024",2024,"ICCO","REPORT","none","HIGH","","https://www.icco.org/","Ivory Coast / Ghana 2024 cocoa crisis","2020_present","Africa",["trade","supply"])
n(C,"tea","Rappaport","Erika","A Thirst for Empire: How Tea Shaped the Modern World",2017,"Princeton UP","BOOK","none","HIGH","","",scholar("Rappaport Thirst for Empire Tea"),"pre1900","Global",["trade","demand"])
n(C,"tea","FAO","","Tea Market Review 2024",2024,"FAO","REPORT","none","MEDIUM","","https://www.fao.org/markets-and-trade/commodities/tea/","","2020_present","Global",["supply","trade"])
n(C,"spices","Krondl","Michael","The Taste of Conquest: The Rise and Fall of the Three Great Cities of Spice",2008,"Ballantine","BOOK","none","MEDIUM","","",scholar("Krondl Taste of Conquest Spice"),"pre1900","Global",["trade"])
n(C,"spices","Freedman","Paul","Out of the East: Spices and the Medieval Imagination",2008,"Yale UP","BOOK","none","MEDIUM","","","","pre1900","Global",["trade","demand"])
n(C,"spices","Rai","Kishore","Vanilla Price Volatility: Madagascar Supply Dynamics",2020,"J Ag Econ","ARTICLE","none","MEDIUM","","","","2010_2020","Africa",["trade","supply"])
n(C,"seafood","Pauly","Daniel","Fishing Down Marine Food Webs",1998,"Science","ARTICLE","none","HIGH","","https://doi.org/10.1126/science.279.5352.860","Canonical fisheries decline","1980_2010","Global",["supply","climate"])
n(C,"seafood","Naylor","Rosamond L.","Effect of Aquaculture on World Fish Supplies",2000,"Nature","ARTICLE","none","HIGH","","","","1980_2010","Global",["supply","technology"])
n(C,"seafood","FAO","","The State of World Fisheries and Aquaculture (SOFIA) 2024",2024,"FAO","REPORT","none","CRITICAL","","https://www.fao.org/publications/sofia/","Flagship","2020_present","Global",["supply","methodology"])
n(C,"seafood","NOAA","","Fisheries of the United States 2023",2024,"NOAA","REPORT","none","HIGH","","https://www.fisheries.noaa.gov/","","2020_present","US",["supply","methodology"])
n(C,"seafood","Froese","Rainer","FishBase: Species Database",2024,"FishBase","DATASET_DOC","none","LOW","","https://www.fishbase.org/","","2020_present","Global",["methodology"])
n(C,"honey_pollinators","Gallai","Nicola","Economic Valuation of the Vulnerability of World Agriculture Confronted with Pollinator Decline",2009,"Ecological Economics","ARTICLE","multi","MEDIUM","","","","1980_2010","Global",["climate","supply"])
n(C,"honey_pollinators","USDA","","Honey Production Annual 2024",2024,"USDA NASS","DATASET_DOC","none","MEDIUM","","https://www.nass.usda.gov/","","2020_present","US",["supply","methodology"])
n(C,"nuts","USDA","","California Almond Industry: An Economic Review",2022,"USDA ERS","REPORT","produce","HIGH","","","","2020_present","US",["supply","climate"])
n(C,"nuts","USDA","","Pistachio Market Outlook",2023,"USDA FAS","REPORT","produce","MEDIUM","","","","2020_present","US",["supply","trade"])
n(C,"coffee","Talbot","John M.","Grounds for Agreement: The Political Economy of the Coffee Commodity Chain",2004,"Rowman & Littlefield","BOOK","none","MEDIUM","","","","1980_2010","Global",["trade","supply"])
n(C,"cocoa","Gayi","Samuel K.","Cocoa Industry: Integrating Small Farmers into the Global Value Chain",2016,"UNCTAD","REPORT","none","MEDIUM","","","","2010_2020","Africa",["trade","labor"])
n(C,"seafood","Smith","Martin D.","Sustainability and Global Seafood",2010,"Science","ARTICLE","none","MEDIUM","","","","1980_2010","Global",["supply","climate"])

# =============================================================================
# CATEGORY 24 — AG R&D, EXTENSION & INSTITUTIONS (target 15)
# =============================================================================
C = "Ag R&D"
n(C,"land_grant","Alston","Julian M.","Persistence Pays: U.S. Agricultural Productivity Growth and the Benefits from Public R&D Spending",2010,"Springer","BOOK","multi","FLAGSHIP","Flagship Cat 24","",scholar("Alston Persistence Pays agricultural productivity"),"spanning","US",["policy","technology"])
n(C,"land_grant","Fuglie","Keith","Productivity Growth and Technology Capital in the Global Agricultural Economy",2012,"in Productivity Growth","CHAPTER","multi","HIGH","","","","1980_2010","Global",["methodology","technology"])
n(C,"land_grant","USDA","","USDA Agricultural Research Service: TEKTRAN Database",2024,"USDA ARS","DATASET_DOC","multi","HIGH","","https://tellus.ars.usda.gov/","","2020_present","US",["technology","methodology"])
n(C,"land_grant","Marcus","Alan I.","Agricultural Science and the Quest for Legitimacy: Farmers, Agricultural Colleges, and Experiment Stations, 1870-1890",1985,"Iowa State","BOOK","multi","MEDIUM","","","","pre1900","US",["policy","technology"])
n(C,"cgiar","Baum","Warren C.","Partners Against Hunger: The Consultative Group on International Agricultural Research",1986,"World Bank","BOOK","multi","HIGH","","",archorg("Baum Partners Against Hunger CGIAR"),"1945_1980","Global",["technology","policy"])
n(C,"cgiar","Renkow","Mitch","Impacts of CGIAR Research: A Review of Recent Evidence",2010,"Food Policy","ARTICLE","multi","HIGH","","","","1980_2010","Global",["technology","methodology"])
n(C,"cgiar","CGIAR","","CGIAR Annual Performance Report 2023",2024,"CGIAR","REPORT","multi","HIGH","","https://www.cgiar.org/","","2020_present","Global",["technology"])
n(C,"foundations","Fitzgerald","Deborah","Exporting American Agriculture: The Rockefeller Foundation in Mexico",1986,"Social Studies of Science","ARTICLE","multi","HIGH","","","","1945_1980","LatAm",["technology","policy"])
n(C,"foundations","Perkins","John H.","The Rockefeller Foundation and the Green Revolution, 1941-56",1990,"Agriculture and Human Values","ARTICLE","multi","MEDIUM","","","","1945_1980","Global",["technology","policy"])
n(C,"extension_service","True","Alfred C.","A History of Agricultural Extension Work in the United States, 1785-1923",1928,"USDA","BOOK","multi","HIGH","","",archorg("True Agricultural Extension Work"),"pre1900","US",["policy","technology"])
n(C,"extension_service","Scheer","Scott D.","The Future of Cooperative Extension",2011,"J Extension","ARTICLE","multi","LOW","","","","2010_2020","US",["policy","technology"])
n(C,"productivity","Fuglie","Keith O.","Productivity Growth and the Composition of Capital Services",2018,"USDA ERS","REPORT","multi","HIGH","","https://www.ers.usda.gov/data-products/international-agricultural-productivity/","TFP data product","2010_2020","Global",["methodology","technology"])
n(C,"productivity","Pardey","Philip G.","Agricultural R&D: The Investment Gap",2016,"Ag Econ","ARTICLE","multi","MEDIUM","","","","2010_2020","Global",["policy","technology"])
n(C,"land_grant","Hightower","Jim","Hard Tomatoes, Hard Times: A Report of the Agribusiness Accountability Project",1972,"Schenkman","BOOK","multi","MEDIUM","Critique of land-grant","",scholar("Hightower Hard Tomatoes Hard Times"),"1945_1980","US",["policy","labor"])
n(C,"productivity","USDA ERS","","Agricultural Productivity in the U.S.",2024,"USDA ERS","DATASET_DOC","multi","HIGH","","https://www.ers.usda.gov/data-products/agricultural-productivity-in-the-us/","","2020_present","US",["methodology","technology"])

# =============================================================================
# CATEGORY 25 — WATER, IRRIGATION & SOIL (target 15)
# =============================================================================
C = "Water Irrigation Soil"
n(C,"dust_bowl","Worster","Donald","Dust Bowl: The Southern Plains in the 1930s",1979,"Oxford UP","BOOK","multi","FLAGSHIP","Flagship Cat 25","",scholar("Worster Dust Bowl Southern Plains"),"1900_1945","US",["climate","policy"])
n(C,"dust_bowl","Egan","Timothy","The Worst Hard Time: The Untold Story of Those Who Survived the Great American Dust Bowl",2006,"Houghton Mifflin","BOOK","multi","HIGH","","",scholar("Egan Worst Hard Time Dust Bowl"),"1900_1945","US",["climate"])
n(C,"reclamation","Worster","Donald","Rivers of Empire: Water, Aridity, and the Growth of the American West",1985,"Pantheon","BOOK","multi","HIGH","","",scholar("Worster Rivers of Empire"),"spanning","US",["climate","policy"])
n(C,"reclamation","Reisner","Marc","Cadillac Desert: The American West and Its Disappearing Water",1986,"Viking","BOOK","multi","HIGH","","",scholar("Reisner Cadillac Desert"),"spanning","US",["climate","policy"])
n(C,"ogallala","Opie","John","Ogallala: Water for a Dry Land",1993,"U Nebraska Press","BOOK","multi","HIGH","","",scholar("Opie Ogallala Water Dry Land"),"spanning","US",["climate","supply"])
n(C,"ogallala","Deines","Jillian M.","Transitions from Irrigated to Dryland Agriculture in the Ogallala Aquifer",2020,"Environmental Research Letters","ARTICLE","cereals","HIGH","","","","2020_present","US",["climate","supply"])
n(C,"sgma_california","PPIC","","California's Groundwater Sustainability Management Act: Five Years On",2020,"PPIC","REPORT","produce","HIGH","","https://www.ppic.org/","","2020_present","US",["climate","policy"])
n(C,"sgma_california","Lund","Jay","California's Agricultural Water Economy",2020,"UC Davis","REPORT","produce","HIGH","","","","2020_present","US",["climate","policy"])
n(C,"soil_conservation","Helms","Douglas","Readings in the History of the Soil Conservation Service",1992,"USDA NRCS","BOOK","multi","MEDIUM","","",archorg("Helms Readings History Soil Conservation Service"),"1900_1945","US",["climate","policy"])
n(C,"soil_conservation","Lal","Rattan","Soil Carbon Sequestration Impacts on Global Climate Change and Food Security",2004,"Science","ARTICLE","multi","HIGH","","https://doi.org/10.1126/science.1097396","","1980_2010","Global",["climate","technology"])
n(C,"reclamation","Hundley","Norris","The Great Thirst: Californians and Water, A History",2001,"UC Press","BOOK","multi","MEDIUM","","","","spanning","US",["climate","policy"])
n(C,"ogallala","Scanlon","Bridget R.","Groundwater Depletion and Sustainability of Irrigation in the U.S. High Plains and Central Valley",2012,"PNAS","ARTICLE","multi","HIGH","","https://doi.org/10.1073/pnas.1200311109","","2010_2020","US",["climate","supply"])
n(C,"sgma_california","Medellin-Azuara","Josue","Economic Impacts of California Drought 2022-2023",2023,"UC Merced","REPORT","produce","HIGH","","","","2020_present","US",["climate","finance"])
n(C,"soil_conservation","USDA NRCS","","National Resources Inventory (NRI) 2024",2024,"USDA NRCS","DATASET_DOC","multi","MEDIUM","","https://www.nrcs.usda.gov/","","2020_present","US",["climate","methodology"])
n(C,"dust_bowl","Hansen","Zeynep K.","Bust and Boom: American Political Economy of the Prairie Grass, 1930-37",2009,"J Economic History","ARTICLE","cereals","MEDIUM","","","","1900_1945","US",["climate","policy"])


# =============================================================================
# EMIT CSV + JSON
# =============================================================================
CSV_HEADER = [
    "Number","Category","Subcategory","Author_Last","Author_First","Title","Year",
    "Publisher_Journal","Type","Commodity_Tag","Era","Geography","Priority","Status",
    "Acquisition_Notes","Anna_Archive_Link","Archive_Org_Link","Direct_URL","Search_Query"
]

def load_v1_rows() -> list[dict]:
    rows = []
    with open(V1_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def v1_enriched() -> list[tuple]:
    """Convert v1 CSV rows into v2 tuple format with era/geo/themes added."""
    out = []
    for r in load_v1_rows():
        num = int(r["Number"])
        era, geo, themes = V1_OVERRIDES.get(num, (DEFAULT_ERA, DEFAULT_GEO, list(DEFAULT_THEMES)))
        prio = "FLAGSHIP" if num in V1_FLAGSHIPS else r["Priority"]
        out.append((
            r["Category"], r["Subcategory"], r["Author_Last"], r["Author_First"],
            r["Title"], r["Year"], r["Publisher_Journal"], r["Type"],
            r["Commodity_Tag"], prio, r["Status"], r["Acquisition_Notes"],
            r["Direct_URL"], "", era, geo, themes, "v1"
        ))
    return out

def main() -> None:
    v1_rows = v1_enriched()
    # new v2 rows — append v2 marker
    v2_rows = [t + ("v2",) for t in N]
    all_rows = v1_rows + v2_rows

    cat_counter = Counter()
    prio_counter = Counter()
    comm_counter = Counter()
    era_counter = Counter()
    geo_counter = Counter()
    theme_counter = Counter()
    ver_counter = Counter()

    json_entries = []
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(CSV_HEADER)
        for i, row in enumerate(all_rows, start=1):
            (cat, sub, last, first, title, year, pub, typ, comm, prio, status,
             notes, url, rel, era, geo, themes, ver) = row
            q = f"{last} {title}".strip()
            aa = annas(q); ao = archorg(q)
            w.writerow([
                i, cat, sub, last, first, title, year, pub, typ, comm, era, geo,
                prio, status, notes, aa, ao, url, q
            ])
            cat_counter[cat] += 1
            prio_counter[prio] += 1
            comm_counter[comm] += 1
            era_counter[era] += 1
            geo_counter[geo] += 1
            for t in themes: theme_counter[t] += 1
            ver_counter[ver] += 1
            json_entries.append({
                "id": f"FB-{(sub or 'none')[:4].upper()}-{i:04d}",
                "number": i,
                "category": cat, "subcategory": sub,
                "author_last": last, "author_first": first,
                "title": title, "year": year,
                "publisher_journal": pub, "type": typ,
                "commodity_tag": comm, "era": era, "geography": geo,
                "priority": prio, "status": status,
                "acquisition_notes": notes,
                "anna_archive_link": aa, "archive_org_link": ao,
                "direct_url": url, "search_query": q,
                "relevance_to_foodberg": rel,
                "themes": themes,
                "added_in_version": ver,
                "verified": False, "acquired": False,
            })

    payload = {
        "schema_version": "2.0",
        "generated": datetime.now(UTC).isoformat(),
        "project": "Foodberg — Historical Food Price Explorer",
        "total_entries": len(all_rows),
        "category_counts": dict(cat_counter),
        "priority_counts": dict(prio_counter),
        "commodity_counts": dict(comm_counter),
        "era_counts": dict(era_counter),
        "geography_counts": dict(geo_counter),
        "theme_counts": dict(theme_counter),
        "version_counts": dict(ver_counter),
        "entries": json_entries,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(all_rows)} entries ({ver_counter['v1']} v1 + {ver_counter['v2']} v2)")
    print(f"  CSV:  {CSV_PATH}")
    print(f"  JSON: {JSON_PATH}")
    print(f"\nCategories: {len(cat_counter)}")
    for k, v in sorted(cat_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nPriorities:")
    for k, v in sorted(prio_counter.items()):
        print(f"  {v:4d}  {k}")
    print(f"\nEras:")
    for k, v in sorted(era_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nGeographies:")
    for k, v in sorted(geo_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nThemes:")
    for k, v in sorted(theme_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print(f"\nCommodities:")
    for k, v in sorted(comm_counter.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")

if __name__ == "__main__":
    main()
