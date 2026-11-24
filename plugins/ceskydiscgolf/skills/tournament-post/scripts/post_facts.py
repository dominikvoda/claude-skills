#!/usr/bin/env python3
"""Verifiable facts for a post-tournament report on a closed ceskydiscgolf.cz event.

usage: post_facts.py <tournament uuid> [--out FACTS.json]
Prints podiums (to par, "po rozhozu"), finishers, best rounds, aces, hole averages and the
next events of the same main league. Every number comes from IDG; nothing is estimated.
Public data only, so it works for anyone, not just the event's director.
"""
import collections, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../ceskydiscgolf/scripts'))


def podium(results_rows, lb_by_user):
    """Places 1-3 (a shared 3rd keeps every member) with to-par; `tiebreak` marks a player placed
    above someone on the same total (won the rozhoz)."""
    rows = sorted(results_rows, key=lambda r: r['place'])
    out = []
    for i, r in enumerate(rows):
        if r['place'] > 3:
            break
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        out.append({'place': r['place'], 'name': lb_by_user[r['user_id']]['player_name'], 'total': r['total'],
                    'to_par': lb_by_user[r['user_id']]['to_par'],
                    'tiebreak': bool(nxt and nxt['total'] == r['total'] and nxt['place'] != r['place'])})
    return out


def hole_stats(lb_rows):
    """Average score per event hole number, aces, and the best single rounds."""
    scores, aces, rounds = collections.defaultdict(list), [], []
    for e in lb_rows:
        for rnd, hs in (e.get('hole_scores') or {}).items():
            for h, s in hs.items():
                scores[int(h)].append(s)
                if s == 1:
                    aces.append({'name': e['player_name'], 'round': rnd, 'hole': int(h)})
            rounds.append({'name': e['player_name'], 'round': rnd, 'score': sum(hs.values()), 'holes': len(hs)})
    avg = {h: round(sum(v) / len(v), 2) for h, v in sorted(scores.items())}
    best = sorted(rounds, key=lambda r: r['score'])
    best = [r for r in best if best and r['score'] == best[0]['score'] and r['holes'] == best[0]['holes']]
    return avg, aces, best


def main():
    from idg import call
    a = sys.argv[1:]
    t = a[0]
    _, det = call('GET', f'/tournaments/{t}/')
    _, res = call('GET', f'/tournaments/{t}/results/')
    if not res.get('divisions'):
        raise SystemExit('results/ is empty: the event is not closed yet (ceskydiscgolf references/close.md).')
    div_ids = {d['division_abbreviation']: d['division'] for d in det['divisions']}
    facts = {'name': det['name'], 'date': det['start_date'], 'venue': det.get('city'), 'divisions': {}, 'all_lb': []}
    for d in res['divisions']:
        code = d['division_abbr']
        rows = next(v for v in d.values() if isinstance(v, list))
        _, lb = call('GET', f'/scoring/tournaments/{t}/live-scoring/leaderboard/?division={div_ids[code]}')
        facts['all_lb'] += lb
        facts['divisions'][code] = {'finishers': len(rows), 'podium': podium(rows, {e['user_id']: e for e in lb})}
    lb = facts.pop('all_lb')
    facts['players'] = len(lb)
    facts['rounds'] = len({rnd for e in lb for rnd in (e.get('hole_scores') or {})})
    facts['hole_avg'], facts['aces'], facts['best_rounds'] = hole_stats(lb)
    _, lst = call('GET', f"/tournaments/?year={det['start_date'][:4]}")
    lst = lst.get('results', lst) if isinstance(lst, dict) else lst
    league = next((x.get('main_league_name') for x in lst if x['id'] == t), None)
    facts['league'] = league
    facts['next_events'] = sorted(({'date': x['start_date'], 'name': x['name'], 'id': x['id'], 'capacity': x.get('capacity'),
                                    'registered': x.get('registered_count'), 'phase': x.get('registration_phase_state')}
                                   for x in lst if league and x.get('main_league_name') == league and x['start_date'] > det['start_date']),
                                  key=lambda x: x['date'])[:2]
    s = json.dumps(facts, ensure_ascii=False, indent=1)
    if '--out' in a:
        open(a[a.index('--out') + 1], 'w').write(s)
    print(s)


if __name__ == '__main__':
    main()
