"""
algos.py - pure-Python algorithms behind the Deadlock Lab (COMP-2115, Chapter 7).

Nothing in here depends on Streamlit, so every function can be tested on its own.
Vectors are plain lists of ints, matrices are lists of lists.
"""
from __future__ import annotations

import re

# ----------------------------------------------------------------------------
# small vector helpers
# ----------------------------------------------------------------------------


def fmt(v) -> str:
    """(3, 3, 2) style text for a vector."""
    return "(" + ", ".join(str(int(x)) for x in v) + ")"


def leq(a, b) -> bool:
    """a <= b component-wise (the 'Need_i <= Work' test of the slides)."""
    return all(x <= y for x, y in zip(a, b))


def vadd(a, b):
    return [x + y for x, y in zip(a, b)]


def vsub(a, b):
    return [x - y for x, y in zip(a, b)]


def natural_key(name: str):
    m = re.search(r"(\d+)", name)
    return (name.rstrip("0123456789"), int(m.group(1)) if m else 0)


# ----------------------------------------------------------------------------
# graph helper: cycle detection (used for RAG, wait-for graph, avoidance)
# ----------------------------------------------------------------------------


def find_cycle(edges):
    """Return one directed cycle as a node list [a, b, ..., a], or None."""
    adj: dict[str, list[str]] = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, [])
    color = {n: 0 for n in adj}  # 0 white, 1 grey, 2 black
    stack: list[str] = []

    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in adj[u]:
            if color[v] == 1:
                return stack[stack.index(v):] + [v]
            if color[v] == 0:
                found = dfs(v)
                if found:
                    return found
        stack.pop()
        color[u] = 2
        return None

    for n in list(adj):
        if color[n] == 0:
            found = dfs(n)
            if found:
                return found
    return None


# ----------------------------------------------------------------------------
# Banker's algorithm (Lecture 26) and the detection algorithm (Lecture 27)
# Both are the same "reduction" idea:  Work = Available, repeatedly find a
# process whose demand <= Work, let it finish, give its Allocation back.
#   Safety algorithm   : demand = Need,    Finish[i] starts False for everyone
#   Detection algorithm: demand = Request, Finish[i] starts True if Allocation_i = 0
# ----------------------------------------------------------------------------


def need_matrix(mx, alloc):
    return [[m - a for m, a in zip(rm, ra)] for rm, ra in zip(mx, alloc)]


def available_vector(total, alloc):
    used = [sum(col) for col in zip(*alloc)] if alloc else [0] * len(total)
    return [t - u for t, u in zip(total, used)]


def _reduce(available, alloc, demand, finish):
    n = len(alloc)
    work = list(available)
    finish = list(finish)
    seq, steps = [], []
    while True:
        for i in range(n):
            if not finish[i] and leq(demand[i], work):
                new_work = vadd(work, alloc[i])
                steps.append(
                    {
                        "pick": i,
                        "demand": list(demand[i]),
                        "work_before": list(work),
                        "alloc": list(alloc[i]),
                        "work_after": new_work,
                    }
                )
                work, finish[i] = new_work, True
                seq.append(i)
                break
        else:
            break
    return {"finish": finish, "sequence": seq, "steps": steps, "work": work}


def safety_algorithm(available, alloc, need):
    r = _reduce(available, alloc, need, [False] * len(alloc))
    r["safe"] = all(r["finish"])
    r["stuck"] = [i for i, f in enumerate(r["finish"]) if not f]
    return r


def detection_algorithm(available, alloc, request):
    finish = [all(a == 0 for a in row) for row in alloc]  # slide step 1(b)
    r = _reduce(available, alloc, request, finish)
    r["deadlocked"] = [i for i, f in enumerate(r["finish"]) if not f]
    return r


def check_sequence(seq, available, alloc, demand):
    """Verify a user-typed sequence step by step. Returns (ok, log)."""
    work, log = list(available), []
    for i in seq:
        ok = leq(demand[i], work)
        row = {"pick": i, "demand": list(demand[i]), "work_before": list(work), "ok": ok}
        if ok:
            work = vadd(work, alloc[i])
            row["work_after"] = list(work)
        log.append(row)
        if not ok:
            return False, log
    return True, log


def resource_request(i, req, available, alloc, need):
    """Resource-Request algorithm for process P_i (slide 7.6)."""
    if not leq(req, need[i]):
        return {"status": "error", "why": "Request > Need: the process exceeded its declared maximum claim."}
    if not leq(req, available):
        return {"status": "wait", "why": "Request > Available: not enough free instances, so the process must wait."}
    new_av = vsub(available, req)
    new_alloc = [list(r) for r in alloc]
    new_need = [list(r) for r in need]
    new_alloc[i] = vadd(new_alloc[i], req)
    new_need[i] = vsub(new_need[i], req)
    safety = safety_algorithm(new_av, new_alloc, new_need)
    return {
        "status": "granted" if safety["safe"] else "unsafe",
        "available": new_av,
        "alloc": new_alloc,
        "need": new_need,
        "safety": safety,
    }


