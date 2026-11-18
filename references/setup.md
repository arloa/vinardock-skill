# Tool bootstrap: probe → ask → install

Follow this when vinardock-skill.md step 1 routes here. Resolve `<skill_dir>` from the
location of the invoked vinardock-skill.md; do not change the caller's working directory,
as `probe` deliberately inspects that directory.

Everything install writes stays inside the repo: `<skill_dir>/.tools/`
(gitignored) holds the PLIP venv, the uv cache and `install.json`. Binaries
and parameters are used in place from `bin/` and `param/` — nothing is
copied and nothing is written outside the repo.

## 1. Probe

```bash
python3 "<skill_dir>/scripts/setup.py" probe
```

Prints JSON per tool: `{path, version_line}` for launchable binaries;
binaries that exist but cannot launch are listed under `unusable` with
the error — "not found" for a present tool usually means an unusable
build. `plip` is a boolean (the venv binary exists), `param` a list of
directories holding every parameter file, `launcher` a path or `null`.
Search scope is deliberately narrow — **the repo's `bin/`, the literal
pwd, PATH, and `<repo>/.tools` only**:

- `vinardock`, `obabel-vinardock` — the repo's own `bin/<name>` first
  (it ships fully static builds of both), then `<pwd>/<name>`, PATH,
  `.tools/bin/<name>` (bare `obabel` is NEVER probed or used)
- `param` — the repo's own `param/` first, then `<pwd>/param/` and
  `.tools/param/` (needs all of `param.dat`, `param.TxT.dat`,
  `dun2010bbdep.bin`)
- `plip` — `.tools/plip-venv/bin/plip`
- `launcher` — resolved path of `vinardock-pipeline` on PATH, else
  `.tools/bin/vinardock-pipeline` when installed, else `null`

No filesystem scanning, no guessed directories — a binary elsewhere is
"not found" and is not used; the repo's `bin/` is the supported build.

## 2. Ask (coordinator)

Show the probe result. Binaries and `param/` need no asking — they ship
in the repo. The only provisioned piece is PLIP: if `plip` is false,
install; if true, confirm reuse and skip.

## 3. Install

```bash
python3 "<skill_dir>/scripts/setup.py" install \
    [--skip-plip] [--launcher] [--replace]
```

- PLIP → `uv venv --python <invoking Python> .tools/plip-venv` +
  pinned deps including the self-contained `openbabel` 3.2.1 wheel —
  a different Open Babel than the obabel-vinardock CLI uses; noted in
  report.md's provenance. `UV_CACHE_DIR` is set to `.tools/cache/uv`,
  so the download cache stays in the repo too.
- `--replace` deletes and rebuilds `.tools/plip-venv`.
- `--skip-plip` provisions nothing; `analyse` then fails until PLIP
  exists.
- Binaries and params are not copied: `install` records their bundled
  paths (`bin/`, `param/`) in `.tools/install.json`, which `analyse`
  quotes in report.md's provenance block.
- Launcher: an interactive run offers to write a
  `vinardock-pipeline` wrapper (`exec <install-python> <pipeline.py>
  "$@"`) into `.tools/bin/` — never a PATH directory — and prints a
  hint to add that directory to PATH. A wrapper rather than a symlink
  because it needs no exec bit on `pipeline.py` and pins the
  interpreter that ran install. Non-interactive runs never prompt —
  pass `--launcher` to create it (after the user approves). An existing
  PATH entry for a different wrapper is reported as shadowing.
- `references/*-help.txt` regenerate on every install from the bundled
  binaries so they document the builds actually in use.
  `vinardock-help.txt` masks the timestamp seed default as
  `<timestamp>` so help diffs compare across runs.

Prints a JSON summary (`{path, version_line, source}` per tool, plus
param files and PLIP versions) and writes the same to
`.tools/install.json`.
