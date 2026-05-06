# stingytoken

Reduce GitHub Copilot token usage by surfacing only the files that actually matter for your current task — and by rewriting your prompt so it says more with fewer tokens.

When Copilot pulls context from your workspace it grabs whatever is open — regardless of relevance. On a large repo this means expensive, noisy prompts. `stingytoken` lets you describe what you're working on, get back a ranked shortlist of the most relevant files, and compress your prompt into a tight, imperative instruction before passing it to Copilot.

---

## Installation

Requires **Python 3.10 or later**.

```bash
pip install stingytoken
```

To use the `compress` or `prep` commands with an OpenAI-compatible backend:

```bash
pip install "stingytoken[openai]"
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

```bash
stingytoken scope "user authentication and JWT tokens"
stingytoken scope "database migrations" -n 5 -w
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

### `compress` — rewrite a prompt to be shorter and more precise

```
stingytoken compress QUERY [OPTIONS]
```

Sends your prompt to a local or remote LLM backend and rewrites it following strict rules: imperative verbs only, specific file/function names, one acceptance criterion, no filler. Output is capped at 3 sentences and 80 tokens.

**Arguments**

| Name | Description |
|---|---|
| `QUERY` | The prompt text to compress |

**Options**

| Flag | Default | Description |
|---|---|---|
| `-b, --backend` | `ollama` | Backend to use: `ollama` or `openai` |
| `-m, --model` | `mistral` | Model name passed to the backend |
| `-c, --copy` | off | Copy the rewritten prompt to the clipboard |

**Examples**

```bash
stingytoken compress "I was wondering if you could maybe refactor the auth module"
stingytoken compress "please help fix the login bug" -b openai -m gpt-4o-mini -c
```

**Output**

```
╭─ Rewritten prompt ────────────────────────────────────────────────╮
│ Refactor auth/middleware.py to extract token validation into a    │
│ standalone function. Remove the inline session check in login().  │
│ Constraint: preserve existing tests.                              │
╰───────────────────────────────────────────────────────────────────╯
Original: ~42 tokens  →  Rewritten: ~28 tokens  (33% reduction)
```

---

### `prep` — scope + compress in one step

```
stingytoken prep QUERY [OPTIONS]
```

Runs `scope` and `compress` together and prints a single panel with the ranked context files and the optimised prompt — ready to paste into Copilot or any AI tool.

**Arguments**

| Name | Description |
|---|---|
| `QUERY` | Natural-language description of the task |

**Options**

| Flag | Default | Description |
|---|---|---|
| `-n, --max-files` | 12 | Maximum number of context files |
| `-b, --backend` | `ollama` | Compression backend: `ollama` or `openai` |
| `-m, --model` | `mistral` | Model name passed to the backend |
| `-c, --copy` | off | Copy context files + optimised prompt to clipboard |
| `-r, --root` | `.` | Repository root to scan |

**Examples**

```bash
stingytoken prep "add rate limiting to the API" -n 6 -c
stingytoken prep "fix the broken pagination" -b openai -m gpt-4o-mini --copy
```

**Output**

```
╭──────────────────────────────────────────────────────────────────╮
│ 📁 Context files:                                                │
│   src/api/routes.py                                              │
│   src/api/middleware.py                                          │
│   src/config.py                                                  │
│                                                                  │
│ ✍️  Optimized prompt:                                             │
│ Add rate limiting middleware to src/api/routes.py using a token  │
│ bucket strategy. Configure limits in src/config.py.              │
│ Constraint: preserve existing route signatures.                  │
│                                                                  │
│ Tokens saved: ~31% on prompt | Context: 3 files instead of 87   │
╰──────────────────────────────────────────────────────────────────╯
```

---

## Backends

### Ollama (default)

Runs locally. Install [Ollama](https://ollama.com), pull a model, and start the server:

```bash
ollama pull mistral
ollama serve
```

No API key required.

### OpenAI

Requires `pip install "stingytoken[openai]"` and an API key:

```bash
export OPENAI_API_KEY=sk-...
stingytoken compress "my prompt" -b openai -m gpt-4o-mini
```

Any OpenAI-compatible endpoint (e.g. LM Studio, vLLM) works — override with `base_url` in your config file.

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

[compress]
backend = "openai"
model = "gpt-4o-mini"
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
3. **Compress** — sends the prompt to a local (Ollama) or remote (OpenAI) LLM with a strict system prompt that enforces imperative style, named references, and a single acceptance criterion
4. **Display** — prints ranked files and the optimised prompt; optionally copies to clipboard or writes a `.stingytoken-context` manifest

---

## License

MIT
