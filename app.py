"""
Deadlock Lab - interactive simulation of Chapter 7 (Deadlocks)
COMP-2115 Operating Systems | Lectures 23-27 | Silberschatz, Galvin & Gagne, 9th ed.

Run:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

import algos as A

st.set_page_config(page_title="Deadlock Lab - COMP-2115 Ch.7", page_icon="🔒", layout="wide")

# ----------------------------------------------------------------------------
# small UI helpers
# ----------------------------------------------------------------------------


def urdu(text):
    st.info(f"🇵🇰 **Roman Urdu mein:** {text}")


def real(text):
    st.success(f"🌍 **Real-world (IT) example:** {text}")


def show_graph(dot):
    st.graphviz_chart(dot)


def table(rows, **kw):
    st.dataframe(pd.DataFrame(rows), hide_index=True, **kw)


def to_int_matrix(df):
    return df.fillna(0).astype(int).values.tolist()


def names_of(prefix, n):
    return [f"{prefix}{i}" for i in range(n)]


def steps_table(steps, names, demand_label, lead_text=True):
    """Pretty table of the Work/Finish iterations."""
    rows = []
    for k, s in enumerate(steps, 1):
        rows.append(
            {
                "Step": k,
                "Pick": names[s["pick"]],
                f"{demand_label}(Pi)": A.fmt(s["demand"]),
                "Work (before)": A.fmt(s["work_before"]),
                "+ Allocation(Pi)": A.fmt(s["alloc"]),
                "Work (after)": A.fmt(s["work_after"]),
            }
        )
    table(rows)


def stuck_explanation(stuck, demand, work, names, demand_label):
    rows = [
        {
            "Process": names[i],
            f"{demand_label}(Pi)": A.fmt(demand[i]),
            "Work now": A.fmt(work),
            "Can run?": "❌ " + demand_label + " > Work",
        }
        for i in stuck
    ]
    table(rows)


def matrix_editor(rows, index, cols, key):
    df = pd.DataFrame(rows, index=index, columns=cols)
    return st.data_editor(df, key=key)


# ----------------------------------------------------------------------------
# HOME
# ----------------------------------------------------------------------------


def page_home():
    st.title("🔒 Deadlock Lab")
    st.subheader("Chapter 7 · Deadlocks · COMP-2115 Operating Systems")
    st.caption("Interactive simulation of Lectures 23-27 · Silberschatz, Galvin & Gagne, 9th Edition · Instructor: Usman Rafi")

    st.markdown(
        """
### What is a deadlock?
A **deadlock** is a situation where a set of processes are all *waiting*, and each one is waiting for a resource
that is **held by another process in the same set**. Nobody can move, so nobody ever releases anything - the wait is forever.

Think of four cars arriving at a crossroad at the same moment, each waiting for the car on its right to move first.
"""
    )
    real(
        "Two database transactions: T1 locks row A and wants row B, T2 locks row B and wants row A. "
        "Or two Python threads each holding one lock and wanting the other's. Same pattern, different resources."
    )

    st.markdown("### The 4 ways an OS can deal with deadlocks")
    table(
        [
            {"Strategy": "Deadlock Prevention", "Idea": "Make sure at least one of the 4 necessary conditions can never hold", "Lecture": "24"},
            {"Strategy": "Deadlock Avoidance", "Idea": "Allow requests only if the system stays in a SAFE state (needs max claims in advance)", "Lecture": "25-26"},
            {"Strategy": "Detection & Recovery", "Idea": "Let deadlock happen, detect it, then recover (terminate / preempt)", "Lecture": "27"},
            {"Strategy": "Ignore it (ostrich)", "Idea": "Pretend deadlocks never happen - mostly used by Windows and UNIX", "Lecture": "24"},
        ]
    )

    st.markdown("### Study map - use the sidebar")
    table(
        [
            {"Lecture": 23, "Topic": "Deadlock characterization (4 conditions), Resource-Allocation Graph", "Page": "1️⃣ Characterization & RAG"},
            {"Lecture": 24, "Topic": "Methods of handling deadlocks, Deadlock prevention", "Page": "2️⃣ Prevention"},
            {"Lecture": 25, "Topic": "Deadlock avoidance, safe/unsafe states, RAG algorithm", "Page": "3️⃣ Avoidance"},
            {"Lecture": 26, "Topic": "Banker's algorithm: data structures, safety, resource-request", "Page": "4️⃣ Banker's Algorithm"},
            {"Lecture": 27, "Topic": "Deadlock detection (wait-for graph, matrix algorithm), recovery", "Page": "5️⃣ Detection & Recovery"},
            {"Lecture": "-", "Topic": "Test yourself / one-page summary", "Page": "📝 Quiz · 📌 Cheat sheet"},
        ]
    )
    urdu(
        "Deadlock tab hota hai jab kuch processes ik dusre ke resources ka intezar kar rahe hon aur koi bhi aage na barh sake. "
        "Is app mein har lecture ka topic interactive tareeqay se chala kar dekh sakte hain - slides ke saare examples bhi pre-loaded hain."
    )


# ----------------------------------------------------------------------------
# LECTURE 23 - characterization + RAG
# ----------------------------------------------------------------------------


def rag_analysis_block(procs, res, assigns, requests, key):
    rep = A.rag_report(procs, res, assigns, requests)
    c1, c2 = st.columns([3, 2])
    with c1:
        show_graph(A.rag_dot(procs, res, assigns, requests, cycle=rep["cycle"]))
        st.caption("Circle = process · box with dots = resource type (one dot per instance) · P→R = request edge · R→P = assignment edge · red = cycle found")
    with c2:
        if rep["cycle"]:
            st.warning("Cycle found: **" + " → ".join(rep["cycle"]) + "**")
        else:
            st.success("No cycle in the graph.")
        (st.error if rep["deadlock"] else st.success)(rep["verdict"])
        st.markdown("**Same graph as matrices** (needed by the detection algorithm of Lecture 27)")
        cols = rep["rnames"]
        st.write("Allocation")
        st.dataframe(pd.DataFrame(rep["alloc"], index=procs, columns=cols))
        st.write("Request")
        st.dataframe(pd.DataFrame(rep["request"], index=procs, columns=cols))
        st.write("Available: " + A.fmt(rep["available"]) + "  for " + ", ".join(cols))
    if rep["cycle"] and not all(c == 1 for c in res.values()):
        st.markdown("**Why / why not?** Run the reduction (detection algorithm) on this graph:")
        det = rep["detection"]
        if det["steps"]:
            steps_table(det["steps"], procs, "Request")
        if det["deadlocked"]:
            st.error("Processes that can never finish: " + ", ".join(procs[i] for i in det["deadlocked"]))
        else:
            st.success("Every process can finish in some order, so there is no deadlock even though a cycle exists.")


def page_characterization():
    st.title("1️⃣ Deadlock Characterization & Resource-Allocation Graph")
    st.caption("Lecture 23")
    t1, t2, t3, t4 = st.tabs(["4 necessary conditions", "RAG vocabulary", "Slide examples", "Build your own RAG"])

    with t1:
        st.markdown("A deadlock **can arise only if all four conditions hold simultaneously**.")
        conds = [
            (
                "Mutual exclusion",
                "At least one resource must be held in a non-shareable mode: only one process at a time can use it.",
                "A single printer, a write lock on a file, a mutex.",
            ),
            (
                "Hold and wait",
                "A process holding at least one resource is waiting to acquire additional resources held by other processes.",
                "A thread holds lock A and blocks while trying to take lock B. A DB transaction keeps its row locks while waiting for another row.",
            ),
            (
                "No preemption",
                "A resource can be released only voluntarily by the process holding it, after that process has completed its task. It can't be taken by force.",
                "You cannot snatch a mutex from a running thread; a printer can't be taken away half-way through a print job.",
            ),
            (
                "Circular wait",
                "There is a set {P0, P1, …, Pn} where P0 waits for P1, P1 waits for P2, …, Pn waits for P0.",
                "T1 waits for T2's row lock, T2 waits for T1's row lock.",
            ),
        ]
        for name, definition, example in conds:
            with st.expander(f"**{name}**", expanded=False):
                st.write(definition)
                real(example)

        st.markdown("#### Condition checker")
        st.caption("Switch conditions on/off and see whether a deadlock is still possible.")
        cols = st.columns(4)
        flags = [cols[i].toggle(conds[i][0], value=True, key=f"cond{i}") for i in range(4)]
        if all(flags):
            st.error("All four conditions hold ⇒ a deadlock **can** occur. (They are *necessary*; whether it really happens depends on the actual request pattern.)")
        else:
            missing = [conds[i][0] for i in range(4) if not flags[i]]
            st.success(f"Deadlock is **impossible** because *{', '.join(missing)}* does not hold. This is exactly the idea of **deadlock prevention** (Lecture 24).")
        urdu("Deadlock ke liye chaaron conditions ek sath sach honi chahiyen. Ek bhi toot jaye to deadlock nahi ho sakta.")

    with t2:
        st.markdown(
            """
