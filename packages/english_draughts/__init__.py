"""English draughts declared through the package JSON definition.

Men move and capture diagonally forward. Captures are compulsory; any complete
route may be chosen, without a maximum-capture preference. Kings use short
forward/backward diagonal moves and jumps. Reaching the far rank crowns a man
and completes that action. The last player able to move wins, whether the
opponent has no pieces or all remaining pieces are blocked.

The definition resets no-progress counting after a capture or an uncrowned
man advances. Draw claims, agreed draws, clock results and complete-game
verification gate the ``playable`` flag.

Rules reference: https://wcdf.net/rules/rules_of_checkers_english.pdf
"""
