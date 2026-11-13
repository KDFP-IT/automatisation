from pathlib import Path
p=Path('dist/network-app.js');s=p.read_text(encoding='utf-8').replace("function renderInspector(){renderInspectorContent();renderValidation()}","function renderInspector(){const title=$('inspector-title').textContent,open=new Map([...$('inspector').querySelectorAll('details.inspector-block')].map(v=>[v.querySelector('summary').textContent,v.open]));renderInspectorContent();if(title===$('inspector-title').textContent)for(const v of $('inspector').querySelectorAll('details.inspector-block')){const key=v.querySelector('summary').textContent;if(open.has(key))v.open=open.get(key)}renderValidation()}")
s=s.replace("else pathSet(path,val);if(path.endsWith('.shape')", "else if(path.endsWith('.rotationMode')&&val==='manual'){const w=well(),angle=nodeAngle(p,w);pathSet(path,val);w.rotation=normalizeAngle(angle-(w.zeroAngle||0))}else pathSet(path,val);if(path.endsWith('.shape')")
p.write_text(s,encoding='utf-8')
p=Path('README.md');s=p.read_text(encoding='utf-8').replace('земляные работы v4.5.0','земляные работы v5.0.0');p.write_text(s,encoding='utf-8')
b=Path('../output/kdfp-trench-network-v5.0.0-offline');b.mkdir(exist_ok=True)
s=Path('../output/kdfp-trench-network-v4.5.0-offline/compose.yaml').read_text(encoding='utf-8').replace('4.5.0','5.0.0').replace('trench-projects-api:1.2.0','trench-projects-api:2.0.0');(b/'compose.yaml').write_text(s,encoding='utf-8')
(b/'DEPLOY.md').write_bytes(Path('DEPLOY.md').read_bytes());(b/'.env.example').write_bytes(Path('.env.example').read_bytes())
