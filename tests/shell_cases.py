"""Adversarial shell path cases shared by semantic boundary tests."""
from __future__ import annotations

PRINTF_VARIANTS = (
    '<path>/venv/bin/py$(printf thon)', '$HOME/bin/py$(printf $(printf thon))',
    "$(printf '<path>')/bin/python", "$(printf '<pa')$(printf 'th>')/bin/python",
    "`printf '<path>'`/bin/python", "$HOME/bin/py$(printf '%s' thon)",
    "$(printf '%s' '<pa' 'th>')/bin/python", "`printf '%s' '<pa' 'th>'`/bin/python",
    "$(printf -- '%s' '<path>')/bin/python", r"$(printf '%b' '<pa\x74h>')/bin/python",
    "$(printf '%10s' '<path>')/bin/python", "$(printf '%.6s' '<path>')/bin/python",
    r"$(printf '%b' '<pa\0164h>')/bin/python", "$HOME/bin/py`printf '%s' thon`",
    "$(printf '%c%s' '<' 'path>')/bin/python",
    r"$(printf '%b' '<pa\u0074h>')/bin/python",
    r"$(printf '<pa\x74h>')/bin/python",
    r"$(printf '%b' '\74path\76')/bin/python",
    r"$(printf '%b%s' '\\c' '<path>')/bin/python",
    r'$HOME/bin/{python,node}',
    r'$HOME/bin/py?hon',
    r'$HERMES_HOME/venv/bin/pyt[hz]on',
    r'$HOME/bin/{py,xx}{thon,node}',
    r'$HOME/bin/py[[:alpha:]]hon',
    r'$HOME/bin/{p,p}{y,y}{t,t}{h,h}{o,o}{n,n}',
    r'$HOME/bin/{x,{x,{x,{x,{py,zz}}}}}thon',
    r"$HOME/bin/$'python'",
    r'$HOME/bin/{p..p}ython',
    r'~/.hermes/hermes-agent/venv/bin/python',
    r"$(printf '%*s%s' 1 '<pa' 'th>')/bin/python",
    r"$(command printf '%s%s' '<pa' 'th>')/bin/python",
    r"$(builtin printf '%s%s' '<pa' 'th>')/bin/python",
    "$(printf '%s' '<path>')/bin/python",
)


def shell_variants() -> tuple[str, ...]:
    deep = '<path>'
    for index in range(18):
        deep = f'${{A{index}:-{deep}}}'
    truncated = ''.join('${EMPTY}' for _ in range(17)) + '${ROOT:-<path>}'
    split_root = ''.join(f'${{E{i}}}' for i in range(10)) + '${A:-<pa}${B:-th>}'
    return ('"$HERMES_HOME"/venv/bin/python',
            '$HERMES_HOME/venv/bin/"python"', '{<path>}/venv/bin/python',
            '${HOME:-fallback}/venv/bin/python',
            '${HERMES_HOME:?required}/venv/bin/python',
            '${HOME-fallback}/venv/bin/python', '${HOME:=fallback}/venv/bin/python',
            '${HOME%/}/venv/bin/python', '${HOME#prefix}/venv/bin/python',
            '$HOME/venv/bin/${PYTHON:-python}', '$HOME/venv/bin/py${EMPTY:-}thon',
            '$HOME/venv/bin/py${EMPTY}thon', '$HOME/venv/bin/py${EMPTY:+x}thon',
            '$HOME/venv/bin/py${EMPTY+x}thon',
            '${ROOT:-${FALLBACK:-<path>}}/venv/bin/python',
            '${ROOT[0]:-<path>}/venv/bin/python', '$HOME/bin/py"$EMPTY"thon',
            '$HOME/bin/${cmd%foo}', '`$HOME/bin/python`',
            '$HOME/bin/${cmd#foo}', '${A:+<path>}/bin/python',
            '$HOME/venv/bin/\\\npython',
            deep + '/venv/bin/python', truncated + '/venv/bin/python',
            split_root + '/venv/bin/python', '$HOME\\/venv/bin/python') + PRINTF_VARIANTS
