# Large‑Output Commands

The following commands in this repository are known to generate large volumes of output or many file reads. They should be considered when measuring baseline performance and when evaluating the impact of developer‑tool integration.

- `pytest -q` – runs the full test suite (94 tests, many warnings). Produces verbose test output and loads the entire codebase.
- `npm audit --json` – audits all Node.js dependencies; can output a large JSON report.
- `git diff --stat` – shows diff statistics across the whole repo, potentially many files.
- `git log --oneline --decorate --graph --all` – prints the commit history; can be large for long histories.
- `pip‑audit` – scans all Python packages for known vulnerabilities; produces a JSON/HTML report.
- `find . -type f` – lists every file in the repository; massive output for large trees.

These commands will be used for baseline measurement (pre‑tool) and later for post‑integration comparison.
