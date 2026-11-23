from close_check import payload, podium_ties, unfinished

R = lambda place, uid, name, hs=None: {'place': place, 'user_id': uid, 'tournament_player_id': f'tp{uid}',
                                       'player_name': name, 'hole_scores': hs or {'1': {'1': 3, '2': 3}}}
rows = [R(1, 1, 'A'), R(2, 2, 'B'), R(3, 3, 'C'), R(3, 4, 'D'), R(3, 5, 'E'), R(6, 6, 'F'), R(6, 7, 'G')]
ties = podium_ties(rows)
assert [[r['user_id'] for r in g] for g in ties] == [[3, 4, 5]], ties  # tie for 6th is not podium
assert podium_ties([R(1, 1, 'A'), R(1, 2, 'B')])[0][1]['user_id'] == 2

assert [r['user_id'] for r in unfinished([R(1, 1, 'A'), R(2, 2, 'B', {'1': {'1': 3}})], 1)] == [2]
assert [r['user_id'] for r in unfinished([R(1, 1, 'A')], 2)] == [1]  # round 2 missing

tag = {'standings': {'divisions': [{'division': 'MPO', 'finishers': [
    {'idgV2UserId': 3, 'position': 4, 'isManual': True}, {'idgV2UserId': 4, 'position': 3, 'isManual': True},
    {'idgV2UserId': 5, 'position': 5, 'isManual': True}, {'idgV2UserId': 1, 'position': 1}]}]}}
places, open_groups = payload({'MPO': ties, 'FPO': [[R(3, 8, 'H'), R(3, 9, 'I')]]}, tag)
assert places == [{'tournament_player_id': 'tp3', 'place': 4}, {'tournament_player_id': 'tp4', 'place': 3},
                  {'tournament_player_id': 'tp5', 'place': 5}], places
assert open_groups == [('FPO', ['H', 'I'])]
print('ok')
