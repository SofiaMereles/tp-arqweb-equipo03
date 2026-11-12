"""Genera la tabla LaTeX de A5 desde el CSV; no ejecuta operaciones de servidor."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / 'matriz-riesgos.csv').open(encoding='utf-8-sig', newline='')))
assert len(rows) >= 5 and len({r['id'] for r in rows}) == len(rows)
for row in rows:
    for field in ('p', 'i', 'p_residual', 'i_residual'):
        assert int(row[field]) in (1, 2, 3), (row['id'], field)
    assert int(row['puntaje']) == int(row['p']) * int(row['i']), row['id']
    assert int(row['residual']) == int(row['p_residual']) * int(row['i_residual']), row['id']
    assert all(row.get(field, '').strip() for field in ('mitigacion', 'activador', 'responsable', 'verificacion', 'estado'))

def tex(text):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(char, char) for char in text)

lines = ['% Generado por generar-matriz.py. Editar el CSV y regenerar.\n']
chunks = [rows[index:index + 4] for index in range(0, len(rows), 4)]
for part, chunk in enumerate(chunks, 1):
    label = 'tab:a5-riesgos' if part == 1 else f'tab:a5-riesgos-{part}'
    lines.append(r'\clearpage' + '\n' + r'\begin{table}[H]' + '\n' + r'\centering\small' + '\n')
    lines.append(r'\setlength{\tabcolsep}{4pt}' + '\n' + r'\renewcommand{\arraystretch}{1.10}' + '\n')
    lines.append(r'\caption{Matriz de riesgos de A5, parte ' + str(part) + '/' + str(len(chunks)) + r': probabilidad, impacto, mitigaciones y puntaje residual estimado.}\label{' + label + '}\n')
    lines.append(r'\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{0.75cm} >{\raggedright\arraybackslash}p{2.8cm} >{\raggedright\arraybackslash}p{1.8cm} >{\raggedright\arraybackslash}X}' + '\n')
    lines.append(r'\toprule' + '\n' + r'\textbf{ID} & \textbf{Riesgo} & \textbf{P/I/R} & \textbf{Mitigación, señal y verificación} \\' + '\n' + r'\midrule' + '\n')
    for r in chunk:
        score = f"{r['p']}/{r['i']}/{r['puntaje']}" + r'\par Residual: ' + r['residual']
        detail = tex(r['mitigacion']) + r'\par\textbf{Señal:} ' + tex(r['activador'])
        detail += r'\par\textbf{Rol:} ' + tex(r['responsable']) + r'. \textbf{Verificar:} ' + tex(r['verificacion'])
        lines.append(f"{tex(r['id'])} & {tex(r['riesgo'])} & {score} & {detail} " + r'\\[4pt]' + '\n')
    lines.append('\\bottomrule\n\\end{tabularx}\n\\end{table}\n')
(ROOT / 'matriz-riesgos.tex').write_text(''.join(lines), encoding='utf-8')
print(f'A5: {len(rows)} riesgos; escalas, productos y campos verificados. Matriz LaTeX generada.')
