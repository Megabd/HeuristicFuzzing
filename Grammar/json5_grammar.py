"""JSON5 valid-input-oriented grammar for Fuzzing Book GrammarFuzzer.

Based on JSON5 language specification: https://spec.json5.org/
Designed for grammar-selection experiments, not a full formal implementation
of every Unicode character or all semantic lexer constraints.

Notably:
* Comments and whitespace are reachable from <start> and nested values.
* Hexadecimal with signs is legal JSON5; the Python `json5` SUT may reject
  negative hexadecimal input (an implementation limitation, not bad grammar).
* Raw string characters are restricted to a safe representative alphabet.
* A complete JSON5 language grammar would require additional Unicode coverage.
"""

JSON5_GRAMMAR = {
    "<start>": ["<value>"],

    # Each value can be surrounded by JSON5 whitespace and comments.
    "<value>": [
        "<gap>null<gap>", "<gap>true<gap>", "<gap>false<gap>",
        "<gap><number><gap>", "<gap><string><gap>",
        "<gap><array><gap>", "<gap><object><gap>",
    ],
    "<gap>": ["", " ", "\t", "\n", "\r\n", "\u00a0", "\u2028", "\u2029",
              "/* comment */", "/*multi\nline*/", "// comment\n", " <gap>"],

    "<array>": [
        "[<gap>]", "[<gap><elements><gap>]", "[<gap><elements><gap>,<gap>]",
    ],
    "<elements>": ["<value>", "<value><gap>,<elements>"],

    "<object>": [
        "{<gap>}", "{<gap><members><gap>}", "{<gap><members><gap>,<gap>}",
    ],
    "<members>": ["<key><gap>:<value>", "<key><gap>:<value><gap>,<members>"],
    "<key>": ["<string>", "<identifier>"],
    "<identifier>": [
        "name", "true", "false", "null", "Infinity", "NaN", "default",
        "<identifier-start><identifier-rest>",
    ],
    "<identifier-start>": ["a", "Z", "_", "$", "é", "Ω", "中", "\\u0061"],
    "<identifier-rest>": ["", "<identifier-char><identifier-rest>"],
    "<identifier-char>": [
        "a", "b", "Z", "9", "0", "_", "$", "é", "中", "\u200c", "\u200d"
    ],

    "<number>": [
        "<sign><decimal>", "<sign><hex-number>",
        "<sign>Infinity", "<sign>NaN",
    ],
    "<sign>": ["", "+", "-"],
    "<decimal>": [
        "<integer>", "<integer>.<digits>", "<integer>.",
        ".<positive-digits>", "<integer><exponent>",
        "<integer>.<digits><exponent>", ".<positive-digits><exponent>",
    ],
    "<integer>": ["0", "<nonzero><digits>"],
    "<digits>": ["", "<digit><digits>"],
    "<positive-digits>": ["<digit>", "<digit><positive-digits>"],
    "<digit>": list("0123456789"),
    "<nonzero>": list("123456789"),
    "<exponent>": ["e<sign><positive-digits>", "E<sign><positive-digits>"],
    "<hex-number>": ["0x<hex-digits>", "0X<hex-digits>"],
    "<hex-digits>": ["<hex>", "<hex><hex-digits>"],
    "<hex>": list("0123456789abcdefABCDEF"),

    "<string>": [
        '"<double-chars>"', "'<single-chars>'",
        # The \0 escape is only introduced at the end of a string to avoid \0[0-9].
        '"<double-chars>\\0"', "'<single-chars>\\0'",
    ],
    "<double-chars>": ["", "<double-char><double-chars>"],
    "<single-chars>": ["", "<single-char><single-chars>"],
    "<double-char>": ["<plain-char>", "'", "<double-escape>"],
    "<single-char>": ["<plain-char>", '"', "<single-escape>"],
    "<plain-char>": [chr(i) for i in range(32, 127) if chr(i) not in ('"', "'", "\\")] + ["é", "Ω", "中", "🎼"],
    "<double-escape>": [
        "\\\\", "\\\"", "\\'", "\\/", "\\n", "\\r", "\\t", "\\v", "\\b", "\\f",
        "\\x41", "\\xE9", "\\u0041", "\\u03A9", "\\uD83C\\uDFBC",
        "\\\n", "\\\r\n",
    ],
    "<single-escape>": [
        "\\\\", "\\'", "\\\"", "\\/", "\\n", "\\r", "\\t", "\\v", "\\b", "\\f",
        "\\x41", "\\xE9", "\\u0041", "\\u03A9", "\\uD83C\\uDFBC",
        "\\\n", "\\\r\n",
    ],
}

# FuzzingBook-compatible default name retained for callers that expect GRAMMAR.
GRAMMAR = JSON5_GRAMMAR
