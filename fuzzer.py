from collections import defaultdict

from fuzzingbook.GrammarFuzzer import Callable, DerivationTree, GrammarFuzzer, Optional, all_terminals, nonterminals

from fuzzingbook.Grammars import trim_grammar
from Grammar.json5_grammar import JSON5_GRAMMAR
from Grammar.toml_grammar import TOML_GRAMMAR
import inspect
import random
from collections import defaultdict
import json
from fuzzingbook.GrammarFuzzer import tree_to_string





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





import random
import math
from collections import defaultdict


class HeuristicGrammarFuzzerFrequency(GrammarFuzzer):

    def __init__(
        self,
        grammar,
        *args,
        selection="max",
        frequency_function="inverse",
        normalize_frequency=True,
        frequency_alpha=0.1,
        **kwargs
    ):
        super().__init__(grammar, *args, **kwargs)

        self.production_counts = defaultdict(int)

        # "max", "weighted", or "random"
        self.selection = selection

        # "inverse", "sqrt", "exponential", or "logarithmic"
        self.frequency_function = frequency_function

        self.normalize_frequency = normalize_frequency
        self.frequency_alpha = frequency_alpha

    # --------------------------------------------------
    # Production frequency tracking
    # --------------------------------------------------

    def expansion_frequency_cost(self, symbol, expansion):

        key = (
            symbol,
            repr(self.expansion_to_children(expansion))
        )

        count = self.production_counts[key]

        if self.frequency_function == "inverse":
            return 1 / (1 + count)

        elif self.frequency_function == "sqrt":
            return 1 / math.sqrt(1 + count)

        elif self.frequency_function == "exponential":
            return math.exp(-self.frequency_alpha * count)

        elif self.frequency_function == "logarithmic":
            return -math.log1p(count)

        else:
            raise ValueError(
                f"Unknown frequency function: {self.frequency_function}"
            )

    def update_production_count(self, symbol, expansion):

        key = (
            symbol,
            repr(self.expansion_to_children(expansion))
        )

        self.production_counts[key] += 1

    # --------------------------------------------------
    # Production selection
    # --------------------------------------------------

    def select_heuristic_expansion(self, symbol, expansions):

        scores = [
            self.expansion_frequency_cost(symbol, expansion)
            for expansion in expansions
        ]

        if self.normalize_frequency:
            minimum = min(scores)
            maximum = max(scores)

            if maximum != minimum:
                scores = [
                    (score - minimum) / (maximum - minimum)
                    for score in scores
                ]
            else:
                scores = [1.0] * len(scores)

        if self.selection == "random":
            return random.randrange(len(expansions))

        elif self.selection == "max":

            best_score = max(scores)

            selected_indices = [
                i for i, score in enumerate(scores)
                if score == best_score
            ]

            return random.choice(selected_indices)

        elif self.selection == "weighted":

            weights = [
                max(0.0, score) + 0.01
                for score in scores
            ]

            return random.choices(
                range(len(expansions)),
                weights=weights,
                k=1
            )[0]

        else:
            raise ValueError(
                f"Unknown selection strategy: {self.selection}"
            )

    # --------------------------------------------------
    # Heuristic expansion
    # --------------------------------------------------

    def expand_node_by_heuristic(self, node):

        symbol, children = node
        assert children is None

        expansions = self.grammar[symbol]

        index = self.select_heuristic_expansion(
            symbol, expansions
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

    # --------------------------------------------------
    # Cost-based expansion override
    # --------------------------------------------------

    def expand_node_by_cost(
        self,
        node: DerivationTree,
        choose: Callable = min
    ) -> DerivationTree:

        symbol, children = node
        assert children is None

        expansions = self.grammar[symbol]

        children_alternatives_with_cost = [
            (
                self.expansion_to_children(expansion),
                self.expansion_cost(expansion, {symbol}),
                expansion
            )
            for expansion in expansions
        ]

        costs = [
            cost for child, cost, expansion
            in children_alternatives_with_cost
        ]

        chosen_cost = choose(costs)

        children_with_chosen_cost = [
            child for child, child_cost, _
            in children_alternatives_with_cost
            if child_cost == chosen_cost
        ]

        expansion_with_chosen_cost = [
            expansion for _, child_cost, expansion
            in children_alternatives_with_cost
            if child_cost == chosen_cost
        ]

        index = self.choose_node_expansion(
            node, children_with_chosen_cost
        )

        chosen_children = children_with_chosen_cost[index]
        chosen_expansion = expansion_with_chosen_cost[index]

        # Track productions selected during cost-based expansion
        self.update_production_count(
            symbol, chosen_expansion
        )

        chosen_children = self.process_chosen_children(
            chosen_children, chosen_expansion
        )

        return (symbol, chosen_children)

    # --------------------------------------------------
    # Tree expansion
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def get_production_statistics(self):
        return dict(self.production_counts)

    def reset_production_counts(self):
        self.production_counts.clear()
