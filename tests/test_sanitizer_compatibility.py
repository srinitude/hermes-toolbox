"""Compatibility boundaries for sanitizer markup and shell documentation."""
from __future__ import annotations

from tests.test_semantic_security_boundaries import SemanticCase


class MarkupCompatibilityTests(SemanticCase):
    def test_placeholder_named_markup_and_comparisons_are_valid(self):
        text = ('<private-term-widget data-x="1">ok</private-term-widget>\n'
                '<private-term data-x="1">ok</private-term>\n'
                '<repo-author-email@example.com>\n'
                '<path/>\n<path />\n<path\n d="M0 0"/>\n'
                '<path:node xmlns:path="urn:example"/>\n'
                'const icon = <path {...props} />;\n'
                'const filled = <path {...props} fill="red" />;\n'
                'const clickable = <path onClick={() => draw()} />;\n'
                '<private-term\n hidden>ok</private-term>\n'
                '<path onclick="if (a > b) x()">x</path>\n'
                'std::vector<path*> values;\n'
                'std::vector<path const*> const_values;\n'
                'std::pair<path, int> value;\n'
                'std::vector<std::vector<path>> matrix;\n'
                'std::vector<Path> paths;\n'
                'std::variant<int, Skill> value;\n'
                'using X = Meta<ns::path>;\n'
                'std::vector <Path> spaced_paths;\n'
                'std::vector<Profile<int>> profiles;\n'
                'std::is_same<path &&, path&&> same;\n'
                'static_assert(std::is_same<path const&, path const&>::value);\n'
                'template<class... path> using paths = std::tuple<path...>;\n'
                'int f(int x, int path) { if (x<path) return 1; return 0; }\n'
                'template <typename path> struct Holder;\n'
                'template <class name> struct Label;\n'
                'if (repo-author-email>limit) return true;\n'
                'pattern: "private-term>"\n')
        self.assertEqual(self.errors(text), [])


class CppArrayCompatibilityTests(SemanticCase):
    def test_compact_array_reference_template_type_is_valid(self):
        text = 'std::is_same<path(&)[3], path(&)[3]> value;\n'
        self.assertEqual(self.errors(text), [])

    def test_array_reference_template_type_is_valid(self):
        text = 'std::is_same<path const(&)[3], path const(&)[3]> value;\n'
        self.assertEqual(self.errors(text), [])

    def test_array_template_type_is_valid(self):
        self.assertEqual(self.errors('box<path[]> value;\n'), [])


class CppComparisonCompatibilityTests(SemanticCase):
    def test_return_ternary_comparison_is_valid(self):
        text = 'int f(int x, int path) { return x<path ? 1 : 0; }\n'
        self.assertEqual(self.errors(text), [])


class JsxCompatibilityTests(SemanticCase):
    def test_components_nested_content_and_block_arrows_are_valid(self):
        text = ('const view = <Profile>content</Profile>;\n'
                'const icon = <Path.Icon data-x="1" />;\n'
                'const body = <Path>{ok ? <Skill /> : null}</Path>;\n'
                'const click = <Path onClick={() => { draw(); }} />;\n'
                'const nested = <Path data={{a: {b: 1}}} />;\n'
                'const lower = <path.icon data-x="1" />;\n'
                'const template = <Path data={`x${value} }`} />;\n'
                'const escaped = <Path data={`x\\` ${value}`} />;\n')
        self.assertEqual(self.errors(text), [])


class CppCompatibilityTests(SemanticCase):
    def test_compact_comparisons_and_spaced_rvalue_reference_are_valid(self):
        text = ('std::is_reference<path &&> value;\n'
                'for (int i = 0; i<path; ++i) { use(i); }\n'
                'return size<path;\n'
                'assert(size<path);\n'
                'bool low = size<path;\n'
                'template<class T> struct vector {}; struct Path {}; vector <Path> values;\n'
                'using F = std::function<Path(int)>;\n'
                'struct path {}; std::vector<path volatile*> values;\n')
        self.assertEqual(self.errors(text), [])


