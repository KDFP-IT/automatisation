"""Read-only extraction of the supplied engineering workbook's inspected cells."""
import json,re
from pathlib import Path
doc=json.loads(Path('source-inspection.json').read_text(encoding='utf8'))
sheet=doc['sheets'][0]; cells={c['cell']:c for c in sheet['cells']}
def value(col,row):return cells.get(f'{col}{row}',{}).get('value','')
def number(col,row):return float(value(col,row))
def entry(row):return {'cell':f'D{row}','formula':cells.get(f'D{row}',{}).get('formula'),'original':number('D',row)}
starts=[int(c['cell'][1:]) for c in sheet['cells'] if re.fullmatch('A[0-9]+',c['cell']) and str(c['value']).startswith('Участок трассы')]
projects=[]
for idx,start in enumerate(starts):
 end=starts[idx+1] if idx+1<len(starts) else 436
 p={'id':f'excel-{start}','name':value('A',start).removeprefix('Участок трассы '),'source':{'file':doc['source'],'sheet':sheet['sheet'],'range':f'A{start}:I{end-1}'},'materials':[],'pipes':[],'structures':[],'groups':[0,0,0,0],'notes':[],'sourceWarnings':[]}
 in_pipes=False;in_structures=False
 for row in range(start+1,end):
  label=value('B',row)
  if not label:continue
  if label=='Общая выемка грунта':p['totalExcavation']=number('D',row);p['soilNote']=value('E',row);p['totalSource']=entry(row)
  elif re.match('грунты [IVX]+ группы',label):
   group=re.search('грунты ([IVX]+)',label)[1];p['groups'][['I','II','III','IV'].index(group)]=round(number('D',row)/p['totalExcavation']*100,8)
   p['notes'].append({'label':label,**entry(row)})
  elif label.startswith(('Подушка из ЩПС','Засыпка из ЩПС','Защитный слой из ЩПС','Засыпка траншеи ЩПС')):p['materials'].append({'name':label,'volume':number('D',row),**entry(row)})
  elif label=='Объем трубопроводов':in_pipes=True;in_structures=False
  elif label=='Объем колодцев':in_pipes=False;in_structures=True
  elif label=='Обратная засыпка траншеи':p['originalBackfill']=number('D',row);p['backfillSource']=entry(row);in_structures=False
  elif label=='Обратная засыпка котлованов колодцев':p['originalPitBackfill']=number('D',row);p['pitBackfillSource']=entry(row)
  elif in_pipes and label.startswith(('Труба','Футляр')):
   formula=cells[f'D{row}'].get('formula','');match=re.fullmatch(r'([\d.]+)\*([\d.]+)',formula)
   length,area=map(float,match.groups()) if match else (0,0)
   dia=re.search(r'Ду\s*=\s*([\d,]+)',label)
   titlelength=re.search(r'l\s*=\s*([\d,]+)',label)
   if titlelength and abs(float(titlelength[1].replace(',','.'))-length)>.00001:p['sourceWarnings'].append(f'B{row} и D{row}: в названии длина {titlelength[1]} м, в формуле {length:g} м. Сохранена длина из формулы.')
   p['pipes'].append({'name':label,'length':length,'area':area,'diameter':float(dia[1].replace(',','.')) if dia else 0,'method':'area','count':1,**entry(row)})
  elif in_structures and label.startswith('Выемка грунтов'):
   if p['structures']:p['structures'][-1].update({'excavation':number('D',row),'excavationSource':entry(row),'soilNote':value('E',row)})
  elif in_structures:
   p['structures'].append({'name':label,'volume':number('D',row),'excavation':0,**entry(row)})
 # Diagnose supplied main group labels against the note, without changing source.
 note_groups=[0,0,0,0]
 for roman,percent in re.findall(r'\(([IV]+) гр\.\)\s*-\s*([\d,]+)%',p.get('soilNote','')):note_groups[['I','II','III','IV'].index(roman)]+=float(percent.replace(',','.'))
 if abs(sum(note_groups)-100)<.001 and any(abs(a-b)>.001 for a,b in zip(note_groups,p['groups'])):p['sourceWarnings'].append('Группы грунтов в примечании E и строках расчёта D расходятся. В расчёт перенесены группы из строк D; исходное примечание сохранено.')
 if abs(sum(p['groups'])-100)>.001:p['sourceWarnings'].append(f"Сумма долей групп в исходных строках = {sum(p['groups']):g}%, а не 100%. Доли не нормализованы автоматически; требуется уточнение инженера.")
 pit=sum(x['excavation'] for x in p['structures']);materials=sum(x['volume'] for x in p['materials']);pipe=sum(x['length']*x['area'] for x in p['pipes'])
 back=p['totalExcavation']-pit-materials-pipe
 if abs(back-p.get('originalBackfill',back))>.001:p['sourceWarnings'].append(f"Обратная засыпка: исходная {p['backfillSource']['cell']} = {p['originalBackfill']:.5f} м³; по всем строкам котлованов = {back:.5f} м³. Расхождение {back-p['originalBackfill']:+.5f} м³; проверьте состав ссылок в исходных итогах.")
 for row in range(start,end):
  label=value('I',row)
  expected={'Выемка под траншею':p['totalExcavation']-pit,'Обратная засыпка траншеи':back,'ЩПС без Подушки':materials-p['materials'][0]['volume']}.get(label)
  if expected is not None and value('I',row+1):
   actual=number('I',row+1)
   if abs(actual-expected)>.001:p['sourceWarnings'].append(f'Боковая колонка I{row+1}: {actual:.5f} м³, по подробным строкам {expected:.5f} м³ ({label.lower()}). В системе используется сумма подробных строк, а не боковой итог.')
 projects.append(p)
Path('dist/seed.js').write_text('export const sourceInfo = '+json.dumps({'file':doc['source'],'sheet':sheet['sheet']},ensure_ascii=False)+';\nexport const seedProjects = '+json.dumps(projects,ensure_ascii=False,indent=2)+';\n',encoding='utf8')
print(f'{len(projects)} sections imported')
for p in projects:
 print(p['name'], 'pipes',len(p['pipes']),'structures',len(p['structures']),'warnings:',p['sourceWarnings'])
