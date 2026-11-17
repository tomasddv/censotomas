"""Regenerar la cartera congelada del PDA usando el censo oficial Sept-26.

Uso desde la raíz del repo: python scripts/generar_carteras.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pda_candidates import build_candidates


def main():
    census = ROOT / 'data' / 'septiembre_2026_oficial.xlsx'
    if not census.exists():
        raise SystemExit(f'No existe la fuente oficial: {census}')
    result = build_candidates(census.read_bytes())
    output = ROOT / 'data' / 'pda_objetivos_septiembre_2026.csv'
    result.to_csv(output, index=False, encoding='utf-8-sig')
    print(f'Generado {output.name} con {len(result)} combinaciones plan-PDV y '
          f'{result.PDV.nunique()} PDV únicos.')
    for plan, d in result.groupby('Plan ID'):
        wave = d[d.Ola == 'Ola 1']
        print(f'{plan}: {len(d)} PDV, {d["HL Mercado"].sum():.2f} HL; '
              f'Ola 1 {len(wave)} PDV, {wave["HL Mercado"].sum():.2f} HL.')


if __name__ == '__main__':
    main()
