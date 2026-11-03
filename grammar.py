# Small JSON grammar for initial testing
JSON_GRAMMAR = {
    "<start>": ["<value>"],

    "<value>": [
        "null",
        "true",
        "false",
        "<number>",
        "<string>",
        "<array>",
        "<object>"
    ],

    "<number>": ["0", "1", "-1", "42"],
    "<string>": ['""', '"hello"', '"example"'],

    "<array>": [
        "[]",
        "[<value>]",
        "[<value>,<value>]"
    ],

    "<object>": [
        "{}",
        '{"a":<value>}',
        '{"a":<value>,"b":<value>}'
    ]
}
