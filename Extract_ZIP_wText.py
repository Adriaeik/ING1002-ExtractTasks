# -*- coding: utf-8 -*-
"""
Ekstraherer oppgåver (markdown) + første kodecelle etter kvar oppgåve frå alle
.ipynb i ZIP-arkiv lista i ZIP_Path.csv. Éi utfil per ZIP.
I tillegg lagar skriptet ein rapport (ZIP_Report.csv) som fortel om kvar ZIP
har ≥ 50 % besvarte oppgåver.
"""

import os
import re
import csv
import uuid
import shutil
import zipfile
import tempfile
import logging
from typing import Tuple, List, Dict

import nbformat


# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


# ---------- ZIP ----------
def unzip_file_to_temp(zip_file_path: str) -> str:
    """Pakk ut ZIP til ei midlertidig mappe og returner stien."""
    temp_dir = tempfile.mkdtemp(prefix="nb_unzip_")
    with zipfile.ZipFile(zip_file_path, "r") as zf:
        zf.extractall(temp_dir)
    return temp_dir


# ---------- Notebook-lesing (robust) ----------
def _ensure_cell_ids(nb):
    """Sørg for at alle celler har id (framtidige nbformat-krav)."""
    changed = False
    for cell in getattr(nb, "cells", []):
        if "id" not in cell or not cell.get("id"):
            cell["id"] = uuid.uuid4().hex
            changed = True
    if changed:
        logging.debug("La til manglande cell.id på nokre celler.")
    return nb


def _read_notebook_robust(path: str):
    """Les notebook og normaliser. Tolerer ikkje-UTF8."""
    with open(path, "rb") as f:
        raw = f.read()

    # Prøv UTF-8 → cp1252 → latin-1 (med erstatning)
    for enc, kw in (
        ("utf-8", {}),
        ("cp1252", {}),
        ("latin-1", {"errors": "replace"}),
    ):
        try:
            text = raw.decode(enc, **kw)
            if enc != "utf-8":
                logging.warning(f"Ikkje-UTF8 notebook, tolka som {enc}: {path}")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError("Kunne ikkje dekode notebook som tekst.")

    nb = nbformat.reads(text, as_version=4)

    try:
        nb = nbformat.normalize(nb)  # type: ignore[attr-defined]
    except Exception:
        pass

    nb = _ensure_cell_ids(nb)
    return nb


# ---------- Ekstrahering og vurdering ----------
TASK_HEADER_RE = re.compile(r'^\s*#+\s*([a-zA-Z])\)\s*')
SKIP_DIRS = {".git", ".ipynb_checkpoints", "__MACOSX", "resources"}

# Her lagrar vi skeletthash per oppgave
SKELETON_CODE: Dict[str, str] = {}


def _normalize_code(src: str) -> str:
    """Normaliser kode for samanlikning (fjerner whitespace og tomme linjer)."""
    lines = [ln.strip() for ln in (src or "").splitlines() if ln.strip()]
    return "\n".join(lines)


def _codecell_is_answered(cell, task_id: str) -> bool:
    """Heuristikk for 'besvart': kodecelle finst og ikkje identisk med skjelett."""
    if cell is None or cell.cell_type != "code":
        return False
    norm = _normalize_code(cell.source)
    if not norm:
        return False
    skeleton_norm = SKELETON_CODE.get(task_id, "")
    if norm == skeleton_norm:
        return False
    return True


def extract_tasks_and_answers(
    notebook_path: str, file_index: str
) -> Tuple[List[dict], int, int]:
    nb = _read_notebook_robust(notebook_path)

    tasks_cells: List[dict] = []
    inside_task = False
    pending_answer_cell = None

    total_tasks = 0
    answered_tasks = 0

    for cell in nb.cells:
        if cell.cell_type == "markdown":
            matched = False
            for line in cell.source.splitlines():
                m = TASK_HEADER_RE.search(line.strip())
                if m:
                    letter = m.group(1)
                    task_id = f"{file_index}.{letter}"
                    tasks_cells.append(
                        nbformat.v4.new_markdown_cell(
                            source=f"### Oppgave {task_id}:"
                        )
                    )
                    tasks_cells.append(cell)
                    inside_task = True
                    pending_answer_cell = None
                    total_tasks += 1
                    current_task_id = task_id
                    matched = True
                    break
            if matched:
                continue

        if inside_task and cell.cell_type == "code":
            tasks_cells.append(cell)
            pending_answer_cell = cell
            inside_task = False
            if _codecell_is_answered(pending_answer_cell, current_task_id):
                answered_tasks += 1

    return tasks_cells, total_tasks, answered_tasks


