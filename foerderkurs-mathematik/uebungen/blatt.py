#!/usr/bin/env python3
"""
blatt.py – Übungsblätter aus der Übungsdatenbank erzeugen

Die Aufgaben liegen als YAML-Dateien in db/ (eine Datei pro Strang).
Das Skript wählt Aufgaben nach Feld, Stufe, Typ usw. aus und erzeugt eine
LaTeX-Datei in blaetter/ (Schülerversion, mit --pdf zusätzlich beide PDFs).

Beispiele
---------
  python3 blatt.py katalog                      # Übersicht: was ist vorhanden?
  python3 blatt.py pruefen                      # Datenbank auf Fehler prüfen

  # Übungsblatt zu einem Feld, Stufen 1 und 2, mit Kurzlösungen
  python3 blatt.py blatt --felder 3B --stufen 1 2 --kurzloesungen \\
      --titel "Rechnen mit Brüchen" -o 3B_uebung --pdf

  # Brückenblatt: Aufgabenpaare mit Zahlen und mit Variablen
  python3 blatt.py blatt --felder 3B 3C 6C --bruecken \\
      --titel "Von Zahlen zu Variablen" -o bruecken --pdf

  # Persönliches Blatt nach Profil: höchstens 2 Aufgaben pro Feld, gemischt
  python3 blatt.py blatt --felder 3B 6B 6C --pro-feld 2 --ohne-checks \\
      --mischen 7 --kurzloesungen --titel "Mein Übungsblatt" -o profil --pdf

  # Check zu einem Feld (nur Aufgaben vom Typ Check, ohne Kurzlösungen)
  python3 blatt.py check 6B --pdf
"""

import argparse
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Das Paket PyYAML fehlt: pip install pyyaml")

HIER = Path(__file__).resolve().parent
DB = HIER / "db"
AUSGABE = HIER / "blaetter"
STYLE_DIR = HIER.parent          # dort liegt foerderkurs.sty

TYPEN = ["Routine", "Verständnis", "Fehlersuche", "Umkehrung", "Text", "Check"]
ID_MUSTER = re.compile(r"^([0-9])([A-D])-(\d{2})$")
NIVEAUS = "ABCD"


# ---------------------------------------------------------------------------
# Datenbank
# ---------------------------------------------------------------------------
def lade_datenbank():
    aufgaben, fehler = [], []
    for datei in sorted(DB.glob("*.yaml")):
        with open(datei, encoding="utf-8") as f:
            daten = yaml.safe_load(f)
        strang = daten.get("strang")
        for a in daten.get("aufgaben", []):
            a["_datei"] = datei.name
            a["_strang"] = strang
            a["_strangtitel"] = daten.get("titel", f"Strang {strang}")
            aufgaben.append(a)
    return aufgaben, fehler


def feld(a):
    return a["id"][:2]


def sortschluessel(a):
    m = ID_MUSTER.match(a["id"])
    return (int(m.group(1)), NIVEAUS.index(m.group(2)), a.get("stufe", 9), int(m.group(3)))


def pruefe(aufgaben):
    meldungen = []
    ids = {}
    for a in aufgaben:
        ort = f"{a.get('_datei')}: {a.get('id', '(ohne id)')}"
        if "id" not in a or not ID_MUSTER.match(str(a["id"])):
            meldungen.append(f"{ort}: ungültige id (erwartet z. B. 3B-07)")
            continue
        if a["id"] in ids:
            meldungen.append(f"{ort}: id doppelt vergeben")
        ids[a["id"]] = a
        if int(a["id"][0]) != a["_strang"]:
            meldungen.append(f"{ort}: id passt nicht zum Strang {a['_strang']} der Datei")
        for schluessel in ("stufe", "typ", "aufgabe", "loesung"):
            if schluessel not in a:
                meldungen.append(f"{ort}: Feld «{schluessel}» fehlt")
        if a.get("stufe") not in (1, 2, 3):
            meldungen.append(f"{ort}: stufe muss 1, 2 oder 3 sein")
        if a.get("typ") not in TYPEN:
            meldungen.append(f"{ort}: unbekannter typ «{a.get('typ')}» (erlaubt: {', '.join(TYPEN)})")
        for f in a.get("fehler", []) or []:
            if "antwort" not in f or "hinweis" not in f:
                meldungen.append(f"{ort}: Eintrag unter «fehler» braucht antwort und hinweis")
    for a in aufgaben:
        ziel = a.get("bruecke")
        if ziel and ziel not in ids:
            meldungen.append(f"{a['_datei']}: {a['id']}: Brücke zu unbekannter Aufgabe {ziel}")
    return meldungen


