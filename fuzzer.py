from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from grammar import JSON_GRAMMAR

def baseLineFuzz():
    return GrammarFuzzer(JSON_GRAMMAR, max_nonterminals=10).fuzz()