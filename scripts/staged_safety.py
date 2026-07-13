"""Full public-safety validation for a package staging tree."""
from __future__ import annotations

from pathlib import Path

from author_policy import author_identity_terms, metadata_author_context
from safety_checks import _scan_text, deny_terms, path_is_forbidden
from toolbox_common import git_files, read_text_or_skip


def staged_safety_errors(repo: Path, staging: Path) -> list[str]:
    files = sorted(path for path in staging.rglob('*') if path.is_file())
    authors, locations, invalid, spans = metadata_author_context(staging, files)
    repo_authors, _, _, _ = metadata_author_context(repo, git_files(repo))
    authors.update(repo_authors)
    context = {
        'terms': deny_terms(repo),
        'author_locations': locations,
        'invalid_author_locations': invalid,
        'author_spans': spans,
        'author_terms': author_identity_terms(authors),
        'semantic': True,
    }
    errors = []
    for path in files:
        rel = path.relative_to(staging).as_posix()
        violation = path_is_forbidden(rel)
        if violation:
            errors.append(f'{rel}: {violation}')
            continue
        text = read_text_or_skip(path)
        if text is None:
            errors.append(f'{rel}: binary or non-UTF-8 file is not public-safe')
            continue
        errors.extend(_scan_text(rel, text, context))
    return errors
