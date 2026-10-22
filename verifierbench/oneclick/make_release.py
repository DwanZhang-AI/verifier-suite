#!/usr/bin/env python3
"""Produce a source-only, SHA-bound distribution; never copy experiment output."""
from pathlib import Path
import hashlib,json,os,stat,zipfile

TOP={"README.md","NOTICE.md","run.sh","bootstrap.py","hf_assets.py","native_setup.py","environment_image.py","dataset-lock.json","toolchain-lock.json","requirements-generation.txt","validation.json","make_release.py"}
DIRS={"runtime","vendor","runner"}
FORBIDDEN={"__pycache__",".git",".env",".ssh",".aws",".netrc","credentials.json",".proxy-token"}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def selected(root):
 out=[]
 for p in sorted(root.rglob("*")):
  rel=p.relative_to(root)
  if rel.parts[0] not in DIRS and str(rel) not in TOP:continue
  if rel.parts[:2]==("runner","tests"):continue
  if set(rel.parts)&FORBIDDEN or p.suffix==".pyc":continue
  if p.is_symlink():raise ValueError("Release symlink rejected: "+str(rel))
  if not p.is_file():continue
  if rel.parts[0]=="runner" and p.suffix==".json":continue
  if rel.parts[0]=="runtime" and any(x in str(rel).lower() for x in ("main_table","round_records","score_table","artifact_exemption")):raise ValueError("Historical result file rejected: "+str(rel))
  out.append(p)
 missing=TOP-{str(p.relative_to(root)) for p in out}
 if missing:raise ValueError("Missing release files: "+str(sorted(missing)))
 return out

def build(root):
 root=Path(root).resolve();files=selected(root)
 manifest={"schema":"verifierbench-oneclick-source-v1","dataset_repo":"Catherine1213/VerifierBench","dataset_revision":"8e5d72dfc112aaffca75934a0caaa22067ba8df1","files":[{"path":str(p.relative_to(root)),"size":p.stat().st_size,"sha256":sha(p)} for p in files]}
 pin=root/"SUITE_MANIFEST.json";pin.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
 archive=root.parent/(root.name+".zip");temporary=archive.with_suffix(".zip.tmp")
 with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in [*files,pin]:
   name=root.name+"/"+str(p.relative_to(root));info=zipfile.ZipInfo(name)
   info.create_system=3;info.external_attr=(stat.S_IFREG|(0o755 if p.name=="run.sh" else 0o644))<<16
   info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,p.read_bytes())
 with zipfile.ZipFile(temporary) as z:
  assert z.testzip() is None
  for row in manifest["files"]:
   raw=z.read(root.name+"/"+row["path"])
   assert len(raw)==row["size"] and hashlib.sha256(raw).hexdigest()==row["sha256"]
 temporary.replace(archive)
 receipt={"archive":str(archive),"sha256":sha(archive),"bytes":archive.stat().st_size,"files":len(files)+1,"manifest_sha256":sha(pin),"archive_checked":True,"models_called":0}
 (root/"build/release-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print(json.dumps(receipt,indent=2))

if __name__=="__main__":build(Path(__file__).resolve().parent)
