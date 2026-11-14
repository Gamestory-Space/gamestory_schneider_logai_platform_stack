"""Verify the image's migration resources against the pinned upstream checkout.
Usage: python3 verify-migrations.py UPSTREAM_CHECKOUT MODEL_JPA_JAR
Writes provenance and per-table source-operation mappings beside this script.
"""
import pathlib,zipfile,hashlib,json,xml.etree.ElementTree as E,collections,sys,subprocess
out=pathlib.Path(__file__).resolve().parent
src=pathlib.Path(sys.argv[1])/'model/jpa/src/main/resources'
jar=pathlib.Path(sys.argv[2])
revision=subprocess.check_output(['git','-C',sys.argv[1],'rev-parse','HEAD'],text=True).strip()
assert revision=='9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7', revision
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=[]
with zipfile.ZipFile(jar) as z:
 for name in sorted(z.namelist()):
  if not (name.startswith('META-INF/jpa-changelog') and name.endswith('.xml')):continue
  raw=z.read(name);local=(src/name).read_bytes()
  assert raw==local,name
  manifest.append({'resource':name,'sha256':sha(raw),'upstream_matches_image':True})
# Follow included changelogs, not every historical XML in the source directory.
reachable=[]
def visit(name):
 if name in reachable:return
 reachable.append(name)
 for e in E.parse(src/name).getroot():
  if e.tag.endswith('}include'):visit(e.attrib['file'])
visit('META-INF/jpa-changelog-master.xml')
tables=json.loads((out/'catalogue.json').read_text())['tables']
refs=collections.defaultdict(list)
for name in reachable:
 for cs in E.parse(src/name).getroot():
  if not cs.tag.endswith('}changeSet'):continue
  for el in cs.iter():
   for attr in ('tableName','baseTableName','referencedTableName','oldTableName','newTableName'):
    table=el.get(attr,'').lower()
    if table:
     r={'file':'model/jpa/src/main/resources/'+name,'change_set':cs.get('id'),'operation':el.tag.split('}')[-1]}
     if r not in refs[table]:refs[table].append(r)
result={t['name']:refs[t['name']] for t in tables}
missing=[t for t,r in result.items() if not r]
print('Tables without XML operation:',missing)
for name in missing:
 assert name in ('databasechangelog','databasechangeloglock'), name
 result[name]=[{'library':'Liquibase','evidence':'reference-schema.sql and catalogue.json','operation':'migration bookkeeping table'}]
(out/'table-sources.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'source-provenance.json').write_text(json.dumps({
 'deployment_repository':'Gamestory-Space/gamestory_schneider_logai_platform_stack',
 'deployment_revision':'9f5f9123364b4914d1fb05dc8ce4846f0e33713a',
 'keycloak_version':'26.0.8',
 'configured_image':'quay.io/keycloak/keycloak:26.0.8@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858',
 'image_config_id':'e447933b6a5015646c24a1b927a40202ce07adbadac839e7a1f99c463d68a224',
 'architecture':'amd64',
 'upstream_repository':'https://github.com/keycloak/keycloak',
 'upstream_tag':'26.0.8','upstream_revision':'9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7',
 'liquibase_version':'4.29.1',
 'model_jpa_jar':'/opt/keycloak/lib/lib/main/org.keycloak.keycloak-model-jpa-26.0.8.jar',
 'jar_sha256':sha(jar.read_bytes()),
 'schema_evidence':'Exact-image fresh-install reference on isolated PostgreSQL 16.15; NOT a deployed-database catalogue',
 'reachable_changelogs':reachable,
 'image_migration_resources':manifest
},indent=2)+'\n')
print('Verified',len(manifest),'image changelogs byte-identical to upstream; reachable:',len(reachable))
