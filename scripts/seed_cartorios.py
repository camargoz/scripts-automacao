import json
import os
import sys
from datetime import datetime
import openpyxl
import psycopg2

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'examples', 'tabela_cartorios.xlsx')
RESPONSES_DIR = os.path.join(os.path.dirname(__file__), '..', 'responses')

DB_PARAMS = {
    'host':     os.environ.get('PGHOST',     '10.210.10.15'),
    'port':     os.environ.get('PGPORT',     '5432'),
    'user':     os.environ.get('PGUSER',     'postgres'),
    'password': os.environ.get('PGPASSWORD', 'sofkronoos@@2020'),
    'dbname':   os.environ.get('PGDATABASE', 'kronoos'),
}

INSERT_SQL = """
INSERT INTO "CartorioV2" (nome, estado, cidade, cns, atribuicoes, ativo, created_at, updated_at)
VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
"""


def parse_atribuicoes(value):
    if not value:
        return json.dumps([])
    parts = [p.strip() for p in str(value).split('/') if p.strip()]
    return json.dumps(parts, ensure_ascii=False)


def load_rows():
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue
        cns         = row[0]
        nome        = row[2]
        atribuicoes = parse_atribuicoes(row[4])
        estado      = row[8]
        cidade      = row[9]
        if not cns:
            continue
        rows.append({
            'nome':        nome,
            'estado':      estado,
            'cidade':      cidade,
            'cns':         str(cns).strip(),
            'atribuicoes': atribuicoes,
            'ativo':       True,
        })
    wb.close()
    return rows


def save_errors(errors):
    os.makedirs(RESPONSES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(RESPONSES_DIR, f'seed_cartorios_errors_{timestamp}.json')
    payload = {
        'status': 'ERRO',
        'message': 'SEED_ERRORS',
        'data': errors,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Erros salvos em: {path}")


def main():
    dry_run = '--dry-run' in sys.argv

    print(f"Lendo {EXCEL_PATH} ...")
    rows = load_rows()
    total = len(rows)
    print(f"Total de registros encontrados: {total}")

    if dry_run:
        print("\n[DRY-RUN] Primeiros 5 registros:")
        for r in rows[:5]:
            print(r)
        return

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    inserted = 0
    errors = []

    try:
        for i, row in enumerate(rows):
            params = (row['nome'], row['estado'], row['cidade'], row['cns'], row['atribuicoes'], row['ativo'])
            try:
                cur.execute(INSERT_SQL, params)
                conn.commit()
                inserted += 1
            except Exception as e:
                conn.rollback()
                errors.append({'row': row, 'error': str(e)})
            if (i + 1) % 100 == 0 or (i + 1) == total:
                print(f"  {i + 1}/{total} (erros: {len(errors)})", end='\r', flush=True)
    finally:
        cur.close()
        conn.close()

    print(f"\nConcluído: {inserted}/{total} inseridos.")
    if errors:
        print(f"{len(errors)} erro(s) encontrado(s).")
        save_errors(errors)


if __name__ == '__main__':
    main()
