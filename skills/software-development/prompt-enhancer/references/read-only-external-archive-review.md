# Read-only external archive review pattern

Use this when a user asks Hermes to download, unzip/extract, and comb through an external archive, especially if the archive contains Hermes profiles, configs, skills, plugins, or installers.

## Safe execution shape

1. Treat the task as read-only unless the user explicitly asks to install/apply contents.
2. Create a temp directory outside Hermes homes/profile workspaces, e.g. `/tmp/hermes-archive-XXXXXX`; verify it is not under `$HERMES_HOME`, `~/.hermes/profiles`, or any configured profile workspace.
3. Download the source artifact into that temp directory and identify type/size/hash before extraction.
4. Inspect archive member paths for absolute paths or `..` traversal before extracting.
5. Extract only into the temp directory.
6. Inventory all extracted files, classify formats, and concatenate/read text files in a deterministic order for full coverage.
7. Validate parseable formats with focused checks, e.g. YAML parse, skill frontmatter parse, shebang/script review, secret-keyword scan that reports placeholders without exposing secrets.
8. For Hermes-related archives, validate claims against first-party sources: live `hermes --help`/subcommand help and official docs/repo as needed.
9. Do not run installers or copy files into Hermes profiles/configs unless explicitly approved after review.

## Evidence to report

- Temp directory path and proof it is outside Hermes/profile workspaces.
- Downloaded artifact path, byte size, type, and SHA-256.
- Extraction root, archive entry count, unsafe-entry count, extracted file/dir counts.
- Full-read coverage evidence: combined text path or manifest, line/byte counts, and file count.
- Validation checks performed and their pass/fail counts.
- Any safety concerns, especially direct writes to `~/.hermes`, ignored `HERMES_HOME`, raw `.env`/auth handling, or install scripts that suppress errors.
