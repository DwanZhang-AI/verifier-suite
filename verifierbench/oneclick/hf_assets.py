#!/usr/bin/env python3
"""Pinned Hugging Face assets; dependency-free so bootstrap can run before pip.

Only public Hugging Face downloads are supported. Authentication may be supplied
through HF_TOKEN, never through config or receipts. No mutable revisions/default
native environment repo are accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile


class AssetError(ValueError):
    pass


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise AssetError('Expected a nonempty POSIX relative path')
    p = PurePosixPath(value)
    if p.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise AssetError('Unsafe asset path: ' + value)
    return p


def _revision(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{40}', value) is None:
        raise AssetError('A full immutable 40-character Hugging Face commit is required')
    return value


def _digest(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise AssetError('A SHA256 is required')
    return value


def _url(repo_id, revision, name, repo_type):
    if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo_id or '') is None:
        raise AssetError('Expected a Hugging Face owner/repository ID')
    prefix = {'dataset': 'datasets/', 'model': '', 'space': 'spaces/'}.get(repo_type)
    if prefix is None:
        raise AssetError('repo_type must be dataset, model or space')
    _revision(revision)
    _relative(name)
    return 'https://huggingface.co/' + prefix + repo_id + '/resolve/' + revision + '/' + urllib.parse.quote(name, safe='/')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _validate_file(path, spec):
    p = Path(path)
    size = spec.get('size', spec.get('bytes'))
    if not isinstance(size, int) or size < 0:
        raise AssetError('Exact nonnegative asset size is required')
    if p.is_symlink() or not p.is_file() or p.stat().st_size != size:
        raise AssetError('Asset type/size mismatch: ' + str(p))
    digest = sha256(p)
    expected = spec.get('sha256')
    git_digest = spec.get('git_blob_sha1')
    if expected:
        if digest != _digest(expected):
            raise AssetError('Asset SHA256 mismatch: ' + str(p))
    elif git_digest and re.fullmatch(r'[0-9a-f]{40}', git_digest):
        h = hashlib.sha1(b'blob ' + str(size).encode() + b'\0')
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        if h.hexdigest() != git_digest:
            raise AssetError('Asset Git blob mismatch: ' + str(p))
    else:
        raise AssetError('Every file needs SHA256 or Git blob identity')
    return {'path': spec['path'], 'bytes': size, 'sha256': digest}


def _download(url, path, maximum_bytes):
    headers = {'User-Agent': 'verifierbench-oneclick/1'}
    token = os.environ.get('HF_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    # urllib removes Authorization when following a redirect to another host
    # only through this explicit handler, avoiding credential forwarding to CDNs.
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            result = super().redirect_request(req, fp, code, msg, hdrs, newurl)
            if result is not None and urllib.parse.urlsplit(req.full_url).netloc != urllib.parse.urlsplit(newurl).netloc:
                result.remove_header('Authorization')
            return result
    opener = urllib.request.build_opener(Redirect())
    with opener.open(urllib.request.Request(url, headers=headers), timeout=120) as response, Path(path).open('xb') as f:
        total = 0
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            total += len(block)
            if total > maximum_bytes:
                raise AssetError('Download exceeded pinned size')
            f.write(block)
        f.flush()
        os.fsync(f.fileno())


def download_snapshot(repo_id, revision, destination, files, repo_type='dataset'):
    """Download exactly locked files. Existing output is accepted only if exact."""
    _revision(revision)
    specs = list(files)
    names = [str(_relative(x['path'])) for x in specs]
    if len(names) != len(set(names)) or not names:
        raise AssetError('Empty or duplicated asset manifest')
    dest = Path(destination)
    if dest.exists():
        if dest.is_symlink() or not dest.is_dir():
            raise AssetError('Destination must be a real directory')
        actual = {str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() or p.is_symlink()}
        if actual != set(names):
            raise AssetError('Existing snapshot has missing or additional files')
        records = [_validate_file(dest / x['path'], x) for x in specs]
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='.' + dest.name + '.', dir=dest.parent))
        try:
            records = []
            for spec in specs:
                p = stage / spec['path']
                p.parent.mkdir(parents=True, exist_ok=True)
                size = spec.get('size', spec.get('bytes'))
                if not isinstance(size, int) or size < 0:
                    raise AssetError('Exact asset size is required')
                _download(_url(repo_id, revision, spec['path'], repo_type), p, size)
                records.append(_validate_file(p, spec))
            if dest.exists():
                raise FileExistsError(dest)
            stage.rename(dest)
        finally:
            if stage.exists():
                shutil.rmtree(stage)
    return {'repo_id': repo_id, 'repo_type': repo_type, 'revision': revision,
            'destination': str(dest.resolve()), 'files': records, 'verified': True}


def extract_archive(archive, destination, *, max_bytes, max_entries):
    """Extract into a new directory. No links/devices; pinned archive stays intact."""
    dest = Path(destination)
    if dest.exists():
        raise FileExistsError(dest)
    if not isinstance(max_bytes, int) or max_bytes <= 0 or not isinstance(max_entries, int) or max_entries <= 0:
        raise AssetError('Positive extraction bounds are required')
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.' + dest.name + '.', dir=dest.parent))
    total = 0
    names = set()
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as z:
                entries = z.infolist()
                if len(entries) > max_entries:
                    raise AssetError('Archive entry bound exceeded')
                for entry in entries:
                    name = entry.filename.rstrip('/')
                    p = stage / str(_relative(name))
                    if name in names:
                        raise AssetError('Duplicate archive entry')
                    names.add(name)
                    mode = entry.external_attr >> 16
                    if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode))):
                        raise AssetError('Archive links or special files are not supported')
                    if entry.is_dir():
                        p.mkdir(parents=True, exist_ok=True)
                        continue
                    total += entry.file_size
                    if total > max_bytes:
                        raise AssetError('Archive byte bound exceeded')
                    p.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(entry) as src, p.open('xb') as out:
                        shutil.copyfileobj(src, out)
                    p.chmod(0o755 if mode & 0o111 else 0o644)
        else:
            with tarfile.open(archive, 'r:*') as t:
                for count, entry in enumerate(t, 1):
                    if count > max_entries:
                        raise AssetError('Archive entry bound exceeded')
                    name = entry.name.rstrip('/')
                    p = stage / str(_relative(name))
                    if name in names:
                        raise AssetError('Duplicate archive entry')
                    names.add(name)
                    if entry.isdir():
                        p.mkdir(parents=True, exist_ok=True)
                        continue
                    if not entry.isfile():
                        raise AssetError('Archive links or special files are not supported')
                    total += entry.size
                    if total > max_bytes:
                        raise AssetError('Archive byte bound exceeded')
                    p.parent.mkdir(parents=True, exist_ok=True)
                    with t.extractfile(entry) as src, p.open('xb') as out:
                        shutil.copyfileobj(src, out)
                    p.chmod(0o755 if entry.mode & 0o111 else 0o644)
        if dest.exists():
            raise FileExistsError(dest)
        stage.rename(dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {'destination': str(dest.resolve()), 'entries': len(names), 'bytes': total}


def download_environment(config, destination):
    """Download an explicitly supplied HF environment archive. No guessed repo.

    Config keys: repo_id, repo_type, revision, path, sha256, bytes,
    max_extracted_bytes, max_entries. Archive must contain regular files/directories;
    environments should store symlink-bearing binary assets as nested archives and
    reconstruct their links in the environment's own verified installation step.
    """
    if not isinstance(config, dict):
        raise AssetError('Explicit pinned HF environment configuration is required')
    required = ('repo_id', 'repo_type', 'revision', 'path', 'sha256', 'bytes', 'max_extracted_bytes', 'max_entries')
    if any(k not in config for k in required):
        raise AssetError('Missing HF environment fields: ' + ', '.join(k for k in required if k not in config))
    _digest(config['sha256'])
    dest = Path(destination)
    if dest.exists():
        raise FileExistsError(dest)
    spec = {'path': config['path'], 'size': config['bytes'], 'sha256': config['sha256']}
    cache = dest.parent / ('.hf-environment-' + config['sha256'])
    receipt = download_snapshot(config['repo_id'], config['revision'], cache, [spec], config['repo_type'])
    extraction = extract_archive(cache / spec['path'], dest,
                                 max_bytes=config['max_extracted_bytes'], max_entries=config['max_entries'])
    return {'download': receipt, 'extraction': extraction, 'verified': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--environment', action='store_true')
    args = parser.parse_args()
    lock = json.loads(args.lock.read_text())
    result = (download_environment(lock, args.destination) if args.environment else
              download_snapshot(lock['repo_id'], lock['revision'], args.destination, lock['files'], lock.get('repo_type', 'dataset')))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