# ----------------------------------------------------------------------------
# Resource-allocation graph helpers (Lectures 23, 25, 27)
# ----------------------------------------------------------------------------

SLIDE_RAGS = {
    "Example of a Resource-Allocation Graph (no cycle)": dict(
        res={"R1": 1, "R2": 2, "R3": 1, "R4": 3},
        assigns=[("R1", "P2"), ("R2", "P1"), ("R2", "P2"), ("R3", "P3")],
        requests=[("P1", "R1"), ("P2", "R3")],
        claims=[],
    ),
    "Resource-Allocation Graph WITH a deadlock": dict(
        res={"R1": 1, "R2": 2, "R3": 1, "R4": 3},
        assigns=[("R1", "P2"), ("R2", "P1"), ("R2", "P2"), ("R3", "P3")],
        requests=[("P1", "R1"), ("P2", "R3"), ("P3", "R2")],
        claims=[],
    ),
    "Graph with a cycle but NO deadlock": dict(
        res={"R1": 2, "R2": 2},
        assigns=[("R1", "P2"), ("R1", "P3"), ("R2", "P1"), ("R2", "P4")],
        requests=[("P1", "R1"), ("P3", "R2")],
        claims=[],
    ),
}

_ARROW = re.compile(r"^(\w+)\s*(->|~>)\s*(\w+)$")


def parse_resources(text: str) -> dict:
    res: dict[str, int] = {}
    for tok in re.split(r"[,\n;]+", text):
        tok = tok.strip()
        if not tok:
            continue
        if ":" in tok:
            name, cnt = tok.split(":", 1)
            try:
                cnt = int(cnt)
            except ValueError:
                raise ValueError(f"'{tok}': the number of instances must be an integer, e.g. R2:3")
        else:
            name, cnt = tok, 1
        name = name.strip().upper()
        if not name.startswith("R"):
            raise ValueError(f"Resource names must start with R (got '{name}').")
        if cnt < 1:
            raise ValueError(f"{name} needs at least 1 instance.")
        res[name] = cnt
    return res


def parse_edges(text: str, res: dict):
    """Lines:  P1->R1 (request) | R1->P2 (assignment) | P1~>R2 (claim)."""
    res = dict(res)
    assigns, requests, claims = [], [], []
    for ln, line in enumerate(text.splitlines(), 1):
        s = line.split("#")[0].strip()
        if not s:
            continue
        s = s.replace("→", "->").replace("-->", "->").replace("=>", "->").replace("..>", "~>").replace("⇢", "~>")
        m = _ARROW.match(s)
        if not m:
            raise ValueError(f"Line {ln}: cannot read '{line.strip()}'. Use P1->R1, R1->P2 or P1~>R2.")
        a, arrow, b = m.group(1).upper(), m.group(2), m.group(3).upper()
        if a[0] == "P" and b[0] == "R":
            (requests if arrow == "->" else claims).append((a, b))
            r = b
        elif a[0] == "R" and b[0] == "P" and arrow == "->":
            assigns.append((a, b))
            r = a
        else:
            raise ValueError(f"Line {ln}: '{line.strip()}' is not a valid edge (P->R request, R->P assignment, P~>R claim).")
        res.setdefault(r, 1)
    for r, cnt in res.items():
        held = sum(1 for (rr, _) in assigns if rr == r)
        if held > cnt:
            raise ValueError(f"{r} has {cnt} instance(s) but {held} assignment edges leave it.")
    return res, assigns, requests, claims


def processes_of(assigns, requests, claims):
    ps = {p for _, p in assigns} | {p for p, _ in requests} | {p for p, _ in claims}
    return sorted(ps, key=natural_key)


def rag_edges(assigns, requests, claims=(), include_claims=False):
    e = [(p, r) for p, r in requests] + [(r, p) for r, p in assigns]
    if include_claims:
        e += [(p, r) for p, r in claims]
    return e


def rag_matrices(procs, res, assigns, requests):
    """Convert a RAG into Available / Allocation / Request (Lecture 27 data structures)."""
    rnames = list(res.keys())
    alloc = [[sum(1 for (r, p) in assigns if p == pp and r == rr) for rr in rnames] for pp in procs]
    req = [[sum(1 for (p, r) in requests if p == pp and r == rr) for rr in rnames] for pp in procs]
    avail = [res[rr] - sum(1 for (r, _) in assigns if r == rr) for rr in rnames]
    return rnames, alloc, req, avail


