# 🔒 Deadlock Lab

Interactive Streamlit simulation of **Chapter 7 - Deadlocks** (COMP-2115 Operating Systems, Lectures 23-27,
Silberschatz, Galvin & Gagne 9th ed., instructor Usman Rafi).

| Page | Lecture | What you can do |
|---|---|---|
| 1 Characterization & RAG | 23 | 4-condition checker, resource-allocation graph viewer, slide examples, build-your-own RAG with cycle/deadlock verdict |
| 2 Prevention | 24 | Mutual exclusion, hold-and-wait protocols (DVD example), preemption protocols, circular-wait ordering simulator |
| 3 Avoidance | 25 | Safe/unsafe states (tape-drive example), safe-unsafe-deadlock diagram, RAG algorithm with claim edges |
| 4 Banker's Algorithm | 26 | Editable Allocation/Max/Total, Need & Available, safety algorithm, sequence verifier, resource-request algorithm |
| 5 Detection & Recovery | 27 | Wait-for graph, matrix detection algorithm, detection frequency, termination & preemption recovery, starvation demo |
| Quiz / Cheat sheet | - | 16 MCQs and a one-page summary |

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run on Google Colab
```python
!pip install -q streamlit pandas
!npm install -g localtunnel
```
Upload `app.py` and `algos.py` to Colab, then:
```python
!streamlit run app.py &>/content/logs.txt &
!curl ipv4.icanhazip.com        # copy this IP - it is the tunnel password
!npx localtunnel --port 8501
```
Open the printed `https://....loca.lt` link and paste the IP as password.

## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repo (`app.py`, `algos.py`, `requirements.txt` at the repo root).
2. Go to https://share.streamlit.io → **New app** → pick the repo, branch `main`, main file `app.py` → **Deploy**.

`algos.py` has no Streamlit dependency, so the algorithms can be unit-tested on their own.
