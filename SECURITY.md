# Security Policy

Do not add secrets, personal configuration, runtime caches, transcripts,
authentication files, or generated observations to this repository.

Before opening a pull request, run:

```bash
git grep -nE '(ghp_|github_pat_|sk-[A-Za-z0-9]|api[_-]?key|password=)' || true
```

Report accidental exposure privately to the repository owner and rotate the
affected credential immediately.
