# Loyalty program → alliance + member airlines (all current alliance members)
LOYALTY_PROGRAMS: dict[str, dict[str, str | list[str]]] = {
    # ── Star Alliance ──
    "Miles & More": {
        "alliance": "star_alliance",
        "airlines": [
            "Austrian Airlines",
            "Brussels Airlines",
            "Croatia Airlines",
            "LOT Polish Airlines",
            "Lufthansa",
            "SWISS",
        ],
    },
    "Miles&Smiles": {
        "alliance": "star_alliance",
        "airlines": ["Turkish Airlines"],
    },
    "Miles+Bonus": {
        "alliance": "star_alliance",
        "airlines": ["Aegean Airlines"],
    },
    "Aeroplan": {
        "alliance": "star_alliance",
        "airlines": ["Air Canada"],
    },
    "MileagePlus": {
        "alliance": "star_alliance",
        "airlines": ["United Airlines"],
    },
    "KrisFlyer": {
        "alliance": "star_alliance",
        "airlines": ["Singapore Airlines"],
    },
    "Miles&Go": {
        "alliance": "star_alliance",
        "airlines": ["TAP Air Portugal"],
    },
    "ANA Mileage Club": {
        "alliance": "star_alliance",
        "airlines": ["ANA"],
    },
    "Royal Orchid Plus": {
        "alliance": "star_alliance",
        "airlines": ["Thai Airways"],
    },
    "Infinity MileageLands": {
        "alliance": "star_alliance",
        "airlines": ["EVA Air"],
    },
    "LifeMiles": {
        "alliance": "star_alliance",
        "airlines": ["Avianca"],
    },
    "ConnectMiles": {
        "alliance": "star_alliance",
        "airlines": ["Copa Airlines"],
    },
    "EgyptAir Plus": {
        "alliance": "star_alliance",
        "airlines": ["EgyptAir"],
    },
    "ShebaMiles": {
        "alliance": "star_alliance",
        "airlines": ["Ethiopian Airlines"],
    },
    "Voyager": {
        "alliance": "star_alliance",
        "airlines": ["South African Airways"],
    },
    "PhoenixMiles": {
        "alliance": "star_alliance",
        "airlines": ["Air China"],
    },
    "Flying Returns": {
        "alliance": "star_alliance",
        "airlines": ["Air India"],
    },
    "Asiana Club": {
        "alliance": "star_alliance",
        "airlines": ["Asiana Airlines"],
    },
    # ── Oneworld ──
    "Executive Club": {
        "alliance": "oneworld",
        "airlines": ["British Airways"],
    },
    "Iberia Plus": {
        "alliance": "oneworld",
        "airlines": ["Iberia"],
    },
    "Vueling Club": {
        "alliance": "oneworld",
        "airlines": ["Vueling"],
    },
    "AerClub": {
        "alliance": "oneworld",
        "airlines": ["Aer Lingus"],
    },
    "AAdvantage": {
        "alliance": "oneworld",
        "airlines": ["American Airlines"],
    },
    "Qantas Frequent Flyer": {
        "alliance": "oneworld",
        "airlines": ["Qantas"],
    },
    "Asia Miles": {
        "alliance": "oneworld",
        "airlines": ["Cathay Pacific"],
    },
    "Finnair Plus": {
        "alliance": "oneworld",
        "airlines": ["Finnair"],
    },
    "JAL Mileage Bank": {
        "alliance": "oneworld",
        "airlines": ["Japan Airlines"],
    },
    "Enrich": {
        "alliance": "oneworld",
        "airlines": ["Malaysia Airlines"],
    },
    "Privilege Club": {
        "alliance": "oneworld",
        "airlines": ["Qatar Airways"],
    },
    "Mileage Plan": {
        "alliance": "oneworld",
        "airlines": ["Alaska Airlines"],
    },
    "Royal Club": {
        "alliance": "oneworld",
        "airlines": ["Royal Jordanian"],
    },
    "Safar Flyer": {
        "alliance": "oneworld",
        "airlines": ["Royal Air Maroc"],
    },
    "FlySmiLes": {
        "alliance": "oneworld",
        "airlines": ["SriLankan Airlines"],
    },
    "Sindbad": {
        "alliance": "oneworld",
        "airlines": ["Oman Air"],
    },
    "Fiji Airways Tabua Club": {
        "alliance": "oneworld",
        "airlines": ["Fiji Airways"],
    },
    "LATAM Pass": {
        "alliance": "oneworld",
        "airlines": ["LATAM Airlines"],
    },
    # ── SkyTeam ──
    "Flying Blue": {
        "alliance": "skyteam",
        "airlines": ["Air France", "KLM"],
    },
    "SkyMiles": {
        "alliance": "skyteam",
        "airlines": ["Delta Air Lines"],
    },
    "SKYPASS": {
        "alliance": "skyteam",
        "airlines": ["Korean Air"],
    },
    "EuroBonus": {
        "alliance": "skyteam",
        "airlines": ["Scandinavian Airlines"],
    },
    "Club Premier": {
        "alliance": "skyteam",
        "airlines": ["AeroMexico"],
    },
    "Volare": {
        "alliance": "skyteam",
        "airlines": ["ITA Airways"],
    },
    "Alfursan": {
        "alliance": "skyteam",
        "airlines": ["Saudia"],
    },
    "Lotusmiles": {
        "alliance": "skyteam",
        "airlines": ["Vietnam Airlines"],
    },
    "Flying Club": {
        "alliance": "skyteam",
        "airlines": ["Virgin Atlantic"],
    },
    "Dynasty Flyer": {
        "alliance": "skyteam",
        "airlines": ["China Airlines"],
    },
    "Eastern Miles": {
        "alliance": "skyteam",
        "airlines": ["China Eastern"],
    },
    "Cedar Miles": {
        "alliance": "skyteam",
        "airlines": ["Middle East Airlines"],
    },
    "SUMA": {
        "alliance": "skyteam",
        "airlines": ["Air Europa"],
    },
    "Egret Club": {
        "alliance": "skyteam",
        "airlines": ["XiamenAir"],
    },
    "Aerolíneas Plus": {
        "alliance": "skyteam",
        "airlines": ["Aerolíneas Argentinas"],
    },
    "Asante": {
        "alliance": "skyteam",
        "airlines": ["Kenya Airways"],
    },
    "TAROM FrequentFlyer": {
        "alliance": "skyteam",
        "airlines": ["TAROM"],
    },
}

# Reverse: airline name → program name (built from LOYALTY_PROGRAMS)
AIRLINE_TO_PROGRAM: dict[str, str] = {}
for _prog_name, _prog_info in LOYALTY_PROGRAMS.items():
    for _airline in _prog_info["airlines"]:
        AIRLINE_TO_PROGRAM[str(_airline)] = _prog_name
