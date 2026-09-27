import sys, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
tree = ET.parse(r'd:\Work\GIS_tools\project_dudc\DUDC V3\template_extracted\word\document.xml')
root = tree.getroot()
ns = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'
}

pgMar = root.find('.//w:pgMar', ns)
if pgMar is not None:
    print('PAGE MARGINS:', pgMar.attrib)

pgSz = root.find('.//w:pgSz', ns)
if pgSz is not None:
    print('PAGE SIZE:', pgSz.attrib)

print('--- BODY ELEMENTS ---')
for i, el in enumerate(root.find('.//w:body', ns)):
    tag = el.tag.split('}')[-1]
    if tag == 'p':
        txt = ''.join(el.itertext()).strip()
        drawings = el.findall('.//w:drawing', ns)
        print(f'P{i:02d}: drawings={len(drawings)} | text="{txt}"')
    elif tag == 'tbl':
        tblGrid = el.find('w:tblGrid', ns)
        cols = [c.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w', '?') for c in tblGrid.findall('w:gridCol', ns)] if tblGrid is not None else []
        print(f'TBL{i:02d}: cols={cols} ({len(cols)} cols)')
        for r_i, tr in enumerate(el.findall('w:tr', ns)):
            cells_info = []
            for c_i, tc in enumerate(tr.findall('w:tc', ns)):
                tcPr = tc.find('w:tcPr', ns)
                span = tcPr.find('w:gridSpan', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '1') if tcPr is not None and tcPr.find('w:gridSpan', ns) is not None else '1'
                txt = ''.join(tc.itertext()).strip()
                cells_info.append(f'C{c_i}(span={span}): "{txt}"')
            print(f'  Row {r_i:02d}: ' + ' | '.join(cells_info))
