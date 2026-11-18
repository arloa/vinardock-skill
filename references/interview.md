# Interview

Follow this when SKILL.md step 2 routes here. Collect everything in ONE
question pass — scripts never ask questions.

## Questions

1. **Receptor** — path to a `.pdb` (or `.pdbt`) file. Trust the extension;
   do not open the file to inspect it.
   - **ASK**: how to handle receptor HETATM records — three choices:
     keep all (default), standard prep (`--drop_hetatm --keep_metals`:
     strips waters/ions/cofactors/co-crystal ligands but keeps metal
     ions, detected by element column), or strip everything including
     metals (`--drop_hetatm` alone). Ask directly — do not read the
     receptor to enumerate the residues. Prepare reports the residue
     names kept or dropped in its warnings/metrics.
     Modified amino acids (MSE, SEP, TPO, …) are the polymer even when
     marked HETATM: they are kept under every choice (never stripped,
     never offered by `scan`), so no answer can delete them.
2. **Ligands** — exactly one source:
   - structure files (`.pdbt`, `.sdf`, `.mol2`, `.pdb`) via
     `--prepare_ligand`, or
   - SMILES via `--prepare_ligand` — create a `.smi` input file
     outside the run directory, `SMILES<space>name` per line; inputs
     are read in place (never copied into the run directory), or
   - **extracted from the receptor** via `--ligand_from_receptor
     <RESNAME[:CHAIN:SEQ]>` — the redock case. When the user wants the
     receptor's co-crystal ligand, run `pipeline.py scan <receptor>`
     first, present the candidate list (`RESNAME:chain:seq atoms=n`),
     and **ASK** which molecule to use. The extracted molecule is
     always removed from the receptor (docking into an occupied
     pocket is meaningless) and doubles as the autobox reference —
     `--autobox <pad>` alone then boxes the original binding site.
   - 2D structures are handled (prepare runs `--gen3d`); duplicate
     ligand names are a hard error.
3. **Box** — pick one:
   - manual: `center_x center_y center_z size_x size_y size_z` —
     passed verbatim as vinardock flags (`--center_x 10 --size_x 22 …`)
   - autobox: a reference ligand file (usually the co-crystal ligand or
     one of the docking ligands) + pad in Å → `--autobox {pad}` +
     `--prepare_autobox_ligand {ref}`. The reference must be a single
     molecule (`.pdbt`/`.smi`/`.sdf`/`.mol2`/`.pdb`); 2D input gets
     `--gen3d`, multi-molecule files are rejected.
   - The resolved box is scraped from vinardock's `Search box:` log line
     (autobox) or computed from the flags, recorded in `resolved_box`.
4. **Run dir** — where results go.
5. **Defaults** — unless the user says otherwise: conformations 9, pose 1
   (the conformer PLIP analyses, applied to every ligand), seed from the
   timestamp (recorded in `metrics.seed`), threads `nproc`. Batch VS
   parallelizes across ligands only when `n_ligands >= threads`; PLIP
   runs in parallel across ligands.
6. **recipe** — see table below; config grammar and merge order are in
   `references/recipes.md`. Confirm or let the user pick.
7. **Recipe-specific flags** — whatever the chosen recipe still needs:
   `flexres.res`/`flexres.autoflex` for flexible, the mutation spec for
   mutation-dg.

## Recipe selection table (deterministic)

| User intent (keywords) | Recipe |
|---|---|
| flexible, flexres, sidechain | `flexible` |
| screen, library, batch, many ligands, VS | `screening` |
| mutation, mutate, dG, ΔG | `mutation-dg` |
| rescore, score-only, evaluate pose | `rescore` * |
| minimize, polish pose | `--minimize` flag on `standard` |
| anything else / ambiguous | `standard` |

No matching intent → `standard`, and list the options above so the user
can override. If multiple recipe intents are present (e.g. flexible + deep),
ask which protocol to use; do not silently
pick one. A `.conf` path is also accepted (`--recipe <path>`).

\* `rescore` scores the ligand **as supplied** — it requires an
already-posed ligand (e.g. a `.pdbt` output from a previous run) and a
box that contains that pose. Routing a plain `.smi`/`.sdf` through it
runs `--gen3d` and scores an arbitrary conformer — not what the user
means by "score-only"; use `standard` unless they have a real pose.

`mutation-dg` constraints (fail-closed): exactly **one** ligand, and
`--flexres.res` must be a `chain:OLDresNEW` spec with `OLD != NEW` (e.g.
`A:S63T`). If vinardock ignores `--calc_mutate_dG` the dock stage fails
rather than reporting an ordinary score as a ΔG.

## Flag rules

- Pass vinardock flags verbatim on the same command line (`--key value`
  only — `--key=value` is rejected). If a recipe needs a value you don't
  have, ask; never invent one.
- `--prepare_autobox_ligand <file>` is prepared like a ligand; to use an
  already-prepared reference, pass `--autobox_ligand <file.pdbt>`.
- `--timeout <seconds>` bounds the vinardock run (default 21600 = 6h);
  `prepare`/`analyse` have their own per-stage timeouts.
