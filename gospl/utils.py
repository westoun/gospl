from typing import List

from gospl.variable import Variable
from gospl.constraint import Constraint


def extract_constraints(variables: List[Variable]) -> List[Constraint]:
    constraints: List[Constraint] = []
    for variable in variables:
        for constraint in variable.constraints:
            if constraint not in constraints:
                constraints.append(constraint)

    return constraints
