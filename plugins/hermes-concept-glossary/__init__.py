from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_FILE = PLUGIN_DIR / 'data' / 'plugin.json'
PLUGIN_NAME = PLUGIN_DIR.name
TOOLSET = 'tutorial'


def _load_data() -> dict[str, Any]:
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _error(message: str, **extra: Any) -> str:
    payload = {'success': False, 'plugin': PLUGIN_NAME, 'error': message}
    payload.update(extra)
    return _json(payload)


def _progress_path() -> Path:
    root = Path(os.environ.get('HERMES_HOME') or Path.home() / '.hermes')
    return root / 'data' / PLUGIN_NAME / 'progress.json'


def _read_progress() -> dict[str, Any]:
    path = _progress_path()
    if not path.exists():
        return {'lessons': {}, 'events': []}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            data.setdefault('lessons', {})
            data.setdefault('events', [])
            return data
    except Exception:
        pass
    return {'lessons': {}, 'events': []}


def _write_progress(data: dict[str, Any]) -> None:
    path = _progress_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r'[a-zA-Z][a-zA-Z0-9_-]{2,}', text or '')}


def _find_matches(data: dict[str, Any], query: str) -> list[dict[str, Any]]:
    q = _keywords(query)
    if not q:
        return data.get('lessons', [])[:3]
    matches = []
    for item in data.get('lessons', []) + data.get('examples', []):
        hay = _keywords(' '.join(str(item.get(k, '')) for k in ('id', 'title', 'summary', 'body', 'kind')))
        score = len(q & hay)
        if score:
            out = dict(item)
            out['score'] = score
            matches.append(out)
    return sorted(matches, key=lambda x: x.get('score', 0), reverse=True)[:5]


def _level_path(level: str | None = None) -> list[dict[str, Any]]:
    data = _load_data()
    curriculum = data.get('curriculum') or []
    if level:
        wanted = str(level).lower().replace('level ', '')
        return [node for node in curriculum if str(node.get('level', '')).lower() in {wanted, f'level {wanted}'} or str(node.get('level_key', '')).lower() == wanted]
    return curriculum


def _explain_term(term: str) -> dict[str, Any]:
    data = _load_data()
    glossary = data.get('glossary', {})
    key = (term or '').strip().lower()
    if key in glossary:
        return {'term': key, 'explanation': glossary[key]}
    for candidate, explanation in glossary.items():
        if key and (key in candidate or candidate in key):
            return {'term': candidate, 'explanation': explanation}
    return {'term': key or 'Hermes concept', 'explanation': 'I do not have an exact glossary card for that term yet. Validate against the official Hermes docs and live CLI output.'}


def _classify_risk(text: str) -> dict[str, Any]:
    lower = (text or '').lower()
    high_markers = ['rm -rf', 'delete', 'wipe', 'password', 'token', 'auth.json', '.env', 'mcp-tokens', 'state.db', 'sessions/', 'logs/', 'cache/', 'payment', 'send to everyone']
    medium_markers = ['write', 'edit', 'commit', 'push', 'cron', 'gateway', 'plugin', 'profile', 'config set']
    if any(m in lower for m in high_markers):
        return {'risk': 'high', 'reason': 'The action touches secrets, runtime state, destructive commands, broad delivery, or credential-adjacent files.', 'safer_action': 'Use official setup/config tools, narrow the path, make a backup, and require explicit approval.'}
    if any(m in lower for m in medium_markers):
        return {'risk': 'medium', 'reason': 'The action can modify configuration, files, automation, or external state.', 'safer_action': 'Plan the exact write surface, validate first, and keep rollback options.'}
    return {'risk': 'low', 'reason': 'The action appears read-only or explanatory.', 'safer_action': 'Still verify the target and avoid exposing secrets.'}


def _score_text(text: str, expected: list[str]) -> dict[str, Any]:
    words = _keywords(text)
    hits = [kw for kw in expected if kw.lower() in words or kw.lower() in (text or '').lower()]
    score = round(len(hits) / max(1, len(expected)), 2)
    return {'score': score, 'matched_keywords': hits, 'expected_keywords': expected, 'passed': score >= 0.5}


