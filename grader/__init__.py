"""Answer graders. Same signature: grade(reply, problem, rtol=...) -> 1.0 | 0.0."""
from grader.v0 import grade as grade_v0
from grader.v1 import grade as grade_v1

GRADERS = {"v0": grade_v0, "v1": grade_v1}

__all__ = ["GRADERS", "grade_v0", "grade_v1"]
