from pathlib import Path
p=Path('tests_backend.py');s=p.read_text(encoding='utf-8');a=s.index(' def test_persistent_catalogue')
s=s[:a]+''' def test_v4_node_fields_roundtrip_and_physical_counts(self):
  model=copy.deepcopy(MODEL);model['version']=4
  model['wells'][0].update(kind='endpoint',rotation=32,zeroAngle=10,rotationMode='manual',heightMode='total',height=3.7)
  project=self.project();r=self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':model,'name':'Узлы'})
  self.assertEqual(r.status_code,201,r.json);item=r.json
  self.assertEqual(item['well_count'],len(model['wells'])-1);self.assertEqual(item['endpoint_count'],1)
  self.assertEqual(self.client.get('/api/schemes/'+item['id']).json['model']['wells'][0]['height'],3.7)
 def test_reject_invalid_optional_node_fields(self):
  project=self.project()
  for key,value in [('height','3'),('rotationMode','other'),('kind','other'),('rotationEdge',42)]:
   model=copy.deepcopy(MODEL);model['version']=4;model['wells'][0][key]=value
   self.assertEqual(self.client.post('/api/projects/'+project['id']+'/schemes',json={'model':model,'name':'Ошибка'}).status_code,400)
''' +s[a:];p.write_text(s,encoding='utf-8')
p=Path('dist/network-model.js');s=p.read_text(encoding='utf-8').replace("id(w.id);if(!['well'", "id(w.id);if(w.rotationEdge!==undefined&&(typeof w.rotationEdge!=='string'||w.rotationEdge.length>150))throw Error('Некорректная опорная труба.');if(!['well'");p.write_text(s,encoding='utf-8')
for f in ['README.md','NETWORK.md','DEPLOY.md']:
 p=Path(f);s=p.read_text(encoding='utf-8');s=s.replace('kdfp-trench-network-v4.5.0','kdfp-trench-network-v5.0.0');s=s.replace('Установка и обновление 4.5.0','Установка и обновление 5.0.0');p.write_text(s,encoding='utf-8')
p=Path('NETWORK.md');p.write_text(p.read_text(encoding='utf-8')+'''

## Версия 5.0.0 · свободные трубы и ориентация

Инструмент «Труба»: два щелчка по колодцам или свободным точкам плана. Свободный конец не создаёт котлован. Отметки и координаты редактируются в карточке точки, грунты — у трубы.

«Длина трубы» — длина по оси с учётом уклона. Enter или уход из поля применяет значение: начало и высотные отметки остаются, конец перемещается, промежуточные вершины масштабируются в плане. Связанные с конечным узлом трубы также изменяются. Геометрия, направление и границы зон доступны отдельно; длины в ведомости остаются длинами в плане.

У колодца блок «Поворот на плане»: ручной угол или ориентация по выбранной связанной трубе с поправкой. Для прямоугольной формы автоматически включается ориентация по трубе. Ось Z проходит через центр; переносить ось отдельно от центра нельзя. Синяя ручка поворачивает объект и включает ручной режим; оранжевая задаёт направление 0° без физического поворота. Контур и котлован учитывают поворот в расчёте пересечений и объёмов исключения.

Новая общая высота: поверхность → наружный низ днища. Рабочая часть 1,8 м, горловина = высота − 1,8 − перекрытие − днище. Подготовка отдельно. Отрицательная горловина блокирует итог. Старые схемы сохраняют высоты частей до явного изменения общей высоты.

JSON версии 4; читаются также модели версии 3. API 2.0.0, SQLite схема 2. Старый API 1.2.0 не понимает новые модели. Для полного отката используйте сохранённую БД до обновления, предварительно экспортировав новые изменения.
''',encoding='utf-8')
p=Path('DEPLOY.md');p.write_text(p.read_text(encoding='utf-8')+'''

## Обновление до 5.0.0

В комплекте web 5.0.0 и API 2.0.0. Обновляйте оба контейнера. Таблицы SQLite не меняются (схема 2), модели получают JSON 4 при редактировании. Сделайте резервную копию БД перед обновлением. Откат к API 1.2.0 требует прежней БД: новые модели JSON 4 им не поддерживаются. Запуск и offline-команды выше актуальны для 5.0.0.
''',encoding='utf-8')