def rag_report(procs, res, assigns, requests):
    cyc = find_cycle(rag_edges(assigns, requests))
    rnames, alloc, req, avail = rag_matrices(procs, res, assigns, requests)
    det = detection_algorithm(avail, alloc, req)
    single = all(c == 1 for c in res.values())
    if cyc is None:
        verdict, deadlock = "No cycle in the graph  ⇒  NO deadlock.", False
    elif single:
        verdict, deadlock = "Cycle + every resource has a single instance  ⇒  DEADLOCK.", True
    elif det["deadlocked"]:
        verdict = "Cycle + several instances: the detection algorithm cannot finish some processes  ⇒  DEADLOCK."
        deadlock = True
    else:
        verdict = (
            "There is a cycle, but some resources have several instances and a process outside the cycle can "
            "finish and release one  ⇒  NO deadlock (a cycle only means a *possibility* of deadlock)."
        )
        deadlock = False
    return {
        "cycle": cyc, "verdict": verdict, "deadlock": deadlock, "rnames": rnames,
        "alloc": alloc, "request": req, "available": avail, "detection": det,
    }


def rag_dot(procs, res, assigns, requests, claims=(), cycle=None, extra_procs=()):
    """Graphviz DOT text of a resource-allocation graph."""
    hot = set()
    if cycle:
        hot = {(cycle[k], cycle[k + 1]) for k in range(len(cycle) - 1)}
    lines = [
        "digraph G {", "rankdir=TB;", 'bgcolor="transparent";',
        'node [fontname="Helvetica", fontsize=13];', 'edge [color="#7a7a7a", arrowsize=0.9];',
    ]
    allp = sorted(set(procs) | set(extra_procs), key=natural_key)
    for p in allp:
        lines.append(f'{p} [shape=circle, style=filled, fillcolor="#cfe8ff", fontcolor="#111111"];')
    for r, cnt in res.items():
        dots = " ".join(["●"] * cnt)
        lines.append(f'{r} [shape=box, style=filled, fillcolor="#e3e3e3", fontcolor="#111111", label="{r}\\n{dots}"];')

    def edge(u, v, dashed=False):
        attrs = []
        if dashed:
            attrs.append("style=dashed")
        if (u, v) in hot:
            attrs.append('color="#e53935", penwidth=2.8')
        a = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f"{u} -> {v}{a};")

    for p, r in requests:
        edge(p, r)
    for r, p in assigns:
        edge(r, p)
    for p, r in claims:
        edge(p, r, dashed=True)
    lines.append("}")
    return "\n".join(lines)


def wait_for_graph(requests, assigns):
    """Single-instance RAG -> wait-for graph (edge Pi -> Pj if Pi waits for a resource held by Pj)."""
    holder = {r: p for r, p in assigns}
    return sorted({(p, holder[r]) for p, r in requests if r in holder and holder[r] != p},
                  key=lambda e: (natural_key(e[0]), natural_key(e[1])))


def wait_for_dot(procs, edges, cycle=None):
    hot = set()
    if cycle:
        hot = {(cycle[k], cycle[k + 1]) for k in range(len(cycle) - 1)}
    lines = ["digraph W {", "rankdir=LR;", 'bgcolor="transparent";',
             'node [fontname="Helvetica", fontsize=13];', 'edge [color="#7a7a7a"];']
    for p in procs:
        lines.append(f'{p} [shape=circle, style=filled, fillcolor="#cfe8ff", fontcolor="#111111"];')
    for u, v in edges:
        extra = ' [color="#e53935", penwidth=2.8]' if (u, v) in hot else ""
        lines.append(f"{u} -> {v}{extra};")
    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Lecture 24: prevention simulators
# ----------------------------------------------------------------------------


def lock_simulation(needs: dict, order: dict | None = None, max_rounds: int = 40):
    """
    Round-based simulation of processes that acquire resources ONE AT A TIME in the
    order of their list, then finish and release everything.
    `order` (resource -> number) switches on the 'prevent circular wait' rule:
    every process then requests in increasing order of that number.
    """
    plan = {p: list(rs) for p, rs in needs.items()}
    if order:
        plan = {p: sorted(rs, key=lambda r: order[r]) for p, rs in plan.items()}
    holder: dict[str, str] = {}
    held = {p: [] for p in plan}
    finished: set[str] = set()
    log = []
    deadlock = False
    for rnd in range(1, max_rounds + 1):
        progress = False
        for p in plan:
            if p in finished:
                continue
            if len(held[p]) == len(plan[p]):
                for r in held[p]:
                    del holder[r]
                log.append({"Round": rnd, "Process": p, "Action": f"has everything, finishes and releases {', '.join(held[p])}"})
                finished.add(p)
                progress = True
                continue
            r = plan[p][len(held[p])]
            if r not in holder:
                holder[r] = p
                held[p].append(r)
                log.append({"Round": rnd, "Process": p, "Action": f"requests {r}  →  granted"})
                progress = True
            else:
                log.append({"Round": rnd, "Process": p, "Action": f"requests {r}  →  BLOCKED (held by {holder[r]})"})
        if len(finished) == len(plan):
            break
        if not progress:
            deadlock = True
            break
    stuck = [p for p in plan if p not in finished]
    assigns = [(r, p) for r, p in holder.items()]
    requests = [(p, plan[p][len(held[p])]) for p in stuck if len(held[p]) < len(plan[p])]
    return {"log": log, "deadlock": deadlock, "plan": plan, "assigns": assigns, "requests": requests, "stuck": stuck}