# ---------------------------------------------------------------------------
# Auswahl
# ---------------------------------------------------------------------------
def auswaehlen(aufgaben, args):
    nach_id = {a["id"]: a for a in aufgaben}
    if args.ids:
        unbekannt = [i for i in args.ids if i not in nach_id]
        if unbekannt:
            sys.exit(f"Unbekannte Aufgaben: {', '.join(unbekannt)}")
        return [nach_id[i] for i in args.ids]

    wahl = list(aufgaben)
    if args.felder:
        wahl = [a for a in wahl if feld(a) in args.felder]
    if args.stufen:
        wahl = [a for a in wahl if a["stufe"] in args.stufen]
    if args.typen:
        wahl = [a for a in wahl if a["typ"] in args.typen]
    if args.ohne_checks:
        wahl = [a for a in wahl if a["typ"] != "Check"]

    if args.bruecken:
        # nur Aufgaben mit Brücke, jeweils mit ihrem Partner
        paare = []
        for a in sorted(wahl, key=sortschluessel):
            if a.get("bruecke"):
                for x in (a, nach_id[a["bruecke"]]):
                    if x not in paare:
                        paare.append(x)
        wahl = paare

    wahl.sort(key=sortschluessel)

    if args.pro_feld:
        rng = random.Random(args.zufall) if args.zufall is not None else None
        gruppiert = {}
        for a in wahl:
            gruppiert.setdefault(feld(a), []).append(a)
        wahl = []
        for f, liste in gruppiert.items():
            if rng:
                liste = sorted(rng.sample(liste, min(args.pro_feld, len(liste))),
                               key=sortschluessel)
            else:
                liste = liste[:args.pro_feld]
            wahl.extend(liste)

    if args.mischen is not None:
        random.Random(args.mischen).shuffle(wahl)

    if not wahl:
        sys.exit("Keine Aufgaben passen zu dieser Auswahl.")
    return wahl


# ---------------------------------------------------------------------------
# LaTeX erzeugen
# ---------------------------------------------------------------------------
def tex_aufgabe(a):
    t = a["aufgabe"].strip()
    raum = a.get("raum", 2.5)
    teile = [
        # Aufgabe nicht über einen Seitenwechsel trennen
        rf"\needspace{{\dimexpr {raum}cm + 6\baselineskip\relax}}",
        r"\question",
        rf"\aufgabenkopf{{{a['id']}}}{{{a['stufe']}}}{{{a['typ']}}}"
        rf"{{{a.get('ml', '')}}}{{{a.get('bruecke', '')}}}",
        t,
        r"\begin{solution}",
        a["loesung"].strip(),
    ]
    if a.get("weg"):
        teile += [r"\par\smallskip\textit{Lösungsweg:} " + a["weg"].strip()]
    if a.get("fehler"):
        teile += [r"\par\smallskip\textit{Typische Fehler:}", r"\begin{itemize}"]
        for f in a["fehler"]:
            teile.append(rf"  \item {f['antwort']}: {f['hinweis']}")
        teile.append(r"\end{itemize}")
    teile += [r"\end{solution}", rf"\raum{{{raum}cm}}", ""]
    return "\n".join(teile)


def tex_kurzloesungen(wahl):
    z = [r"\ifprintanswers\else",
         r"\newpage",
         r"\abschnitt{Kurzlösungen}",
         r"Kontrollieren Sie erst, wenn Sie eine Aufgabe fertig gelöst und "
         r"eingeschätzt haben, wie sicher Sie sind.",
         r"\begin{itemize}"]
    for a in wahl:
        eintrag = rf"  \item[\textbf{{{a['id']}}}] {a['loesung'].strip()}"
        if a.get("fehler"):
            eintrag += r"\par\small"
            for f in a["fehler"]:
                eintrag += rf" \emph{{Haben Sie {f['antwort']}?}} {f['hinweis']}"
        z.append(eintrag)
    z += [r"\end{itemize}", r"\fi"]
    return "\n".join(z)


