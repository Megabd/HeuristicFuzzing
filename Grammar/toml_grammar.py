"""TOML 1.0 valid-input-oriented Fuzzing Book grammar.

Reference: https://toml.io/en/v1.0.0

This deliberately constructs distinct key paths in multi-entry documents to
avoid accidental duplicate-key or table-redefinition errors. Values are
recursive and allow *mixed-type arrays*, as TOML expressly requires.

This is a representative testing grammar, NOT a complete TOML definition:
full Unicode keys, arbitrary validated dates/times, all integer magnitudes,
and unrestricted document-level table relationships need additional handling.
Some valid outputs may be rejected by the third-party `toml` package; check
those against `tomllib` before labeling them invalid TOML.
"""

TOML_GRAMMAR = {
    "<start>": ["<document>"],
    "<document>": [
        "",  # Empty TOML document is valid.
        "<entry-a>",
        "<front-comment><entry-a>",
        "<entry-a><entry-b>",
        "<entry-a>\n<entry-b>",
        "<entry-a>[section]\n<entry-b>",
        "[section]\n<entry-a>",
        "[section.sub]\n<entry-a>",
        "<entry-a>[section]\n<entry-b>[other]\n<entry-a>",
        "[[entries]]\n<entry-a>",
        "[[entries]]\n<entry-a>[[entries]]\n<entry-a>",
        "[section]\n<entry-a>[section.sub]\n<entry-b>",
        "<front-comment>[section]\n<entry-a>",
    ],
    "<front-comment>": ["# comment\n", "# first\n# second\n", "\n", "\n# comment\n"],
    "<entry-a>": ["<key-a><around-equals>=<around-equals><value><endline>"],
    "<entry-b>": ["<key-b><around-equals>=<around-equals><value><endline>"],
    "<key-a>": ["alpha<tail>", '"alpha <key-text>"', "'alpha <key-text>'", "alpha.inner<tail>"],
    "<key-b>": ["beta<tail>", '"beta <key-text>"', "'beta <key-text>'", "beta.inner<tail>"],
    "<tail>": ["", "<key-char><tail>"],
    "<key-char>": list("aA09_-"),
    "<key-text>": ["x", "Z", "9", "name", "é", "hello world"],
    "<around-equals>": ["", " ", "  ", "\t"],
    "<endline>": ["\n", " # comment\n", "\n\n", "\r\n"],

    "<value>": [
        "<string>", "<integer>", "<floating-point>", "<boolean>",
        "<date-time>", "<array>", "<inline-table>",
    ],
    "<boolean>": ["true", "false"],
    "<array>": [
        "[]", "[<values>]", "[<values>,]",
        "[\n<values>\n]", "[\n <value>, # comment\n <value>\n]",
    ],
    "<values>": ["<value>", "<value>, <values>"],
    "<inline-table>": [
        "{}", "{a = <value>}", "{a = <value>, b = <value>}",
        "{a = <value>, b = <value>, c = <value>}",
        "{a.inner = <value>, b = <value>}",
    ],

    "<string>": [
        '"<basic-chars>"', "'<literal-chars>'",
        '"""<multi-basic-chars>"""', "'''<multi-literal-chars>'''",
    ],
    "<basic-chars>": ["", "<basic-char><basic-chars>"],
    "<basic-char>": ["<safe-char>", "'", "<escape>"],
    "<literal-chars>": ["", "<literal-char><literal-chars>"],
    "<literal-char>": ["<safe-char>", '"', "\\"],
    "<multi-basic-chars>": ["", "<basic-char><multi-basic-chars>", "\n<multi-basic-chars>"],
    "<multi-literal-chars>": ["", "<literal-char><multi-literal-chars>", "\n<multi-literal-chars>"],
    "<safe-char>": ["a", "b", "c", "Z", "7", "9", " ", "_", "-", "!", "#", "é", "中"],
    "<escape>": [
        "\\\\", "\\\"", "\\b", "\\t", "\\n", "\\f", "\\r", "\\u0041", "\\u00E9", "\\U0001F3BC",
    ],

    # Bound digit lengths to avoid generating TOML integers outside signed int64.
    "<integer>": [
        "<sign><small-decimal>", "0x<small-hex>", "0o<small-octal>",
        "0b<small-binary>", "9223372036854775807", "-9223372036854775808",
    ],
    "<sign>": ["", "+", "-"],
    "<small-decimal>": ["0", "<nonzero><short-digits>"],
    "<short-digits>": ["", "<digit>", "<digit><digit>", "<digit>_<digit>", "<digit><digit><digit>"],
    "<digit>": list("0123456789"),
    "<nonzero>": list("123456789"),
    "<small-hex>": ["<hex>", "<hex><hex>", "<hex>_<hex>", "<hex><hex><hex>"],
    "<hex>": list("0123456789abcdefABCDEF"),
    "<small-octal>": ["<oct>", "<oct><oct>", "<oct>_<oct>", "<oct><oct><oct>"],
    "<oct>": list("01234567"),
    "<small-binary>": ["<bit>", "<bit><bit>", "<bit>_<bit>", "<bit><bit><bit>"],
    "<bit>": ["0", "1"],
    "<floating-point>": [
        "<sign><small-decimal>.<positive-digits>",
        "<sign><small-decimal><exponent>",
        "<sign><small-decimal>.<positive-digits><exponent>",
        "<sign>inf", "<sign>nan",
    ],
    "<positive-digits>": ["<digit>", "<digit><digit>", "<digit>_<digit>"],
    "<exponent>": ["e<sign><positive-digits>", "E<sign><positive-digits>"],

    # Calendar-valid representatives (rather than unconstrained MM/DD digits).
    "<date-time>": [
        "<date>", "<time>", "<date>T<time>",
        "<date>T<time>Z", "<date>t<time>+02:00", "<date> <time>-05:30",
    ],
    "<date>": ["1979-05-27", "2024-02-29", "2000-01-01", "9999-12-31"],
    "<time>": ["00:00:00", "12:34:56", "23:59:59.999999"],
}

GRAMMAR = TOML_GRAMMAR
