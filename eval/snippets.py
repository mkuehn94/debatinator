"""Clean German snippets (A says X, B answers with one pattern): per-trick noul vs one choice question.
usage: python eval/snippets.py [noul|choice]"""
import json, sys
from d1client import ask, wait
from taxonomy import SCHOOL

TRICKS = {
    "strohmann": "Verzerrt B die Position von A, um sie leichter angreifen zu können (Strohmann)? / Does B misrepresent A's position (straw man)?",
    "red_herring": "Lenkt B vom eigentlichen Thema ab, statt auf A einzugehen (Red Herring)? / Does B change the subject (red herring)?",
    "dammbruch": "Behauptet B ohne Belege eine Kette immer schlimmerer Folgen (Dammbruch / slippery slope)?",
    "falsches_dilemma": "Stellt B nur zwei Optionen zur Wahl, obwohl es mehr gibt (falsches Dilemma)?",
    "ad_hominem": "Greift B die Person von A an statt deren Argument (ad hominem)?",
    "whataboutism": "Kontert B mit einem Fehlverhalten der anderen Seite statt auf den Vorwurf einzugehen (Whataboutism)?",
    "steelman": "Gibt B die Position von A fair oder sogar stärker wieder, bevor B widerspricht (Steelman)?",
    "good_faith": "Argumentiert B in gutem Glauben: geht auf A ein, räumt Punkte ein oder fragt nach?",
}
CHOICE = {"type": "choice", "instructions": "Welches Muster beschreibt die Antwort von B auf A am besten?",
        "criteria": {"strohmann": "B verzerrt A's Position ('Du willst also ...') und greift die verzerrte Version an",
                     "red_herring": "B wechselt zu einem anderen, unverbundenen Thema",
                     "dammbruch": "B malt eine Kette immer schlimmerer Folgen aus",
                     "falsches_dilemma": "B lässt nur zwei Extreme zu ('entweder ... oder ...')",
                     "ad_hominem": "B greift die Person von A an statt des Arguments",
                     "whataboutism": "B kontert mit einem Fehler der anderen Seite ('und was ist mit ...')",
                     "steelman": "B gibt A's Argument fair/stärker wieder und widerspricht dann",
                     "good_faith": "B geht sachlich auf A ein, räumt etwas ein oder fragt nach"}}
# (A, B, expected tricks, expected school)
CASES = [
    ("Ich finde, wir sollten den Mindestlohn moderat erhöhen.",
     "Du willst also, dass der Staat jedem Unternehmen vorschreibt, was es zahlt, und die freie Wirtschaft abschafft.",
     {"strohmann"}, "libertaer"),
    ("Die Mieten in München sind in zehn Jahren um 60 Prozent gestiegen.",
     "Ja, aber schau dir mal an, wie schlecht die Bahn inzwischen pünktlich ist.",
     {"red_herring"}, "neutral"),
    ("Wir sollten Cannabis für Erwachsene legalisieren.",
     "Wenn wir Cannabis erlauben, kommen als Nächstes Kokain und Heroin, und am Ende ist die ganze Jugend abhängig.",
     {"dammbruch"}, "konservativ"),
    ("Ich bin skeptisch bei der neuen Überwachungsregel.",
     "Entweder du bist für mehr Überwachung, oder du stehst auf der Seite der Terroristen.",
     {"falsches_dilemma"}, "konservativ"),
    ("Studien zeigen, dass ein Tempolimit die Zahl der Verkehrstoten senkt.",
     "Du hast doch nicht mal einen Führerschein, was willst du überhaupt mitreden.",
     {"ad_hominem"}, "neutral"),
    ("Deine Partei hat beim Maskendeal Millionen verschwendet.",
     "Und was ist mit eurer Partei und dem Cum-Ex-Skandal? Darüber redet keiner.",
     {"whataboutism"}, "neutral"),
    ("Steuern sind notwendig, damit Schulen und Krankenhäuser finanziert werden.",
     "Wenn ich dich richtig verstehe: Ohne gemeinsame Finanzierung bekämen ärmere Menschen keine Bildung, und das wäre ungerecht. Ein starker Punkt. Ich glaube trotzdem, dass freiwillige Finanzierung und Wettbewerb das besser und günstiger leisten.",
     {"steelman", "good_faith"}, "libertaer"),
    ("Das Heizungsgesetz war handwerklich schlecht gemacht.",
     "Da hast du recht, die Kommunikation war chaotisch. Welche Teile hältst du denn inhaltlich für falsch?",
     {"good_faith"}, "neutral"),
    ("Wir brauchen mehr Windkraft im Süden.",
     "Klar, und dann stellen wir überall Windräder hin, die Landschaft ist weg, der Tourismus bricht ein und am Ende wandern alle ab.",
     {"dammbruch"}, "konservativ"),
    ("Die Rente mit 63 belastet die jüngere Generation.",
     "Wer so redet, hat noch nie körperlich gearbeitet, typischer Schreibtisch-Akademiker.",
     {"ad_hominem"}, "sozialdemokratisch"),
    ("Vermögenssteuer würde Kapital ins Ausland treiben.",
     "Das Argument kenne ich. Aber Länder wie die Schweiz haben eine Vermögenssteuer und trotzdem viel Kapital. Woran liegt das deiner Meinung nach?",
     {"good_faith"}, "sozialdemokratisch"),
    ("Der CO2-Preis sollte schneller steigen.",
     "Du willst also, dass sich arme Rentner im Winter das Heizen nicht mehr leisten können und frieren.",
     {"strohmann"}, "sozialdemokratisch"),
]


def run(mode):
    wait()
    qs = {"m": CHOICE} if mode == "choice" else {k: {"type": "noul", "instructions": v} for k, v in TRICKS.items()} | {"schule": SCHOOL}
    ask("A: Hallo.\nB: Hallo.", qs)  # warmup
    tp = fp = fn = top1 = sch = 0; ms = []
    for a, b, exp, s in CASES:
        ans, t = ask(f"A: {a}\nB: {b}", qs); ms.append(t)
        if mode == "choice":
            v = ans["m"]["value"]; top1 += v in exp
            print(f"{t:5.0f} ms {'✓' if v in exp else '✗'} exp={sorted(exp)} got={v} p={ans['m']['probabilities'][v]:.2f}")
            continue
        p = {k: ans[k]["p"] for k in TRICKS}; hit = {k for k, x in p.items() if x >= 0.5}
        tp += len(hit & exp); fp += len(hit - exp); fn += len(exp - hit)
        top1 += max(p, key=p.get) in exp; sch += ans["schule"]["value"] == s
        print(f"{t:5.0f} ms exp={sorted(exp)} hit={sorted(hit)} schule={ans['schule']['value']}/{s}")
    res = {"mode": mode, "top1": f"{top1}/{len(CASES)}", "ms_median": round(sorted(ms)[len(ms) // 2])}
    if mode == "noul":
        res |= {"precision": round(tp / max(tp + fp, 1), 2), "recall": round(tp / max(tp + fn, 1), 2), "schule": f"{sch}/{len(CASES)}"}
    print(json.dumps(res))

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "choice")
