# Repository publication check — 17 October 2026

Checked the existing project snapshot before publishing it to GitHub.

- The repository had one initial commit (`21ce354`) and a clean working tree.
- The snapshot contained 2,283 tracked files totaling 70,897,178 bytes. The largest file was below 6 MiB.
- No tracked files matched the current `.gitignore` exclusions. `API_KEY.txt`, raw downloads, text-bearing corpus and annotation files, and course-provided materials remain excluded as documented in the README.
- Compared tracked file contents with credential-like values from the local key file and scanned for common GitHub tokens, Google API keys, and private-key headers. No matches were found. Additional credential-assignment and URL-query matches were reviewed and were documentation placeholders or collection-policy descriptions.
- All 99 tracked Python files passed Python AST parsing in the local conda base environment.
- `git fsck --full` and `git diff --check` passed.

This was a repository publication review. The collection pipeline, full research rebuild, statistical findings, and rendered report and slides were not revalidated during this check. A fresh clone still requires the local-only inputs described in the README for a complete rebuild.
