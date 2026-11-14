
## 2026-11-03: Task 01 (projectiles)
- Done: Problem/Family/generate in envs/base.py, 4-template projectile family with 4 difficulty levels, 35 tests (written first, mutation-checked).
- Next: Task 02 (grader v0). Open question: level 3/4 always ask for a non-SI unit (spec said "e.g."); change if you want a mix.

## 2026-11-11: Task 02 (graders)
- Done: grader v0 (naive on purpose: first number, 5%, no units) and v1 (one box, number+unit grammar, own alias table, 1%), exposed as GRADERS; 151 grader tests written first, mutation-checked; empty data/labels/hand_labeled_replies.jsonl.
- Next: fill hand labels; separate task to make every generator level state the answer unit.
- Open: v0's "first number in the reply" scores almost every real chain-of-thought 0 (it grabs a number from the givens), so RL on v0 may learn "lead with the answer" rather than the box hacks. Decide before E3.
