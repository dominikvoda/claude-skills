from post_facts import hole_stats, podium

res = [{'place': 1, 'user_id': 1, 'total': 57}, {'place': 2, 'user_id': 2, 'total': 60},
       {'place': 3, 'user_id': 3, 'total': 61}, {'place': 4, 'user_id': 4, 'total': 61}]
lb = {i: {'player_name': n, 'to_par': tp} for i, n, tp in [(1, 'A', -9), (2, 'B', -6), (3, 'C', -5), (4, 'D', -5)]}
p = podium(res, lb)
assert [x['tiebreak'] for x in p] == [False, False, True], p  # C won the rozhoz against D
shared = podium(res[:3] + [{'place': 3, 'user_id': 4, 'total': 61}], lb)
assert len(shared) == 4 and not shared[2]['tiebreak'], shared  # unresolved 3rd keeps both

rows = [{'player_name': 'A', 'hole_scores': {'1': {'1': 2, '2': 1}, '2': {'1': 3, '2': 3}}},
        {'player_name': 'B', 'hole_scores': {'1': {'1': 3, '2': 3}, '2': {'1': 2, '2': 1}}}]
avg, aces, best = hole_stats(rows)
assert avg == {1: 2.5, 2: 2.0} and len(aces) == 2 and {b['name'] for b in best} == {'A', 'B'}, (avg, aces, best)
print('ok')
