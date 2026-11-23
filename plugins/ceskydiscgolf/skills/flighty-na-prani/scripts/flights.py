#!/usr/bin/env python3
"""Draft shotgun flights from flight wishes (Google Form sheet) + IDG registrations.

  flights.py <cards.json> <players.json> <wishes.tsv> <tournament keyword>
             [--holes N] [--director "Jméno Příjmení" --director-hole H] [--hole-avg avg.json] [--out payload.json]

cards.json   = GET /tournaments/{t}/admin-rounds/{round1}/cards/ --auth
players.json = GET /tournaments/{t}/admin-players/ --auth   (for idg_rating)
wishes.tsv   = google:gsheets read of the form answers tab (cols: time, tournament, name, wants)
"""
import argparse
import csv
import json
import math
import re
import sys
import unicodedata

MAX_PER_HOLE = 5


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r'"[^"]*"', " ", s).replace("-", " ").split())


def matcher(players):
    """name text -> card row id, by full name, then by unique surname. None if unknown/ambiguous."""
    full = {norm(p["player_name"]): p["id"] for p in players}
    by_last = {}
    for p in players:
        by_last.setdefault(norm(p["last_name"]), []).append(p["id"])

    def match(text):
        t = norm(text)
        if t in full:
            return full[t]
        hits = by_last.get(t.split()[-1], []) if t else []
        return hits[0] if len(hits) == 1 else None
    return match


def clusters(wishes, match):
    """Union-find over wishes -> list of sets of row ids, plus unmatched names."""
    parent, unknown = {}, []

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for who, wants in wishes:
        ids = []
        for name in [who] + re.split(r"[,;&+/]| a ", wants):
            if name.strip():
                rid = match(name)
                (ids.append(rid) if rid is not None else unknown.append(name.strip()))
        for rid in ids:
            parent[find(rid)] = find(ids[0])
    groups = {}
    for x in parent:
        groups.setdefault(find(x), set()).add(x)
    return [g for g in groups.values() if len(g) > 1], unknown


