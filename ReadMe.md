## Studass on Ezy Mode

Dette prosjektet inneheld to skript:

1. **Extract_ZIP_wText.py** - Hentar ut oppgåvebesvarelser med tekst.
2. **Extract_ZIP.py** - Hentar ut oppgåvebesvarelser utan tekst.

## Bruk av programmet

1. Opprett ei fil kalla `ZIP_Path.csv` og plasser den i same mappe som skripta. I denne fila legg du til stien til mappa med ZIP-filene frå rotmappa på PC-en din.
2. Programmet vil deretter extracte ZIP-filene og lagre dei som `.md`-dokument med same namn som ZIP-fila, i same mappe.


## Installasjon av nødvendige bibliotek

Du treng berre å installere eitt eksternt bibliotek, `nbformat`. For å gjere dette, kan du bruke følgjande kommando:

```bash
pip install nbformat
```

### Tilpassing av lagringssted

For å endre lagringssted til noko anna enn samme mappe som ZIP fila kan du finne og modifisere denne linja i skriptet:

```python
output_file = os.path.splitext(zip_file_path)[0] + '.ipynb'
```

## Køyre koden
- køyr koden
