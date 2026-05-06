# stingytoken

Reduce GitHub Copilot token usage by surfacing only the files that actually matter for your current task.

When Copilot pulls context from your workspace it grabs whatever is open — regardless of relevance. On a large repo this means expensive, noisy prompts. `stingytoken` lets you describe what you're working on and get back a ranked shortlist of the files most semantically related to that task, so you can point Copilot at the right context instead of the whole codebase.

---

## Installation

Requires **Python 3.10 or later**.

```bash
pip install stingytoken
```

To install from source:

```bash
git clone https://github.com/your-org/stingytoken
cd stingytoken
pip install -e ".[dev]"
```

---

## Usage

### `scope` — find the most relevant files for a task

```
stingytoken scope QUERY [OPTIONS]
```

Scans your repository, ranks every file by how closely it relates to `QUERY`, and prints a table showing the top matches with relevance scores and estimated token counts.

**Arguments**

| Name | Description |
|---|---|
| `QUERY` | Natural-language description of what you're working on |

**Options**

| Flag | Default | Description |
|---|---|---|
| `-n, --max-files` | 12 | Maximum number of files to return |
| `-w, --write-context` | off | Write results to `.stingytoken-context` (one path per line) |
| `-r, --root` | `.` | Repository root to scan |

**Examples**

Find files related to authentication in the current repo:
```bash
stingytoken scope "user authentication and JWT tokens"
```

Limit to the 5 most relevant files and write a context manifest:
```bash
stingytoken scope "database migrations" -n 5 -w
```

Scan a different directory:
```bash
stingytoken scope "error handling middleware" -r ./backend
```

**Output**

```
                    Scope Results
 Rank  Score  File                          Est. Tokens
 ────  ─────  ────────────────────────────  ───────────
    1  0.612  src/auth/jwt.py                       340
    2  0.481  src/auth/middleware.py                210
    3  0.307  src/users/models.py                   180
    4  0.094  tests/test_auth.py                    290
    5  0.041  src/config.py                          95

Scanned 142 files · Est. tokens saved: 18,420 (19,250 → 830)
```

Rows are colour-coded by relevance: **green** ≥ 0.3 · **yellow** ≥ 0.1 · dim < 0.1.

---

### Other commands

`compress` and `prep` are reserved for upcoming features (prompt compression and context preparation). They are not yet implemented.

---

## Configuration

`stingytoken` looks for config in three places, applied in order (later overrides earlier):

1. Built-in defaults
2. `~/.stingytokenrc` (user-wide)
3. `.stingytoken.toml` in the current directory (project-level)

Both files use TOML format.

**Example `.stingytoken.toml`:**

```toml
[scope]
max_files = 8
extensions = [".py", ".ts", ".go"]
ignore = ["node_modules", ".venv", "dist", "__pycache__"]
```

**Full defaults:**

```toml
[scope]
max_files = 12
extensions = [".py", ".ts", ".js", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php"]
ignore = ["node_modules", "dist", ".venv", "__pycache__", ".git", "build", "coverage"]
write_context = false

[compress]
backend = "ollama"
model = "mistral"
max_output_tokens = 120
temperature = 0.2
```

---

## How it works

1. **Scan** — walks the repo, skips ignored directories and `.gitignore` entries, reads files matching the configured extensions (max 500 KB each)
2. **Rank** — builds a TF-IDF matrix from file contents, computes cosine similarity between each file and your query
3. **Display** — prints a rich table sorted by relevance score; optionally writes a `.stingytoken-context` manifest you can reference in other tools

---

## License

MIT
