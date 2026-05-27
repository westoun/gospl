import math
from typing import List


class Variable:
    name: str
    allowed: List
    constraints: List

    def __init__(self, name: str, allowed: List):
        for value in allowed:
            if type(value) not in [int, str]:
                raise ValueError(
                    f"Type '{type(value)}' not supported by variable class at the moment.")

        # Sort to avoid semantic errors due to different
        # orderings of allowed values between variables.
        self.allowed = sorted(allowed)

        self.name = name
        self.constraints = []

    @property
    def qubit_count(self) -> int:
        return math.ceil(math.log2(len(self.allowed)))
