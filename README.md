# vinardock-skill — Agent Skill

Vinardock molecular docking pipeline (prepare → dock → analyse)
packaged as an [Agent Skills](https://agentskills.io)-format skill: a
`SKILL.md` instruction file plus the Python scripts and reference docs
the agent needs to coordinate the run.

## Requirements

- Linux x86_64 — `bin/` ships linux-amd64 static `vinardock` +
  `obabel-vinardock` builds (no host libraries needed) and `param/`
  ships the parameter files, so install needs no binary or param
  downloads
- Python ≥ 3.9 (stdlib only; no pip dependencies)
- Network access is needed only to build the PLIP venv into
  `<repo>/.tools` (or pass `--skip-plip`); everything else is bundled.
  `--tools_dir` overrides the location per run.

## Install

Copy or symlink this directory into your agent's skills folder:

| Host | Location |
|---|---|
| Devin | `~/.config/devin/skills/vinardock-skill` |
| Claude Code | `~/.claude/skills/vinardock-skill` or `<project>/.claude/skills/vinardock-skill` |
| Codex / generic | `~/.agents/skills/vinardock-skill` or `<project>/.agents/skills/vinardock-skill` |
| Cursor | `<project>/.cursor/skills/vinardock-skill` |

On a single machine, a symlink keeps one source of truth:

```bash
ln -s /path/to/vinardock-skill ~/.claude/skills/vinardock-skill
```

This skill-directory placement is the only thing that lives outside the
repo; `scripts/setup.py install` writes only to `<repo>/.tools/`
(gitignored) and never touches your home directory or PATH.

## Usage

Ask the agent to dock a receptor against one or more ligands (`.pdb`,
`.sdf`, `.mol2`, `.pdbt`, or a `.smi` SMILES file). It interviews for
inputs, box, recipe and run directory, then runs
`scripts/pipeline.py workflow`, which gates each stage on its
`status.json` and writes `<run_dir>/report.md`. Every interview answer
maps to a flag, so a non-interactive agent can supply them all; see
`SKILL.md` and `references/contract.md` for the invocation and the
validation rules.

## Development

- Tests: `python3 -m unittest discover -s tests` — the `IntegrationTests`
  class runs the real binaries (the dock half always; analyse when
  `<repo>/.tools/plip-venv` exists) and asserts their actual output formats.
- `AGENTS.md` documents repo conventions; `references/contract.md` is
  the stage interface.
