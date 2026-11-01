"""Debate patterns as d1 questions. German instructions (debates are German); ids are stable keys for the dashboard."""

# one choice = main pattern of a turn; "sachlich" is the default
MAIN = {
    "type": "choice",
    "instructions": "TV-Duell, automatisches Transkript ohne Satzzeichen. Welches Muster beschreibt den Redebeitrag von B (Antwort auf A) am besten?",
    "criteria": {
        "sachlich": "sachliches Argument, Forderung, Zahl, Erklärung, Programm, ohne erkennbaren Kniff",
        "strohmann": "B verzerrt die Position von A und greift die verzerrte Version an",
        "red_herring": "B wechselt zu einem anderen, unverbundenen Thema",
        "dammbruch": "B malt eine Kette immer schlimmerer Folgen oder einen Kollaps aus",
        "falsches_dilemma": "B lässt nur zwei Extreme zu ('entweder ... oder', 'ja oder nein')",
        "ad_hominem": "B greift die Person oder Partei von A an statt des Arguments",
        "whataboutism": "B kontert mit einem Fehler der anderen Seite ('und was ist mit ...')",
        "anekdote": "B nutzt einen Einzelfall als Beleg für eine allgemeine Behauptung",
    },
}

# positives are rare and not exclusive → separate yes/no questions with a high threshold
POSITIVE = {
    "steelman": {"type": "noul", "instructions": "Gibt B das Argument von A fair und zutreffend wieder, bevor B widerspricht?"},
    "good_faith": {"type": "noul", "instructions": "Geht B ehrlich auf A ein: räumt einen Punkt ein oder fragt aufrichtig nach?"},
}

SCHOOL = {
    "type": "choice",
    "instructions": "Welcher Denkschule steht die Aussage von B am nächsten?",
    "criteria": {
        "libertaer": "Freiheit des Einzelnen, Markt, wenig Staat, Eigentum",
        "sozialdemokratisch": "Sozialstaat, Umverteilung, Regulierung, Gerechtigkeit",
        "konservativ": "Tradition, Ordnung, Nation, Familie, Sicherheit",
        "gruen_progressiv": "Klima, Umwelt, Minderheitenrechte, gesellschaftlicher Wandel",
        "neutral": "keine erkennbare politische Richtung",
    },
}

MAIN_MIN_P = 0.5   # below → "sachlich"
POSITIVE_MIN_P = 0.7