def _handle_progress(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    data = _read_progress()
    lessons = data.setdefault('lessons', {})
    events = data.setdefault('events', [])
    lesson_id = str(args.get('lesson_id') or args.get('query') or '').strip()
    if tool_name == 'tutorial_get_progress':
        completed = sorted(k for k, v in lessons.items() if v.get('status') == 'completed')
        return {'success': True, 'plugin': PLUGIN_NAME, 'progress': data, 'completed_lessons': completed}
    if tool_name in {'tutorial_record_progress', 'tutorial_mark_lesson_complete'}:
        if not lesson_id:
            return {'success': False, 'plugin': PLUGIN_NAME, 'error': 'lesson_id is required'}
        status = 'completed' if tool_name == 'tutorial_mark_lesson_complete' else str(args.get('status') or 'in_progress')
        lessons[lesson_id] = {'status': status}
        events.append({'lesson_id': lesson_id, 'status': status})
        _write_progress(data)
        return {'success': True, 'plugin': PLUGIN_NAME, 'lesson_id': lesson_id, 'status': status}
    completed = {k for k, v in lessons.items() if v.get('status') == 'completed'}
    recommendations = ['profile-basics', 'tools-overview', 'write-safety']
    review = [item for item in recommendations if item not in completed]
    return {'success': True, 'plugin': PLUGIN_NAME, 'recommend_review': review or ['mastery-capstones']}


def _handle_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        return {'success': False, 'plugin': PLUGIN_NAME, 'error': 'args must be an object'}
    data = _load_data()
    query = str(args.get('query') or args.get('term') or args.get('topic') or args.get('action') or args.get('prompt') or args.get('answer') or '').strip()
    if tool_name.startswith('tutorial_') and 'progress' in tool_name or tool_name == 'tutorial_mark_lesson_complete':
        return _handle_progress(tool_name, args)
    if tool_name in {'tutorial_get_path'}:
        return {'success': True, 'plugin': PLUGIN_NAME, 'path': _level_path(args.get('level')), 'official_sources': data.get('official_sources', [])}
    if tool_name in {'tutorial_next_lesson'}:
        current = str(args.get('current_lesson_id') or args.get('lesson_id') or '').strip()
        curriculum = data.get('curriculum') or data.get('lessons', [])
        ids = [node.get('id') for node in curriculum if node.get('id')]
        next_id = ids[0] if not current or current not in ids else (ids[(ids.index(current) + 1) % len(ids)] if ids else None)
        return {'success': True, 'plugin': PLUGIN_NAME, 'current_lesson_id': current or None, 'next_lesson_id': next_id, 'next_lesson': next((n for n in curriculum if n.get('id') == next_id), None)}
    if tool_name in {'tutorial_explain_concept', 'explain_hermes_term'}:
        return {'success': True, 'plugin': PLUGIN_NAME, **_explain_term(query)}
    if 'risk' in tool_name or 'safe' in tool_name or 'write_surface' in tool_name:
        risk = _classify_risk(query)
        return {'success': True, 'plugin': PLUGIN_NAME, 'input': query, **risk}
    if tool_name == 'tutorial_check_install':
        return {'success': True, 'plugin': PLUGIN_NAME, 'hermes_on_path': bool(shutil.which('hermes')), 'next_step': 'Run `hermes doctor` and `hermes setup` if Hermes is not configured.'}
    if tool_name == 'tutorial_check_provider':
        providers = ['OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'XAI_API_KEY']
        configured = [name for name in providers if os.environ.get(name)]
        return {'success': True, 'plugin': PLUGIN_NAME, 'configured_env_present': configured, 'secret_values_hidden': True, 'next_step': 'Use `hermes model` or `hermes auth` for provider setup.'}
    if tool_name == 'tutorial_explain_schedule':
        schedule = query or str(args.get('schedule') or '')
        kind = 'cron expression' if len(schedule.split()) == 5 else ('duration/every phrase' if schedule else 'unknown')
        return {'success': True, 'plugin': PLUGIN_NAME, 'schedule': schedule, 'kind': kind, 'note': 'Cron jobs need self-contained prompts and explicit delivery targets.'}
    if tool_name == 'tutorial_make_safe_cron_example':
        return {'success': True, 'plugin': PLUGIN_NAME, 'example': {'schedule': 'every 2h', 'prompt': 'Check the official status page and summarize only new incidents. Do not modify files or credentials.', 'deliver': 'local'}, 'tui_caveat': 'In TUI sessions, local-only cron output is saved but not live-delivered back into the TUI.'}
    if tool_name == 'tutorial_validate_cron_prompt':
        prompt = query
        has_scope = any(word in prompt.lower() for word in ['do not', 'only', 'summarize', 'check'])
        return {'success': True, 'plugin': PLUGIN_NAME, 'valid': bool(prompt and has_scope), 'checks': {'self_contained_hint': bool(prompt), 'scope_boundary_hint': has_scope}}
    if 'quiz' in tool_name:
        return {'success': True, 'plugin': PLUGIN_NAME, 'questions': data.get('quiz', [])[:3]}
    if 'grade' in tool_name or 'evaluate' in tool_name or 'score' in tool_name:
        expected = data.get('assessment_keywords', ['profile', 'skill', 'plugin', 'safety', 'validation'])
        return {'success': True, 'plugin': PLUGIN_NAME, **_score_text(query, expected)}
    if 'rewrite_prompt' in tool_name:
        return {'success': True, 'plugin': PLUGIN_NAME, 'rewritten_prompt': f'Objective: {query or "state the task"}. Context: include relevant paths and constraints. Write scope: list allowed and prohibited surfaces. Validation: define objective proof of success.'}
    if 'extract_prompt_scope' in tool_name:
        return {'success': True, 'plugin': PLUGIN_NAME, 'scope': {'objective': query[:160], 'write_scope_required': any(w in query.lower() for w in ['write', 'edit', 'create', 'delete', 'commit', 'push']), 'needs_validation': True}}
    if 'detect_jargon' in tool_name:
        jargon = [term for term in data.get('glossary', {}) if term in query.lower()]
        return {'success': True, 'plugin': PLUGIN_NAME, 'jargon_terms': jargon, 'recommendation': 'Define each term before using it in a procedure.'}
    if 'simplify' in tool_name:
        return {'success': True, 'plugin': PLUGIN_NAME, 'simplified': query or data.get('lesson', ''), 'plain_language_rule': 'Use short steps, define jargon, and check confidence.'}
    if 'docs' in tool_name or 'stale' in tool_name:
        url = str(args.get('url') or query)
        official = url.startswith('https://hermes-agent.nousresearch.com/docs') if url else False
        return {'success': True, 'plugin': PLUGIN_NAME, 'url': url or None, 'official_docs_link': official, 'note': 'Official Hermes docs and live CLI output are the source of truth.'}
    if 'manifest' in tool_name:
        text = str(args.get('manifest_text') or query)
        has_required = all(token in text for token in ['name', 'plugin.yaml']) or all(token in text for token in ['name:', 'kind:'])
        return {'success': True, 'plugin': PLUGIN_NAME, 'looks_like_plugin_manifest': has_required, 'required_fields': ['name', 'kind', 'version', 'description', 'provides_tools', 'requires_env']}
    if 'skill_shape' in tool_name:
        text = str(args.get('skill_text') or query)
        return {'success': True, 'plugin': PLUGIN_NAME, 'has_frontmatter': text.strip().startswith('---'), 'recommended_fields': ['name', 'description', 'version', 'author', 'license']}
    matches = _find_matches(data, query)
    return {
        'success': True,
        'plugin': PLUGIN_NAME,
        'tool': tool_name,
        'query': query or None,
        'summary': data.get('lesson'),
        'lessons': data.get('lessons', [])[:5],
        'matches': matches,
        'official_sources': data.get('official_sources', [])[:5],
        'safety_note': data.get('safety_note'),
    }


def _tool_handler(tool_name: str):
    def handler(args: dict | None = None, **kwargs: Any) -> str:
        try:
            return _json(_handle_tool(tool_name, args if isinstance(args, dict) else {'__bad_args__': args} if args is not None else {}))
        except Exception as exc:
            return _error(str(exc), tool=tool_name)
    return handler


def _format_command(command: str, raw_args: str = '') -> str:
    data = _load_data()
    arg = (raw_args or '').strip()
    if command in {'progress', 'review', 'resume-tutorial'}:
        progress = _read_progress()
        completed = sorted(k for k, v in progress.get('lessons', {}).items() if v.get('status') == 'completed')
        return f"{data['description']}\nCompleted lessons: {', '.join(completed) if completed else 'none yet'}\nNext: use the tutorial compass or mark a lesson complete."
    if command == 'tutorial' and arg in {'next', 'map', 'reset'}:
        if arg == 'reset':
            path = _progress_path()
            if path.exists():
                path.unlink()
            return 'Tutorial runtime progress reset for this profile.'
        payload = _handle_tool('tutorial_next_lesson' if arg == 'next' else 'tutorial_get_path', {})
        return json.dumps(payload, indent=2, ensure_ascii=False)
    lines = [data['description']]
    if arg:
        lines.append(f'Focus: {arg}')
    lines.append('Lessons:')
    for lesson in data.get('lessons', [])[:5]:
        lines.append(f"- {lesson.get('id')}: {lesson.get('title')} — {lesson.get('summary')}")
    lines.append('Safety: ' + data.get('safety_note', 'Use official docs and live CLI output to verify.'))
    return '\n'.join(lines)


def _command_handler(command: str):
    def handler(raw_args: str = '') -> str:
        try:
            return _format_command(command, raw_args)
        except Exception as exc:
            return f'{PLUGIN_NAME} command error: {exc}'
    return handler


def _schema(tool_name: str, description: str) -> dict[str, Any]:
    return {
        'name': tool_name,
        'description': description,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Concept, question, answer, or user text to evaluate.'},
                'term': {'type': 'string', 'description': 'Hermes term to explain.'},
                'topic': {'type': 'string', 'description': 'Lesson, recipe, platform, tool, or concept topic.'},
                'level': {'type': 'string', 'description': 'Learning level such as 0, 1, 2, 3, 4, beginner, intermediate, advanced, or mastery.'},
                'lesson_id': {'type': 'string', 'description': 'Tutorial lesson identifier.'},
                'status': {'type': 'string', 'description': 'Progress status such as in_progress, completed, blocked, or review.'},
                'action': {'type': 'string', 'description': 'Hermes action or write surface to classify for safety.'},
                'prompt': {'type': 'string', 'description': 'Prompt text to inspect, rewrite, or validate.'},
                'answer': {'type': 'string', 'description': 'Learner answer or capstone response to grade.'},
                'schedule': {'type': 'string', 'description': 'Cron schedule or human interval phrase.'},
                'url': {'type': 'string', 'description': 'Official documentation URL to check.'},
                'manifest_text': {'type': 'string', 'description': 'Plugin manifest text to review.'},
                'skill_text': {'type': 'string', 'description': 'Skill markdown text to review.'},
            },
            'additionalProperties': False,
        },
    }


def register(ctx) -> None:
    data = _load_data()
    for tool in data.get('tools', []):
        ctx.register_tool(
            name=tool,
            toolset=TOOLSET,
            schema=_schema(tool, data.get('tool_descriptions', {}).get(tool, data['description'])),
            handler=_tool_handler(tool),
        )
    for command in data.get('commands', []):
        ctx.register_command(command, _command_handler(command), description=data['description'], args_hint='[topic|subcommand]')
    for skill in data.get('skills', []):
        skill_path = PLUGIN_DIR / 'skills' / skill / 'SKILL.md'
        ctx.register_skill(skill, skill_path, data['description'])
