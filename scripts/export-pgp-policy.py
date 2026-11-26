#!/usr/bin/env python3
"""Project the PGP companion from an exact backend revision, never a floating SDK."""
import argparse, hashlib, json, subprocess, importlib.util, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SELECTION = {'/pgp': ['get', 'put'], '/pgp/keys': ['delete'],
 '/pgp/policy/banks/{Bank}': ['put', 'delete'], '/pgp/policy/lock': ['post'],
 '/session/action-mfa': ['post'], '/integrator/accounts': ['get']}
def clean(value):
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if not k.startswith('x-amazon-') and k not in ('example','x-code-samples','x-codeSamples')}
 if isinstance(value,list):return [clean(v) for v in value]
 if isinstance(value,str):
  for old,new in [('Candidate-only Admin operation.','Admin operation.'),('Not available until Rust registration deployment is qualified.',''),('Not available until Rust registration, audit-reader and candidate routing are qualified.',''),('Candidate Rust API policy metadata.','PGP authorization policy metadata.')]:value=value.replace(old,new)
 return value
def project(source,guide,samples):
 paths={p:{m:clean(source['paths'][p][m]) for m in methods} for p,methods in SELECTION.items()}
 definitions={}
 def refs(value):
  if isinstance(value,dict):
   if '$ref' in value:
    assert value['$ref'].startswith('#/definitions/')
    name=value['$ref'].split('/')[-1]
    if name not in definitions:
     definitions[name]=clean(source['definitions'][name]);refs(definitions[name])
   for v in value.values():refs(v)
  elif isinstance(value,list):
   for v in value:refs(v)
 refs(paths)
 for methods in paths.values():
  for op in methods.values():
   op['security']=[{'X-Api-Key':[],'Authorizer':[]}]
   op['description']='Available on production V2 and Test; production rollout verified 25 November 2026.\n\n'+op['description']
   op['x-code-samples']=[{'lang':'TypeScript','label':'Official TypeScript SDK 6.1.0','source':samples[op['operationId']]}]
 return {'swagger':'2.0','info':{'title':'ISECure PGP authorization API','version':'1.1.0','description':guide,'contact':{'email':'support@isecure.fi'}},'host':'ws-api.isecure.fi','basePath':'/v2','schemes':['https'],'consumes':['application/json'],'produces':['application/json'],'securityDefinitions':clean(source['securityDefinitions']),'tags':[{'name':'Pgp','description':'Registered keys, per-bank thresholds, required signers and irreversible locking.'},{'name':'Session','description':'Fresh action MFA for an established Admin factor.'},{'name':'Integrator','description':'Read account policy state before editing.'}],'paths':paths,'definitions':definitions,'externalDocs':{'description':'Official TypeScript SDK 6.1.0','url':'https://github.com/isecurefi/isecure-ts-client'}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--repository',required=True);p.add_argument('--revision',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 revision=subprocess.check_output(['git','rev-parse',a.revision+'^{commit}'],cwd=a.repository,text=True).strip()
 inputs={name:subprocess.check_output(['git','show',revision+':ws-channel-api/'+name],cwd=a.repository) for name in ['config.json','__wsapi.json.tmpl','render.py']}
 with tempfile.TemporaryDirectory() as tmp:
  folder=Path(tmp)
  for name,data in inputs.items():(folder/name).write_bytes(data)
  spec=importlib.util.spec_from_file_location('render_pinned',folder/'render.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  raw=module.render_api(folder/'config.json',folder/'__wsapi.json.tmpl',{'__API_STAGE__':'rc','__AWS_ACCOUNT__':'507820410808','__API_ID__':'gky0hkiw7k','__USER_POOL_ID__':'eu-west-1_iTHy7kDHx','__API_HOST__':'ws-api.isecure.fi','__API_BASE_PATH__':'rc'},pgp_policy=True).encode()
 doc=project(json.loads(raw),(ROOT/'pgp-policy-guide.md').read_text(),json.loads((ROOT/'pgp-policy-samples.json').read_text()))
 data=json.dumps(doc,indent=2,ensure_ascii=False)+'\n'
 metadata={'repository':'https://github.com/isecurefi/aws','revision':revision,'sourceFiles':{'ws-channel-api/'+k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()},'renderedSha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data.encode()).hexdigest(),'sdkVersion':'6.1.0','availability':{'gpgtest':'https://ws-api.test.isecure.fi/v2','productionRc':'https://ws-api.isecure.fi/rc','productionV2PolicyAdministration':True,'productionV2':'https://ws-api.isecure.fi/v2','verifiedAt':'2026-11-26','deploymentId':'i7hvpf'}}
 main=json.loads((ROOT/'wsapi_v2.json').read_text())
 for path,methods in doc['paths'].items():
  for method,operation in methods.items():
   if operation['operationId'] in ('ConfigureBankPgpPolicy','BlockBankPgpPolicy','DeletePgpKey','LockPgpPolicy'):main['paths'].setdefault(path,{})[method]=operation
 for name,definition in doc['definitions'].items():
  if name not in main['definitions']:main['definitions'][name]=definition
 main['definitions']['AccountDescriptor']['properties']['PgpAuthorization']=doc['definitions']['AccountDescriptor']['properties']['PgpAuthorization']
 main['definitions']['UploadKeyReq']['properties']['ExpectedRevision']['description']='Reviewed PGP authorization policy revision. Omit or use zero only when no policy exists. Read the current revision before changing keys.'
 main['info']['version']='v2.20.0'
 for name,text in [('wsapi_v2.json',json.dumps(main,indent=2,ensure_ascii=False)+'\n'),('pgp-policy-api.json',data),('pgp-policy-api.source.json',json.dumps(metadata,indent=2)+'\n')]:
  file=ROOT/name
  if a.check:assert file.read_text()==text,'Contract drift: '+name
  else:file.write_text(text)
 print('Verified PGP companion' if a.check else 'Generated PGP companion')
if __name__=='__main__':main()
