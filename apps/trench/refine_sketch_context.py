from pathlib import Path
f=Path('dist/network-app.js');s=f.read_text(encoding='utf-8').replace("field('Ширина по поверхности',sp+'.topWidth',s.topWidth,{unit:'м',hint:'Углы обеих стенок рассчитываются автоматически.'})", "field('Ширина поверху в начале зоны',sp+'.topWidth',s.topWidth,{unit:'м',hint:'Задаётся в начале зоны. Дальше ширина меняется с глубиной; углы стенок одинаковые.'})")
s=s.replace('Сечение на ${fmt(state.ratio*res.length)} м от начала. Глубина зависит','Глубина зависит');f.write_text(s,encoding='utf-8')
f=Path('dist/parameter-sketches.js');s=f.read_text(encoding='utf-8');a=s.index('export function trenchParametersSketch');section=s[a:]
line=" if(s.method!=='trench')return '<svg viewBox=\"0 0 340 200\"><text x=\"30\" y=\"100\" fill=\"#60798c\">Труба на опорах — траншеи нет.</text></svg>';"
section=section.replace(line,'');section=section.replace('export function trenchParametersSketch(e,s,c){','export function trenchParametersSketch(e,s,c){\n'+line)
section=section.replace('return `<svg viewBox="0 0 340 200" aria-label="Поперечное', 'return `<div class="sketch-caption">Сечение на ${number(c.s)} м от начала</div><svg viewBox="0 0 340 200" aria-label="Поперечное')
s=s[:a]+section;f.write_text(s,encoding='utf-8')