class MarkupRejectionTests(SemanticCase):
    def test_quoted_empty_author_placeholder_is_rejected(self):
        self.assertTrue(any('malformed placeholder' in error
                            for error in self.errors('author: "<>"\n')))


class ShellCompatibilityTests(SemanticCase):
    def test_near_miss_executable_name_is_valid(self):
        harmless = ' '.join(f'$V{i}' for i in range(10))
        text = ('$HOME/venv/bin/python-config --help\n'
                '${HOME+safe}/bin/python --help\n'
                '${HOME:+safe}/bin/python --help\n'
                '$HOME/venv/bin/python. --help\n'
                'printf "%s\\n" "$HOME"; stamp=$(date +%s)\n'
                '<https://example.com/$HOME/bin/python>\n'
                'https://example.com/?x=1&next=$HOME/bin/python\n'
                'https://example.com/path;next=$HOME/bin/python\n'
                'See https://example.com/?x=1&next=$HOME/bin/python\n'
                "$(printf '%b%s' '\\c' '<path>')/bin/python\n"
                "$(printf '%b' '\\')\n"
                r"$(printf '\UFFFFFFFF')" '\n'
                'curl "https://example.com;$HOME/bin/python task.py"\n'
                '[docs](https://example.com/$HOME/bin/python)\n'
                '[docs](https://example.com/?x=1&next=$HOME/bin/python)\n'
                '[docs](https://example.com/path;next=$HOME/bin/python)\n'
                '<a href=https://example.com/$HOME/bin/python>docs</a>\n'
                '<widget data-url=https://example.com/$HOME/bin/python>docs</widget>\n'
                '<a href="https://example.com/$HOME/bin/python">docs</a>\n'
                '<a href=$HOME/bin/python>local docs</a>\n'
                '<x-demo data-path="$HOME/bin/python">x</x-demo>\n'
                r'Run $HOME/bin/py\?hon task.py' '\n'
                r'Run $HOME/bin/py\[t]hon task.py' '\n'
                'Run "~/.hermes/hermes-agent/venv/bin/python" task.py\n'
                r'Run \~/.hermes/hermes-agent/venv/bin/python task.py' '\n'
                f'$HOME/docs {harmless}\n')
        self.assertEqual(self.errors(text), [])


class MarkdownShellBoundaryTests(SemanticCase):
    def test_adjacent_code_spans_are_not_a_shell_path(self):
        text = 'Use `-p <profile>`/`HERMES_HOME` explicitly.\n'
        self.assertEqual(self.errors(text), [])


class ShellBraceCompatibilityTests(SemanticCase):
    def test_literal_and_oversized_brace_ranges_do_not_crash(self):
        mixed = 'Run $HOME/bin/{a..1}\n'
        huge = 'Run $HOME/bin/{1..' + ('9' * 5000) + '}\n'
        harmless = 'Run $HOME/docs/{' + ','.join(f'tool{i}' for i in range(65)) + '}\n'
        numeric = 'Run $HOME/bin/{1..65}\n'
        product = 'Run $HOME/bin/{a,b,c,d,e,f,g,h,i}{j,k,l,m,n,o,p,q,r}\n'
        self.assertEqual(self.errors(mixed), [])
        self.assertEqual(self.errors(harmless), [])
        self.assertEqual(self.errors(numeric), [])
        self.assertEqual(self.errors(product), [])
        self.assertEqual(self.errors('printf %s docs~/bin/python\n'), [])
        literals = ("printf %s '$HOME/bin/python'\n"
                    'printf %s \\$HOME/bin/python\n'
                    'printf %s "$HOME/bin/{python,node}"\n')
        self.assertEqual(self.errors(literals), [])
        self.assertTrue(any('executable path' in error
                            for error in self.errors(huge)))
