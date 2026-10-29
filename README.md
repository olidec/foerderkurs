# Förderkurs Mathematik

Materialien für den Förderunterricht Mathematik im ersten Jahr: Standortbestimmung,
Mini-Lektionen, Werkzeugkasten und eine Übungsdatenbank mit Website.

> **Entwurf.** Konzept und Materialien sind ein Vorschlag zur Diskussion und
> noch nicht beschlossen.

## Inhalt

| Ordner                | Inhalt                                                                         |
| --------------------- | ------------------------------------------------------------------------------ |
| `konzept/`            | Kurzkonzept für die Fachschaft                                                 |
| `standortbestimmung/` | Standortbestimmung mit Lösungen und Auswertungsraster                          |
| `minilektionen/`      | Mini-Lektionen (Handout und Lehrpersonenversion)                               |
| `werkzeugkasten/`     | Einheiten W1 «Sprache und Mathematik», W2 «Vertrauen in die eigene Mathematik» |
| `uebungen/`           | Übungsdatenbank (`db/`), Generator `blatt.py`, Website-Build `build_site.py`   |
| `site/`               | Website: Auswertungsraster eingeben, Übungspaket als PDF erhalten              |
| `foerderkurs.sty`     | gemeinsames Layout aller Dokumente                                             |

## Website

Die Website läuft auf GitHub Pages. Lehrpersonen tragen die Punkte aus dem
Auswertungsraster ein, die Seite schlägt die passenden Felder vor und fügt die
Übungsblätter im Browser zu einem PDF mit Deckblatt zusammen. Namen und Punkte
verlassen den Browser nicht.

Bei jeder Änderung auf `main` baut die GitHub Action
(`.github/workflows/website.yml`) alle Übungsblätter neu und veröffentlicht die
Seite. Einmalig einrichten: _Settings → Pages → Source: GitHub Actions_.

Lokal testen:

```
pip install pyyaml
python3 uebungen/build_site.py      # erzeugt site/pdf/ und site/manifest.json
cd site && python3 -m http.server   # dann http://localhost:8000 öffnen
```

Regel für den Vorschlag: Pro Strang wird das tiefste Niveau vorgeschlagen, das
nicht sicher gelöst ist (die _Bruchstelle_). Ist es nur teilweise gelöst, kommt
auf Wunsch das nächste Niveau dazu. Die Regel steht in `site/app.js`
(Funktion `vorschlaege`).

## Dokumente kompilieren

Alle Dokumente brauchen `foerderkurs.sty` aus dem Hauptordner. Aus einem
Unterordner heraus zum Beispiel so:

```
cd minilektionen
TEXINPUTS=..: pdflatex ML_0-1_Gleichheitszeichen.tex
TEXINPUTS=..: pdflatex -jobname=ML_0-1_Gleichheitszeichen_LP \
    "\def\mitloesungen{1}\input{ML_0-1_Gleichheitszeichen}"
```

Die zweite Zeile erzeugt die Lehrpersonenversion mit Lösungen und Hinweisen.

## Aufgaben ergänzen

Siehe `uebungen/README.md`. Kurz: Aufgabe in der passenden YAML-Datei in
`uebungen/db/` erfassen, `python3 uebungen/blatt.py pruefen` ausführen,
committen. Die Website wird automatisch aktualisiert.

## Vor dem Veröffentlichen klären

- **Lösungen:** Ist das Repository öffentlich, sind auch alle
  Lehrpersonenversionen und Lösungen öffentlich, insbesondere die der
  Standortbestimmung. Die Website selbst enthält nur Schülerversionen.
- **Rechte:** Nur eigene oder offen lizenzierte Aufgaben aufnehmen und die
  Herkunft im Feld `quelle` angeben.
