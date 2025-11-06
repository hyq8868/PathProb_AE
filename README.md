# PathProb: Probabilistic AS Relationship Inference and Route-Leak Detection

This repository contains the **artifact** for our NDSS submission *"PathProb: Probabilistic AS Relationship Inference for Detecting BGP Route Leaks."*
It enables reviewers to reproduce the main experimental results (E1–E3) using scaled-down datasets.

---

## 1. Access & Requirements


### Hardware

* CPU: x86-64 (≥8 cores)
* RAM: ≥16 GB
* Disk: ≥10 GB free

### Software

* OS: Ubuntu 20.04.2 LTS (tested)
* Python 3.8+ and PyPy 3.10+
* Dependencies: installable via `requirements.txt` and `requirements_pypy.txt`

> Note: Ubuntu’s default PyPy may be outdated; please ensure PyPy ≥3.10.

---

## 2. Installation

### Python Environment

```bash
python3 -m venv .python_venv
source .python_venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### PyPy Environment

```bash
pypy3 -m ensurepip --upgrade
pypy3 -m venv .pypy_venv
source .pypy_venv/bin/activate
pypy3 -m pip install -r requirements_pypy.txt
deactivate
```

### Dataset

```bash
tar -xJvf test_data.tar.xz
```

---

## 3. Experiment Workflow

### E1 – Probabilistic AS Relationship Inference

**Time:** 5 min + 2 compute hours
**Goal:** Infer AS relationships and validate against ASPA & CAIDA Serial-2.

```bash
source .python_venv/bin/activate
python3 infer_prob/asrel_prob.py \
  --path_dir test_data/prob_inference/paths/202506 \
  --print_dir test_data/prob_inference/result/202506
python3 eval_asrel.py --probs test_data/prob_inference/result/202506/pathprob.txt
```

Expected output: Validation report.

---

### E2 – Route-Leak Detection

**Time:** 5 min + 10 compute minutes
**Goal:** Compute path legitimacy scores and evaluate Precision/Recall/FPR.

```bash
source .python_venv/bin/activate
python3 route_leak_detection.py
python3 figure_route_leak.py
```

Results saved in: `test_data/leak_detection/result/`

---

### E3 – Simulation (LIR & LCR Evaluation)

**Time:** 5 min + 3 compute hours
**Goal:** Simulate BGP scenarios using BGPy; evaluate LIR/LCR.

```bash
cd PathProb
source .pypy_venv/bin/activate
export PYTHONHASHSEED=0
pypy3 -m pathprob_sim --trials 100
python3 pathprob_sim/graph/graph.py
```

Plots saved in: `pathprob_sim/data/graphs/`

