import json, zipfile, xml.etree.ElementTree as E
from pathlib import Path
source=Path('C:/Users/a.kriuchkov/Downloads/Копия Таблица грунтов (разработка траншеи).xlsx')
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(source) as z:
 strings=[]
 if 'xl/sharedStrings.xml' in z.namelist():
  strings=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
 wb=E.fromstring(z.read('xl/workbook.xml'))
 rel={r.attrib['Id']:r.attrib['Target'] for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
 sheets=[]
 for s in wb.find('s:sheets',ns):
  target=rel[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
  path=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  root=E.fromstring(z.read(path));cells=[]
  for c in root.findall('.//s:sheetData/s:row/s:c',ns):
   v=c.find('s:v',ns); f=c.find('s:f',ns); value=v.text if v is not None else None
   if c.attrib.get('t')=='s' and value is not None:value=strings[int(value)]
   if c.attrib.get('t')=='inlineStr':value=''.join(c.find('s:is',ns).itertext())
   if value is not None or f is not None:cells.append({'cell':c.attrib['r'],'value':value,**({'formula':f.text} if f is not None else {})})
  sheets.append({'sheet':s.attrib['name'],'cells':cells,'merges':[m.attrib['ref'] for m in root.findall('.//s:mergeCell',ns)]})
 result={'source':source.name,'sheets':sheets}
 Path('source-inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 for s in sheets:
  print(s['sheet'],len(s['cells']))
  for c in s['cells']:print(c['cell'],str(c['value']),('= '+str(c['formula'])) if 'formula' in c else '')
