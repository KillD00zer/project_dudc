import docx

doc = docx.Document('شهادة.docx')
t = doc.tables[0]
tblPr = t._tbl.tblPr
print('tblBorders:', [b.tag.split('}')[-1] + '=' + b.attrib.get('{http://schemas.openxmlformats.org/wordprocessingDrawing}val', b.attrib.get('{http://schemas.openxmlformats.org/wordprocessingDrawing}color', str(b.attrib))) for b in tblPr.xpath('.//w:tblBorders/*')])

for r_idx in [0, 1, 6, 7, 8, 12, 13]:
    row = t.rows[r_idx]
    for c_idx, cell in enumerate(row.cells):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = tcPr.xpath('./w:shd/@w:fill')
        borders = [b.tag.split('}')[-1] + ':' + b.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '') + ':' + b.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color', '') for b in tcPr.xpath('./w:tcBorders/*')]
        w = tcPr.xpath('./w:tcW/@w:w')
        if shd or borders or w:
            print(f'R{r_idx}C{c_idx}: txt="{cell.text.strip()[:15]}", shd={shd}, w={w}, borders={borders}')
        break
