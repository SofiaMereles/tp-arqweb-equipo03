"""Empaqueta solo fuentes seleccionadas; excluye entornos y secretos."""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CNA = ROOT / 'cna'
selected = [CNA / '.dockerignore', CNA / 'services/requirements.lock']
mode = sys.argv[1] if len(sys.argv) > 1 else 'audit'
if mode not in ('audit','search','bridge'):
    raise SystemExit('Usar: empaquetar-b2.py [audit|search|bridge]')
search = mode == 'search'
for folder, pattern in [('services/audit_svc', '*.py'), ('services/tests', '*.py'),
                         ('services/tools', '*.py'), ('services/audit-svc', 'Dockerfile'),
                         ('contracts', '*.yaml'), ('deploy/b2-audit', '*')]:
    selected.extend(p for p in (CNA / folder).glob(pattern) if p.is_file() and p.name != 'build.env')
if search:
    for folder,pattern in [('services/search_svc','*.py'),('services/search-svc','Dockerfile'),('deploy/b2-search','*')]:
        selected.extend(p for p in (CNA/folder).glob(pattern) if p.is_file() and p.name != 'build.env')
if mode == 'bridge':
    for folder,pattern in [('services/event_bridge','*.py'),('services/event-bridge','Dockerfile'),('deploy/b4-integration','*')]:
        selected.extend(p for p in (CNA/folder).glob(pattern) if p.is_file() and p.name != 'build.env')
selected = sorted(set(selected))
digest = hashlib.sha256()
for path in selected:
    digest.update(path.relative_to(ROOT).as_posix().encode())
    digest.update(path.read_bytes())
source_hash = digest.hexdigest()[:12]
commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
service = {'audit':'audit','search':'search','bridge':'event-bridge'}[mode]
image = f'cna-{service}-svc:1.0.0-{commit}-{source_hash}'
prefix = {'audit':'AUDIT','search':'SEARCH','bridge':'BRIDGE'}[mode]
deploy_folder = {'audit':'b2-audit','search':'b2-search','bridge':'b4-integration'}[mode]
manifest = f'BUILD_COMMIT={commit}\n{prefix}_IMAGE={image}\n'
output = ROOT / {'audit':'tmp/b2-auditoria.tar.gz','search':'tmp/b2-busqueda.tar.gz','bridge':'tmp/b4-integracion.tar.gz'}[mode]
output.parent.mkdir(exist_ok=True)
with tarfile.open(output, 'w:gz') as archive:
    for path in selected:
        archive.add(path, arcname=path.relative_to(ROOT).as_posix(), recursive=False)
    data = manifest.encode()
    info = tarfile.TarInfo(f'cna/deploy/{deploy_folder}/build.env')
    info.size, info.mode = len(data), 0o644
    archive.addfile(info, io.BytesIO(data))
print(json.dumps(dict(package=str(output), files=len(selected) + 1, image=image,
                      source_sha256_prefix=source_hash, base_commit=commit,
                      note='Incluye fuentes locales sin commit; el hash adicional identifica su contenido.'), indent=2))
