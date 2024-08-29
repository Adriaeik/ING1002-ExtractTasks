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

# Funksjon for å identifisere oppgaver og hente studentens svar
def extract_code_cells(notebook_path, file_index):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    tasks = []
    task_number = 1  # Teller oppgavene i hver notebook-fil

    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'markdown':
            # Iterer gjennom hver linje i markdown-cellen for å finne bokstaven
            for line in cell.source.splitlines():
                match = re.search(r'^\s*#+\s*([a-zA-Z])\)\s*', line.strip())
                if match:
                    task_letter = match.group(1)
                    # Hent den første kodecella rett etter markdown-cella
                    if i + 1 < len(nb.cells) and nb.cells[i + 1].cell_type == 'code':
                        code_cell = nb.cells[i + 1]
                        # Formaterer oppgaven med filindex og task_number i markdown
                        task_header = nbformat.v4.new_markdown_cell(source=f"### Oppgave {file_index}.{task_number}{task_letter}:")
                        tasks.append(task_header)
                        tasks.append(code_cell)
                        task_number += 1  # Øker task_number for neste oppgave
                    break  # Når vi finner en match, kan vi hoppe til neste celle

    return tasks

# Hovedfunksjon for å behandle en ZIP-fil og lagre resultatet som en .ipynb-fil
def process_zip_file(zip_file_path, index):
    temp_unzip_dir = unzip_file_to_temp(zip_file_path)

    try:
        output_nb = nbformat.v4.new_notebook()
        for root, dirs, files in os.walk(temp_unzip_dir):
            for file in files:
                if file.endswith(".ipynb"):
                    notebook_path = os.path.join(root, file)
                    # Bruker filnavn til å hente ut en unik indeks
                    match = re.search(r'(\d+)_', file)
                    if match:
                        file_index = match.group(1)
                    else:
                        file_index = str(index)  # Bruker CSV-indeksen hvis ingen tall finnes i filnavnet

                    tasks = extract_code_cells(notebook_path, file_index)
                    output_nb.cells.extend(tasks)

        # Lagre resultatet som en .ipynb-fil med samme navn som  ZIP-filen
        output_file = os.path.splitext(zip_file_path)[0] + '.ipynb'
        with open(output_file, 'w', encoding='utf-8') as f:
            nbformat.write(output_nb, f)
    finally:
        # Slett den midlertidige mappa etter bruk
        shutil.rmtree(temp_unzip_dir)

# Funksjon for å lese ZIP-fil stier fra CSV og behandle dem
def process_csv(csv_file_path):
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for index, row in enumerate(reader, start=1):
            zip_file_path = row[0]  # Anta at stien til ZIP-filen er i første kolonne
            if os.path.exists(zip_file_path):
                process_zip_file(zip_file_path, index)

# CSV-fil som inneholder stier til ZIP-filer
csv_file_path = 'ZIP_Path.csv'

# Kjør prosessen for alle ZIP-filer oppført i CSV-filen
process_csv(csv_file_path)
