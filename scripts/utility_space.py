import json


class UtilitySpace:
    def __init__(self, utility_file):
        utility_file = utility_file.split(":")[-1]

        with open(utility_file, "r") as f:
            raw_utility_space = json.load(f)

        self._parse_utility_space(raw_utility_space)

    def _parse_utility_space(self, raw):
        raw = raw["LinearAdditiveUtilitySpace"]

        self.issue_weights = {i: w for i, w in raw["issueWeights"].items()}
        self.value_weights = {}

        for issue, values in raw["issueUtilities"].items():
            issue_value_weights = {
                v: w for v, w in values["discreteutils"]["valueUtilities"].items()
            }
            self.value_weights[issue] = issue_value_weights

    def get_utility(self, bid):
        return sum(
            self.issue_weights[i] * self.value_weights[i][v] for i, v in bid.items()
        )
