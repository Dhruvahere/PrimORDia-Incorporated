# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from Bio.Align import PairwiseAligner
import RNA

from game_data import ZETA_SEQ, DONORS, ARCHIVES

app = FastAPI(title="PrimORDia Research Workstation")

# In-memory session state (single player local app)
STATE = {
    "fold_restored": False,
    "bookmarks": [],
    "staged_patches": {},  # donor_id -> candidate_key
    "submitted": False,
}

aligner = PairwiseAligner()
aligner.mode = "local"
aligner.match_score = 2.0
aligner.mismatch_score = -1.5
aligner.open_gap_score = -5.0
aligner.extend_gap_score = -1.0


class CommandRequest(BaseModel):
    command: str


def apply_staged_sequence() -> str:
    """Returns Zeta sequence with all currently staged patches applied."""
    seq = list(ZETA_SEQ)
    for donor_id, cand_key in STATE["staged_patches"].items():
        cand = DONORS[donor_id]["candidates"][cand_key]
        seq[cand["start"]:cand["end"]] = list(cand["seq"])
    return "".join(seq)


@app.post("/api/command")
def run_command(req: CommandRequest):
    raw = req.command.strip()
    parts = raw.split()
    if not parts:
        return {"terminal": "", "state": STATE}

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        return {
            "terminal": (
                "Available contractor commands:\n"
                "  help                         Show this message\n"
                "  inspect [zeta|donors|alpha]  Inspect sequence workspace or restricted regions\n"
                "  read <DOC_ID>                Read company archive (WO-017, VET-017, MEMO-92, PREV-NOTE)\n"
                "  align <DONOR_ID>             Run Smith-Waterman local alignment against Zeta\n"
                "  restore fold                 Restore missing ViennaRNA secondary-structure module\n"
                "  fold <START> <END>           Compute RNA secondary structure & MFE on current Zeta\n"
                "  patch <DONOR_ID> <CAND_ID>   Stage a candidate sequence replacement\n"
                "  validate                     Check reading frames, structure, and staged patches\n"
                "  submit                       Authorize final genome repair submission"
            ),
            "state": STATE,
        }

    if cmd == "inspect":
        target = args[0].lower() if args else "zeta"
        if target not in ("zeta", "donors"):
            return {
                "terminal": (
                    "ACCESS DENIED\n\n"
                    "The remaining intellectual property is worth more\n"
                    "than your entire bloodline.\n\n"
                    "Please return to Fragment Zeta."
                ),
                "state": STATE,
            }
        if target == "donors":
            lines = ["DONOR SEQUENCE RECORDS:"]
            for d_id, d in DONORS.items():
                lines.append(f"  {d_id}: {d['title']} ({len(d['sequence'])} bp)")
                for c_id, c in d["candidates"].items():
                    lines.append(f"      -> candidate {c_id} [{c['start']}..{c['end']}]: {c['desc']}")
            return {"terminal": "\n".join(lines), "state": STATE}

        current_seq = apply_staged_sequence()
        return {
            "terminal": (
                f"Fragment Zeta loaded ({len(current_seq)} bp).\n"
                f"Staged patches: {len(STATE['staged_patches'])}\n"
                "Sequence viewer updated."
            ),
            "sequence": current_seq,
            "state": STATE,
        }

    if cmd == "read":
        if not args:
            avail = ", ".join(ARCHIVES.keys())
            return {"terminal": f"Usage: read <DOC_ID>. Available: {avail}", "state": STATE}
        doc_id = args[0].upper()
        doc = ARCHIVES.get(doc_id)
        if not doc:
            return {"terminal": f"Record '{doc_id}' not found.", "state": STATE}
        return {
            "terminal": f"=== {doc['title']} ===\n{doc['body']}",
            "record": doc,
            "state": STATE,
        }

    if cmd == "align":
        if not args or args[0].upper() not in DONORS:
            return {"terminal": f"Usage: align <DONOR_ID> ({', '.join(DONORS.keys())})", "state": STATE}
        donor_id = args[0].upper()
        donor = DONORS[donor_id]
        alignments = aligner.align(ZETA_SEQ, donor["sequence"])
        top_hits = []
        for aln in list(alignments)[:3]:
            coords = aln.aligned[0][0]
            start, end = int(coords[0]), int(coords[1])
            if {"label": f"{donor_id}@{start}..{end}", "start": start, "end": end} not in STATE["bookmarks"]:
                STATE["bookmarks"].append({"label": f"{donor_id}@{start}..{end}", "start": start, "end": end})
            top_hits.append(f"Score: {aln.score:.1f} | Zeta interval: {start}..{end}\n{aln}")

        out = f"Biopython PairwiseAligner results for {donor_id}:\n\n" + "\n".join(top_hits)
        return {"terminal": out, "analysis": out, "state": STATE}

    if cmd == "restore" and args and args[0].lower() == "fold":
        STATE["fold_restored"] = True
        return {
            "terminal": (
                "Restoring /usr/local/bin/vienna_fold from backup tape...\n"
                "Recovered symbol table. Note found in /tmp/.j_h_recovery:\n"
                "  'Check Locus 1200..1260 after staging DNR-04 candidates.'\n"
                "Module `fold` is now online."
            ),
            "state": STATE,
        }

    if cmd == "fold":
        if not STATE["fold_restored"]:
            return {
                "terminal": "ERROR: Secondary structure binary missing. Run `restore fold` to recover from tape.",
                "state": STATE,
            }
        if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
            return {"terminal": "Usage: fold <START> <END> (e.g., fold 1200 1260)", "state": STATE}
        start, end = int(args[0]), int(args[1])
        current_seq = apply_staged_sequence()
        subseq_dna = current_seq[start:end]
        subseq_rna = subseq_dna.replace("T", "U")
        structure, mfe = RNA.fold(subseq_rna)
        report = (
            f"ViennaRNA RNA.fold({start}..{end}):\n"
            f"  Transcript : {subseq_rna}\n"
            f"  Dot-Bracket: {structure}\n"
            f"  MFE        : {mfe:.2f} kcal/mol"
        )
        return {"terminal": report, "analysis": report, "state": STATE}

    if cmd == "patch":
        if len(args) < 2:
            return {"terminal": "Usage: patch <DONOR_ID> <CANDIDATE_ID>", "state": STATE}
        d_id, c_id = args[0].upper(), args[1].upper()
        if d_id not in DONORS or c_id not in DONORS[d_id]["candidates"]:
            return {"terminal": f"Unknown donor or candidate: {d_id} / {c_id}", "state": STATE}
        STATE["staged_patches"][d_id] = c_id
        return {
            "terminal": f"Staged {c_id} for {d_id}. Run `validate` or `fold` to inspect impact.",
            "sequence": apply_staged_sequence(),
            "state": STATE,
        }

    if cmd == "validate":
        lines = ["VALIDATION SUMMARY:"]
        for d_id, d in DONORS.items():
            chosen = STATE["staged_patches"].get(d_id)
            if not chosen:
                lines.append(f"  [MISSING] {d_id}: No candidate staged.")
            else:
                cand = d["candidates"][chosen]
                lines.append(f"  [STAGED]  {d_id} -> {chosen} ({cand['start']}..{cand['end']})")
                if d_id == "DNR-04":
                    rna_seq = cand["seq"].replace("T", "U")
                    _, mfe = RNA.fold(rna_seq)
                    lines.append(f"            ViennaRNA check: MFE = {mfe:.2f} kcal/mol")
                if chosen == "DNR-05-ENH":
                    lines.append("            WARNING: Exceeds clinical reflex safety threshold (VET-017).")
        return {"terminal": "\n".join(lines), "analysis": "\n".join(lines), "state": STATE}

    if cmd == "submit":
        if len(STATE["staged_patches"]) < len(DONORS):
            return {
                "terminal": "SUBMISSION REJECTED: Not all donor assignments have staged patches. Run `validate`.",
                "state": STATE,
            }
        effects = [
            DONORS[d_id]["candidates"][c_id]["effect"]
            for d_id, c_id in STATE["staged_patches"].items()
        ]
        if "ESCAPE" in effects:
            ending = (
                "OUTCOME REPORT — INCIDENT PR-017-OMEGA\n\n"
                "Forty-eight hours post-transfection, Specimen PR-017 demonstrated "
                "unprecedented forelimb coordination, unlatched its containment paddock, "
                "and breached the perimeter fence into the cloud forest.\n\n"
                "Legal has terminated your contract and advised against travel to San José."
            )
        elif "PARALYSIS" in effects:
            ending = (
                "OUTCOME REPORT — CLINICAL FAILURE\n\n"
                "Specimen PR-017 developed acute motor block following expression of the "
                "patched Zeta construct. Veterinary intervention stabilized the animal, "
                "and your consulting fee has been withheld."
            )
        else:
            ending = (
                "OUTCOME REPORT — CONTRACT COMPLETE\n\n"
                "Tremors resolved within 72 hours. Dr. Morales reports that PR-017 is "
                "alert, vocal, and spent the morning repeatedly carrying its chewed rubber "
                "enrichment ball back to the handler's boots, chirping until it was thrown.\n\n"
                "Wire transfer initiated. Access to Fragment Zeta revoked."
            )
        return {"terminal": ending, "analysis": ending, "state": STATE}

    return {"terminal": f"contractor: {cmd}: command not found. Type `help`.", "state": STATE}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")