def erzeuge_tex(wahl, titel, untertitel, kurzloesungen, hinweis_sicherheit):
    felder = sorted({feld(a) for a in wahl}, key=lambda f: (int(f[0]), NIVEAUS.index(f[1])))
    if not untertitel:
        untertitel = "Felder: " + ", ".join(felder)
    z = [
        "% Automatisch erzeugt mit blatt.py – Änderungen in db/ vornehmen, nicht hier.",
        r"\documentclass[11pt]{exam}",
        r"\usepackage{foerderkurs}",
        r"\begin{document}",
        rf"\uebungsblatt{{{titel}}}{{{untertitel}}}",
    ]
    if hinweis_sicherheit:
        z.append(r"\ifprintanswers\else\begin{tcolorbox}[fkbasis, colframe=fkgrau, "
                 r"colback=white]\small Notieren Sie bei jeder Aufgabe, bevor Sie "
                 r"kontrollieren, wie sicher Sie sind: 1 = rate nur, 4 = ganz sicher."
                 r"\end{tcolorbox}\fi")
    z.append(r"\begin{questions}")
    z += [tex_aufgabe(a) for a in wahl]
    z.append(r"\end{questions}")
    if kurzloesungen:
        z.append(tex_kurzloesungen(wahl))
    z.append(r"\end{document}")
    return "\n".join(z) + "\n"


