from sortedcontainers import SortedDict
import json
import os

def _read_asrel(asrelfile):  # if as1<as2, then asrel[(as1,as2)]=rel
    asrel = SortedDict()
    with open(asrelfile) as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            as1, as2, rel = line.strip().split("|")[:3]
            rel = int(rel)
            if rel == 1: # remove sibling relation of problink and toposcope
                asrel[(min(as1, as2), max(as1, as2))] = 2
                continue
            asrel[(min(as1, as2), max(as1, as2))] = rel if as1 < as2 else -rel
    return asrel

def _read_prob(probfile):
    prob = SortedDict()  # [p2c,p2p,c2p]
    corefile = probfile if isinstance(probfile, str) else probfile[0]

    if not isinstance(probfile, str) and len(probfile) == 2:
        edgefile = probfile[1]
        with open(edgefile) as f:
            for line in f:
                if line and not line.startswith("#"):
                    as1, as2, p2c, p2p, c2p = line.strip().split("|")
                    probs = [float(p2c), float(p2p), float(c2p)]
                    if as1 > as2:
                        probs = [float(c2p), float(p2p), float(p2c)]
                    prob[(min(as1, as2), max(as1, as2))] = probs

    with open(corefile) as f:
        for line in f:
            if line and not line.startswith("#"):
                as1, as2, p2c, p2p, c2p = line.strip().split("|")
                probs = [float(p2c), float(p2p), float(c2p)]
                if as1 > as2:
                    probs = [float(c2p), float(p2p), float(p2c)]
                prob[(min(as1, as2), max(as1, as2))] = probs

    return prob

def comp2aspadata(asrel_file, aspa_data_file):
    provider_set = SortedDict()
    with open(aspa_data_file, "r") as f:
        for line in f.readlines():
            cu_as, pr_ases = line.strip().split(":")
            provider_set[cu_as] = set(pr_ases.split("|"))
    myrel = (
        _read_prob(asrel_file) if "pathprob" in asrel_file else _read_asrel(asrel_file)
        if isinstance(asrel_file, str)
        else _read_prob(asrel_file)
    )
    res = {"p2c": {"p2c": 0, "other": 0}, "other": {"p2c": 0, "other": 0}}

    for link, rel in myrel.items():
        as1, as2 = link

        if as1 in provider_set:
            is_provider = as2 in provider_set[as1]
            is_p2c = rel == 1 if isinstance(rel, int) else rel[2] == max(rel)

            res["p2c" if is_provider else "other"]["p2c" if is_p2c else "other"] += 1

        if as2 in provider_set:

            is_provider = as1 in provider_set[as2]
            is_p2c = rel == -1 if isinstance(rel, int) else rel[0] == max(rel)

            res["p2c" if is_provider else "other"]["p2c" if is_p2c else "other"] += 1

    results = {}

    results["accuracy"] = res["p2c"]["p2c"] / (res["p2c"]["p2c"] + res["p2c"]["other"])
    return results

def comp_asrel(asrelfile, truthfile):
    P2C, P2P, C2P, Other = -1, 0, 1, 2

    truthrel = _read_asrel(truthfile)
    myrel = (
        _read_prob(asrelfile) if "pathprob" in asrelfile else _read_asrel(asrelfile)
    )

    res = {P2C: {P2C: 0, P2P: 0, C2P: 0, Other: 0}, P2P: {P2C: 0, P2P: 0, C2P: 0, Other: 0}}

    for link, rel in truthrel.items():
        if link not in myrel:
            continue

        pred = myrel[link]
        if isinstance(pred, int):
            # rel = -rel, pred = -pred if rel == C2P else rel, pred
            if rel == C2P:
                rel = P2C
                pred = -pred
            if rel == P2P and pred == C2P:
                pred = P2C
            if pred==-2:
                pred=Other
            res[rel][pred] += 1
        else:
            p2c, p2p, c2p = pred
            if rel == C2P:
                rel, p2c, c2p = P2C, c2p, p2c

            if rel == P2C:
                max_prob = max(p2c, p2p, c2p)
                if max_prob == p2c:
                    res[P2C][P2C] += 1
                elif max_prob == p2p:
                    res[P2C][P2P] += 1
                else:
                    res[P2C][C2P] += 1
            elif rel == P2P:
                res[P2P][P2P if p2p >= max(p2c, c2p) else P2C] += 1

    total = sum(sum(v.values()) for v in res.values())
    correct = res[P2C][P2C] + res[P2P][P2P]
    accuracy = correct / total
    
    results = {
        "accuracy": accuracy
    }
    return results

def path_and_link_num(pathnum_dir):
    for file in os.listdir(pathnum_dir):
        paths=set()
        links=set()
        num=0
        with open(os.path.join(pathnum_dir,file),'r') as f:
            for line in f:
                path,n=line.strip().split(' ')
                paths.add(path)
                path, n = tuple(path.split('|')), int(n)
                num+=n
                for i in range(len(path)-1):
                    links.add((path[i],path[i+1]) if path[i]<path[i+1] else (path[i+1],path[i]))
        print(file,len(paths),len(links),num)
    
if __name__ == "__main__":
    import argparse

    aspa_validation_file = "test_data/prob_inference/validation/aspa_data_202507.txt"
    caida_validation_file = "test_data/prob_inference/validation/20250601.as-rel2.txt"

    parser = argparse.ArgumentParser(description="Evaluate path probability predictions against validation datasets.")
    parser.add_argument("--probs", type=str, required=True, help="Path to the predicted path probability file.")
    args = parser.parse_args()

    probs_file = args.probs

    res_aspa = comp2aspadata(probs_file, aspa_validation_file)
    print(f"Results for ASPA validation:")
    for key, value in res_aspa.items():
        print(f"  {key}: {value*100:.2f}%")

    res_caida = comp_asrel(probs_file, caida_validation_file)
    print(f"Results for CAIDA validation:")
    for key, value in res_caida.items():
        print(f"  {key}: {value*100:.2f}%")