
from enum import Enum

import json5
import tomllib

from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzer import HeuristicGrammarFuzzer
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR
from deepdiff import DeepHash


class SUT(Enum):
    JSON5 = "json5"
    TOML = "toml"
    DEEPHASH = "deephash"

def deephash_sut(source):
    data = json5.loads(source)
    return DeepHash(data)

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
    ),
    SUT.DEEPHASH: (
    JSON5_GRAMMAR,
    deephash_sut,
    "deepdiff",
    "*/deepdiff/deephash.py"
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
MAX_TESTS = 5000
MAX_NONTERMINALS = 50