from collections import defaultdict

from fuzzingbook.GrammarFuzzer import GrammarFuzzer, all_terminals, nonterminals
from fuzzingbook.Grammars import trim_grammar
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR
import inspect
import random
from collections import defaultdict



def baseLineFuzz(isJson5 : bool):
    if isJson5:
        Grammar = trim_grammar(JSON5_GRAMMAR)
        return GrammarFuzzer(Grammar, start_symbol="<value>", max_nonterminals=10).fuzz()
    else:
        Grammar = trim_grammar(TOML_GRAMMAR)
        return GrammarFuzzer(Grammar, start_symbol="<start>", max_nonterminals=10).fuzz()

def heuristicFuzz(isJson5 : bool):
    if isJson5:
        Grammar = trim_grammar(JSON5_GRAMMAR)
        return HeuristicGrammarFuzzer(Grammar, start_symbol="<value>", heuristic_weights={"depth": 1.0}, max_nonterminals=30).fuzz()
    else:
        Grammar = trim_grammar(TOML_GRAMMAR)
        return HeuristicGrammarFuzzer(Grammar, start_symbol="<start>", max_nonterminals=10).fuzz()




class HeuristicGrammarFuzzer(GrammarFuzzer):

    MAX_HEURISTIC_DEPTH = 10

    def __init__(
        self,
        grammar,
        *args,
        heuristic_weights=None,
        selection="max",
        **kwargs
    ):
        super().__init__(grammar, *args, **kwargs)

        self.production_counts = defaultdict(int)

        # Default to depth-oriented expansion
        self.heuristic_weights = heuristic_weights or {
            "depth": 1.0
        }

        # "max" or "weighted"
        self.selection = selection

    def expand_node(self, node):
        return self.expand_node_by_heuristic(node)
    # --------------------------------------------------
    # Heuristic cost functions
    # --------------------------------------------------

    def symbol_depth_cost(self, symbol, depth=0):
        if depth >= self.MAX_HEURISTIC_DEPTH:
            return 0

        return max(
            self.expansion_depth_cost(e, depth + 1)
            for e in self.grammar[symbol]
        )

    def expansion_depth_cost(self, expansion, depth=0):
        symbols = nonterminals(expansion)

        if not symbols:
            return 1

        if depth >= self.MAX_HEURISTIC_DEPTH:
            return 0

        return 1 + max(
            self.symbol_depth_cost(s, depth)
            for s in symbols
        )

    def symbol_total_cost(self, symbol, depth=0):
        if depth >= self.MAX_HEURISTIC_DEPTH:
            return 0

        return max(
            self.expansion_total_cost(e, depth + 1)
            for e in self.grammar[symbol]
        )

    def expansion_total_cost(self, expansion, depth=0):
        symbols = nonterminals(expansion)

        if not symbols:
            return 1

        if depth >= self.MAX_HEURISTIC_DEPTH:
            return 0

        return 1 + sum(
            self.symbol_total_cost(s, depth)
            for s in symbols
        )

    def expansion_width_cost(self, expansion):
        return len(nonterminals(expansion))

    # --------------------------------------------------
    # Heuristic selection
    # --------------------------------------------------

    def calculate_heuristic_scores(self, expansions):

        heuristic_functions = {
            "depth": self.expansion_depth_cost,
            "total": self.expansion_total_cost,
            "width": self.expansion_width_cost
        }

        scores = [0.0] * len(expansions)

        for heuristic, weight in self.heuristic_weights.items():

            if heuristic not in heuristic_functions:
                raise ValueError(
                    f"Unknown heuristic: {heuristic}"
                )

            function = heuristic_functions[heuristic]

            raw_scores = [
                function(expansion)
                for expansion in expansions
            ]

            # Min-max normalization
            minimum = min(raw_scores)
            maximum = max(raw_scores)

            if maximum == minimum:
                normalized = [1.0] * len(raw_scores)
            else:
                normalized = [
                    (score - minimum) / (maximum - minimum)
                    for score in raw_scores
                ]

            for i, score in enumerate(normalized):
                scores[i] += weight * score

        return scores

    # --------------------------------------------------
    # Production selection
    # --------------------------------------------------

    def choose_node_expansion(
        self, node, children_alternatives, heuristic_scores=None
    ):
        symbol, _ = node
        weights = []

        for i, alternative in enumerate(children_alternatives):
            key = (symbol, repr(alternative))
            count = self.production_counts[key]

            weight = 1 / (1 + count)

            if heuristic_scores is not None:
                weight *= max(heuristic_scores[i], 0.01)

            weights.append(weight)

        selected = random.choices(
            range(len(children_alternatives)),
            weights=weights,
            k=1
        )[0]

        key = (symbol, repr(children_alternatives[selected]))
        self.production_counts[key] += 1

        return selected
    
    def expand_node_by_heuristic(self, node):

        symbol, children = node
        assert children is None

        expansions = self.grammar[symbol]

        scores = self.calculate_heuristic_scores(expansions)

        if self.selection == "max":
            best_score = max(scores)
            selected_indices = [
                i for i, score in enumerate(scores)
                if score == best_score
            ]
            selection_scores = None

        elif self.selection == "weighted":
            selected_indices = list(range(len(expansions)))
            selection_scores = scores

        else:
            raise ValueError(
                f"Unknown selection strategy: {self.selection}"
            )

        selected_expansions = [
            expansions[i] for i in selected_indices
        ]

        children_alternatives = [
            self.expansion_to_children(expansion)
            for expansion in selected_expansions
        ]

        index = self.choose_node_expansion(
            node, children_alternatives, selection_scores
        )

        chosen_expansion = selected_expansions[index]
        chosen_children = children_alternatives[index]

        chosen_children = self.process_chosen_children(
            chosen_children, chosen_expansion
        )

        return (symbol, chosen_children)

    def expand_node_max_heuristic(self, node):

        if self.log:
            print(
                "Expanding",
                all_terminals(node),
                "using heuristic:",
                self.heuristic_weights
            )

        return self.expand_node_by_heuristic(node)
