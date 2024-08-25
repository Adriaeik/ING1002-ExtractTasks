import nbformat
import os
import zipfile
import shutil
import tempfile
import re
import csv

# Funksjon for å pakke ut zip-fila til ei midlertidig mappe
def unzip_file_to_temp(zip_file_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

# Funksjon for å identifisere oppgaver, oppgavetekst og studentens svar
def extract_tasks_and_answers(notebook_path, file_index):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    tasks = []
    inside_task = False

    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'markdown':
            # Iterer gjennom hver linje i markdown-cellen for å finne bokstaven
            for line in cell.source.splitlines():
                match = re.search(r'^\s*#+\s*([a-zA-Z])\)\s*', line.strip())
                if match:
                    task_letter = match.group(1)
                    # Formaterer oppgåva med filindex og bokstav
                    task_header = nbformat.v4.new_markdown_cell(source=f"### Oppgave {file_index}.{task_letter}:")
                    tasks.append(task_header)
                    # Legg til selve oppgaveteksten
                    tasks.append(cell)
                    inside_task = True
                    break  # Når vi finner en match, kan vi hoppe til neste celle

        elif inside_task and cell.cell_type == 'code':
            # Legg til den første kodecellen rett etter markdown-cellen
            tasks.append(cell)
            inside_task = False  # Avslutt når kodecellen er lagt til

    return tasks

# Hovedfunksjon for å gå gjennom alle notebook-filene i en ZIP-fil
def process_notebooks(notebooks_dir, output_file):
    output_nb = nbformat.v4.new_notebook()
    for root, dirs, files in os.walk(notebooks_dir):
        for file in files:
            if file.endswith(".ipynb"):
                file_index = re.search(r'(\d+)_', file).group(1)  # Henter ut nummeret frå filnavnet
                notebook_path = os.path.join(root, file)
                tasks = extract_tasks_and_answers(notebook_path, file_index)
                output_nb.cells.extend(tasks)

    # Skriv resultata til ein ny .ipynb fil
    with open(output_file, 'w', encoding='utf-8') as f:
        nbformat.write(output_nb, f)

# Funksjon for å behandle en ZIP-fil og lagre resultatet som en .ipynb-fil
def process_zip_file(zip_file_path):
    temp_unzip_dir = unzip_file_to_temp(zip_file_path)

    try:
        output_file = os.path.splitext(zip_file_path)[0] + '.ipynb'
        process_notebooks(temp_unzip_dir, output_file)
    finally:
        # Slett den midlertidige mappa etter bruk
        shutil.rmtree(temp_unzip_dir)

# Funksjon for å lese ZIP-fil stier fra CSV og behandle dem
def process_csv(csv_file_path):
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            zip_file_path = row[0]  # Anta at stien til ZIP-filen er i første kolonne
            if os.path.exists(zip_file_path):
                process_zip_file(zip_file_path)

# CSV-fil som inneholder stier til ZIP-filer
csv_file_path = 'ZIP_Path.csv'

# Kjør prosessen for alle ZIP-filer oppført i CSV-filen
process_csv(csv_file_path)
