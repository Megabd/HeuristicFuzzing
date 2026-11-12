
// Project note: adapted for heuristic-guided grammar fuzzing (November 2026).
// Source: https://github.com/antlr/grammars-v4/blob/master/json5/JSON5.g4
// Original contribution: Student Main (2020-07-22), public domain.
//
// Local changes following tests against the Python `json5` parser:
//
// 1. EXP: require at least one digit after e/E and optional sign,
//    changing [0-9]* to [0-9]+.
//    Inputs such as "0e+" and "-9.3e" were rejected.
//
// 2. ESCAPE_SEQUENCE: remove the standalone '0' alternative.
//    Generated strings containing \05 and \09 were rejected because
//    JSON5 does not permit a decimal digit immediately following \0.
//    This is a pragmatic simplification: valid JSON5 \0 escapes
//    are now excluded, too.
//
// Other aspects of the original grammar were not formally verified
// against the JSON5 specification; generated samples still require
// validation.


grammar JSON5;

json5
    : value? EOF
    ;

obj
    : '{' pair (',' pair)* ','? '}'
    | '{' '}'
    ;

pair
    : key ':' value
    ;

key
    : STRING
    | IDENTIFIER
    | LITERAL
    | NUMERIC_LITERAL
    ;

value
    : STRING
    | number
    | obj
    | arr
    | LITERAL
    ;

arr
    : '[' value (',' value)* ','? ']'
    | '[' ']'
    ;

number
    : SYMBOL? (NUMERIC_LITERAL | NUMBER)
    ;

// Lexer

SINGLE_LINE_COMMENT
    : '//' .*? (NEWLINE | EOF) -> skip
    ;

MULTI_LINE_COMMENT
    : '/*' .*? '*/' -> skip
    ;

LITERAL
    : 'true'
    | 'false'
    | 'null'
    ;

STRING
    : '"' DOUBLE_QUOTE_CHAR* '"'
    | '\'' SINGLE_QUOTE_CHAR* '\''
    ;

fragment DOUBLE_QUOTE_CHAR
    : ~["\\\r\n]
    | ESCAPE_SEQUENCE
    ;

fragment SINGLE_QUOTE_CHAR
    : ~['\\\r\n]
    | ESCAPE_SEQUENCE
    ;

fragment ESCAPE_SEQUENCE
    : '\\' (
        NEWLINE
        | UNICODE_SEQUENCE       // \u1234
        | ['"\\/bfnrtv]          // single escape char
        | ~['"\\bfnrtv0-9xu\r\n] // non escape char
        | 'x' HEX HEX            // \x3a
    )
    ;

NUMBER
    : INT ('.' [0-9]*)? EXP? // +1.e2, 1234, 1234.5
    | '.' [0-9]+ EXP?        // -.2e3
    | '0' [xX] HEX+          // 0x12345678
    ;

NUMERIC_LITERAL
    : 'Infinity'
    | 'NaN'
    ;

SYMBOL
    : '+'
    | '-'
    ;

fragment HEX
    : [0-9a-fA-F]
    ;

fragment INT
    : '0'
    | [1-9] [0-9]*
    ;

fragment EXP
    : [Ee] SYMBOL? [0-9]+
    ;

IDENTIFIER
    : IDENTIFIER_START IDENTIFIER_PART*
    ;

fragment IDENTIFIER_START
    : [\p{L}]
    | '$'
    | '_'
    | '\\' UNICODE_SEQUENCE
    ;

fragment IDENTIFIER_PART
    : IDENTIFIER_START
    | [\p{M}]
    | [\p{N}]
    | [\p{Pc}]
    | '\u200C'
    | '\u200D'
    ;

fragment UNICODE_SEQUENCE
    : 'u' HEX HEX HEX HEX
    ;

fragment NEWLINE
    : '\r\n'
    | [\r\n\u2028\u2029]
    ;

WS
    : [ \t\n\r\u00A0\uFEFF\u2003]+ -> skip
    ;