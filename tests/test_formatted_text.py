from __future__ import annotations

from prompt_toolkit.formatted_text import (
    ANSI,
    HTML,
    FormattedText,
    PygmentsTokens,
    Template,
    merge_formatted_text,
    to_formatted_text,
)
from prompt_toolkit.formatted_text.utils import split_lines


def test_basic_html():
    html = HTML("<i>hello</i>")
    assert to_formatted_text(html) == [("class:i", "hello")]

    html = HTML("<i><b>hello</b></i>")
    assert to_formatted_text(html) == [("class:i,b", "hello")]

    html = HTML("<i><b>hello</b>world<strong>test</strong></i>after")
    assert to_formatted_text(html) == [
        ("class:i,b", "hello"),
        ("class:i", "world"),
        ("class:i,strong", "test"),
        ("", "after"),
    ]

    # It's important that `to_formatted_text` returns a `FormattedText`
    # instance. Otherwise, `print_formatted_text` won't recognize it and will
    # print a list literal instead.
    assert isinstance(to_formatted_text(html), FormattedText)


def test_html_with_fg_bg():
    html = HTML('<style bg="ansired">hello</style>')
    assert to_formatted_text(html) == [
        ("bg:ansired", "hello"),
    ]

    html = HTML('<style bg="ansired" fg="#ff0000">hello</style>')
    assert to_formatted_text(html) == [
        ("fg:#ff0000 bg:ansired", "hello"),
    ]

    html = HTML(
        '<style bg="ansired" fg="#ff0000">hello <world fg="ansiblue">world</world></style>'
    )
    assert to_formatted_text(html) == [
        ("fg:#ff0000 bg:ansired", "hello "),
        ("class:world fg:ansiblue bg:ansired", "world"),
    ]


def test_ansi_formatting():
    value = ANSI("\x1b[32mHe\x1b[45mllo")

    assert to_formatted_text(value) == [
        ("ansigreen", "H"),
        ("ansigreen", "e"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "o"),
    ]

    # Bold and italic.
    value = ANSI("\x1b[1mhe\x1b[0mllo")

    assert to_formatted_text(value) == [
        ("bold", "h"),
        ("bold", "e"),
        ("", "l"),
        ("", "l"),
        ("", "o"),
    ]

    # Zero width escapes.
    value = ANSI("ab\001cd\002ef")

    assert to_formatted_text(value) == [
        ("", "a"),
        ("", "b"),
        ("[ZeroWidthEscape]", "cd"),
        ("", "e"),
        ("", "f"),
    ]

    assert isinstance(to_formatted_text(value), FormattedText)


def test_ansi_dim():
    # Test dim formatting
    value = ANSI("\x1b[2mhello\x1b[0m")

    assert to_formatted_text(value) == [
        ("dim", "h"),
        ("dim", "e"),
        ("dim", "l"),
        ("dim", "l"),
        ("dim", "o"),
    ]

    # Test dim with other attributes
    value = ANSI("\x1b[1;2;31mhello\x1b[0m")

    assert to_formatted_text(value) == [
        ("ansired bold dim", "h"),
        ("ansired bold dim", "e"),
        ("ansired bold dim", "l"),
        ("ansired bold dim", "l"),
        ("ansired bold dim", "o"),
    ]

    # Test dim reset with code 22
    value = ANSI("\x1b[1;2mhello\x1b[22mworld\x1b[0m")

    assert to_formatted_text(value) == [
        ("bold dim", "h"),
        ("bold dim", "e"),
        ("bold dim", "l"),
        ("bold dim", "l"),
        ("bold dim", "o"),
        ("", "w"),
        ("", "o"),
        ("", "r"),
        ("", "l"),
        ("", "d"),
    ]


def test_ansi_256_color():
    assert to_formatted_text(ANSI("\x1b[38;5;124mtest")) == [
        ("#af0000", "t"),
        ("#af0000", "e"),
        ("#af0000", "s"),
        ("#af0000", "t"),
    ]


def test_ansi_true_color():
    assert to_formatted_text(ANSI("\033[38;2;144;238;144m$\033[0;39;49m ")) == [
        ("#90ee90", "$"),
        ("ansidefault bg:ansidefault", " "),
    ]


