#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

EXCLUDED_CATEGORIES = [
    'env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache',
    'state', 'pairing', 'runtime'
]
ALLOWED_SKILL_SUPPORT_DIRS = {'references', 'templates', 'scripts', 'assets'}
DEFAULT_PUBLIC_SKILLS = [
    'autonomous-ai-agents/openrouter-mcp-server',
    'hermes-agent/honcho-memory-provider',
    'hermes-agent/hermes-config-audits',
    'hermes-agent/profile-builder',
    'software-development/prompt-enhancer',
    'software-development/plugin-builder',
]
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@(?!(?:example\.com)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
HERMES_HOME_RE = re.compile(r'(?<![A-Za-z0-9_<])/(home|Users)/([A-Za-z0-9._-]+)/\.hermes(?=/|\b)')
USER_HOME_RE = re.compile(r'(?<![A-Za-z0-9_<])/(home|Users)/([A-Za-z0-9._-]+)(?=/|\b)')
API_KEY_CONFIG_RE = re.compile(r'hermes config set ([A-Z][A-Z0-9_]*_API_KEY)\s+<[^\n>]+>')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def read_text_or_skip(path: Path) -> str | None:
    data = path.read_bytes()
    if b'\0' in data:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def copy_tree_public(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        parts = set(rel.parts)
        if parts & {'.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs', 'cache', 'pairing'}:
            continue
        if any(str(part).startswith('state.db') for part in rel.parts):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def skip_inventory_file(repo: Path, path: Path) -> bool:
    """Return true for local/private files that must not enter public inventory."""
    if not path.is_file() or '.git' in path.parts:
        return True
    rel = path.relative_to(repo).as_posix()
    parts = set(Path(rel).parts)
    if '.hermes' in parts:
        return True
    if parts & {'.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs', 'cache', 'pairing', 'checkpoints', 'backups'}:
        return True
    if any(str(part).startswith('state.db') for part in Path(rel).parts):
        return True
    if rel == 'inventory/source-fingerprints.json':
        return True
    if '__pycache__' in path.parts or rel.endswith(('.pyc', '.pyo')):
        return True
    return False


def safe_child_file(root: Path, rel: object, label: str) -> Path:
    if not isinstance(rel, str) or not rel.strip():
        raise SystemExit(f'{label} must be a non-empty relative path')
    rel_path = Path(rel)
    if rel_path.is_absolute() or '..' in rel_path.parts:
        raise SystemExit(f'{label} must stay inside its package: {rel}')
    root_resolved = root.resolve()
    path = (root / rel_path).resolve()
    if root_resolved not in path.parents:
        raise SystemExit(f'{label} resolves outside its package: {rel}')
    if not path.is_file():
        raise SystemExit(f'{label} references missing file: {rel}')
    return path


def ensure_local_info(repo: Path, private_prefix: str | None, public_plugin_profile: str | None, approved_author_line: str | None):
    info = repo / '.git' / 'info'
    info.mkdir(parents=True, exist_ok=True)
    write(info / 'private-profile-denylist.txt', '\n'.join([private_prefix or '']) + '\n')
    write(info / 'private-plugin-denylist.txt', '\n'.join([public_plugin_profile or '']) + '\n')
    if approved_author_line:
        write(info / 'approved-authorship.txt', approved_author_line + '\n')
    existing = info / 'identity-denylist.txt'
    if not existing.exists():
        existing.write_text('', encoding='utf-8')


def public_skill_rels(cli_values: list[str]) -> list[Path]:
    raw: list[str] = []
    if cli_values:
        raw.extend(cli_values)
    env = os.environ.get('HERMES_TOOLBOX_PUBLIC_SKILLS', '')
    if env:
        raw.extend(part.strip() for part in env.split(',') if part.strip())
    if not raw:
        raw = DEFAULT_PUBLIC_SKILLS
    rels = []
    for item in raw:
        rel = Path(item)
        if rel.is_absolute() or '..' in rel.parts or not item.strip():
            raise SystemExit(f'public skill path must be relative and stay under skills/: {item}')
        rels.append(rel)
    return sorted(set(rels), key=lambda p: p.as_posix())


def frontmatter_author(skill_text: str) -> str | None:
    if not skill_text.startswith('---'):
        return None
    marker = re.search(r'\n---\s*\n', skill_text[3:])
    if not marker:
        return None
    frontmatter = skill_text[3:marker.start() + 3]
    for line in frontmatter.splitlines():
        if line.startswith('author:'):
            return line.split(':', 1)[1].strip().strip('"\'')
    return None


def local_private_terms(repo: Path) -> list[str]:
    terms: list[str] = []
    deny_file = repo / '.git' / 'info' / 'identity-denylist.txt'
    if deny_file.exists():
        terms.extend(
            line.strip()
            for line in deny_file.read_text(encoding='utf-8', errors='ignore').splitlines()
            if line.strip() and not line.strip().startswith('#')
        )
    env = os.environ.get('HERMES_TOOLBOX_DENY_TERMS', '')
    if env:
        terms.extend(part.strip() for part in env.split(',') if part.strip())
    return sorted(set(terms), key=len, reverse=True)


def replacement_terms(repo: Path, author_name: str | None, private_prefix: str | None, public_plugin_profile: str | None) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    if author_name:
        first = author_name.split()[0]
        terms.extend([
            (f"{first}'s VPS", 'the local Hermes environment'),
            (f"{first}'s public repos", "the repository owner's public repos"),
            (f"{first}'s repos", "the repository owner's repos"),
            (f"{first}'s", "the repository owner's"),
            (f'{first}-authored', 'repository-author-authored'),
            (f'{first}-specific/private/user-specific', 'user-specific/private'),
            (f'{first}-specific/private', 'user-specific/private'),
            (f'{first}-specific', 'user-specific'),
            (f'non-{first}-specific', 'reusable/public'),
            (f'Non-{first}-specific', 'Reusable/public'),
            (f'non-{first}', 'public'),
            (f'Non-{first}', 'Public'),
            (f'{first} as a person', 'the repository owner as a person'),
            (author_name, '<repo-author-name>'),
        ])
    if private_prefix:
        terms.extend([
            (f'`{private_prefix}`', '`<first-name>-`'),
            (private_prefix, '<first-name>-'),
        ])
    if public_plugin_profile:
        terms.extend([
            (f'`{public_plugin_profile}`', '`<public-plugin-source-profile>`'),
            (public_plugin_profile, '<public-plugin-source-profile>'),
        ])
    terms.extend([
        ('on ' + 'this ' + 'VPS', 'for this Hermes environment'),
        ('For ' + 'this ' + 'VPS', 'For this Hermes environment'),
        ('this ' + 'VPS', 'this Hermes environment'),
    ])
    terms.extend((term, '<private-term>') for term in local_private_terms(repo))
    return terms


def sanitize_public_text(text: str, rel: Path, repo: Path, author_name: str | None, private_prefix: str | None, public_plugin_profile: str | None) -> str:
    out_lines: list[str] = []
    for line in text.splitlines():
        # Approved authorship metadata remains only in the SKILL.md frontmatter author line.
        if rel.name == 'SKILL.md' and author_name and line.strip() == f'author: {author_name}':
            out_lines.append(line)
            continue
        new = line
        for old, repl in replacement_terms(repo, author_name, private_prefix, public_plugin_profile):
            new = new.replace(old, repl)
        new = HERMES_HOME_RE.sub('$HERMES_HOME', new)
        new = USER_HOME_RE.sub('$HOME', new)
        new = EMAIL_RE.sub('<repo-author-email>', new)
        new = API_KEY_CONFIG_RE.sub(lambda m: f'# Configure {m.group(1)} through the official setup/auth/env flow, not as a non-secret config key', new)
        new = new.replace('$HERMES_HOME/hermes-agent/venv/bin/python', '${HERMES_AGENT_PYTHON:-python3}')
        new = new.replace('$HOME/.hermes/plugins', '$HERMES_HOME/plugins')
        out_lines.append(new)
    return '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')


def copy_public_skill(source_skills: Path, repo: Path, rel: Path, private_prefix: str | None, public_plugin_profile: str | None) -> None:
    src = source_skills / rel
    skill_md = src / 'SKILL.md'
    if not skill_md.is_file():
        raise SystemExit(f'missing public skill source: {skill_md}')
    skill_text = skill_md.read_text(encoding='utf-8')
    author = frontmatter_author(skill_text)
    dst = repo / 'skills' / rel
    if dst.exists():
        shutil.rmtree(dst)
    for path in sorted(src.rglob('*')):
        if not path.is_file():
            continue
        file_rel = path.relative_to(src)
        if file_rel.name.startswith('.') or '__pycache__' in file_rel.parts or file_rel.suffix in {'.pyc', '.pyo'}:
            continue
        if file_rel.name != 'SKILL.md' and (not file_rel.parts or file_rel.parts[0] not in ALLOWED_SKILL_SUPPORT_DIRS):
            continue
        text = read_text_or_skip(path)
        if text is None:
            continue
        target = dst / file_rel
        write(target, sanitize_public_text(text, rel / file_rel, repo, author, private_prefix, public_plugin_profile))


def export_public_skills(hermes_home: Path, repo: Path, skill_rels: list[Path], private_prefix: str | None, public_plugin_profile: str | None) -> None:
    source_skills = hermes_home / 'skills'
    for rel in skill_rels:
        copy_public_skill(source_skills, repo, rel, private_prefix, public_plugin_profile)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    parser.add_argument('--repo', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--private-profile-prefix', default=os.environ.get('HERMES_PRIVATE_PROFILE_PREFIX', ''))
    parser.add_argument('--public-plugin-profile', default=os.environ.get('HERMES_PUBLIC_PLUGIN_PROFILE', ''))
    parser.add_argument('--approved-author-line', default=os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE', ''))
    parser.add_argument('--public-skill', action='append', default=[], help='Relative skill path under $HERMES_HOME/skills to publish. Repeatable. Defaults to the repo allowlist.')
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    hermes_home = Path(args.hermes_home).resolve()
    ensure_local_info(repo, args.private_profile_prefix, args.public_plugin_profile, args.approved_author_line)

    export_public_skills(
        hermes_home,
        repo,
        public_skill_rels(args.public_skill),
        args.private_profile_prefix,
        args.public_plugin_profile,
    )

    manifest = {'version': 1, 'skills': [], 'profiles': [], 'plugins': [], 'personalities': []}
    for skill_path in sorted((repo / 'skills').rglob('SKILL.md')):
        manifest['skills'].append({'path': skill_path.relative_to(repo).as_posix(), 'sha256': sha(skill_path)})

    for personality_manifest in sorted((repo / 'primitives' / 'personalities').glob('*/manifest.json')):
        try:
            personality_data = json.loads(personality_manifest.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise SystemExit(f'invalid personality manifest {personality_manifest}: {exc}') from exc
        if personality_data.get('type') != 'personality' or personality_data.get('sanitized') is not True:
            raise SystemExit(f'personality manifest must declare type=personality and sanitized=true: {personality_manifest}')
        config_path = safe_child_file(
            personality_manifest.parent,
            personality_data.get('config_file'),
            f'{personality_manifest}: config_file',
        )
        manifest['personalities'].append({
            'name': personality_data.get('name', personality_manifest.parent.name),
            'path': personality_manifest.parent.relative_to(repo).as_posix(),
            'manifest_sha256': sha(personality_manifest),
            'config_sha256': sha(config_path),
            'sanitized': True,
        })

    # Export sanitized plugin packages from configured source profile when present.
    if args.public_plugin_profile:
        source_root = hermes_home / 'profiles' / args.public_plugin_profile / 'plugins'
        if source_root.exists():
            for plugin_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
                if args.private_profile_prefix and plugin_dir.name.startswith(args.private_profile_prefix):
                    continue
                dst = repo / 'plugins' / plugin_dir.name
                copy_tree_public(plugin_dir, dst)
                write(dst / 'manifest.json', json.dumps({
                    'package': plugin_dir.name,
                    'type': 'plugin',
                    'source_gate': 'configured-public-plugin-source-profile',
                    'sanitized': True,
                    'included_files': sorted(str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()),
                    'excluded_categories': EXCLUDED_CATEGORIES,
                }, indent=2, sort_keys=True) + '\n')
                manifest['plugins'].append({'path': f'plugins/{plugin_dir.name}', 'sanitized': True})

    profiles_root = repo / 'profiles'
    if profiles_root.exists():
        for profile_dir in sorted(p for p in profiles_root.iterdir() if p.is_dir()):
            manifest_file = profile_dir / 'manifest.json'
            if not manifest_file.exists():
                continue
            try:
                profile_manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError as exc:
                raise SystemExit(f'invalid profile manifest {manifest_file}: {exc}') from exc
            if profile_manifest.get('sanitized') is not True:
                raise SystemExit(f'profile manifest must declare sanitized=true: {manifest_file}')
            manifest['profiles'].append({'path': f'profiles/{profile_dir.name}', 'sanitized': True})

    write(repo / 'inventory' / 'public-manifest.json', json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    fingerprints = {}
    for path in sorted(repo.rglob('*')):
        if skip_inventory_file(repo, path):
            continue
        rel = path.relative_to(repo).as_posix()
        fingerprints[rel] = sha(path)
    write(repo / 'inventory' / 'source-fingerprints.json', json.dumps(fingerprints, indent=2, sort_keys=True) + '\n')
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-public-safety.py')], cwd=repo)
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-identity-neutrality.py')], cwd=repo)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
