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

        self.allowed = allowed

        self.name = name
        self.constraints = []

    @property
    def qubit_count(self) -> int:
        return math.ceil(math.log2(len(self.allowed)))
