# Übungsdatenbank Förderkurs Mathematik

Die Aufgaben liegen in `db/`, eine YAML-Datei pro Strang
(z. B. `03-brueche.yaml`). Das Skript `blatt.py` stellt daraus Übungsblätter
zusammen und erzeugt LaTeX-Dateien in `blaetter/`, die das gemeinsame Layout
`foerderkurs.sty` verwenden.

Voraussetzungen: Python 3 mit PyYAML (`pip install pyyaml`), für PDFs eine
LaTeX-Installation mit `pdflatex`.

## Felder und Niveaus

Jede Aufgabe gehört zu einem **Feld** = Strang + Niveau, z. B. `3B`
(Brüche, mit Zahlen). Die Niveaus entsprechen der Standortbestimmung:

| Niveau | Bedeutung |
|---|---|
| A | Grundlagen: Bedeutung und Zahlverständnis |
| B | Numerisch: Verfahren mit konkreten Zahlen |
| C | Symbolisch: dieselben Ideen mit Variablen |
| D | Formal: Parameter, Strukturen, Lösungsmengen |

Unabhängig davon hat jede Aufgabe eine **Stufe** (Schwierigkeit innerhalb
des Feldes): 1 = ★, 2 = ★★, 3 = ★★★.

## Aufbau einer Aufgabe

```yaml
- id: 3B-03            # Feld + laufende Nummer, nie wiederverwenden
  stufe: 2             # 1, 2 oder 3
  typ: Routine         # Routine | Verständnis | Fehlersuche | Umkehrung | Text | Check
  ml: "3.1"            # zugehörige Mini-Lektion (optional)
  bruecke: 3C-01       # Partneraufgabe auf dem nächsten Niveau (optional)
  quelle: eigene       # Herkunft und Rechte bei übernommenem Material (optional)
  raum: 3              # Platz für die Antwort in cm
  aufgabe: |
    Berechnen Sie ...  # LaTeX, wie in der exam-Klasse (parts usw.)
  loesung: |
    a) ...             # Kurzlösung (erscheint auch in den Kurzlösungen)
  weg: |
    ...                # ausführlicher Lösungsweg, nur Lehrpersonenversion (optional)
  fehler:              # typische Fehler mit Hinweis (optional)
    - antwort: '$\frac{3}{7}$ bei a)'
      hinweis: 'Zähler und Nenner wurden getrennt addiert. Mini-Lektion 3.1.'
```

Hinweise zum Erfassen:

- LaTeX-Text immer als Block (`|`) schreiben; `antwort` und `hinweis` in
  einfache Anführungszeichen setzen.
- `antwort` so formulieren, dass «Haben Sie … ?» einen Satz ergibt.
- Konventionen des Kurses einhalten: Dezimalpunkt, `\cdot` vor Klammern,
  negative Zahlen in Klammern, `\geteilt` für die Division, Anrede *Sie*.
- Nach jeder Änderung `python3 blatt.py pruefen` ausführen.

## Befehle

```
python3 blatt.py katalog      # was ist vorhanden?
python3 blatt.py pruefen      # Datenbank auf Fehler prüfen
python3 blatt.py blatt ...    # Übungsblatt erzeugen
python3 blatt.py check 6B     # Check-Blatt für ein Feld
```

Optionen für `blatt` (kombinierbar):

| Option | Wirkung |
|---|---|
| `--titel T`, `--untertitel U` | Titel des Blatts |
| `--felder 3B 3C` | nur diese Felder |
| `--ids 3B-01 6C-02` | genau diese Aufgaben, in dieser Reihenfolge |
| `--stufen 1 2` | nur diese Schwierigkeitsstufen |
| `--typen Routine Text` | nur diese Aufgabentypen |
| `--ohne-checks` | Check-Aufgaben weglassen |
| `--bruecken` | nur Brückenaufgaben, jeweils mit Partneraufgabe |
| `--pro-feld N` | höchstens N Aufgaben pro Feld |
| `--zufall SEED` | mit `--pro-feld`: zufällig statt der ersten N |
| `--mischen SEED` | Reihenfolge mischen (verschachteltes Üben) |
| `--kurzloesungen` | Kurzlösungen mit Fehlerhinweisen am Schluss |
| `--ohne-sicherheit` | ohne den Hinweis «Wie sicher sind Sie?» |
| `-o NAME` | Dateiname |
| `--pdf` | Schüler- und Lehrpersonenversion kompilieren |

Gleicher `SEED` ergibt immer dasselbe Blatt.

## Beispiele

```
python3 blatt.py blatt --felder 3B --stufen 1 2 --ohne-checks --kurzloesungen \
    --titel "Rechnen mit Brüchen" -o 3B_Uebung --pdf

python3 blatt.py blatt --felder 3B 3C 3D 6C --bruecken --kurzloesungen \
    --titel "Von Zahlen zu Variablen" -o Bruecken --pdf

python3 blatt.py blatt --felder 3B 6B 6C --pro-feld 2 --zufall 3 --ohne-checks \
    --mischen 7 --kurzloesungen --titel "Mein Übungsblatt" -o Profil_Beispiel --pdf

python3 blatt.py check 6B --pdf
```

Die Dateien in `blaetter/` werden bei jedem Aufruf überschrieben. Änderungen
immer in `db/` vornehmen, nicht in den erzeugten Dateien.
