"""Create explicit, verified source and Linux/amd64 offline releases."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
ENTRIES = ('dist', 'tests', 'Dockerfile', 'nginx.conf', 'compose.yaml',
           '.dockerignore', '.env.example', 'deploy.sh', 'DEPLOY.md', 'README.md',
           'package.json', 'start.cmd', 'package_release.py', 'vendor-hash.mjs',
           'build_names.py')
FORBIDDEN = {'.pdf', '.sig', '.sgn', '.p7s', '.pfx', '.p12', '.key', '.pem'}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def manifest(folder):
    files = sorted(p for p in folder.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (folder / 'SHA256SUMS').write_bytes(''.join(f'{digest(p)}  {p.relative_to(folder).as_posix()}\n' for p in files).encode('utf-8'))

def verify_archive(path):
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'Bad ZIP entry: {bad}')
        names = set(archive.namelist())
        base = 'kdfp-signature-checker/'
        for name in names:
            parts = PurePosixPath(name)
            if not name.startswith(base) or parts.is_absolute() or '..' in parts.parts:
                raise ValueError(f'Unsafe ZIP path: {name}')
            if parts.suffix.lower() in FORBIDDEN or parts.name == '.env':
                raise ValueError(f'Unexpected private file: {name}')
        for line in archive.read(base + 'SHA256SUMS').decode('utf-8').splitlines():
            expected, filename = line.split('  ', 1)
            actual = hashlib.sha256(archive.read(base + filename)).hexdigest()
            if expected != actual:
                raise ValueError(f'Checksum mismatch: {filename}')
        assert base + 'dist/vendor/pdf.worker.mjs' in names
        assert base + 'dist/vendor/hash.mjs' in names
        assert base + 'dist/vendor/HASH-LICENSES.txt' in names
        return len(names)

def write_archive(folder, output):
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(folder.rglob('*')):
            if not file.is_file():
                continue
            name = 'kdfp-signature-checker/' + file.relative_to(folder).as_posix()
            compression = zipfile.ZIP_STORED if file.name.endswith('.tar.gz') else zipfile.ZIP_DEFLATED
            archive.write(file, name, compress_type=compression)
    count = verify_archive(output)
    output.with_name(output.name + '.sha256').write_bytes(f'{digest(output)}  {output.name}\n'.encode('ascii'))
    return {'path': str(output), 'bytes': output.stat().st_size, 'files': count, 'sha256': digest(output)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT.parent / 'output' / 'signature-checker')
    parser.add_argument('--image-tar', type=Path)
    parser.add_argument('--image-id', default='')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))['version']
    with tempfile.TemporaryDirectory(prefix='signature-release-', dir=output) as temporary:
        stage = Path(temporary).resolve()
        if not stage.is_relative_to(output):
            raise ValueError('Staging directory escaped output root')
        folder = stage / 'kdfp-signature-checker'
        folder.mkdir()
        for entry in ENTRIES:
            source = ROOT / entry
            files = sorted(source.rglob('*')) if source.is_dir() else [source]
            for file in files:
                if not file.is_file():
                    continue
                if not file.resolve().is_relative_to(ROOT) or file.suffix.lower() in FORBIDDEN or file.name == '.env':
                    raise ValueError(f'Unexpected input: {file}')
                target = folder / file.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, target)
        release = {'name': 'kdfp-signature-checker', 'version': version,
                   'created_at_utc': datetime.now(timezone.utc).isoformat(),
                   'platform': 'linux/amd64', 'image': f'kdfp/signature-checker:{version}',
                   'base_image': 'nginx:stable-alpine@sha256:0e52bd054126cdc040b1276c0af347aeb02a41b9cfe305d6094767ac30e97949',
                   'documents_included': False}
        (folder / 'RELEASE.json').write_text(json.dumps(release, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest(folder)
        results = [write_archive(folder, output / 'kdfp-signature-checker-deploy.zip')]
        if args.image_tar:
            if not args.image_tar.is_file():
                raise ValueError('Exported Docker image not found')
            image = folder / 'signature-checker-image.tar.gz'
            with args.image_tar.open('rb') as source, image.open('wb') as target:
                with gzip.GzipFile(filename='', mode='wb', compresslevel=6, fileobj=target, mtime=0) as compressed:
                    shutil.copyfileobj(source, compressed, 1024 * 1024)
            (folder / 'IMAGE-ID.txt').write_text(args.image_id + '\n', encoding='ascii')
            manifest(folder)
            results.append(write_archive(folder, output / 'kdfp-signature-checker-linux-amd64.zip'))
        (output / 'release-verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
