# PrimORDia GmbH (1992 Research Workstation)

PrimORDia GmbH is a short, terminal-driven bioinformatics mystery set in 1992. It is a bioinformatics puzzle taking real gene fragments from birds and reptiles (Gallus gallus, Taeniopygia guttata, and Alligator mississippiensis) and using them to repair PrimORDia's prized synthetic genome for their expensive "pet lizard" `Specimen PR-017`). Rumor has it that PrimORDia's lizard is not exactly of this time... and the lizard has feathers.

Built with FastAPI, Biopython `PairswiseAlign`), and ViennaRNA `RNA.fold`), presented inside an early-1990s SGI/IRIX-inspired workstation interface.



# Quick Start

# 1. Create a virtual environment and install dependencies

```bash

python3 -m venv .venv

source .venv/bin/activate

pip install fastapi uvicorn biopython viennarna

```

# 2. Start the workstation server

```bash

./.venv/bin/python -m uvicorn app:app --reload

```

# 3. Open the workstation

Visit [[http://127.0.0.1:8000](http://127.0.0.1:8000)](http://127.0.0.1:8000](http://127.0.0.1:8000)) in your browser.



#Contractor Terminal Commands

| Command | Description |

| `help` | List all available workstation commands |

| `read <DOC_ID>` | Read archived records `WO-017`, `VET-017`, `MEMO-92`, `PREV-NOTE`) |

| `inspect zeta` | Load Fragment Zeta into the Sequence Viewer |

| `inspect donors` | List the 5 donor sequence records `DNR-01` – `DNR-05`) and candidate patches |

| `align <DONOR_ID>` | Run Smith-Waterman local alignment via Biopython against Fragment Zeta |

| `restore fold` | Recover the unlinked ViennaRNA secondary-structure binary from backup tape |

| `fold <START> <END>` | Compute RNA secondary structure (dot-bracket) and Minimum Free Energy (MFE) |

| `patch <DONOR_ID> <CAND_ID>` | Stage a candidate sequence replacement onto Fragment Zeta |

| `validate` | Verify reading frames, secondary structure stability, and clinical warnings |

| `submit` | Authorize final genome repair submission and receive the outcome report |
