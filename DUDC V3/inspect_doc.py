import sys, os, docx

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('شهادة.docx')

def examine_p(p, label=''):
    pPr = p._p.get_or_add_pPr()
    jc = pPr.xpath('./w:jc/@w:val')
    jc_val = jc[0] if jc else 'none'
    r_info = []
    for r in p.runs:
        font = r.font.name or 'default'
        sz = r.font.size.pt if r.font.size else 'default'
        b = r.font.bold
        color = r.font.color.rgb if (r.font.color and r.font.color.rgb) else 'none'
        txt = r.text.strip()
        if txt:
            r_info.append(f'"{txt}" (f={font}, sz={sz}, b={b}, col={color})')
    print(f'{label}: jc={jc_val}')
    for ri in r_info:
        print('   ', ri)

print('--- HEADER PARAGRAPHS ---')
for i in [0, 1, 2, 3]:
    examine_p(doc.paragraphs[i], f'P{i}')

print('\n--- FOOTER PARAGRAPHS ---')
for i in range(4, len(doc.paragraphs)):
    if doc.paragraphs[i].text.strip():
        examine_p(doc.paragraphs[i], f'P{i}')

print('\n--- TABLE 0 STRUCTURE & STYLES ---')
t = doc.tables[0]
for r_idx in range(len(t.rows)):
    row = t.rows[r_idx]
    seen = []
    cells_out = []
    for c_idx, cell in enumerate(row.cells):
        if cell._tc not in seen:
            seen.append(cell._tc)
            tcPr = cell._tc.get_or_add_tcPr()
            shd = tcPr.xpath('./w:shd/@w:fill')
            shd_val = shd[0] if shd else 'none'
            txt = cell.text.strip()
            runs = cell.paragraphs[0].runs if cell.paragraphs else []
            sz = runs[0].font.size.pt if runs and runs[0].font.size else '?'
            b = runs[0].font.bold if runs else '?'
            col = runs[0].font.color.rgb if runs and runs[0].font.color and runs[0].font.color.rgb else 'none'
            cells_out.append(f'[{c_idx}] "{txt}" (shd={shd_val}, sz={sz}, b={b}, col={col})')
    print(f'Row {r_idx:02d}:', ' | '.join(cells_out))
