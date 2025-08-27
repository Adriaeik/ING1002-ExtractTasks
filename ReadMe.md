
## Studass on Ezy Mode

Dette prosjektet inneheld eit skript:

1. **Extract_ZIP_wText.py** – Hentar ut oppgåvebesvarelser frå studentane sine `.ipynb`-filer inne i ZIP-filene, og set dei saman i éi samlenotebook per student.  
   Skriptet lagar òg ein rapport (`ZIP_Report.csv`) som viser kor mange oppgåver kvar student har fått ut, kor mange som er besvart, prosent, og om ZIP-fila er vurdert til å vere **BESTÅTT** (≥ 50 % besvart).

---

## Bruk av programmet

1. Opprett ei fil kalla `ZIP_Path.csv` og plasser den i same mappe som skriptet.  
   I denne fila legg du inn stien til mappa som inneheld ZIP-filene du har lasta ned frå Blackboard.
2. Programmet vil for kvar ZIP-fil:
   - Pakkje ut innhaldet.
   - Finne alle `.ipynb`-filene rekursivt.
   - Ekstrahere oppgåver og første tilhøyrande kodecelle.
   - Bygge ei ny `.ipynb` med namn lik ZIP-fila.
   - Logge resultatet til `ZIP_Report.csv` med info om totalt tal oppgåver, besvarte oppgåver, prosent og bestått/ikkje bestått.

> Note: Har ikkje funne ein brukandes måte å laste ned frå Blackboard, så ZIP-filene må lastast ned manuelt.

---

## Installasjon av nødvendige bibliotek

Du treng berre å installere eitt eksternt bibliotek: `nbformat`.

```bash
pip install nbformat
````

---

## Tilpassing av lagringsstad

Som standard blir samlenotebooken lagra i same mappe som ZIP-fila.
Dersom du vil endre dette, kan du modifisere denne linja i `Extract_ZIP_wText.py`:

```python
out_ipynb = os.path.splitext(zip_file_path)[0] + ".ipynb"
```

---

## Køyre koden

Køyr koden

Resultat:

* Éi `.ipynb`-fil per ZIP, lagra i same mappe som ZIP-fila.
* Éi `ZIP_Report.csv` med oversikt over kven som bestod (≥ 50 % besvarte oppgåver).

