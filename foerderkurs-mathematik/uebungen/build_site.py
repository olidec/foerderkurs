#!/usr/bin/env python3
"""
build_site.py – Übungsblätter für die Website erzeugen

Erzeugt für jedes Feld der Übungsdatenbank
  - ein Übungsblatt (alle Aufgaben ausser Checks, mit Kurzlösungen) und
  - ein Check-Blatt (nur Aufgaben vom Typ Check), falls vorhanden,
jeweils nur in der Schülerversion, dazu site/manifest.json.

Wird von der GitHub Action bei jeder Änderung ausgeführt, kann aber auch
lokal laufen:  python3 uebungen/build_site.py
"""

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blatt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "site"
PDF_DIR = SITE / "pdf"

NIVEAU_NAMEN = {
    "A": "Grundlagen",
    "B": "Rechnen mit Zahlen",
    "C": "Rechnen mit Variablen",
    "D": "Vertiefung",
}


def main():
    aufgaben, _ = blatt.lade_datenbank()
    meldungen = blatt.pruefe(aufgaben)
    if meldungen:
        print("\n".join(meldungen))
        sys.exit("Die Datenbank enthält Fehler; es wurde nichts erzeugt.")

    felder = {}
    for a in aufgaben:
        felder.setdefault(blatt.feld(a), []).append(a)

    if PDF_DIR.exists():
        shutil.rmtree(PDF_DIR)
    PDF_DIR.mkdir(parents=True)

    manifest = {"erstellt": datetime.now(timezone.utc).isoformat(timespec="minutes"),
                "felder": {}}
    fehler = False

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for f in sorted(felder, key=lambda f: (int(f[0]), "ABCD".index(f[1]))):
            liste = sorted(felder[f], key=blatt.sortschluessel)
            strangtitel = liste[0]["_strangtitel"]
            titel = f"{strangtitel}: {NIVEAU_NAMEN[f[1]]}"
            eintrag = {"titel": titel, "strang": int(f[0]), "niveau": f[1],
                       "uebung": None, "check": None, "anzahl": 0}

            uebung = [a for a in liste if a["typ"] != "Check"]
            if uebung:
                name = f"Uebung_{f}"
                tex = blatt.erzeuge_tex(uebung, titel, f"Feld {f}",
                                        kurzloesungen=True, hinweis_sicherheit=True)
                (tmp / f"{name}.tex").write_text(tex, encoding="utf-8")
                if blatt.kompiliere(name, tmp, lehrperson=False, melden=False):
                    shutil.copy(tmp / f"{name}.pdf", PDF_DIR / f"{name}.pdf")
                    eintrag["uebung"] = f"pdf/{name}.pdf"
                    eintrag["anzahl"] = len(uebung)
                else:
                    fehler = True

            checks = [a for a in liste if a["typ"] == "Check"]
            if checks:
                name = f"Check_{f}"
                tex = blatt.erzeuge_tex(checks, f"Check {f}", titel,
                                        kurzloesungen=False, hinweis_sicherheit=False)
                (tmp / f"{name}.tex").write_text(tex, encoding="utf-8")
                if blatt.kompiliere(name, tmp, lehrperson=False, melden=False):
                    shutil.copy(tmp / f"{name}.pdf", PDF_DIR / f"{name}.pdf")
                    eintrag["check"] = f"pdf/{name}.pdf"
                else:
                    fehler = True

            manifest["felder"][f] = eintrag
            print(f"{f}: {eintrag['anzahl']} Aufgaben"
                  f"{', Check' if eintrag['check'] else ''}")

    (SITE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest.json mit {len(manifest['felder'])} Feldern geschrieben.")
    if fehler:
        sys.exit("Mindestens ein Blatt liess sich nicht kompilieren.")


if __name__ == "__main__":
    main()
