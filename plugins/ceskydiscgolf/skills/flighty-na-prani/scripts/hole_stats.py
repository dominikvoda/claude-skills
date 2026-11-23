#!/usr/bin/env python3
"""Average score per hole on a course layout, from every past tournament round played on it.

  hole_stats.py <field uuid> "<layout name>" > hole_avg.json      # {"1": 3.48, ...}, summary on stderr

Feed the result to flights.py --hole-avg. Hole numbers are the source layout's; if the event's
layout differs (temporary holes), renumber the keys by hand and leave the unknown holes out.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../ceskydiscgolf/scripts"))
from idg import call  # noqa: E402


def get(path):
    status, body = call("GET", path)
    return body if status == 200 else None


def main():
    field, layout = sys.argv[1], sys.argv[2]
    tot = {}
    for t in get(f"/core/fields/{field}/tournament-layouts/")["tournaments"]:
        rounds = [r for r in t["rounds"] if r["division_overrides"]
                  and all(o["layout"]["name"] == layout for o in r["division_overrides"])]
        det = get(f"/tournaments/{t['id']}/") if rounds else None
        if not det:
            continue
        for r in rounds:
            for dv in det["divisions"]:
                if not dv.get("active_player_count"):
                    continue
                s = get(f"/scoring/tournaments/{t['id']}/live-scoring/rounds/{r['id']}/hole-stats/?division={dv['division']}")
                for h in (s or {}).get("holes", []):
                    if h["played"] and h["avg"] is not None:
                        a = tot.setdefault(h["hole_number"], [0.0, 0, h.get("dist")])
                        a[0] += h["avg"] * h["played"]
                        a[1] += h["played"]
    avg = {h: round(s / n, 2) for h, (s, n, _) in sorted(tot.items())}
    for h in sorted(avg, key=avg.get):
        print(f"jamka {h}: ø {avg[h]} (n={tot[h][1]}, {tot[h][2]} m)", file=sys.stderr)
    json.dump(avg, sys.stdout)


if __name__ == "__main__":
    main()
