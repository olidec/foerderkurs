/* Förderkurs Mathematik – Übungspaket zusammenstellen
 *
 * Läuft vollständig im Browser: Die Punkte aus dem Auswertungsraster werden
 * nicht gespeichert oder übertragen. Die Übungsblätter (pdf/*.pdf) und
 * manifest.json erzeugt die GitHub Action mit uebungen/build_site.py.
 */
"use strict";

// --------------------------------------------------------------------------
// Grunddaten (entsprechen der Standortbestimmung)
// --------------------------------------------------------------------------
const STRAENGE = [
  { nr: 1, titel: "Zahlen und Stellenwert" },
  { nr: 2, titel: "Operationen und Rechenreihenfolge" },
  { nr: 3, titel: "Brüche" },
  { nr: 4, titel: "Proportionalität und Prozent" },
  { nr: 5, titel: "Terme" },
  { nr: 6, titel: "Gleichungen" },
  { nr: 7, titel: "Funktionen und Graphen" },
  { nr: 8, titel: "Geometrie und Grössen" },
  { nr: 9, titel: "Sprache und Mathematik" },
];
const NIVEAUS = ["A", "B", "C", "D"];
const AUFGABEN = { A: [1, 2], B: [3, 4], C: [5], D: [6] };  // Aufgabennummern pro Niveau

// --------------------------------------------------------------------------
// Auswertung (reine Funktionen, ohne Browser testbar)
// --------------------------------------------------------------------------

/** Status eines Feldes: null (nichts eingetragen), 0, 1 oder 2 */
function zellstatus(strang, niveau, punkte) {
  const werte = AUFGABEN[niveau]
    .map((n) => punkte[`${strang}.${n}`])
    .filter((w) => w !== undefined);
  if (werte.length === 0) return null;
  const mittel = werte.reduce((a, b) => a + b, 0) / werte.length;
  if (mittel >= 1.5) return 2;
  if (mittel >= 0.5) return 1;
  return 0;
}

/** Bruchstelle eines Strangs: tiefstes Niveau, das nicht sicher gelöst ist.
 *  Rückgabe: null (keine Daten), {niveau: null} (alles sicher) oder
 *  {niveau, status}. Nicht bearbeitete Niveaus werden übersprungen. */
function bruchstelle(strang, punkte) {
  let daten = false;
  for (const n of NIVEAUS) {
    const s = zellstatus(strang, n, punkte);
    if (s === null) continue;
    daten = true;
    if (s < 2) return { niveau: n, status: s };
  }
  return daten ? { niveau: null } : null;
}

/** Vorgeschlagene Felder, z. B. ["3B", "3C", "6B"] */
function vorschlaege(punkte, naechstesNiveau) {
  const felder = [];
  for (const { nr } of STRAENGE) {
    const b = bruchstelle(nr, punkte);
    if (!b || !b.niveau) continue;
    felder.push(`${nr}${b.niveau}`);
    const i = NIVEAUS.indexOf(b.niveau);
    if (naechstesNiveau && b.status === 1 && i < NIVEAUS.length - 1) {
      felder.push(`${nr}${NIVEAUS[i + 1]}`);
    }
  }
  return felder;
}

function sortiereFelder(felder) {
  return [...felder].sort((a, b) =>
    a[0] - b[0] || NIVEAUS.indexOf(a[1]) - NIVEAUS.indexOf(b[1]));
}

function befehl(felder, name) {
  if (felder.length === 0) return "Noch keine Felder ausgewählt.";
  const titel = name ? `Übungsblatt ${name}` : "Übungsblatt";
  const datei = dateiname(name, "Uebungsblatt");
  return [
    "python3 uebungen/blatt.py blatt",
    `  --felder ${felder.join(" ")}`,
    "  --ohne-checks --kurzloesungen --mischen 1",
    `  --titel "${titel.replace(/"/g, "'")}"`,
    `  -o ${datei} --pdf`,
  ].join(" \\\n");
}

