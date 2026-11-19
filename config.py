
from enum import Enum

import json5
import tomllib

from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzer import HeuristicGrammarFuzzer
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR


class SUT(Enum):
    JSON5 = "json5"
    TOML = "toml"


SUT_CONFIG = {
    SUT.JSON5: (
        JSON5_GRAMMAR,
        json5.loads,
        "json5",
        "*/json5/parser.py"
    ),
    SUT.TOML: (
        TOML_GRAMMAR,
        tomllib.loads,
        "tomllib",
        "*/tomllib/_parser.py"
    )
}


class Strategy(Enum):
    BASELINE = "baseline"
    HEURISTIC = "heuristic"


STRATEGY_CLASSES = {
    Strategy.BASELINE: GrammarFuzzer,
    Strategy.HEURISTIC: HeuristicGrammarFuzzer
}


DEFAULT_SUT = SUT.JSON5
DEFAULT_STRATEGY = Strategy.BASELINE
MAX_TESTS = 200
MAX_NONTERMINALS = 30