def test_ansi_interpolation():
    # %-style interpolation.
    value = ANSI("\x1b[1m%s\x1b[0m") % "hello\x1b"
    assert to_formatted_text(value) == [
        ("bold", "h"),
        ("bold", "e"),
        ("bold", "l"),
        ("bold", "l"),
        ("bold", "o"),
        ("bold", "?"),
    ]

    value = ANSI("\x1b[1m%s\x1b[0m") % ("\x1bhello",)
    assert to_formatted_text(value) == [
        ("bold", "?"),
        ("bold", "h"),
        ("bold", "e"),
        ("bold", "l"),
        ("bold", "l"),
        ("bold", "o"),
    ]

    value = ANSI("\x1b[32m%s\x1b[45m%s") % ("He", "\x1bllo")
    assert to_formatted_text(value) == [
        ("ansigreen", "H"),
        ("ansigreen", "e"),
        ("ansigreen bg:ansimagenta", "?"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "o"),
    ]

    # Format function.
    value = ANSI("\x1b[32m{0}\x1b[45m{1}").format("He\x1b", "llo")
    assert to_formatted_text(value) == [
        ("ansigreen", "H"),
        ("ansigreen", "e"),
        ("ansigreen", "?"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "o"),
    ]

    value = ANSI("\x1b[32m{a}\x1b[45m{b}").format(a="\x1bHe", b="llo")
    assert to_formatted_text(value) == [
        ("ansigreen", "?"),
        ("ansigreen", "H"),
        ("ansigreen", "e"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "l"),
        ("ansigreen bg:ansimagenta", "o"),
    ]

    value = ANSI("\x1b[32m{:02d}\x1b[45m{:.3f}").format(3, 3.14159)
    assert to_formatted_text(value) == [
        ("ansigreen", "0"),
        ("ansigreen", "3"),
        ("ansigreen bg:ansimagenta", "3"),
        ("ansigreen bg:ansimagenta", "."),
        ("ansigreen bg:ansimagenta", "1"),
        ("ansigreen bg:ansimagenta", "4"),
        ("ansigreen bg:ansimagenta", "2"),
    ]


def test_interpolation():
    value = Template(" {} ").format(HTML("<b>hello</b>"))

    assert to_formatted_text(value) == [
        ("", " "),
        ("class:b", "hello"),
        ("", " "),
    ]

    value = Template("a{}b{}c").format(HTML("<b>hello</b>"), "world")

    assert to_formatted_text(value) == [
        ("", "a"),
        ("class:b", "hello"),
        ("", "b"),
        ("", "world"),
        ("", "c"),
    ]


def test_html_interpolation():
    # %-style interpolation.
    value = HTML("<b>%s</b>") % "&hello"
    assert to_formatted_text(value) == [("class:b", "&hello")]

    value = HTML("<b>%s</b>") % ("<hello>",)
    assert to_formatted_text(value) == [("class:b", "<hello>")]

    value = HTML("<b>%s</b><u>%s</u>") % ("<hello>", "</world>")
    assert to_formatted_text(value) == [("class:b", "<hello>"), ("class:u", "</world>")]

    # Format function.
    value = HTML("<b>{0}</b><u>{1}</u>").format("'hello'", '"world"')
    assert to_formatted_text(value) == [("class:b", "'hello'"), ("class:u", '"world"')]

    value = HTML("<b>{a}</b><u>{b}</u>").format(a="hello", b="world")
    assert to_formatted_text(value) == [("class:b", "hello"), ("class:u", "world")]

    value = HTML("<b>{:02d}</b><u>{:.3f}</u>").format(3, 3.14159)
    assert to_formatted_text(value) == [("class:b", "03"), ("class:u", "3.142")]


def test_merge_formatted_text():
    html1 = HTML("<u>hello</u>")
    html2 = HTML("<b>world</b>")
    result = merge_formatted_text([html1, html2])

    assert to_formatted_text(result) == [
        ("class:u", "hello"),
        ("class:b", "world"),
    ]


def test_pygments_tokens():
    text = [
        (("A", "B"), "hello"),  # Token.A.B
        (("C", "D", "E"), "hello"),  # Token.C.D.E
        ((), "world"),  # Token
    ]

    assert to_formatted_text(PygmentsTokens(text)) == [
        ("class:pygments.a.b", "hello"),
        ("class:pygments.c.d.e", "hello"),
        ("class:pygments", "world"),
    ]


def test_split_lines():
    lines = list(split_lines([("class:a", "line1\nline2\nline3")]))

    assert lines == [
        [("class:a", "line1")],
        [("class:a", "line2")],
        [("class:a", "line3")],
    ]


def test_split_lines_2():
    lines = list(
        split_lines([("class:a", "line1"), ("class:b", "line2\nline3\nline4")])
    )

    assert lines == [
        [("class:a", "line1"), ("class:b", "line2")],
        [("class:b", "line3")],
        [("class:b", "line4")],
    ]


def test_split_lines_3():
    "Edge cases: inputs ending with newlines."
    # -1-
    lines = list(split_lines([("class:a", "line1\nline2\n")]))

    assert lines == [
        [("class:a", "line1")],
        [("class:a", "line2")],
        [("class:a", "")],
    ]

    # -2-
    lines = list(split_lines([("class:a", "\n")]))

    assert lines == [
        [("class:a", "")],
        [("class:a", "")],
    ]

    # -3-
    lines = list(split_lines([("class:a", "")]))

    assert lines == [
        [("class:a", "")],
    ]


def test_split_lines_4():
    "Edge cases: inputs starting and ending with newlines."
    # -1-
    lines = list(split_lines([("class:a", "\nline1\n")]))

    assert lines == [
        [("class:a", "")],
        [("class:a", "line1")],
        [("class:a", "")],
    ]
