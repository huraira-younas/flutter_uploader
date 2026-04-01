# CLI reference

Run **`python3 run.py`** from this repository. Same content under **Read Me → CLI** in the app.

Headless runs need **`--cli`** (otherwise the GUI opens and run flags are ignored). **`--list-steps`** and **`--no-install`** work without `--cli`.

Set the Flutter project root in the GUI (**App Info → Flutter project root**), or set **`FLUTTER_PROJECT_ROOT`** in `.env` to override for a run. See [`ENVIRONMENT.md`](ENVIRONMENT.md).

---

## Flags

| Flag | Purpose |
|:---|:---|
| `--cli` | Headless pipeline |
| `--no-install` | Skip `pip install -r requirements.txt` |
| `--list-steps` | Print step keys and exit |
| `-h`, `--help` | Full help |

### With `--cli`

| Flag | Default |
|:---|:---|
| `--version` · `--build` · `--recipients` · `--commit-message` | from pubspec / see `--help` |
| `--pub-mode` | `pub-get` |
| `--power-mode` | `shutdown` |
| `--quit-after-power` | off |
| `--android` / `--no-android` · `--ios` / `--no-ios` · `--git` / `--no-git` · `--post` / `--no-post` | sections on |
| `--steps` | comma-separated keys (`--list-steps`) |

---

## Examples

```bash
python3 run.py --help
python3 run.py --list-steps
python3 run.py --cli --no-git --no-post --no-ios \
  --version 1.0.6 --build 65
python3 run.py --cli --steps clean,pub_get
python3 run.py --cli \
  --recipients "a@x.com,b@y.com" --commit-message "Release v2.0"
python3 run.py --cli --no-ios
```

Exit **`0`** success · **`1`** failure.

[`README.md`](README.md) · [`ENVIRONMENT.md`](ENVIRONMENT.md)