A deadlock can be described precisely with a **directed graph** called the *system resource-allocation graph*.

**Vertices (V)** - two kinds
- **Process** set P = {P1, P2, …, Pn}: all processes in the system
- **Resource** set R = {R1, R2, …, Rm}: all resource *types* (a type can have several instances)

**Edges (E)** - two kinds
- **Request edge** `Pi → Rj` : Pi has requested an instance of Rj and is waiting for it
- **Assignment edge** `Rj → Pi` : an instance of Rj is allocated to Pi
"""
        )
        procs = ["P1"]
        res = {"R1": 1, "R2": 4}
        show_graph(A.rag_dot(procs, res, [("R2", "P1")], [("P1", "R1")]))
        st.caption("Legend example: P1 holds one instance of R2 (a type with 4 instances) and requests R1 (a type with 1 instance).")
        st.markdown("**Basic facts** (slide 7.13)")
        st.markdown(
            "- No cycle ⇒ **no deadlock**\n"
            "- Cycle and only **one instance** per resource type ⇒ **deadlock**\n"
            "- Cycle and **several instances** per resource type ⇒ **possibility** of deadlock"
        )
        real("The OS's lock manager or a database engine keeps exactly this kind of graph internally (who holds which lock, who waits for which).")

    with t3:
        name = st.selectbox("Pick a graph from the slides", list(A.SLIDE_RAGS.keys()))
        g = A.SLIDE_RAGS[name]
        procs = A.processes_of(g["assigns"], g["requests"], g["claims"])
        rag_analysis_block(procs, g["res"], g["assigns"], g["requests"], key="slide")
        if "NO deadlock" in name:
            st.info("In the last graph, P2 and P4 are **not waiting**, so they can finish and release an instance. That lets P3 and then P1 continue - the cycle is only a *possibility*.")

    with t4:
        st.markdown(
            "Type your own graph. **Resources:** `R1:1, R2:2` (name:instances). "
            "**Edges, one per line:** `P1->R1` request · `R1->P2` assignment."
        )
        c1, c2 = st.columns(2)
        res_text = c1.text_input("Resources", "R1:1, R2:1")
        edge_text = c2.text_area("Edges", "R1->P1\nR2->P2\nP1->R2\nP2->R1", height=130)
        try:
            res = A.parse_resources(res_text)
            res, assigns, requests, _ = A.parse_edges(edge_text, res)
            procs = A.processes_of(assigns, requests, [])
            if not procs:
                st.info("Add at least one edge.")
            else:
                rag_analysis_block(procs, res, assigns, requests, key="custom")
        except ValueError as e:
            st.error(str(e))


# ----------------------------------------------------------------------------
# LECTURE 24 - prevention
# ----------------------------------------------------------------------------


def page_prevention():
    st.title("2️⃣ Methods of Handling Deadlocks & Deadlock Prevention")
    st.caption("Lecture 24")
    t0, t1, t2, t3, t4 = st.tabs(["Overview", "Mutual exclusion", "Hold and wait", "No preemption", "Circular wait"])

    with t0:
        st.markdown(
            "**Methods for handling deadlocks**\n"
            "1. Ensure the system will *never* enter a deadlock state → **prevention** or **avoidance**\n"
            "2. Allow the system to enter a deadlock state, **detect** it, then **recover**\n"
            "3. **Ignore** the problem and pretend deadlocks never occur - mostly used by Windows and UNIX"
        )
        st.markdown("**Prevention = make sure at least one necessary condition cannot hold.**")
        table(
            [
                {"Condition to break": "Mutual exclusion", "How": "Make resources sharable (e.g. read-only files)", "Problem": "Printers, write-locks are inherently non-sharable"},
                {"Condition to break": "Hold and wait", "How": "Request everything at start, OR request only when holding nothing", "Problem": "Starvation, low resource utilisation"},
                {"Condition to break": "No preemption", "How": "Preempt resources of a waiting process", "Problem": "Only works for resources whose state can be saved/restored"},
                {"Condition to break": "Circular wait", "How": "Total ordering of resource types; request in increasing order", "Problem": "Programmers must follow the order (but it is cheap and very practical)"},
            ]
        )
        urdu("Prevention ka matlab hai chaar mein se kam az kam ik condition ko kabhi sach hone hi na dena.")

    with t1:
        st.markdown(
            "Mutual exclusion **must** hold for non-sharable resources (write-only files, printers). "
            "**Sharable** resources (read-only files) never need exclusive access, so a process never waits for them and they **cannot be involved in a deadlock**."
        )
        items = {
            "Read-only file": True,
            "Printer": False,
            "File opened for writing": False,
            "Mutex / lock": False,
            "Read-only database table (snapshot)": True,
        }
        pick = st.selectbox("Choose a resource", list(items.keys()))
        if items[pick]:
            st.success(f"**{pick}** is sharable → several processes can use it at the same time → no waiting → can't cause deadlock.")
        else:
            st.error(f"**{pick}** is non-sharable → mutual exclusion must hold → we **can't** prevent deadlock by removing this condition.")
        real("Print spooling makes a printer *look* sharable: processes write to a spool queue and only the spooler touches the real printer. Databases use multi-version snapshots so readers don't lock out each other.")
        urdu("Sharable resource (jaise read-only file) mein koi intezar nahi, is liye deadlock nahi. Printer jaisi cheezon ko sharable nahi bana sakte.")

    with t2:
        st.markdown(
            "**Rule:** whenever a process requests a resource it must not hold any other resource.\n\n"
            "**Task (slides):** copy data from a DVD drive to a file on disk, sort the file, then print the result."
        )
        phases = ["1 Copy DVD → disk", "2 Sort file", "3 Print result"]
        res_names = ["DVD drive", "Disk", "Printer"]
        used = {"DVD drive": [1, 0, 0], "Disk": [1, 1, 1], "Printer": [0, 0, 1]}
        hold1 = {r: [1, 1, 1] for r in res_names}
        hold2 = {"DVD drive": [1, 0, 0], "Disk": [1, 1, 1], "Printer": [0, 0, 1]}

        def grid(hold):
            rows, held_slots, used_slots = [], 0, 0
            for r in res_names:
                row = {"Resource": r}
                for k, ph in enumerate(phases):
                    h, u = hold[r][k], used[r][k]
                    held_slots += h
                    used_slots += h and u
                    row[ph] = "🟩 held & used" if h and u else ("🟨 held but IDLE" if h else "· not held")
                rows.append(row)
            return rows, held_slots, used_slots

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Protocol 1 - request all resources before execution starts**")
            rows, h, u = grid(hold1)
            table(rows)
            st.metric("Utilisation of held resources", f"{u}/{h} = {100 * u // h}%")
            st.caption("The process holds the printer for its entire run even though it needs it only at the end. If the printer is busy, it waits without starting at all.")
        with c2:
            st.markdown("**Protocol 2 - request only when holding nothing**")
            rows, h, u = grid(hold2)
            table(rows)
            st.metric("Utilisation of held resources", f"{u}/{h} = {100 * u // h}%")
            st.caption("Copy: DVD+disk, then release both. Sort and print: ask for disk (and printer) again, holding nothing else at that moment.")
        st.warning(
            "**Problems with both protocols:**  \n"
            "• **Starvation** - a process that needs several popular resources may wait indefinitely.  \n"
            "• **Under-utilisation** - resources may be allocated but unused for a long period."
        )
        real("A batch job that grabs a GPU, a licence and a database connection at start-up and holds them for hours while it only needs the GPU at the end. Cloud schedulers (gang scheduling) do 'all-or-nothing' allocation for the same reason - and pay the idle-resource price.")
        urdu("Hold-and-wait rokne ke do tareeqay: shuru mein sab resources ek sath maang lo, ya naya resource tab maango jab kuch hold na kar rahe ho. Nuqsan: starvation aur resources ka zaya hona.")

    with t3:
        st.markdown("Scenario: P1 holds **R1** and requests **R2**; P2 holds **R2**. Pick a protocol and what P2 is doing.")
        c1, c2 = st.columns(2)
        proto = c1.radio("Protocol", [1, 2], format_func=lambda x: f"Protocol {x}", horizontal=True)
        p2w = c2.radio("P2 is…", [False, True], format_func=lambda w: "waiting for another resource (R3)" if w else "running (not waiting)", horizontal=True)
        steps, outcome = A.preemption_scenario(proto, p2w)
        for k, s in enumerate(steps, 1):
            st.markdown(f"**{k}.** {s}")
        st.success("Outcome: " + outcome)
        st.markdown(
            "- **Protocol 1:** if a process holding resources requests one that can't be allocated immediately, *all* resources it holds are preempted and added to the list it is waiting for.\n"
            "- **Protocol 2:** if the requested resources are held by a process that is *waiting* for more resources, preempt them from that waiting process and give them to the requester."
        )
        real("CPU registers and memory pages can be saved and restored, so they can be preempted safely. A half-written file or a printer mid-job can't - that's why this method isn't used for them. Databases do it with 'wound-wait / wait-die' schemes.")

    with t4:
        st.markdown(
            "Impose a **total ordering F** of all resource types and require every process to request resources "
            "**in increasing order of F**. Then a circular wait can never form."
        )
        c = st.columns(3)
        F = {
            "tape drive": c[0].number_input("F(tape drive)", value=1, step=1),
            "disk drive": c[1].number_input("F(disk drive)", value=5, step=1),
            "printer": c[2].number_input("F(printer)", value=12, step=1),
        }
        if len(set(F.values())) < 3:
            st.error("Every resource type needs a different F value (it is a *total* ordering).")
            F = {"tape drive": 1, "disk drive": 5, "printer": 12}
            st.info("Showing the slide values (1, 5, 12) until you fix this.")
        needs = {"A": ["printer", "tape drive"], "B": ["tape drive", "disk drive"], "C": ["disk drive", "printer"]}
        st.markdown("Processes (slides): **A** needs (printer, tape drive) · **B** needs (tape drive, disk drive) · **C** needs (disk drive, printer)")
        left, right = st.columns(2)
        for col, enforce in ((left, False), (right, True)):
            with col:
                sim = A.lock_simulation(needs, F if enforce else None)
                st.markdown("#### " + ("✅ WITH ordering rule" if enforce else "❌ WITHOUT ordering rule"))
                st.caption("Request order used: " + " · ".join(f"{p}: {' → '.join(r)}" for p, r in sim["plan"].items()))
                table(sim["log"])
                if sim["deadlock"]:
                    st.error("DEADLOCK - no process can make progress: " + ", ".join(sim["stuck"]))
                    nodes = {"tape drive": "Tape", "disk drive": "Disk", "printer": "Printer"}
                    rn = {n: nodes[n] for n in nodes}
                    assigns = [(rn[r], p) for r, p in sim["assigns"]]
                    requests = [(p, rn[r]) for p, r in sim["requests"]]
                    res = {v: 1 for v in rn.values()}
                    rep = A.rag_report(sim["stuck"], res, assigns, requests)
                    show_graph(A.rag_dot(sim["stuck"], res, assigns, requests, cycle=rep["cycle"]))
                else:
                    st.success("All processes finished - no deadlock.")
        st.markdown(
            "**Why it works (proof sketch):** suppose a circular wait existed: P0 holds R0 and waits for R1 held by P1 … Pn holds Rn and waits for R0. "
            "Because each process asks in increasing order, F(R0) < F(R1) < … < F(Rn) < F(R0), which is impossible."
        )
        st.markdown("**Same idea in code (Python threads):**")
        c1, c2 = st.columns(2)
        c1.code(
            "# ❌ can deadlock\n"
            "def worker1():\n    with lock_a:\n        with lock_b:\n            work()\n\n"
            "def worker2():\n    with lock_b:      # opposite order!\n        with lock_a:\n            work()",
            language="python",
        )
        c2.code(
            "# ✅ lock ordering: always a, then b\n"
            "def worker1():\n    with lock_a:\n        with lock_b:\n            work()\n\n"
            "def worker2():\n    with lock_a:      # same order\n        with lock_b:\n            work()",
            language="python",
        )
        real("The Linux kernel documents a lock-ordering hierarchy and checks it with *lockdep*; applications that update several DB tables always touch them in the same order.")
        urdu("Har resource ko ik number do aur har process se kaho ke resources hamesha barhte hue number ke order mein maange. Is se circular wait mumkin hi nahi rehta.")


# ----------------------------------------------------------------------------
# LECTURE 25 - avoidance
# ----------------------------------------------------------------------------

SAFE_SVG = """
<svg viewBox="0 0 420 270" width="100%" style="max-width:460px">
  <rect x="5" y="5" width="410" height="260" rx="8" fill="#cfd8dc"/>
  <polygon points="5,5 415,5 415,125 5,185" fill="#bfe3f7"/>
  <rect x="30" y="25" width="150" height="62" fill="#9fa8b0" stroke="#37474f" stroke-width="2"/>
  <text x="105" y="62" font-family="Helvetica" font-size="17" text-anchor="middle" fill="#111">deadlock</text>
  <text x="350" y="40" font-family="Helvetica" font-size="17" text-anchor="middle" fill="#111">unsafe</text>
  <text x="300" y="205" font-family="Helvetica" font-size="17" text-anchor="middle" fill="#111">safe</text>