def preemption_scenario(protocol: int, p2_waiting: bool):
    """Narrated example for the two 'prevent no-preemption' protocols (slides 7.9-7.10)."""
    steps = [
        "Start: P1 holds R1, P2 holds R2" + (", and P2 is itself waiting for R3 (held by P3)." if p2_waiting else " and P2 is running (not waiting)."),
        "P1 now requests R2, which is not available.",
    ]
    if protocol == 1:
        steps += [
            "Protocol 1: P1 holds resources and cannot get the new one immediately  ⇒  ALL resources P1 holds (R1) are preempted.",
            "R1 is added to the list of resources P1 is waiting for, so P1 now waits for {R1, R2}.",
            "R1 is free again, so other processes can use it. P1 resumes only when it can regain R1 AND obtain R2.",
        ]
        outcome = "P1 loses R1 and waits for {R1, R2}."
    else:
        steps.append("Protocol 2: check whether R2 is available → no. Check whether R2 is held by a process that is waiting for more resources.")
        if p2_waiting:
            steps += [
                "Yes - P2 is waiting. So R2 is preempted from P2 and given to P1.",
                "R2 is added to the list of resources P2 is waiting for (P2 resumes only when it regains R2 and gets R3).",
            ]
            outcome = "P1 gets R2 by preempting it from the waiting P2."
        else:
            steps += [
                "No - P2 is running, so R2 cannot be taken from it.",
                "P1 simply waits. While P1 waits, its own resource R1 can be preempted if another process asks for it.",
            ]
            outcome = "P1 waits (no preemption possible)."
    return steps, outcome


# ----------------------------------------------------------------------------
# Lecture 27: recovery
# ----------------------------------------------------------------------------


def recover_by_termination(available, alloc, request, cost, all_at_once=False):
    """
    Detect, pick victim(s), terminate, release their resources, detect again.
    cost[i] = price of aborting process i (higher = worse victim).
    """
    n = len(alloc)
    active = list(range(n))
    avail = list(available)
    rounds, aborted = [], []
    for _ in range(n + 1):
        sub_alloc = [alloc[i] for i in active]
        sub_req = [request[i] for i in active]
        det = detection_algorithm(avail, sub_alloc, sub_req)
        dead = [active[k] for k in det["deadlocked"]]
        if not dead:
            rounds.append({"deadlocked": [], "victims": [], "freed": None})
            break
        victims = dead if all_at_once else [min(dead, key=lambda i: (cost[i], i))]
        freed = [0] * len(avail)
        for v in victims:
            freed = vadd(freed, alloc[v])
            avail = vadd(avail, alloc[v])
            active.remove(v)
            aborted.append(v)
        rounds.append({"deadlocked": dead, "victims": victims, "freed": freed})
    return {"rounds": rounds, "aborted": aborted, "survivors": active}


def preempt_victim(available, alloc, request, victim):
    """Resource preemption: take the victim's resources, roll it back, run detection again."""
    new_av = vadd(available, alloc[victim])
    new_alloc = [list(r) for r in alloc]
    new_alloc[victim] = [0] * len(alloc[victim])
    det = detection_algorithm(new_av, new_alloc, request)
    return {"available": new_av, "alloc": new_alloc, "detection": det}


def starvation_rounds(base_cost: dict, k: int, rounds: int = 8):
    """Same cheap victim again and again?  Add k * (number of rollbacks) to the cost."""
    rb = {p: 0 for p in base_cost}
    out = []
    for r in range(1, rounds + 1):
        costs = {p: base_cost[p] + k * rb[p] for p in base_cost}
        victim = min(costs, key=lambda p: (costs[p], natural_key(p)))
        out.append({"Round": r, **{f"cost {p}": costs[p] for p in base_cost}, "Victim": victim})
        rb[victim] += 1
    return out
