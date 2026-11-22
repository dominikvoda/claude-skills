from flights import clusters, matcher, pack

P = [{"id": i, "player_name": n, "last_name": n.split()[-1]} for i, n in
     enumerate(["Kateřina Smetanová", "Martin Šrámek", "Adam Levý", "Tomáš Levý", "Ľuboš Petrák", "Jiří Novák", "Lukáš Novák"])]
m = matcher(P)
assert m("Káča Smetanová ") == 0 and m("Adam levý") == 2 and m("Luboš Petrák") == 4
assert m("Jiří Novák") == 5 and m("Novák") is None and m("Pepa Levý") is None  # ambiguous surname
g, unk = clusters([("Adam levý", "Tomáš levý, Luboš Petrák"), ("Ľuboš Petrák", "Káča Smetanová"), ("X Y", "Martin Šrámek")], m)
assert g == [{2, 3, 4, 0}] and unk == ["X Y"], (g, unk)
f = pack(list(range(7)), g, {i: 900 - i for i in range(7)}, 2)
assert sorted(map(len, f)) == [3, 4] and any({0, 2, 3, 4} <= set(x) for x in f)
print("ok")
from flights import holes_for
assert holes_for([[1], [2], [3]], 10, director=3, director_hole=1) == [2, 3, 1]
assert holes_for([[1], [2], [3]], 10, director=1, director_hole=7) == [7, 1, 2]
assert holes_for([[1], [2]], 10) == [1, 2]
mixed = pack(list(range(8)), [], {i: 1000 - 50 * i for i in range(8)}, 2)
assert {0, 1} not in [set(f[:2]) for f in mixed], mixed  # two strongest split
print("ok2")