</svg>
"""


def page_avoidance():
    st.title("3️⃣ Deadlock Avoidance")
    st.caption("Lecture 25")
    t0, t1, t2, t3 = st.tabs(["Concept", "Safe & unsafe states", "Safe / unsafe / deadlock", "Resource-allocation graph algorithm"])

    with t0:
        st.markdown(
            "Avoidance requires **a priori information**. The simplest, most useful model: each process declares the **maximum number of resources of each type it may need**.\n\n"
            "The algorithm dynamically examines the **resource-allocation state** - the number of *available* and *allocated* resources and the *maximum demands* of the processes - "
            "to ensure there can never be a circular-wait condition.\n\n"
            "When a process requests an available resource, the system decides whether granting it immediately leaves the system in a **safe state**. "
            "The request is granted **only if** the state stays safe; otherwise the process waits."
        )
        table(
            [
                {"System has…": "Single instance of each resource type", "Use": "Resource-allocation graph (this lecture)"},
                {"System has…": "Multiple instances of a resource type", "Use": "Banker's algorithm (Lecture 26)"},
            ]
        )
        real("A cloud scheduler that knows each job's maximum CPU/RAM quota can refuse to start a job if starting it could leave the cluster unable to finish everyone - that's avoidance. The price: users must declare their maximum needs up front.")
        urdu("Avoidance mein har process pehle batati hai ke zyada se zyada kitne resources chahiyen. OS sirf wohi request manzoor karta hai jis ke baad system 'safe' rahe.")

    with t1:
        st.markdown(
            "**Safe state:** there exists a sequence ⟨P1, P2, …, Pn⟩ of **all** processes such that for each Pi, the resources Pi can still request can be satisfied by "
            "*currently available resources + resources held by all Pj with j < i*.  \n"
            "**Unsafe state:** no such sequence exists. Not all unsafe states are deadlocks - an unsafe state *may* lead to deadlock."
        )
        st.markdown("#### Magnetic tape drive example (slides)")
        preset = st.radio(
            "Situation",
            ["t0 (slide)", "t1: P2 is allocated one more tape drive", "Custom"],
            horizontal=True,
        )
        total = 12
        mx = [10, 4, 9]
        al = [5, 2, 2]
        if preset.startswith("t1"):
            al = [5, 2, 3]
        if preset == "Custom":
            c = st.columns(7)
            total = c[0].number_input("Total drives", 1, 100, 12)
            mx = [c[1 + i].number_input(f"Max P{i}", 0, 100, v) for i, v in enumerate(mx)]
            al = [c[4 + i].number_input(f"Alloc P{i}", 0, 100, v) for i, v in enumerate(al)]
        names = ["P0", "P1", "P2"]
        if sum(al) > total or any(a > m for a, m in zip(al, mx)):
            st.error("Allocation can't exceed the total drives or a process's maximum.")
        else:
            alloc = [[a] for a in al]
            need = A.need_matrix([[m] for m in mx], alloc)
            av = A.available_vector([total], alloc)
            table(
                [
                    {"Process": names[i], "Maximum": mx[i], "Allocated": al[i], "Need = Max − Alloc": need[i][0]}
                    for i in range(3)
                ]
            )
            st.write(f"Available = {total} − ({' + '.join(map(str, al))}) = **{av[0]}**")
            res = A.safety_algorithm(av, alloc, need)
            if res["safe"]:
                st.success("SAFE state. Safe sequence: ⟨" + ", ".join(names[i] for i in res["sequence"]) + "⟩")
                steps_table(res["steps"], names, "Need")
            else:
                st.error("UNSAFE state - no safe sequence exists (deadlock is possible).")
                if res["steps"]:
                    steps_table(res["steps"], names, "Need")
                st.write("Stuck processes:")
                stuck_explanation(res["stuck"], need, res["work"], names, "Need")
            if preset.startswith("t0"):
                st.markdown("**What if, at t1, P2 asks for one more tape drive?** Let's apply the avoidance rule:")
                r = A.resource_request(2, [1], av, alloc, need)
                if r["status"] == "unsafe":
                    st.error("Granting it would leave the system UNSAFE ⇒ **P2 must wait**, even though a drive is free. Avoidance never lets the system enter an unsafe state.")
                else:
                    st.success("Granting would stay safe.")
        urdu("Safe state mein koi na koi tarteeb (safe sequence) hoti hai jis mein har process apna kaam mukammal kar sakti hai. Unsafe ka matlab deadlock zaroor nahi, bas khatra hai.")

    with t2:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(SAFE_SVG, unsafe_allow_html=True)
        with c2:
            st.markdown(
                "**Basic facts**\n"
                "- Safe state ⇒ **no deadlock**\n"
                "- Unsafe state ⇒ **possibility** of deadlock\n"
                "- Avoidance ⇒ ensure the system will **never enter an unsafe state**\n\n"
                "Deadlock states are a *subset* of unsafe states."
            )
            st.markdown(
                "**Intuition:** being unsafe means 'if everyone now asks for their maximum, someone is stuck'. "
                "The processes might not ask for their maximum at the same time (so no deadlock), but the OS can no longer *guarantee* it."
            )

    with t3:
        st.markdown(
            "For **single-instance** resources we add a **claim edge** `Pi ⇢ Rj` (dashed): Pi *may* request Rj in future (declared a priori).\n"
            "- claim edge → **request edge** when the process requests the resource\n"
            "- request edge → **assignment edge** when it is allocated\n"
            "- assignment edge → back to **claim edge** when the resource is released\n\n"
            "**Algorithm:** grant a request only if converting the request edge to an assignment edge does **not create a cycle** (claim edges count as edges when looking for the cycle)."
        )
        procs = ["P1", "P2"]
        res = {"R1": 1, "R2": 1}
        assigns = [("R1", "P1")]
        requests = [("P2", "R1")]
        claims = [("P1", "R2"), ("P2", "R2")]
        st.markdown("**Current state (slide):** R1 is assigned to P1, P2 is waiting for R1, and both P1 and P2 have claim edges to R2.")
        show_graph(A.rag_dot(procs, res, assigns, requests, claims))
        who = st.radio("Now … requests R2", ["P1", "P2"], horizontal=True)
        new_assigns = assigns + [("R2", who)]
        new_claims = [c for c in claims if c != (who, "R2")]
        edges = A.rag_edges(new_assigns, requests, new_claims, include_claims=True)
        cyc = A.find_cycle(edges)
        st.markdown(f"**If R2 is granted to {who}** (request → assignment edge):")
        show_graph(A.rag_dot(procs, res, new_assigns, requests, new_claims, cycle=cyc))
        if cyc:
            st.error(f"Cycle {' → '.join(cyc)} would form ⇒ the state would be **UNSAFE** ⇒ request **denied**, {who} must wait. (This is the slide 'Unsafe state in RAG'.)")
        else:
            st.success(f"No cycle ⇒ the state stays **safe** ⇒ request **granted** to {who}.")
        st.warning("This only works when every resource type has a **single instance**. With multiple instances we need the Banker's algorithm.")


# ----------------------------------------------------------------------------
# LECTURE 26 - Banker's algorithm
# ----------------------------------------------------------------------------

BANKER_PRESETS = {
    "Slide example - snapshot at T0": dict(
        alloc=[[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
        mx=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
        note="Try: P1 requests (1,0,2) → granted. P4 requests (3,3,0) → can't be granted safely.",
    ),
    "State after P1's request (1,0,2) was granted": dict(
        alloc=[[0, 1, 0], [3, 0, 2], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
        mx=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
        note="Try: P4 requests (3,3,0) → exceeds Available, must wait. P0 requests (0,2,0) → resources exist, but the resulting state is unsafe.",
    ),
}


def banker_state_ui():
    name = st.selectbox("Load a state", list(BANKER_PRESETS.keys()))
    pre = BANKER_PRESETS[name]
    st.caption(pre["note"])
    rn = ["A", "B", "C"]
    cols = st.columns(3)
    total = [cols[j].number_input(f"Total instances of {rn[j]}", 0, 99, v, key=f"tot{j}_{name}") for j, v in enumerate([10, 5, 7])]
    pn = names_of("P", 5)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Allocation** (editable)")
        alloc = to_int_matrix(matrix_editor(pre["alloc"], pn, rn, f"alloc_{name}"))
    with c2:
        st.markdown("**Max** (editable)")
        mx = to_int_matrix(matrix_editor(pre["mx"], pn, rn, f"max_{name}"))
    need = A.need_matrix(mx, alloc)
    av = A.available_vector(total, alloc)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Need = Max − Allocation**")
        st.dataframe(pd.DataFrame(need, index=pn, columns=rn))
    with c4:
        st.markdown("**Available = Total − Σ Allocation**")
        st.dataframe(pd.DataFrame([av], index=["Available"], columns=rn))
    problems = []
    if any(v < 0 for v in av):
        problems.append("Σ Allocation exceeds the total instances of some resource (Available < 0).")
    if any(v < 0 for row in need for v in row):
        problems.append("Some Allocation is larger than that process's Max (Need < 0).")
    for p in problems:
        st.error(p)
    return dict(names=pn, rn=rn, total=total, alloc=alloc, mx=mx, need=need, av=av, ok=not problems)


def page_banker():
    st.title("4️⃣ Banker's Algorithm")
    st.caption("Lecture 26")
    t0, t1, t2 = st.tabs(["Concept & data structures", "Safety algorithm", "Resource-request algorithm"])

    with t0:
        st.markdown(
            "Used for **multiple instances of different resources**.\n"
            "- Each process must claim its **maximum use a priori**\n"
            "- When a process requests a resource it **may have to wait**\n"
            "- When a process gets all its resources it must **return them in a finite amount of time**\n\n"
            "Let **n** = number of processes, **m** = number of resource types."
        )
        table(
            [
                {"Structure": "Available", "Shape": "vector, length m", "Meaning": "Available[j] = k → k instances of Rj are free"},
                {"Structure": "Max", "Shape": "n × m", "Meaning": "Max[i,j] = k → Pi may request at most k instances of Rj"},
                {"Structure": "Allocation", "Shape": "n × m", "Meaning": "Allocation[i,j] = k → Pi currently holds k instances of Rj"},
                {"Structure": "Need", "Shape": "n × m", "Meaning": "Need[i,j] = Max[i,j] − Allocation[i,j]: what Pi may still need"},
            ]
        )
        real("Name comes from banking: a bank never lends out cash so that it couldn't satisfy the maximum credit lines of all customers. In IT: a cluster manager with a fixed pool of vCPUs/RAM/GPUs deciding whether to give a job more quota; or an OS deciding about memory/file handles.")
        urdu("Banker's algorithm bank ki tarah sochta hai: udhaar (resource) tabhi do jab baad mein sab customers (processes) ko unka maximum de kar wapas lena mumkin ho. Need = Max − Allocation.")

    st.markdown("---")
    st.markdown("### The state (used by both algorithm tabs)")
    S = banker_state_ui()
    st.markdown("---")

    with t1:
        st.markdown(
            "**Safety algorithm**\n"
            "1. `Work = Available`, `Finish[i] = false` for all i\n"
            "2. Find an i with `Finish[i] = false` and `Need_i ≤ Work`; if none, go to step 4\n"
            "3. `Work = Work + Allocation_i`, `Finish[i] = true`, go to step 2\n"
            "4. If `Finish[i] = true` for all i → the system is **safe**"
        )
        if not S["ok"]:
            st.info("Fix the state above first.")
        else:
            res = A.safety_algorithm(S["av"], S["alloc"], S["need"])
            if res["steps"]:
                st.markdown("**Iterations** (always taking the lowest-numbered process that fits):")
                steps_table(res["steps"], S["names"], "Need")
            if res["safe"]:
                st.success("✅ SAFE. One safe sequence: ⟨" + ", ".join(S["names"][i] for i in res["sequence"]) + "⟩")
            else:
                st.error("❌ UNSAFE. These processes can never be satisfied: " + ", ".join(S["names"][i] for i in res["stuck"]))
                stuck_explanation(res["stuck"], S["need"], res["work"], S["names"], "Need")
            st.caption("A state can have several safe sequences. Check one yourself:")
            default = "P1,P3,P4,P2,P0" if S["total"] == [10, 5, 7] else ""
            txt = st.text_input("Sequence to verify (comma separated)", default)
            if txt.strip():
                try:
                    seq = [S["names"].index(x.strip().upper()) for x in txt.split(",")]
                except ValueError:
                    st.error("Use process names from the table, e.g. P1,P3,P4,P2,P0.")
                else:
                    if sorted(seq) != list(range(len(S["names"]))):
                        st.error("A safe sequence must contain every process exactly once.")
                    else:
                        ok, log = A.check_sequence(seq, S["av"], S["alloc"], S["need"])
                        table(
                            [
                                {
                                    "Pick": S["names"][r["pick"]],
                                    "Need(Pi)": A.fmt(r["demand"]),
                                    "Work (before)": A.fmt(r["work_before"]),
                                    "Need ≤ Work?": "✅" if r["ok"] else "❌",
                                    "Work (after)": A.fmt(r["work_after"]) if r["ok"] else "-",
                                }
                                for r in log
                            ]
                        )
                        (st.success if ok else st.error)("⟨" + ", ".join(txt.upper().split()) + "⟩ is " + ("a valid safe sequence." if ok else "NOT a safe sequence."))

    with t2:
        st.markdown(
            "**Resource-request algorithm for Pi**  (`Request_i` = request vector)\n"
            "1. If `Request_i ≤ Need_i` go to 2, else **error** (exceeded maximum claim)\n"
            "2. If `Request_i ≤ Available` go to 3, else Pi must **wait**\n"
            "3. *Pretend* to allocate: `Available −= Request_i`, `Allocation_i += Request_i`, `Need_i −= Request_i`. "
            "Run the safety algorithm: **safe → grant**, **unsafe → Pi waits and the old state is restored**"
        )
        if not S["ok"]:
            st.info("Fix the state above first.")
        else:
            c = st.columns(1 + len(S["rn"]))
            who = c[0].selectbox("Process", S["names"], index=1)
            req = [c[1 + j].number_input(f"Request {S['rn'][j]}", 0, 99, v, key=f"req{j}") for j, v in enumerate([1, 0, 2])]
            i = S["names"].index(who)
            r = A.resource_request(i, req, S["av"], S["alloc"], S["need"])
            st.markdown(f"**Step 1** - Request {A.fmt(req)} ≤ Need({who}) {A.fmt(S['need'][i])}?")
            if r["status"] == "error":
                st.error("No → " + r["why"])
            else:
                st.write("Yes.")
                st.markdown(f"**Step 2** - Request {A.fmt(req)} ≤ Available {A.fmt(S['av'])}?")
                if r["status"] == "wait":
                    st.warning("No → " + r["why"])
                else:
                    st.write("Yes.")
                    st.markdown("**Step 3** - pretend to allocate:")
                    st.dataframe(
                        pd.DataFrame(
                            {
                                "Available": [A.fmt(S["av"]), A.fmt(r["available"])],
                                f"Allocation({who})": [A.fmt(S["alloc"][i]), A.fmt(r["alloc"][i])],
                                f"Need({who})": [A.fmt(S["need"][i]), A.fmt(r["need"][i])],
                            },
                            index=["before", "after (pretend)"],
                        )
                    )
                    sf = r["safety"]
                    steps_table(sf["steps"], S["names"], "Need") if sf["steps"] else None
                    if r["status"] == "granted":
                        st.success(f"✅ The new state is SAFE (sequence ⟨{', '.join(S['names'][k] for k in sf['sequence'])}⟩) → **request granted**.")
                    else:
                        st.error("❌ The new state is UNSAFE → **{} must wait** and the old state is restored.".format(who))
                        stuck_explanation(sf["stuck"], r["need"], sf["work"], S["names"], "Need")
        urdu("Request aane par pehle check karo ke request <= Need aur request <= Available hai. Phir farz karo ke de di, aur safety algorithm chalao. Safe ho to de do, warna process intezar kare.")


# ----------------------------------------------------------------------------
# LECTURE 27 - detection & recovery
# ----------------------------------------------------------------------------

DET_PRESETS = {
    "Slide example - snapshot at T0": dict(
        alloc=[[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
        req=[[0, 0, 0], [2, 0, 2], [0, 0, 0], [1, 0, 0], [0, 0, 2]],
        note="Sequence ⟨P0, P2, P3, P1, P4⟩ gives Finish[i] = true for all i → no deadlock.",
    ),
    "P2 requests an additional instance of C": dict(
        alloc=[[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
        req=[[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0], [0, 0, 2]],
        note="P0's resources can be reclaimed but that is not enough for anyone else → deadlock among P1, P2, P3, P4.",
    ),
}

DEADLOCK_ALLOC = DET_PRESETS["P2 requests an additional instance of C"]["alloc"]
DEADLOCK_REQ = DET_PRESETS["P2 requests an additional instance of C"]["req"]


def page_detection():
    st.title("5️⃣ Deadlock Detection & Recovery")
    st.caption("Lecture 27")
    t0, t1, t2, t3, t4, t5 = st.tabs(
        ["Overview", "Single instance: wait-for graph", "Several instances: detection algorithm", "When to run detection", "Recovery: process termination", "Recovery: resource preemption"]
    )

    with t0:
        st.markdown(
            "Here the system is **allowed to enter a deadlock state**. It needs\n"
            "1. a **detection algorithm** - detects the presence or absence of deadlock\n"
            "2. a **recovery scheme** - gets the system out of the deadlock"
        )
        real("MySQL/InnoDB and PostgreSQL keep a wait-for graph of transactions. When they find a cycle they pick a victim transaction and roll it back - you see the error *'Deadlock found when trying to get lock; try restarting transaction'* and your app simply retries.")
        urdu("Is method mein deadlock hone diya jata hai, phir algorithm se pakra jata hai, aur recovery se (process terminate ya resource preempt karke) nikala jata hai.")

    with t1:
        st.markdown(
            "**Single instance of each resource type** → maintain a **wait-for graph**: nodes are processes, and `Pi → Pj` if Pi is waiting for Pj. "
            "Periodically search for a **cycle**; a cycle means deadlock. It's the resource-allocation graph with the resource nodes removed."
        )
        default = "P1->R1\nR1->P2\nP2->R3\nR3->P5\nP2->R4\nR4->P3\nP3->R5\nR5->P4\nP2->R5\nP4->R2\nR2->P1"
        txt = st.text_area("Resource-allocation graph (slide 7.6 pre-loaded; `Pi->Rj` request, `Rj->Pi` assignment)", default, height=190)
        try:
            res, assigns, requests, _ = A.parse_edges(txt, {})
            err = None if all(c == 1 for c in res.values()) else "The wait-for graph works only for single-instance resources."
        except ValueError as e:
            res, assigns, requests, err = {}, [], [], str(e)
        if err:
            st.error(err)
        else:
            procs = A.processes_of(assigns, requests, [])
            wf = A.wait_for_graph(requests, assigns)
            cyc = A.find_cycle(wf)
            rag_cyc = A.find_cycle(A.rag_edges(assigns, requests))
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**(a) Resource-allocation graph**")
                show_graph(A.rag_dot(procs, res, assigns, requests, cycle=rag_cyc))
            with c2:
                st.markdown("**(b) Corresponding wait-for graph**")
                show_graph(A.wait_for_dot(procs, wf, cyc))
            st.caption("Edges of the wait-for graph: " + (", ".join(f"{u}→{v}" for u, v in wf) or "none"))
            if cyc:
                st.error("Cycle **" + " → ".join(cyc) + "** ⇒ DEADLOCK. Processes in the cycle are deadlocked.")
            else:
                st.success("No cycle in the wait-for graph ⇒ no deadlock.")
            st.caption("The algorithm needs about O(n²) time for n processes, as it searches the graph for a cycle.")

    with t2:
        st.markdown(
            "**Several instances of a resource type** - data structures similar to the Banker's algorithm: "
            "**Available** (vector, length m), **Allocation** (n×m), **Request** (n×m; `Request[i][j] = k` → Pi is requesting k more instances of Rj).\n\n"
            "**Detection algorithm**\n"
            "1. `Work = Available`; for each i: `Finish[i] = false` if `Allocation_i ≠ 0`, else `true`\n"
            "2. Find i with `Finish[i] = false` and `Request_i ≤ Work`; if none go to 4\n"
            "3. `Work = Work + Allocation_i`, `Finish[i] = true`, go to 2\n"
            "4. If `Finish[i] = false` for some i, the system is **deadlocked**, and every such Pi is deadlocked"
        )
        st.caption("Difference from the safety algorithm: it uses *Request* (what the process is waiting for right now) instead of *Need* (what it might ask for in the future).")
        name = st.selectbox("Load a state", list(DET_PRESETS.keys()))
        pre = DET_PRESETS[name]
        st.caption(pre["note"] + "  (Resources: A has 7, B has 2, C has 6 instances.)")
        rn, pn = ["A", "B", "C"], names_of("P", 5)
        avc = st.columns(3)
        av = [avc[j].number_input(f"Available {rn[j]}", 0, 99, 0, key=f"dav{j}_{name}") for j in range(3)]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Allocation**")
            alloc = to_int_matrix(matrix_editor(pre["alloc"], pn, rn, f"dal_{name}"))
        with c2:
            st.markdown("**Request**")
            req = to_int_matrix(matrix_editor(pre["req"], pn, rn, f"dre_{name}"))
        det = A.detection_algorithm(av, alloc, req)
        init = [all(a == 0 for a in row) for row in alloc]
        st.markdown("Initial Finish: " + ", ".join(f"{pn[i]}={'true' if init[i] else 'false'}" for i in range(5)) + "  (true when the process holds nothing)")
        if det["steps"]:
            steps_table(det["steps"], pn, "Request")
        if det["deadlocked"]:
            st.error("❌ DEADLOCK. Deadlocked processes: " + ", ".join(pn[i] for i in det["deadlocked"]))
            stuck_explanation(det["deadlocked"], req, det["work"], pn, "Request")
        else:
            st.success("✅ No deadlock. Order found: ⟨" + ", ".join(pn[i] for i in det["sequence"]) + "⟩")
        ok, log = A.check_sequence([0, 2, 3, 1, 4], av, alloc, req)
        if name.startswith("Slide"):
            st.caption("The slide's sequence ⟨P0, P2, P3, P1, P4⟩ is also valid: " + ("yes ✅" if ok else "no ❌") + " (several orders can work; the answer is the same).")

    with t3:
        st.markdown(
            "**When, and how often, should the detection algorithm be invoked?** It depends on\n"
            "1. **How often a deadlock is likely to occur**\n"
            "2. **How many processes will need to be rolled back** (one for each disjoint cycle)"
        )
        table(
            [
                {"Strategy": "Every time a request can't be granted immediately", "Good": "Finds deadlock at once; knows exactly which request closed the cycle", "Bad": "Large CPU overhead"},
                {"Strategy": "At fixed intervals (e.g. once an hour)", "Good": "Cheap", "Bad": "Deadlocked processes and the resources they hold sit idle until the next run"},
                {"Strategy": "When CPU utilisation drops (e.g. below 40%)", "Good": "Deadlock typically makes processes block, so utilisation falls", "Bad": "Detection comes some time after the deadlock formed"},
            ]
        )
        st.markdown(
            "If detection is run at arbitrary times, the resource graph may contain **many cycles**, and we usually can't tell which of the many deadlocked processes 'caused' the deadlock."
        )

    with t4:
        st.markdown(
            "**Recovery by process termination** - abort **all** deadlocked processes (certain but costly: lots of work lost), or abort **one at a time** until the cycle is eliminated "
            "(needs re-running detection after each abort). Which one first? Factors from the slide: priority · how long it has computed and how much longer to completion · resources used · resources needed to complete · "
            "how many processes will need to be terminated · interactive or batch."
        )
        st.markdown("**Simulation on the deadlocked state of the slides** (P2 asked for one more C; P1-P4 are deadlocked)")
        pn = names_of("P", 5)
        held = [sum(r) for r in DEADLOCK_ALLOC]
        st.markdown("Edit the table; **cost = how bad it is to abort this process** (higher = worse victim).")
        base = pd.DataFrame(
            {
                "Priority": [1, 3, 2, 4, 2],
                "Computed (min)": [5, 10, 2, 8, 1],
                "Remaining (min)": [1, 5, 9, 4, 6],
                "Interactive (1/0)": [0, 1, 0, 1, 0],
            },
            index=pn,
        )
        df = st.data_editor(base, key="cost_tbl")
        w = st.columns(5)
        w_pri = w[0].slider("weight: priority", 0, 10, 3)
        w_done = w[1].slider("weight: time computed", 0, 10, 1)
        w_rem = w[2].slider("weight: time remaining (more left = cheaper to kill)", 0, 10, 1)
        w_int = w[3].slider("weight: interactive", 0, 10, 5)
        w_res = w[4].slider("weight: resources held (more held = cheaper to kill, frees more)", 0, 10, 1)
        cost = [
            float(w_pri * df.iloc[i, 0] + w_done * df.iloc[i, 1] - w_rem * df.iloc[i, 2] + w_int * df.iloc[i, 3] - w_res * held[i])
            for i in range(5)
        ]
        st.write("Abort cost per process: " + ", ".join(f"**{pn[i]}** = {cost[i]:g}" for i in range(5)))
        mode = st.radio("Strategy", ["Abort one at a time (cheapest victim first)", "Abort all deadlocked processes"], horizontal=True)
        out = A.recover_by_termination([0, 0, 0], DEADLOCK_ALLOC, DEADLOCK_REQ, cost, all_at_once=mode.startswith("Abort all"))
        rows = []
        for k, rd in enumerate(out["rounds"], 1):
            if rd["victims"]:
                rows.append(
                    {
                        "Round": k,
                        "Deadlocked": ", ".join(pn[i] for i in rd["deadlocked"]),
                        "Aborted": ", ".join(pn[i] for i in rd["victims"]),
                        "Resources freed": A.fmt(rd["freed"]),
                    }
                )
            else:
                rows.append({"Round": k, "Deadlocked": "none ✅", "Aborted": "-", "Resources freed": "-"})
        table(rows)
        st.metric("Processes terminated", len(out["aborted"]))
        st.caption("Compare both strategies: aborting one at a time usually terminates far fewer processes, but needs detection to be run again after every abort.")
        real("An OS killing a hung process via the OOM-killer or a DB rolling back the cheapest transaction (fewest rows changed) are cost-based victim selection.")

    with t5:
        st.markdown(
            "**Recovery by resource preemption** - take resources away from some processes and give them to others until the deadlock cycle is broken. Three issues:\n"
            "1. **Selecting a victim** - minimise cost\n"
            "2. **Rollback** - return the victim to some safe state and restart it from that state\n"
            "3. **Starvation** - the same process may always be picked as victim; include the **number of rollbacks in the cost factor**"
        )
        st.markdown("#### Try preempting a victim")
        pn = names_of("P", 5)
        dead = A.detection_algorithm([0, 0, 0], DEADLOCK_ALLOC, DEADLOCK_REQ)["deadlocked"]
        victim = st.selectbox("Preempt resources of…", [pn[i] for i in dead])
        v = pn.index(victim)
        pr = A.preempt_victim([0, 0, 0], DEADLOCK_ALLOC, DEADLOCK_REQ, v)
        st.write(f"{victim} loses its Allocation {A.fmt(DEADLOCK_ALLOC[v])} and is rolled back. Available becomes {A.fmt(pr['available'])}.")
        if pr["detection"]["deadlocked"]:
            st.error("Still deadlocked: " + ", ".join(pn[i] for i in pr["detection"]["deadlocked"]) + " → choose another victim.")
        else:
            st.success("Deadlock resolved. Order that now works: ⟨" + ", ".join(pn[i] for i in pr["detection"]["sequence"]) + "⟩. The victim restarts from its safe state and must re-request what it lost.")
        st.markdown("#### Starvation demo")
        st.caption("Three deadlocks happen again and again. Each time the cheapest process is the victim. Without a rollback term, the same process is hit forever.")
        k = st.slider("Cost added per previous rollback (k)", 0, 10, 4)
        base = {"P1": 3, "P2": 5, "P3": 7}
        a, b = st.columns(2)
        a.markdown("**k = 0 (no rollback factor)**")
        a.dataframe(pd.DataFrame(A.starvation_rounds(base, 0)), hide_index=True)
        b.markdown(f"**k = {k} (rollbacks counted)**")
        b.dataframe(pd.DataFrame(A.starvation_rounds(base, k)), hide_index=True)
        if k > 0:
            st.success("With the rollback count in the cost, victims rotate, so no process starves.")
        urdu("Preemption mein kisi process se resource chheen kar dusre ko dete hain. Victim cost ke hisaab se chunte hain, victim ko rollback karte hain, aur starvation se bachne ke liye cost mein rollback ki ginti shamil karte hain.")


# ----------------------------------------------------------------------------
# QUIZ
# ----------------------------------------------------------------------------

QUIZ = [
    ("Which is NOT one of the four necessary conditions for deadlock?", ["Mutual exclusion", "Hold and wait", "Starvation", "Circular wait"], 2, "The four are mutual exclusion, hold and wait, no preemption and circular wait. Starvation is a different problem."),
    ("A resource-allocation graph has a cycle and every resource type has ONE instance. Then…", ["There is no deadlock", "There is a deadlock", "Deadlock is only possible", "Nothing can be said"], 1, "Cycle + single instance per type ⇒ deadlock."),
    ("A RAG has a cycle but some resource types have several instances. Then…", ["Deadlock for sure", "No deadlock for sure", "Deadlock is possible", "The graph is invalid"], 2, "With several instances a cycle only means a possibility of deadlock."),
    ("In a RAG, the edge Rj → Pi is called…", ["Request edge", "Assignment edge", "Claim edge", "Wait-for edge"], 1, "Pi → Rj is a request edge, Rj → Pi is an assignment edge."),
    ("Which prevention method uses a total ordering of resource types?", ["Preventing mutual exclusion", "Preventing hold and wait", "Preventing no-preemption", "Preventing circular wait"], 3, "Request resources in increasing order of enumeration ⇒ no circular wait."),
    ("Two problems of the hold-and-wait prevention protocols are…", ["Deadlock and thrashing", "Starvation and under-utilisation", "Overflow and underflow", "Aging and convoy effect"], 1, "A process needing several popular resources may starve; allocated resources may stay unused for long."),
    ("Which statement is true?", ["Unsafe state = deadlock", "Safe state ⇒ no deadlock", "Deadlock ⇒ safe state", "All unsafe states are deadlocks"], 1, "Safe ⇒ no deadlock. Deadlock states are a subset of unsafe states."),
    ("Deadlock avoidance requires…", ["No information", "Each process's maximum resource claim in advance", "Only the number of processes", "Non-preemptive scheduling"], 1, "Avoidance needs a priori information, typically the maximum claim."),
    ("The RAG avoidance algorithm works when…", ["Resources have multiple instances", "Each resource type has a single instance", "There are no claim edges", "Processes never wait"], 1, "For multiple instances use the Banker's algorithm."),
    ("In the Banker's algorithm, Need[i,j] equals…", ["Allocation − Max", "Max − Allocation", "Available − Max", "Max + Allocation"], 1, "Need = Max − Allocation."),
    ("System has Available=(3,3,2) and Need_P1=(1,2,2). Can P1 be chosen in the safety algorithm?", ["Yes, Need ≤ Work", "No, Need > Work", "Only if Finish is true", "Only after P0"], 0, "(1,2,2) ≤ (3,3,2) in every component."),
    ("The detection algorithm differs from the safety algorithm because it uses…", ["Max instead of Need", "Request instead of Need", "Allocation instead of Available", "Finish instead of Work"], 1, "Detection looks at the current Request of waiting processes, not the future Need."),
    ("A wait-for graph is useful when…", ["Resources have several instances", "Resources have a single instance", "Only for avoidance", "Only for prevention"], 1, "Pi → Pj if Pi waits for Pj; a cycle means deadlock (single-instance case)."),
    ("Which is a factor for choosing a victim for abort?", ["Priority of the process", "Colour of the screen", "File name", "Compiler used"], 0, "Priority, computed time, remaining time, resources used/needed, interactive vs batch…"),
    ("Starvation during resource preemption is avoided by…", ["Aborting all processes", "Including the number of rollbacks in the cost", "Never preempting", "Increasing the memory"], 1, "Counting rollbacks in the cost stops the same victim from being chosen again and again."),
    ("Which OSes mostly 'ignore' the deadlock problem?", ["Windows and UNIX", "Only real-time OS", "Only embedded OS", "None"], 0, "The slide says: mostly used by Windows and UNIX."),
]


def page_quiz():
    st.title("📝 Quiz")
    st.caption("16 quick questions covering Lectures 23-27")
    with st.form("quiz"):
        answers = []
        for k, (q, opts, _, _) in enumerate(QUIZ):
            answers.append(st.radio(f"**{k + 1}. {q}**", opts, index=None, key=f"q{k}"))
        done = st.form_submit_button("Check my answers")
    if done:
        score = 0
        for k, (q, opts, ans, why) in enumerate(QUIZ):
            if answers[k] == opts[ans]:
                score += 1
            else:
                st.error(f"Q{k + 1}: correct answer is **{opts[ans]}**. {why}")
        st.metric("Score", f"{score} / {len(QUIZ)}")
        if score == len(QUIZ):
            st.balloons()


# ----------------------------------------------------------------------------
# CHEAT SHEET
# ----------------------------------------------------------------------------


def page_cheat():
    st.title("📌 One-page cheat sheet")
    st.markdown("### Four conditions\nMutual exclusion · Hold and wait · No preemption · Circular wait  - **all four together**.")
    st.markdown("### RAG facts\nNo cycle ⇒ no deadlock · cycle + single instance ⇒ deadlock · cycle + multiple instances ⇒ maybe.")
    st.markdown("### Strategies compared")
    table(
        [
            {"": "Prevention", "Core idea": "Break ≥ 1 of the 4 conditions", "Needs in advance": "Nothing special", "Cost": "Low utilisation, starvation", "Lecture": 24},
            {"": "Avoidance (RAG)", "Core idea": "Grant only if no cycle forms (claim edges)", "Needs in advance": "Max claims", "Cost": "Single instance only", "Lecture": 25},
            {"": "Avoidance (Banker's)", "Core idea": "Grant only if state stays safe", "Needs in advance": "Max claims", "Cost": "O(m·n²) check per request", "Lecture": 26},
            {"": "Detection (wait-for)", "Core idea": "Find cycle in wait-for graph", "Needs in advance": "Nothing", "Cost": "Periodic search; need recovery", "Lecture": 27},
            {"": "Detection (matrix)", "Core idea": "Work/Finish with Request", "Needs in advance": "Nothing", "Cost": "Periodic run; need recovery", "Lecture": 27},
            {"": "Ignore", "Core idea": "Pretend it never happens", "Needs in advance": "-", "Cost": "Manual reboot/kill", "Lecture": 24},
        ]
    )
    st.markdown("### Formulas")
    st.code(
        "Need[i][j]   = Max[i][j] - Allocation[i][j]\n"
        "Available    = Total - sum(Allocation)\n\n"
        "Safety:      Work = Available; Finish[i] = false\n"
        "             find i: Finish[i]=false and Need_i <= Work\n"
        "             Work += Allocation_i; Finish[i] = true\n"
        "             safe iff all Finish[i] = true\n\n"
        "Request_i:   Request_i <= Need_i ?   else error\n"
        "             Request_i <= Available ? else wait\n"
        "             Available -= Request_i; Allocation_i += Request_i; Need_i -= Request_i\n"
        "             safe -> grant, unsafe -> wait + restore\n\n"
        "Detection:   Work = Available; Finish[i] = (Allocation_i == 0)\n"
        "             find i: Finish[i]=false and Request_i <= Work\n"
        "             Work += Allocation_i; Finish[i] = true\n"
        "             Finish[i] = false at the end -> Pi is deadlocked",
        language="text",
    )
    st.markdown("### Recovery\n- **Terminate**: all, or one at a time (cheapest victim by priority, computed/remaining time, resources, interactive/batch)\n- **Preempt**: select victim → rollback → avoid starvation (count rollbacks in cost)")


# ----------------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------------

PAGES = {
    "🏠 Home": page_home,
    "1️⃣ Characterization & RAG": page_characterization,
    "2️⃣ Prevention": page_prevention,
    "3️⃣ Avoidance": page_avoidance,
    "4️⃣ Banker's Algorithm": page_banker,
    "5️⃣ Detection & Recovery": page_detection,
    "📝 Quiz": page_quiz,
    "📌 Cheat sheet": page_cheat,
}

st.sidebar.title("🔒 Deadlock Lab")
choice = st.sidebar.radio("Go to", list(PAGES.keys()))
st.sidebar.caption("COMP-2115 · Operating Systems\nChapter 7 · Lectures 23-27")
PAGES[choice]()
