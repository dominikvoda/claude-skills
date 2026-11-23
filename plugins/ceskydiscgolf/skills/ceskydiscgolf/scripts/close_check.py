#!/usr/bin/env python3
"""Pre-close check of a ceskydiscgolf.cz tournament: live standings, unfinished players, podium ties.

usage: close_check.py <tournament uuid> [--tagovacka MGMT.json] [--out PAYLOAD.json]
  --tagovacka  the Tagovačka management JSON (tagovacka skill: tag.py idg ... --out FILE);
               its manual/official places become the finalize-places payload.
"""
import collections, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def podium_ties(rows):
    """Tie groups that touch places 1-3: [[row, ...], ...]. Rows come from the live leaderboard."""
    by_place = collections.defaultdict(list)
    for r in rows:
        by_place[r['place']].append(r)
    return [g for p, g in sorted(by_place.items()) if p <= 3 and len(g) > 1]


def unfinished(rows, n_rounds):
    """Rows missing a round or holes in one, against the most holes any player has in that round."""
    full = collections.Counter()
    for r in rows:
        for k, v in (r.get('hole_scores') or {}).items():
            full[k] = max(full[k], len(v))
    rounds = [str(i) for i in range(1, n_rounds + 1)]
    return [r for r in rows if not r.get('is_dnf')
            and any(len((r.get('hole_scores') or {}).get(k, {})) < max(full[k], 1) for k in rounds)]


def payload(ties_by_div, tag):
    """finalize-places entries from Tagovačka's decided places; also the tie groups it hasn't decided."""
    std = tag.get('standings', tag)
    decided = {d['division']: {e['idgV2UserId']: e['position'] for e in d['finishers']
                               if e.get('isManual') or e.get('isOfficial')} for d in std['divisions']}
    places, open_groups = [], []
    for div, groups in ties_by_div.items():
        for g in groups:
            got = [(r, decided.get(div, {}).get(r['user_id'])) for r in g]
            if all(p is not None for _, p in got):
                places += [{'tournament_player_id': r['tournament_player_id'], 'place': p} for r, p in got]
            else:
                open_groups.append((div, [r['player_name'] for r in g]))
    return places, open_groups


def main():
    from idg import call
    a = sys.argv[1:]
    t = a[0]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    _, det = call('GET', f'/tournaments/{t}/', auth=True)
    _, cs = call('GET', f'/tournaments/{t}/close-status/', auth=True)
    print(f"{det['name']} {det['start_date']} director {det['director1_name']} | is_closed={cs['is_closed']}")
    _, players = call('GET', f'/tournaments/{t}/admin-players/', auth=True)
    divs = {(p['division'], p['division_code']) for p in players if p['status'] == 'registered'}
    n_rounds = len(det.get('rounds') or [])
    ties, lb = {}, {}
    for did, code in sorted(divs, key=lambda d: d[1]):
        _, rows = call('GET', f'/scoring/tournaments/{t}/live-scoring/leaderboard/?division={did}', auth=True)
        lb[code] = rows
        reg = sum(1 for p in players if p['status'] == 'registered' and p['division'] == did)
        print(f'--- {code}: {len(rows)} on leaderboard, {reg} registered')
        for r in rows:
            if r['place'] <= 5:
                print(f"{r['place']:>3} {r['total']:>4} {r['player_name']}")
        for r in unfinished(rows, n_rounds):
            print(f"  UNFINISHED {r['player_name']}: rounds {sorted((r.get('hole_scores') or {}))}")
        ties[code] = podium_ties(rows)
        for g in ties[code]:
            print(f"  PODIUM TIE place {g[0]['place']}: {', '.join(r['player_name'] for r in g)}")
    json.dump(lb, open('/tmp/close_check_leaderboard.json', 'w'), ensure_ascii=False)
    if opt('--tagovacka'):
        places, open_groups = payload(ties, json.load(open(opt('--tagovacka'))))
        for div, names in open_groups:
            print(f'  NOT DECIDED in Tagovačka: {div} {names}')
        print(json.dumps({'places': places}, ensure_ascii=False))
        if opt('--out'):
            json.dump({'places': places}, open(opt('--out'), 'w'))


if __name__ == '__main__':
    main()
