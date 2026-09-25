"""Cascade: BFS from triggers>=70, hop+type carried, depth<=3, ward-union pop."""
from collections import deque
from . import config


class CascadeError(Exception):
    def __init__(self, message, code_text="CASCADE_TRIGGER_UNKNOWN"):
        super().__init__(message)
        self.code = config.EXIT_STAGE_INVARIANT
        self.code_text = code_text


def _union_pop(members, asset_ward=None, ward_pop=None, population_by_asset=None):
    if asset_ward and ward_pop:
        wards = {asset_ward.get(m, m) for m in members}
        return sum(ward_pop.get(w, 0) for w in wards)
    if population_by_asset:
        return sum(population_by_asset.get(m, 0) for m in set(members))
    return 0


def build(register, dependencies, population_by_asset=None, asset_ward=None, ward_pop=None):
    scores = {r["asset_id"]: r.get("vulnerability_score", 0) for r in register}
    adj = {}
    for d in dependencies or []:
        fa, ta = d["from_asset"], d["to_asset"]
        if fa not in scores or ta not in scores:
            offender = fa if fa not in scores else ta
            raise CascadeError(f"unknown asset in dependency: {offender}")
        adj.setdefault(fa, []).append((ta, d.get("dependency_type", "power")))
    chains, critical, all_members = [], [], set()
    for trig, sc in scores.items():
        if sc < config.TRIGGER_SCORE:
            continue
        chain, seen, q = [], {trig}, deque([(trig, 0)])
        while q:
            node, hop = q.popleft()
            if hop >= config.MAX_HOPS:
                continue
            for nxt, dtype in adj.get(node, []):
                if nxt in seen:
                    critical.append(f"cycle detected at {nxt} from trigger {trig}")
                    continue
                seen.add(nxt)
                chain.append({"asset_id": nxt, "dependency_type": dtype, "hop": hop + 1})
                q.append((nxt, hop + 1))
        members = [trig] + [c["asset_id"] for c in chain]
        depth = max([c["hop"] for c in chain], default=0)
        chains.append({"trigger_asset_id": trig, "chain": chain, "max_depth": depth,
                       "population_affected": _union_pop(members, asset_ward, ward_pop, population_by_asset),
                       "confidence": {"level": "high", "reason": "deterministic BFS"}})
        all_members.update(members)
    cum = _union_pop(list(all_members), asset_ward, ward_pop, population_by_asset)
    return {"cascade_chains": chains, "cumulative_population_affected": cum, "critical_paths": critical}