function dateiname(name, praefix) {
  const teil = (name || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return teil ? `${praefix}_${teil}` : praefix;
}

if (typeof module !== "undefined") {
  module.exports = { zellstatus, bruchstelle, vorschlaege, sortiereFelder, befehl, dateiname };
}

// --------------------------------------------------------------------------
// Oberfläche
// --------------------------------------------------------------------------
if (typeof document !== "undefined") {
  const zustand = {
    punkte: {},            // "3.2" -> 0 | 1 | 2
    manifest: { felder: {} },
    abgewaehlt: new Set(), // vorgeschlagene Felder, die abgewählt wurden
    zusaetzlich: new Set() // von Hand hinzugefügte Felder
  };
  const $ = (id) => document.getElementById(id);
  const ZYKLUS = [undefined, 2, 1, 0];

  // ---- Raster aufbauen --------------------------------------------------
  function baueRaster() {
    const tbody = $("raster").querySelector("tbody");
    tbody.innerHTML = "";
    for (const { nr, titel } of STRAENGE) {
      const tr = document.createElement("tr");
      const th = document.createElement("th");
      th.scope = "row";
      th.innerHTML = `<b>${nr}</b>${titel}`;
      tr.appendChild(th);
      for (const n of NIVEAUS) {
        const td = document.createElement("td");
        td.className = "zelle";
        td.dataset.feld = `${nr}${n}`;
        for (const a of AUFGABEN[n]) {
          const key = `${nr}.${a}`;
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "wert";
          btn.dataset.key = key;
          btn.innerHTML = `<span class="punkt">–</span><small>${key}</small>`;
          btn.addEventListener("click", () => weiterschalten(key));
          btn.addEventListener("keydown", (e) => tasteGedrueckt(e, key));
          td.appendChild(btn);
        }
        tr.appendChild(td);
      }
      const bs = document.createElement("td");
      bs.className = "bruchstelle";
      bs.dataset.strang = nr;
      tr.appendChild(bs);
      tbody.appendChild(tr);
    }
  }

  function setzePunkte(key, wert) {
    if (wert === undefined) delete zustand.punkte[key];
    else zustand.punkte[key] = wert;
    zustand.abgewaehlt.clear();
    aktualisiere();
  }

  function weiterschalten(key) {
    const i = ZYKLUS.indexOf(zustand.punkte[key]);
    setzePunkte(key, ZYKLUS[(i + 1) % ZYKLUS.length]);
  }

  function tasteGedrueckt(e, key) {
    if (["0", "1", "2"].includes(e.key)) {
      setzePunkte(key, Number(e.key));
      e.preventDefault();
    } else if (e.key === "Backspace" || e.key === "Delete") {
      setzePunkte(key, undefined);
      e.preventDefault();
    }
  }

  // ---- Anzeige aktualisieren -------------------------------------------
  function aktualisiere() {
    // Punkte-Knöpfe
    document.querySelectorAll("button.wert").forEach((btn) => {
      const w = zustand.punkte[btn.dataset.key];
      const span = btn.querySelector(".punkt");
      span.textContent = w === undefined ? "–" : String(w);
      span.className = "punkt" + (w === undefined ? "" : ` p${w}`);
      const text = w === undefined ? "nicht bearbeitet"
        : w === 2 ? "2 Punkte, sicher gelöst"
        : w === 1 ? "1 Punkt, teilweise gelöst" : "0 Punkte, nicht gelöst";
      btn.setAttribute("aria-label", `Aufgabe ${btn.dataset.key}: ${text}`);
    });
    // Zellen und Bruchstellen
    document.querySelectorAll("td.zelle").forEach((td) => {
      const s = zellstatus(td.dataset.feld[0], td.dataset.feld[1], zustand.punkte);
      td.className = "zelle" + (s === null ? "" : ` s${s}`);
    });
    document.querySelectorAll("td.bruchstelle").forEach((td) => {
      const b = bruchstelle(Number(td.dataset.strang), zustand.punkte);
      td.classList.toggle("ok", !!b && !b.niveau);
      td.textContent = !b ? "" : b.niveau ? b.niveau : "alles sicher";
    });
    zeigeVorschlag();
  }

  function ausgewaehlteFelder() {
    const vor = vorschlaege(zustand.punkte, $("naechstes").checked);
    const alle = new Set([...vor, ...zustand.zusaetzlich]);
    return sortiereFelder([...alle]);
  }

  function zeigeVorschlag() {
    const ziel = $("vorschlag");
    const felder = ausgewaehlteFelder();
    if (felder.length === 0) {
      ziel.innerHTML = Object.keys(zustand.punkte).length === 0
        ? "<p>Sobald Punkte eingetragen sind, erscheinen hier die vorgeschlagenen Felder.</p>"
        : "<p>Alle eingetragenen Felder sind sicher gelöst. Es gibt keinen Vorschlag; Sie können unten ein Feld von Hand hinzufügen.</p>";
    } else {
      const ul = document.createElement("ul");
      ul.className = "vorschlag-liste";
      for (const f of felder) {
        const info = zustand.manifest.felder[f];
        const li = document.createElement("li");
        if (info && info.uebung) {
          const checked = !zustand.abgewaehlt.has(f);
          li.innerHTML = `<label><input type="checkbox" data-feld="${f}" ${checked ? "checked" : ""}>
            <span class="id">${f}</span><span>${info.titel}
            <span class="info">(${info.anzahl} Aufgaben${info.check ? ", Check vorhanden" : ""})</span></span></label>`;
          li.querySelector("input").addEventListener("change", (e) => {
            if (e.target.checked) zustand.abgewaehlt.delete(f);
            else zustand.abgewaehlt.add(f);
            zeigeBefehlUndKnopf();
          });
        } else {
          const strang = STRAENGE.find((s) => String(s.nr) === f[0]);
          li.className = "ohne";
          li.innerHTML = `<span class="id">${f}</span> <span class="fehlt">${strang ? strang.titel : ""}:
            noch keine Aufgaben in der Sammlung</span>`;
        }
        ul.appendChild(li);
      }
      ziel.innerHTML = "<p>Vorgeschlagene Felder:</p>";
      ziel.appendChild(ul);
    }
    zeigeBefehlUndKnopf();
  }

  function pdfFelder() {
    return ausgewaehlteFelder().filter((f) =>
      zustand.manifest.felder[f] && zustand.manifest.felder[f].uebung && !zustand.abgewaehlt.has(f));
  }

  function zeigeBefehlUndKnopf() {
    const felder = pdfFelder();
    $("erstellen").disabled = felder.length === 0;
    $("befehl").textContent = befehl(felder, $("name").value.trim());
  }

  function fuelleAuswahl() {
    const sel = $("weiteres");
    sel.innerHTML = '<option value="">Feld wählen …</option>';
    for (const f of sortiereFelder(Object.keys(zustand.manifest.felder))) {
      const info = zustand.manifest.felder[f];
      if (!info.uebung) continue;
      const opt = document.createElement("option");
      opt.value = f;
      opt.textContent = `${f}  ${info.titel}`;
      sel.appendChild(opt);
    }
    sel.addEventListener("change", () => {
      if (!sel.value) return;
      zustand.zusaetzlich.add(sel.value);
      zustand.abgewaehlt.delete(sel.value);
      sel.value = "";
      zeigeVorschlag();
    });
  }

  // ---- PDF zusammenstellen ---------------------------------------------
  function sicherFuerSchrift(text, font) {
    // Standardschriften kennen nur WinAnsi-Zeichen; andere Zeichen ersetzen
    return [...text].map((z) => {
      try { font.encodeText(z); return z; } catch (_) {
        const ohne = z.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        try { font.encodeText(ohne); return ohne; } catch (__) { return "?"; }
      }
    }).join("");
  }

  async function deckblatt(doc, name, felder) {
    const { StandardFonts, rgb } = PDFLib;
    const font = await doc.embedFont(StandardFonts.Helvetica);
    const fett = await doc.embedFont(StandardFonts.HelveticaBold);
    const tinte = rgb(0.04, 0.24, 0.42);
    const grau = rgb(0.36, 0.42, 0.49);
    const seite = doc.insertPage(0, [595.28, 841.89]);
    const x = 64;
    let y = 770;
    const zeile = (text, opt) => {
      seite.drawText(sicherFuerSchrift(text, opt.font || font),
        { x: opt.x || x, y, size: opt.size || 11, font: opt.font || font, color: opt.color || rgb(0.1, 0.15, 0.2) });
    };

    zeile("Förderkurs Mathematik", { color: grau });
    y -= 40;
    zeile("Übungspaket", { size: 28, font: fett, color: tinte });
    y -= 30;
    if (name) { zeile(name, { size: 16 }); y -= 22; }
    zeile(new Date().toLocaleDateString("de-CH", { day: "numeric", month: "long", year: "numeric" }), { color: grau });
    y -= 48;

    zeile("Ihre Schwerpunkte", { size: 14, font: fett, color: tinte });
    y -= 24;
    for (const f of felder) {
      zeile(f, { font: fett });
      zeile(zustand.manifest.felder[f].titel, { x: x + 36 });
      y -= 18;
    }
    y -= 26;

    const profil = STRAENGE.map((s) => ({ ...s, b: bruchstelle(s.nr, zustand.punkte) })).filter((s) => s.b);
    if (profil.length) {
      zeile("Ihr Profil aus der Standortbestimmung", { size: 14, font: fett, color: tinte });
      y -= 24;
      for (const s of profil) {
        zeile(`${s.nr}  ${s.titel}`, {});
        zeile(s.b.niveau ? `Bruchstelle ${s.b.niveau}` : "alles sicher",
          { x: 380, color: s.b.niveau ? tinte : grau });
        y -= 18;
      }
      y -= 26;
    }

    const hinweis = [
      "So arbeiten Sie mit diesem Paket:",
      "Lösen Sie die Aufgaben der Reihe nach, von den einfacheren zu den schwierigeren.",
      "Notieren Sie bei jeder Aufgabe, bevor Sie kontrollieren, wie sicher Sie sind (1 bis 4).",
      "Die Kurzlösungen stehen jeweils am Ende eines Blatts. Lesen Sie bei einem Fehler",
      "den Hinweis dazu: Er sagt Ihnen, welche Mini-Lektion weiterhilft.",
    ];
    hinweis.forEach((t, i) => { zeile(t, { font: i === 0 ? fett : font }); y -= 17; });
  }

  async function erstellePdf() {
    const status = $("status");
    status.className = "status";
    const felder = pdfFelder();
    const name = $("name").value.trim();
    if (typeof PDFLib === "undefined") {
      status.className = "status fehler";
      status.textContent = "Die Bibliothek zum Zusammenfügen der PDFs wurde nicht geladen. Prüfen Sie die Internetverbindung und laden Sie die Seite neu.";
      return;
    }
    status.textContent = "Das PDF wird zusammengestellt …";
    $("erstellen").disabled = true;
    try {
      const doc = await PDFLib.PDFDocument.create();
      const dateien = [];
      for (const f of felder) dateien.push(zustand.manifest.felder[f].uebung);
      if ($("checks").checked) {
        for (const f of felder) if (zustand.manifest.felder[f].check) dateien.push(zustand.manifest.felder[f].check);
      }
      for (const pfad of dateien) {
        const antwort = await fetch(pfad);
        if (!antwort.ok) throw new Error(`${pfad} konnte nicht geladen werden (${antwort.status}).`);
        const quelle = await PDFLib.PDFDocument.load(await antwort.arrayBuffer());
        const seiten = await doc.copyPages(quelle, quelle.getPageIndices());
        seiten.forEach((s) => doc.addPage(s));
      }
      await deckblatt(doc, name, felder);
      const blob = new Blob([await doc.save()], { type: "application/pdf" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${dateiname(name, "Uebungspaket")}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
      status.textContent = `${link.download} wurde erstellt: Deckblatt und ${dateien.length} ${dateien.length === 1 ? "Blatt" : "Blätter"}.`;
    } catch (fehler) {
      status.className = "status fehler";
      status.textContent = `Das PDF konnte nicht erstellt werden: ${fehler.message} ` +
        "Falls Sie die Seite lokal geöffnet haben: Sie funktioniert nur über einen Webserver, " +
        "z. B. mit «python3 -m http.server» im Ordner site.";
    } finally {
      zeigeBefehlUndKnopf();
    }
  }

  // ---- Start -------------------------------------------------------------
  async function start() {
    baueRaster();
    try {
      const antwort = await fetch("manifest.json", { cache: "no-store" });
      if (!antwort.ok) throw new Error(antwort.status);
      zustand.manifest = await antwort.json();
      const stand = new Date(zustand.manifest.erstellt);
      $("stand").textContent = `Aufgabensammlung erstellt am ${stand.toLocaleDateString("de-CH")}.`;
    } catch (_) {
      $("status").className = "status fehler";
      $("status").textContent = "Die Liste der Übungsblätter (manifest.json) fehlt. " +
        "Sie wird von der GitHub Action erzeugt, lokal mit «python3 uebungen/build_site.py».";
    }
    fuelleAuswahl();
    $("naechstes").addEventListener("change", () => { zustand.abgewaehlt.clear(); zeigeVorschlag(); });
    $("name").addEventListener("input", zeigeBefehlUndKnopf);
    $("erstellen").addEventListener("click", erstellePdf);
    $("leeren").addEventListener("click", () => {
      zustand.punkte = {};
      zustand.abgewaehlt.clear();
      zustand.zusaetzlich.clear();
      aktualisiere();
    });
    $("kopieren").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText($("befehl").textContent);
        $("kopieren").textContent = "Befehl kopiert";
      } catch (_) {
        $("kopieren").textContent = "Kopieren nicht möglich; bitte markieren";
      }
      setTimeout(() => { $("kopieren").textContent = "Befehl kopieren"; }, 2500);
    });
    aktualisiere();
  }

  start();
}
