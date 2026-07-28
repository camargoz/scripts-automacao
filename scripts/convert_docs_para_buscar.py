import json
import os

import openpyxl

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'examples', 'docs_para_buscar.xlsx')
INPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'input')

PAGINAS = [
    ("Ouro Bruto PJ", "ouro_bruto_pj"),
    ("Ouro Bruto PF", "ouro_bruto_pf"),
    ("Ouro Fino PF", "ouro_fino_pf"),
    ("Ouro Fino PJ", "ouro_fino_pj"),
]


def load_page(ws):
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        documento = row[0]
        nome = row[1]
        if not documento:
            continue
        rows.append({"nome": str(nome).strip() if nome else "", "documento": str(documento).strip()})
    return rows


def main():
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    os.makedirs(INPUT_DIR, exist_ok=True)

    for sheet_name, slug in PAGINAS:
        ws = wb[sheet_name]
        rows = load_page(ws)
        out_path = os.path.join(INPUT_DIR, f"{slug}_documentos.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"{sheet_name}: {len(rows)} documento(s) -> {out_path}")

    wb.close()


if __name__ == "__main__":
    main()