def kompiliere(name, ausgabe=None, lehrperson=True, melden=True):
    """Kompiliert ausgabe/name.tex; gibt True zurück, wenn alles geklappt hat."""
    ausgabe = Path(ausgabe or AUSGABE)
    if not shutil.which("pdflatex"):
        print("pdflatex nicht gefunden; nur die .tex-Datei wurde erzeugt.")
        return False
    env = dict(os.environ)
    env["TEXINPUTS"] = f"{STYLE_DIR}{os.pathsep}" + env.get("TEXINPUTS", "")
    befehle = [["pdflatex", "-interaction=nonstopmode", f"{name}.tex"]]
    if lehrperson:
        befehle.append(["pdflatex", "-interaction=nonstopmode", f"-jobname={name}_LP",
                        rf"\def\mitloesungen{{1}}\input{{{name}}}"])
    ok = True
    for befehl in befehle:
        for _ in range(2):  # zweimal für die Seitenzahlen
            r = subprocess.run(befehl, cwd=ausgabe, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            ok = False
            print(f"Fehler beim Kompilieren von {name} ({befehl[-1]}); siehe .log-Datei.")
    if ok:
        for endung in (".aux", ".log", ".out"):
            for n in (name, f"{name}_LP"):
                (ausgabe / f"{n}{endung}").unlink(missing_ok=True)
    if melden and ok:
        zusatz = f", {name}_LP.pdf (Lehrperson)" if lehrperson else ""
        print(f"PDFs: {name}.pdf (Schülerversion){zusatz}")
    return ok


# ---------------------------------------------------------------------------
# Befehle
# ---------------------------------------------------------------------------
def befehl_katalog(aufgaben, _args):
    felder = {}
    for a in aufgaben:
        felder.setdefault(feld(a), []).append(a)
    print(f"{len(aufgaben)} Aufgaben in {len(felder)} Feldern\n")
    print(f"{'Feld':<6}{'Total':>6}{'★':>4}{'★★':>4}{'★★★':>5}  Typen")
    for f in sorted(felder, key=lambda f: (int(f[0]), NIVEAUS.index(f[1]))):
        liste = felder[f]
        st = [sum(1 for a in liste if a["stufe"] == s) for s in (1, 2, 3)]
        typen = {}
        for a in liste:
            typen[a["typ"]] = typen.get(a["typ"], 0) + 1
        typtext = ", ".join(f"{t} {n}" for t, n in sorted(typen.items()))
        print(f"{f:<6}{len(liste):>6}{st[0]:>4}{st[1]:>4}{st[2]:>5}  {typtext}")


def befehl_pruefen(aufgaben, _args):
    meldungen = pruefe(aufgaben)
    if meldungen:
        print("\n".join(meldungen))
        sys.exit(1)
    print(f"Keine Fehler gefunden ({len(aufgaben)} Aufgaben).")


def schreibe(wahl, args, titel, untertitel, kurz, sicherheit, name):
    AUSGABE.mkdir(exist_ok=True)
    tex = erzeuge_tex(wahl, titel, untertitel, kurz, sicherheit)
    (AUSGABE / f"{name}.tex").write_text(tex, encoding="utf-8")
    print(f"{len(wahl)} Aufgaben: {', '.join(a['id'] for a in wahl)}")
    print(f"LaTeX: blaetter/{name}.tex")
    if args.pdf:
        kompiliere(name)


def befehl_blatt(aufgaben, args):
    meldungen = pruefe(aufgaben)
    if meldungen:
        sys.exit("Die Datenbank enthält Fehler. Zuerst «blatt.py pruefen» ausführen.")
    wahl = auswaehlen(aufgaben, args)
    name = args.o or re.sub(r"[^A-Za-z0-9_-]+", "_", args.titel).strip("_")
    schreibe(wahl, args, args.titel, args.untertitel, args.kurzloesungen,
             not args.ohne_sicherheit, name)


def befehl_check(aufgaben, args):
    wahl = sorted([a for a in aufgaben if feld(a) == args.feld and a["typ"] == "Check"],
                  key=sortschluessel)
    if not wahl:
        sys.exit(f"Für das Feld {args.feld} gibt es noch keine Check-Aufgaben.")
    schreibe(wahl, args, f"Check {args.feld}",
             "Bestanden mit höchstens einem Fehler, an zwei verschiedenen Tagen",
             False, False, args.o or f"Check_{args.feld}")


def main():
    p = argparse.ArgumentParser(description="Übungsblätter aus der Übungsdatenbank erzeugen.",
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog=__doc__)
    sub = p.add_subparsers(dest="befehl", required=True)

    sub.add_parser("katalog", help="Übersicht über alle Felder")
    sub.add_parser("pruefen", help="Datenbank auf Fehler prüfen")

    b = sub.add_parser("blatt", help="Übungsblatt erzeugen")
    b.add_argument("--titel", required=True)
    b.add_argument("--untertitel", default="")
    b.add_argument("--felder", nargs="+", metavar="FELD", help="z. B. 3B 3C")
    b.add_argument("--ids", nargs="+", metavar="ID", help="genau diese Aufgaben, in dieser Reihenfolge")
    b.add_argument("--stufen", nargs="+", type=int, choices=[1, 2, 3])
    b.add_argument("--typen", nargs="+", choices=TYPEN)
    b.add_argument("--ohne-checks", action="store_true", help="Check-Aufgaben weglassen")
    b.add_argument("--bruecken", action="store_true", help="nur Brückenaufgaben mit Partner")
    b.add_argument("--pro-feld", type=int, metavar="N", help="höchstens N Aufgaben pro Feld")
    b.add_argument("--zufall", type=int, metavar="SEED", help="mit --pro-feld: zufällig auswählen")
    b.add_argument("--mischen", type=int, metavar="SEED", help="Reihenfolge mischen")
    b.add_argument("--kurzloesungen", action="store_true", help="Kurzlösungen ans Ende anhängen")
    b.add_argument("--ohne-sicherheit", action="store_true",
                   help="ohne den Hinweis zur Selbsteinschätzung")
    b.add_argument("-o", metavar="NAME", help="Dateiname ohne Endung")
    b.add_argument("--pdf", action="store_true", help="beide Versionen kompilieren")

    c = sub.add_parser("check", help="Check-Blatt für ein Feld erzeugen")
    c.add_argument("feld", help="z. B. 6B")
    c.add_argument("-o", metavar="NAME")
    c.add_argument("--pdf", action="store_true")

    args = p.parse_args()
    aufgaben, _ = lade_datenbank()
    {"katalog": befehl_katalog, "pruefen": befehl_pruefen,
     "blatt": befehl_blatt, "check": befehl_check}[args.befehl](aufgaben, args)


if __name__ == "__main__":
    main()
