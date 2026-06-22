import glob
import json
import os
import sys

import psycopg2

sys.path.insert(0, os.path.dirname(__file__))
from seed_cartorios import DB_PARAMS, INSERT_SQL, RESPONSES_DIR, save_errors


def find_latest_error_file():
    pattern = os.path.join(RESPONSES_DIR, 'seed_cartorios_errors_*.json')
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"Nenhum arquivo de erros encontrado em {RESPONSES_DIR}")
        sys.exit(1)
    return files[-1]


def load_error_rows(path):
    with open(path, encoding='utf-8') as f:
        payload = json.load(f)
    return payload.get('data', [])


def main():
    dry_run = '--dry-run' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]

    error_file = args[0] if args else find_latest_error_file()
    print(f"Arquivo de erros: {error_file}")

    entries = load_error_rows(error_file)
    total = len(entries)
    print(f"Registros para reenviar: {total}")

    if dry_run:
        print("\n[DRY-RUN] Primeiros 5 registros:")
        for e in entries[:5]:
            print(e['row'])
        return

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    inserted = 0
    errors = []

    try:
        for i, entry in enumerate(entries):
            row = entry['row']
            params = (row['nome'], row['estado'], row['cidade'], row['cns'], row['atribuicoes'], row['ativo'])
            try:
                cur.execute(INSERT_SQL, params)
                conn.commit()
                inserted += 1
            except Exception as e:
                conn.rollback()
                errors.append({'row': row, 'error': str(e)})
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"  {i + 1}/{total} (erros: {len(errors)})", end='\r', flush=True)
    finally:
        cur.close()
        conn.close()

    print(f"\nConcluído: {inserted}/{total} inseridos.")
    if errors:
        print(f"{len(errors)} erro(s) remanescente(s).")
        save_errors(errors)
    else:
        print("Todos os registros inseridos com sucesso.")


if __name__ == '__main__':
    main()
