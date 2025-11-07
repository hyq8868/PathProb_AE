# PathProb: Probabilistic Inference and Path Scoring for Enhanced RPKI-based Route Leak Detection.

This repository contains the artifact for our NDSS submission *"PathProb: Probabilistic Inference and Path Scoring for Enhanced RPKI-based Route Leak Detection."*

---

## 1. Access & Requirements


### Hardware

* CPU: x86-64 (≥8 cores)
* RAM: ≥16 GB
* Disk: ≥10 GB free

### Software

* OS: Ubuntu 20.04.2 LTS (tested)
* System Packages: bulid-essential, graphviz, libjpeg-dev, zlib1g-dev, wget, zstd
* Python 3.8+ and PyPy 3.10+
* Dependencies: installable via `requirements.txt` and `requirements_pypy.txt`

> Note: Ubuntu’s default PyPy may be outdated; please ensure PyPy ≥3.10.

---

## 2. Installation

### Install system packages

```bash
sudo apt-get update
sudo apt-get install -y build-essential graphviz libjpeg-dev zlib1g-dev wget zstd
```

### Python Environment

```bash
python3 -m venv .python_venv
source .python_venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade wheel
pip install -r requirements.txt
deactivate
```

### PyPy Environment

```bash
pypy3 -m venv .pypy_venv
source .pypy_venv/bin/activate
pypy3 -m pip install pip --upgrade
pypy3 -m pip install wheel --upgrade
pypy3 -m pip install -r requirements_pypy.txt
deactivate
```

### Dataset

```bash
wget https://github.com/hyq8868/PathProb_AE/releases/download/v1.0/test_data.tar.zst
zstd -d test_data.tar.zst -c | tar -xf - 
```

---

## 3. Experiment Workflow

### E1 – Probabilistic AS Relationship Inference

**Time:** 5 min + 30 compute minutes

**Goal:** Infer AS relationships and validate against ASPA & CAIDA.

```bash
source .python_venv/bin/activate
python3 infer_prob/asrel_prob.py \
  --path_dir test_data/prob_inference/paths/202506 \
  --print_dir test_data/prob_inference/result/202506
python3 eval_asrel.py --probs test_data/prob_inference/result/202506/pathprob.txt
deactivate
```

Expected output: Validation report.

---

### E2 – Route Leak Detection

**Time:** 5 min + 10 compute minutes

**Goal:** Do route leak detection and evaluate Precision, Recall, FPR.

```bash
source .python_venv/bin/activate
python3 route_leak_detection.py
python3 figure_routeleak.py
deactivate
```

Results saved in: `test_data/leak_detection/result/`

---

### E3 – Large-scale Simulation

**Time:** 5 min + 3 compute hours

**Goal:** Simulate BGP scenarios using BGPy; evaluate LIR/LCR.

```bash
cd PathProb_AE
source .pypy_venv/bin/activate
export PYTHONHASHSEED=0
pypy3 -m pathprob_sim --trials 100
pypy3 pathprob_sim/graph/graph.py
```

Plots saved in: `pathprob_sim/data/graphs/`