# ---------- Ekstraher skjelett ----------
def load_skeleton(zip_file_path: str):
    """Pakk ut skeletthint og lagre kodecellene til global SKELETON_CODE."""
    global SKELETON_CODE
    temp_unzip_dir = unzip_file_to_temp(zip_file_path)
    try:
        for root, dirs, files in os.walk(temp_unzip_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith(".ipynb"):
                    continue
                m = re.search(r'(\d+)_', fname)
                file_index = m.group(1) if m else "0"
                path = os.path.join(root, fname)
                nb = _read_notebook_robust(path)

                inside_task = False
                current_task_id = None
                for cell in nb.cells:
                    if cell.cell_type == "markdown":
                        for line in cell.source.splitlines():
                            m = TASK_HEADER_RE.search(line.strip())
                            if m:
                                letter = m.group(1)
                                current_task_id = f"{file_index}.{letter}"
                                inside_task = True
                                break
                    elif inside_task and cell.cell_type == "code":
                        SKELETON_CODE[current_task_id] = _normalize_code(cell.source)
                        inside_task = False
    finally:
        shutil.rmtree(temp_unzip_dir, ignore_errors=True)


# ---------- Prosessering ----------
def process_notebooks(notebooks_dir: str, output_file: str) -> Dict[str, int]:
    output_nb = nbformat.v4.new_notebook()
    total_tasks = 0
    answered_tasks = 0

    for root, dirs, files in os.walk(notebooks_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            if not fname.endswith(".ipynb"):
                continue
            m = re.search(r'(\d+)_', fname)
            file_index = m.group(1) if m else "0"

            path = os.path.join(root, fname)
            try:
                cells, t_cnt, a_cnt = extract_tasks_and_answers(path, file_index)
                total_tasks += t_cnt
                answered_tasks += a_cnt
                if cells:
                    output_nb.cells.extend(cells)
                else:
                    logging.info(f"Ingen oppgåver funne i: {path}")
            except Exception as e:
                logging.error(f"Hoppar over problematisk notebook: {path} ({e})")

    with open(output_file, "w", encoding="utf-8") as f:
        nbformat.write(output_nb, f)
    logging.info(f"Skreiv ut samlenotebook: {output_file}")

    return {
        "total_tasks": total_tasks,
        "answered_tasks": answered_tasks,
    }


def process_zip_file(zip_file_path: str) -> Dict[str, int]:
    logging.info(f"Behandlar ZIP: {zip_file_path}")
    temp_unzip_dir = unzip_file_to_temp(zip_file_path)
    try:
        out_ipynb = os.path.splitext(zip_file_path)[0] + ".ipynb"
        stats = process_notebooks(temp_unzip_dir, out_ipynb)
        return stats
    finally:
        shutil.rmtree(temp_unzip_dir, ignore_errors=True)


# ---------- Les CSV og køyr ----------
def process_csv(csv_file_path: str):
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"Fann ikkje CSV: {csv_file_path}")

    results = []

    with open(csv_file_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile)
        rows = [row[0] for row in reader if row]

    if len(rows) < 2:
        raise ValueError("CSV må ha minst to linjer: [studentmappe], [skjelettzip]")

    student_folder, skeleton_zip = rows[0], rows[1]
    load_skeleton(skeleton_zip)

    for name in os.listdir(student_folder):
        if not name.lower().endswith(".zip"):
            continue

        zip_path = os.path.join(student_folder, name)
        stats = process_zip_file(zip_path)
        total_tasks = stats.get("total_tasks", 0)
        answered_tasks = stats.get("answered_tasks", 0)
        percent = (answered_tasks / total_tasks * 100.0) if total_tasks else 0.0
        passed = total_tasks > 0 and (answered_tasks / total_tasks) >= 0.5

        results.append({
            "zip_file": zip_path,
            "total_tasks": total_tasks,
            "answered_tasks": answered_tasks,
            "percent": f"{percent:.1f}",
            "passed": "YES" if passed else "NO",
        })

        logging.info(
            f"Resultat {name}: {answered_tasks}/{total_tasks} = {percent:.1f}% "
            f"=> {'BESTÅTT' if passed else 'IKKJE BESTÅTT'}"
        )

    report_path = "ZIP_Report.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["zip_file", "total_tasks", "answered_tasks", "percent", "passed"]
        )
        writer.writeheader()
        writer.writerows(results)

    logging.info(f"Skreiv rapport: {report_path}")


if __name__ == "__main__":
    CSV_FILE = "ZIP_Path.csv"
    process_csv(CSV_FILE)
