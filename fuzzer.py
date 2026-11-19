from collections import defaultdict

from fuzzingbook.GrammarFuzzer import Callable, DerivationTree, GrammarFuzzer, Optional, all_terminals, nonterminals

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
        return HeuristicGrammarFuzzer(Grammar, start_symbol="<value>", max_nonterminals=30).fuzz()
    else:
        Grammar = trim_grammar(TOML_GRAMMAR)
        return HeuristicGrammarFuzzer(Grammar, start_symbol="<start>", max_nonterminals=10).fuzz()




class HeuristicGrammarFuzzer(GrammarFuzzer):

    MAX_HEURISTIC_DEPTH = 5

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
            "depth": 0.4,
            "width": 0.4,
            "frequency": 0.2
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

    def calculate_heuristic_scores(self, symbol, expansions):

        heuristic_functions = {
            "depth": self.expansion_depth_cost,
            "total": self.expansion_total_cost,
            "width": self.expansion_width_cost,
            "frequency": lambda e: self.expansion_frequency_cost(symbol, e)
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

    def expansion_frequency_cost(self, symbol, expansion):
        key = (symbol, repr(self.expansion_to_children(expansion)))
        count = self.production_counts[key]

        return 1 / (1 + count)

    def update_production_count(self, symbol, expansion):
        key = (symbol, repr(self.expansion_to_children(expansion)))
        self.production_counts[key] += 1

    

    def select_heuristic_expansion(self, node, children_alternatives, scores):

        if self.selection == "max":

            best_score = max(scores)

            selected_indices = [
                i for i, score in enumerate(scores)
                if score == best_score
            ]

            return random.choice(selected_indices)

        elif self.selection == "weighted":

            weights = [score + 0.01 for score in scores]

            return random.choices(
                range(len(children_alternatives)),
                weights=weights,
                k=1
            )[0]

        else:
            raise ValueError(
                f"Unknown selection strategy: {self.selection}"
            )
    
    def expand_node_by_heuristic(self, node):


        symbol, children = node
        assert children is None

        expansions = self.grammar[symbol]

        scores = self.calculate_heuristic_scores(
            symbol, expansions
        )

        index = self.select_heuristic_expansion(
            node, expansions, scores
        )

        chosen_expansion = expansions[index]

        self.update_production_count(
            symbol, chosen_expansion
        )

        chosen_children = self.expansion_to_children(
            chosen_expansion
        )

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


    def expand_tree(self, tree):
        self.log_tree(tree)

        tree = self.expand_tree_with_strategy(
            tree,
            self.expand_node_max_cost,
            self.min_nonterminals
        )

        tree = self.expand_tree_with_strategy(
            tree,
            self.expand_node_by_heuristic,
            self.max_nonterminals,
            max_steps=200
        )

        tree = self.expand_tree_with_strategy(
            tree,
            self.expand_node_min_cost
        )

        assert self.possible_expansions(tree) == 0

        return tree

    
    def expand_tree_with_strategy(
        self,
        tree: DerivationTree,
        expand_node_method: Callable,
        limit: Optional[int] = None,
        max_steps: Optional[int] = None
    ):
        """Expand tree using expand_node_method until the limit
        is reached or max_steps expansions have been performed."""

        self.expand_node = expand_node_method

        steps = 0

        while (
            (limit is None or self.possible_expansions(tree) < limit)
            and self.any_possible_expansions(tree)
            and (max_steps is None or steps < max_steps)
        ):
            tree = self.expand_tree_once(tree)
            self.log_tree(tree)
            steps += 1

        return tree

