
from enum import Enum

import json5
import tomlkit

from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzer import HeuristicGrammarFuzzerFrequency
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR
from toml_sort.tomlsort import TomlSort
from io import StringIO
from ruamel.yaml import YAML


class SUT(Enum):
    JSON5 = "json5"
    TOML = "toml"
    TOMLSORT = "tomlsort"
    YAML = "yaml"

def tomlsort_sut(source):
    return TomlSort(source).sorted()

yaml = YAML(typ="safe", pure=True)

def yaml_sut(source):
    data = json5.loads(source)
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()

SUT_CONFIG = {
    SUT.JSON5: (
        JSON5_GRAMMAR,
        json5.loads,
        "json5",
        "*/json5/parser.py"
    ),
    SUT.TOML: (
    TOML_GRAMMAR,
    tomlkit.loads,
    "tomlkit",
    "*/tomlkit/parser.py"
    ),
    SUT.TOMLSORT: (
    TOML_GRAMMAR,
    tomlsort_sut,
    "toml_sort",
    "*/toml_sort/tomlsort.py"),
    SUT.YAML: (
    JSON5_GRAMMAR,
    yaml_sut,
    "ruamel.yaml",
    [
        "*/ruamel/yaml/representer.py",
        "*/ruamel/yaml/serializer.py",
        "*/ruamel/yaml/emitter.py"
    ]
),
}


class Strategy(Enum):
    BASELINE = "baseline"
    HEURISTIC = "heuristic"


STRATEGY_CLASSES = {
    Strategy.BASELINE: GrammarFuzzer,
    Strategy.HEURISTIC: HeuristicGrammarFuzzerFrequency
}


DEFAULT_SUT = SUT.JSON5
DEFAULT_STRATEGY = Strategy.BASELINE
MAX_TESTS = 1000
MAX_NONTERMINALS = 30
MUTATION_RATE = 0.30
MAX_MUTATIONS = 3