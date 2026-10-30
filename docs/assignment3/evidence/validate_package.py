from pathlib import Path
import re,json,hashlib
root=Path.cwd(); base=root/'docs/assignment3'; ev=base/'evidence'
manifest={}
for folder in ['config','apps/authentication','apps/core','ml','scripts','apps/authentication/migrations','apps/core/legacy/predictions/migrations','apps/core/legacy/wellness/migrations','templates','static']:
 for p in (root/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.py','.html','.css'] and '__pycache__' not in str(p):
   manifest[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['requirements/base.txt','README.md','AHM_Assignment_2_Submission.docx','output/docx/AHM_Assignment_2_Submission.docx','tmp_pdf_text/Accurate_Health_Matrix_Project_Document(1).txt','tmp_pdf_text/ISJ107V Assignment 2 ver(1).txt','docs/PROJECT_RESTRUCTURING_REPORT.md']:
 p=root/name
 if p.exists(): manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
(ev/'source_manifest.json').write_text(json.dumps({'prepared':'2026-09-30','algorithm':'SHA-256','files':manifest},indent=2),encoding='utf-8')
text=(base/'ISJ107V_Assignment_3.md').read_text(encoding='utf-8-sig')
expected=[f'{q}.{i}' for q,n in [(1,3),(2,3),(3,6),(4,4),(5,4)] for i in range(1,n+1)]
actual=re.findall(r'^### (\d\.\d)\b',text,re.M)
links=[]
from urllib.parse import unquote
for md in base.rglob('*.md'):
 for target in re.findall(r'\]\(([^()]*(?:\([^()]*\)[^()]*)*)\)',md.read_text(encoding='utf-8-sig')):
  if not target.startswith(('http:','https:','#')):
   links.append({'from':str(md.relative_to(base)), 'target':target,'exists':(md.parent/unquote(target.split('#')[0])).exists()})
reqs=[f'FR{i:02}' for i in range(1,12)]+[f'NFR{i:02}' for i in range(1,8)]+[f'ET{i:02}' for i in range(1,8)]+[f'D{i:02}' for i in range(1,4)]
tests=[f'T{i:02}' for i in range(1,11)]+[f'M{i:02}' for i in range(1,5)]+[f'P{i:02}' for i in range(1,6)]
parts=text.split('### 2.2')[1].split('### 2.3')[0]
result={'prepared':'2026-09-30','subsections_expected':expected,'subsections_found':actual,'subsections_match':actual==expected,'links':links,'all_local_links_exist':all(x['exists'] for x in links),'traceability_all_requirement_rows':all('| '+r+' |' in parts for r in reqs),'test_ids_present':all('| '+t+' |' in text for t in tests),'diagram_sources':{},'rendering':'Not tested; renderer unavailable','screenshots':'Evidence not available; browser connection timeout'}
for p in (base/'diagrams').glob('*.puml'):
 s=p.read_text(encoding='utf-8')
 result['diagram_sources'][p.name]={'start_end':s.startswith('@startuml') and s.rstrip().endswith('@enduml'),'no_multiline_quoted_labels':not any('\n' in x for x in re.findall(r'"[^"]*"',s))}
(ev/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='links'},indent=2))
print('Broken links:',[x for x in links if not x['exists']])
print('Manifest files:',len(manifest))
print('Report words:',len(text.split()))
