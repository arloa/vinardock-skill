#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# install provisions only what cannot live in the repo; .tools/ is gitignored
TOOLS = ROOT / '.tools'
PARAM_FILES = ('param.dat', 'param.TxT.dat', 'dun2010bbdep.bin')


def candidate(path, name):
    """Smoke-test a binary: must exist, be executable, and actually launch."""
    if not path or not path.is_file() or not os.access(path, os.X_OK):
        return None
    path = path.resolve()
    flags = ['-V'] if name == 'obabel-vinardock' else ['--help']
    result = subprocess.run([str(path), *flags], capture_output=True, text=True, timeout=20)
    if name == 'obabel-vinardock' and (result.returncode != 0 or not result.stdout.startswith('Open Babel')):
        raise RuntimeError(f'{path} cannot run: {result.stderr.strip()[:300]}')
    if name == 'vinardock' and not result.stdout.startswith('2Vinardo molecular docking program'):
        raise RuntimeError(f'{path} cannot run: {result.stderr.strip()[:300]}')
    version = (result.stdout + result.stderr).splitlines()
    return {'path': str(path), 'version_line': version[0] if version else ''}


def probe():
    result = {}
    unusable = {}
    for name in ('vinardock', 'obabel-vinardock'):
        paths = [ROOT / 'bin' / name, Path.cwd() / name,
                 Path(shutil.which(name)) if shutil.which(name) else None,
                 TOOLS / 'bin' / name]
        seen = set()
        found = []
        for path in paths:
            if path and path.is_file() and path.resolve() not in seen:
                seen.add(path.resolve())
                try:
                    item = candidate(path, name)
                    if item:
                        found.append(item)
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    unusable.setdefault(name, []).append(
                        {'path': str(path.resolve()), 'error': str(error)})
        result[name] = found
    result['unusable'] = unusable
    result['param'] = [str(directory.resolve())
                       for directory in (ROOT / 'param', Path.cwd() / 'param', TOOLS / 'param')
                       if directory.is_dir() and all((directory / name).is_file() for name in PARAM_FILES)]
    result['plip'] = (TOOLS / 'plip-venv/bin/plip').is_file()
    local = TOOLS / 'bin/vinardock-pipeline'
    found = shutil.which('vinardock-pipeline')
    result['launcher'] = str(Path(found).resolve()) if found else (
        str(local) if local.is_file() else None)
    return result


def make_launcher():
    """Write the wrapper into <tools>/bin — install never touches a PATH dir."""
    script = (ROOT / 'scripts/pipeline.py').resolve()
    target = TOOLS / 'bin' / 'vinardock-pipeline'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n')
    target.chmod(0o755)
    result = {'path': str(target)}
    found = shutil.which('vinardock-pipeline')
    if found and Path(found) != target:
        result['warning'] = f'{found} is earlier on PATH and will shadow this'
    else:
        result['note'] = f'add {target.parent} to PATH to use it'
    return result


def install(args):
    TOOLS.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in ('vinardock', 'obabel-vinardock'):
        source = ROOT / 'bin' / name
        item = candidate(source, name)
        if not item:
            raise ValueError('bundled binary missing or not executable: ' + str(source))
        item['source'] = 'bundled ' + str(source)
        summary[name] = item
    summary['param'] = {}
    for name in PARAM_FILES:
        source = ROOT / 'param' / name
        if not source.is_file():
            raise FileNotFoundError(source)
        summary['param'][name] = {'path': str(source),
                                  'source': 'bundled ' + str(ROOT / 'param')}
    plip = TOOLS / 'plip-venv/bin/plip'
    if args.replace and (TOOLS / 'plip-venv').exists():
        shutil.rmtree(TOOLS / 'plip-venv')
    if not args.skip_plip and not plip.is_file():
        uv = shutil.which('uv')
        if not uv:
            raise RuntimeError('uv is required to provision PLIP')
        # the download cache stays in the repo too
        env = dict(os.environ, UV_CACHE_DIR=str(TOOLS / 'cache/uv'))
        subprocess.run([uv, 'venv', '--python', sys.executable, str(TOOLS / 'plip-venv')],
                       check=True, env=env)
        subprocess.run([uv, 'pip', 'install', '--python', str(TOOLS / 'plip-venv/bin/python'),
                        'plip==3.0.1', 'openbabel==3.2.1', 'numpy==2.2.6', 'lxml==6.1.3'],
                       check=True, env=env)
    if plip.is_file():
        py = TOOLS / 'plip-venv/bin/python'
        info = subprocess.check_output([str(py), '-c',
            "import importlib.metadata as m; print(m.version('plip'), m.version('openbabel'))"], text=True).strip().split()
        summary['plip'] = {'path': str(plip),
                           'version': info[0], 'openbabel_bindings': info[1]}
    # regenerate the checked-in help references from the binaries in use
    refs = ROOT / 'references'
    for name, command in [('vinardock-help.txt', [str(ROOT / 'bin/vinardock'), '--help']),
                          ('obabel-vinardock-help.txt', [str(ROOT / 'bin/obabel-vinardock'), '-H'])]:
        output = subprocess.run(command, capture_output=True, text=True)
        text = output.stdout + output.stderr
        if name == 'vinardock-help.txt':
            text = re.sub(r'(--seed arg[^\n]*?\(default: )\d+(\))', r'\g<1><timestamp>\2', text)
        (refs / name).write_text(text)
    if args.launcher:
        summary['launcher'] = make_launcher()
    elif sys.stdin.isatty():
        local = TOOLS / 'bin/vinardock-pipeline'
        if input(f'install the vinardock-pipeline wrapper in {local.parent}? [y/N] ').strip().lower() == 'y':
            summary['launcher'] = make_launcher()
    (TOOLS / 'install.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('probe')
    install_parser = sub.add_parser('install')
    install_parser.add_argument('--skip-plip', action='store_true')
    install_parser.add_argument('--launcher', action='store_true',
                                help='write the vinardock-pipeline wrapper into <tools>/bin')
    install_parser.add_argument('--replace', action='store_true',
                                help='rebuild the PLIP venv')
    args = parser.parse_args()
    print(json.dumps(probe() if args.action == 'probe' else install(args), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
