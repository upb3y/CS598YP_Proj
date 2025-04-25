# Automated Folder Organizer

> **Research Prototype — CS598YP Project**
>
> Semantic, LLM‑driven re‑structuring of arbitrary local file trees.

---

## 📚  Project Overview

Messy desktops and *Downloads* folders are universal.  Our organizer pipeline—driven by large‑language‑model (LLM) summarisation and embedding‑based clustering—automatically:

1. **Discovers** every (non‑hidden) file under a chosen root (`part1_1_list_files.py`).
2. **Describes** each file’s content ✨ *(LLM prompt – WIP)*.
3. **Designs** an ergonomic folder hierarchy *(LLM + clustering)*.
4. **Builds** that hierarchy on disk, moving/renaming files safely (`part3_file_mover.py`).

This repo contains the currently implemented **Part 1‑1** and **Part 3**, plus an end‑to‑end test harness.

---

## 🗺️  Repository Layout

```
.
├── part1_1_list_files.py        # generates file_list.json (IDs + paths)
├── part3_file_mover.py          # constructs new tree from mapping JSON
├── test_part3_file_mover.py     # unit tests using temporary dirs
├── docs/                        # design notes, paper draft (coming soon)
└── README.md                    # you’re here
```

> *Parts 1‑2* (LLM summarisation & hierarchy generation) live in a separate prototype notebook for now and will be merged shortly.

---

## 🚀  Quick‑start

### 1.  Clone & set up Python

```bash
# clone your freshly‑pushed repo
$ git clone git@github.com:upb3y/CS598YP_Proj.git
$ cd CS598YP_Proj

# (optional but recommended)
$ python -m venv .venv && source .venv/bin/activate
$ pip install -r requirements.txt   # currently none – stdlib only
```

### 2.  Generate the *file_list* JSON

```bash
# example: catalogue everything under ~/Downloads
$ python part1_1_list_files.py ~/Downloads > file_list.json
```

### 3.  Create/obtain the *mapping* JSON

*Until Parts 1‑2 are wired in, craft a tiny demo mapping manually or use the* `test/` *fixture.*

### 4.  Build the new hierarchy (dry‑run first!)

```bash
# DRY‑RUN → just prints planned moves
$ python part3_file_mover.py \
       --file-list file_list.json \
       --mapping   mapping.json \
       --root      ~/Downloads \
       --dest-root ~/Organised \
       --dry-run

# ACTUAL MOVE
$ python part3_file_mover.py --file-list file_list.json --mapping mapping.json --root ~/Downloads --dest-root ~/Organised
```

---

## 🧪  Running Tests

```bash
# stdlib unittest
$ python test_part3_file_mover.py

# or pytest (nicer output)
$ pip install pytest
$ pytest -q
```
The suite spins up temporary directories, so nothing in your real file system is touched.

---

## 🛠️  Development

* Style: **black** + **ruff** (`pre-commit` config coming).
* Branch naming: `feature/…`, `bugfix/…`, `experiment/…`.
* Commit format: *present‑tense imperative* (e.g., “Add collision‑handling test”).
* Pull Requests: 1 approver minimum.

See `docs/roadmap.md` (soon) for milestones.

---

## 📄  License

Released under the **MIT License** — see [`LICENSE`](LICENSE) for details.

---

*Made with ❤️ at the University of Illinois.*

