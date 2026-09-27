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

print('=== HEADER DRAWINGS (LOGOS) ===')
for d in root.findall('.//wp:anchor', ns):
    posH = d.find('.//wp:positionH', ns)
    posV = d.find('.//wp:positionV', ns)
    extent = d.find('wp:extent', ns)
    posH_str = posH.find('wp:posOffset', ns).text if posH is not None and posH.find('wp:posOffset', ns) is not None else '?'
    posV_str = posV.find('wp:posOffset', ns).text if posV is not None and posV.find('wp:posOffset', ns) is not None else '?'
    cx = extent.attrib.get('cx', '?') if extent is not None else '?'
    cy = extent.attrib.get('cy', '?') if extent is not None else '?'
    blip = d.find('.//a:blip', ns)
    rId = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', '?') if blip is not None else '?'
    print(f'Anchor: rId={rId} posH={posH_str} posV={posV_str} cx={cx} cy={cy}')

print('\n=== TABLE CELL WIDTHS & PERCENTAGES ===')
tbl = root.find('.//w:tbl', ns)
tblGrid = tbl.find('w:tblGrid', ns)
cols = [int(c.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w', 0)) for c in tblGrid.findall('w:gridCol', ns)]
total_w = sum(cols)
print(f'Total Grid Width: {total_w} dxa')
for i, w in enumerate(cols):
    print(f'  Col {i}: {w} dxa ({w/total_w*100:.1f}%)')

print('\n=== TABLE ROW 6, 7, 8 STRUCTURE ===')
rows = tbl.findall('w:tr', ns)
for r_idx in [0, 1, 6, 7, 8, 12, 13]:
    tr = rows[r_idx]
    print(f'Row {r_idx}:')
    for c_idx, tc in enumerate(tr.findall('w:tc', ns)):
        tcPr = tc.find('w:tcPr', ns)
        tcW = tcPr.find('w:tcW', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w', '?') if tcPr is not None and tcPr.find('w:tcW', ns) is not None else '?'
        span = tcPr.find('w:gridSpan', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '1') if tcPr is not None and tcPr.find('w:gridSpan', ns) is not None else '1'
        txt = ''.join(tc.itertext()).strip()
        # Find runs inside cell to check font and size
        fonts = [r.find('.//w:rFonts', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii', '?') for r in tc.findall('.//w:r', ns) if r.find('.//w:rFonts', ns) is not None]
        szs = [r.find('.//w:sz', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '?') for r in tc.findall('.//w:sz', ns) if r.find('.//w:sz', ns) is not None]
        bolds = [r.find('.//w:b', ns) is not None for r in tc.findall('.//w:r', ns)]
        print(f'  C{c_idx}: span={span} w={tcW} txt="{txt}" fonts={fonts[:2]} szs={szs[:2]} bolds={bolds[:2]}')

print('\n=== PARAGRAPH FONTS & SIZES ===')
for i, el in enumerate(root.find('.//w:body', ns)):
    if el.tag.endswith('p'):
        txt = ''.join(el.itertext()).strip()
        if not txt: continue
        szs = [r.find('.//w:sz', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '?') for r in el.findall('.//w:r', ns) if r.find('.//w:sz', ns) is not None]
        szCs = [r.find('.//w:szCs', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '?') for r in el.findall('.//w:r', ns) if r.find('.//w:szCs', ns) is not None]
        jc = el.find('.//w:jc', ns).attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '?') if el.find('.//w:jc', ns) is not None else 'default'
        print(f'P{i:02d}: jc={jc} sz={szs[:1]} szCs={szCs[:1]} | "{txt}"')