def pack(row_ids, wish_groups, rating, n_groups):
    sizes = [len(row_ids) // n_groups + (i < len(row_ids) % n_groups) for i in range(n_groups)]
    flights = [[] for _ in sizes]
    for c in sorted(wish_groups, key=len, reverse=True):
        i = max(range(n_groups), key=lambda i: sizes[i] - len(flights[i]))
        flights[i] += sorted(c, key=lambda r: -rating[r])  # may overflow if a cluster > group size; reported below
    placed = {r for f in flights for r in f}
    target = sum(rating[r] for r in row_ids) / len(row_ids)
    for r in sorted((r for r in row_ids if r not in placed), key=lambda r: -rating[r]):
        free = [i for i in range(n_groups) if len(flights[i]) < sizes[i]]
        # mix levels: aim every flight at the overall average; strongest player goes where the open
        # spots need the highest rating to get there
        need = lambda i: (target * sizes[i] - sum(rating[x] for x in flights[i])) / (sizes[i] - len(flights[i]))
        flights[max(free, key=need)].append(r)
    return flights


def weak_in_small(flights, fixed, rating):
    """Uneven sizes: the flights with the weakest player should be the smaller ones.
    Moves a free (non-wish) player from such a big flight to the small flight with the strongest
    weakest player; the sum of the big flights' minimums grows each move, so it ends."""
    small = min(map(len, flights))
    lo = lambda f: min(rating[r] for r in f)
    target = sum(rating[r] for f in flights for r in f) / sum(map(len, flights))
    while True:
        smalls = [f for f in flights if len(f) == small]
        bigs = [f for f in flights if len(f) == small + 1 and any(r not in fixed and rating[r] > lo(f) for r in f)]
        if not smalls or not bigs:
            return flights
        b, s = min(bigs, key=lo), max(smalls, key=lo)
        cand = [r for r in b if r not in fixed and rating[r] > lo(b) and rating[r] >= lo(s)]
        if lo(b) >= lo(s) or not cand:
            return flights
        avg = lambda f: sum(rating[x] for x in f) / len(f)
        r = min(cand, key=lambda r: abs(avg([x for x in b if x != r]) - target) + abs(avg(s + [r]) - target))
        b.remove(r), s.append(r)


def holes_for(flights, n_holes, director=None, director_hole=1, hole_avg=None):
    """flight index -> hole: the director's flight on director_hole, the rest on the other holes.
    With hole_avg {hole: avg score}, bigger (slower) flights start on the easier holes; a hole
    without data counts as the mean. Without it, flights go in order."""
    d = next((i for i, f in enumerate(flights) if director in f), None)
    holes = [h for h in range(1, n_holes + 1) if d is None or h != director_hole]
    others = [i for i in range(len(flights)) if i != d]
    if hole_avg:
        mean = sum(hole_avg.values()) / len(hole_avg)
        holes.sort(key=lambda h: hole_avg.get(h, mean))
        others.sort(key=lambda i: -len(flights[i]))
    hole_of = dict(zip(others, holes))
    return [director_hole if i == d else hole_of[i] for i in range(len(flights))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards"), ap.add_argument("players"), ap.add_argument("wishes"), ap.add_argument("keyword")
    ap.add_argument("--holes", type=int, help="override layout hole count")
    ap.add_argument("--director", help="director's name; their flight starts on --director-hole")
    ap.add_argument("--director-hole", type=int, default=1)
    ap.add_argument("--hole-avg", help="JSON {hole: avg score} from hole_stats.py; big flights get easy holes")
    ap.add_argument("--out", help="write cards-update payload here")
    a = ap.parse_args()
    load = lambda f: json.loads(open(f, encoding="utf-8").read(), strict=False)
    cards, regs = load(a.cards), load(a.players)
    rows = cards["players"]
    rating = {p["id"]: 0 for p in rows}
    by_player = {p["id"]: p.get("idg_rating") or 0 for p in regs}
    for p in rows:
        rating[p["id"]] = by_player.get(p["player_id"], 0)
    name = {p["id"]: f'{p["player_name"]} ({p["division_code"]}, {rating[p["id"]] or "-"})' for p in rows}

    kw = norm(a.keyword)
    wishes = [(r[2], r[3]) for r in csv.reader(open(a.wishes, encoding="utf-8"), delimiter="\t")
              if len(r) >= 4 and kw in norm(r[1])]
    wish_groups, unknown = clusters(wishes, matcher(rows))

    holes = a.holes or cards["max_holes"]
    if len(rows) > MAX_PER_HOLE * holes:
        sys.exit(f"{len(rows)} hráčů se nevejde na {holes} jamek po max {MAX_PER_HOLE}: "
                 f"potřebuješ aspoň {math.ceil(len(rows) / MAX_PER_HOLE)} jamek (--holes nebo delší layout)")
    n_groups = min(holes, math.ceil(len(rows) / cards["group_settings"].get("preferred_group_size", 4)))
    flights = pack([p["id"] for p in rows], wish_groups, rating, n_groups)
    flights = weak_in_small(flights, {r for g in wish_groups for r in g}, rating)
    director = matcher(rows)(a.director) if a.director else None
    if a.director and director is None:
        sys.exit(f"Ředitel {a.director!r} není v registraci")
    hole_avg = {int(k): v for k, v in load(a.hole_avg).items()} if a.hole_avg else None
    hole_of = holes_for(flights, holes, director, a.director_hole, hole_avg)
    order = sorted(range(n_groups), key=lambda i: hole_of[i])

    print(f"{len(rows)} hráčů, {len(wishes)} přání, {n_groups} flightů na {holes} jamek\n")
    wished = {r for g in wish_groups for r in g}
    for i in order:
        f = flights[i]
        diff = f", jamka ø {hole_avg[hole_of[i]]}" if hole_avg and hole_of[i] in hole_avg else ""
        print(f"Jamka {hole_of[i]} ({len(f)}, průměr {sum(rating[r] for r in f) // len(f)}{diff}):")
        for r in f:
            print(f"  {'*' if r in wished else ' '} {name[r]}")
    if unknown:
        print("\nNenalezeno v registraci (zkontroluj ručně):", ", ".join(unknown))
    big = [g for g in wish_groups if len(g) > max(map(len, flights)) or len(g) > MAX_PER_HOLE]
    if big:
        print("\nPřání větší než flight:", [[name[r] for r in g] for g in big])
    if a.out:
        payload = {"assignments": [{"id": r, "starting_hole": h, "tee_time": "", "card_order": i}
                                   for h, f in zip(hole_of, flights) for i, r in enumerate(f, 1)],
                   "holes_to_skip": ""}
        json.dump(payload, open(a.out, "w"), ensure_ascii=False, indent=1)
        print("\nPayload:", a.out)


if __name__ == "__main__":
    sys.exit(main())
