from collections import defaultdict
from fuzzingbook.GrammarFuzzer import GrammarFuzzer
from fuzzingbook.Grammars import trim_grammar
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR

import random

class HeuristicGrammarFuzzer(GrammarFuzzer):
    
    def __init__(self, grammar, *args, **kwargs):
        super().__init__(grammar, *args, **kwargs)
        self.production_counts = defaultdict(int)

    def expand_node_randomly(self, node):
        symbol, _ = node
        productions = self.grammar[symbol]

        # Calculate inverse-frequency weights
        weights = []

        for production in productions:
            count = self.production_counts[(symbol, production)]
            weights.append(1 / (1 + count))

        # Select production using weighted probability
        selected = random.choices(
            range(len(productions)),
            weights=weights,
            k=1
        )[0]

        # Update frequency
        production = productions[selected]
        self.production_counts[(symbol, production)] += 1

        return self.choose_node_expansion(node, selected)

    def expand_node(self, node):
        if random.random() < 0.5:
            return self.expand_node_randomly(node)
        else:
            return self.expand_node_max_cost(node)


