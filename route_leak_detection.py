from sortedcontainers import SortedDict
import os
import numpy as np
import json
import time

ROUTE_LEAK_DIR='test_data/leak_detection/cloudflare_data'
ASREL_DIR="test_data/prob_inference/result/202506/"  # Directory containing AS relationship files
RESULT_DIR="test_data/leak_detection/result"     # Output directory for results
date_list=[f"202506{d:02d}" for d in [4, 10, 16, 22, 28]]
TH=0.4

rrcs = [
        "rrc00","rrc01","rrc03","rrc04","rrc06","rrc10","rrc11","rrc13",
        "rrc16","rrc20","rrc05","rrc07","rrc12","rrc14","rrc15","rrc18",
        "rrc19","rrc21","route-views.eqix","route-views.isc","route-views.kixp",
        "route-views.linx","route-views.napafrica","route-views.nwax","route-views.perth",
        "route-views2","route-views3","route-views.sfmix","route-views.soxrs",   # "route-views.sg",
        "route-views.sydney","route-views.telxatl","route-views.wide",
    ]

def _read_asrel(asrelfile):  # if as1<as2, then asrel[(as1,as2)]=rel
    asrel = SortedDict()
    with open(asrelfile) as f:
        for line in f:
            if not line or line.startswith("#"):
                continue
            as1, as2, rel = line.strip().split("|")[:3]
            rel = int(rel)
            if rel==1:
                continue
            asrel[(min(as1, as2), max(as1, as2))] = rel if as1 < as2 else -rel
    return asrel

def _read_prob(probfile):
    prob = SortedDict()  # [p2c,p2p,c2p]
    with open(probfile) as f:
        for line in f:
            if line and not line.startswith("#"):
                as1, as2, p2c, p2p, c2p = line.strip().split("|")
                probs = [float(p2c), float(p2p), float(c2p)]
                if as1 > as2:
                    probs = [float(c2p), float(p2p), float(p2c)]
                prob[(min(as1, as2), max(as1, as2))] = probs
    return prob


def _read_path(pathfiles):
    files = pathfiles if isinstance(pathfiles, list) else [pathfiles]
    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip().split(" ")
                yield line[0].split("|"), int(line[1]) if len(line) == 2 else 1


def _partical_detect_by_asrel(path, asrel):  # leak or valid
    state = "p"
    for i in range(len(path) - 1):
        as1, as2 = path[i : i + 2]
        if (as1, as2) not in asrel and (as2, as1) not in asrel:
            continue
        rel = asrel[(as1, as2)] if (as1, as2) in asrel else -asrel[(as2, as1)]
        if state == "p" and rel != 1:
            state = "c"
        elif state == "c" and rel != -1:
            return "leak"
    return "valid"

def _partical_detect_by_prob_mintriple(path, asrelprob):
    prob = 1.0
    c2p0 = 1.0
    for i in range(len(path) - 1):
        link = tuple(path[i : i + 2])
        if link in asrelprob:
            p2c, _, c2p = asrelprob[link]
        elif link[::-1] in asrelprob:
            c2p, _, p2c = asrelprob[link[::-1]]
        else:
            continue
        prob = min(p2c + c2p0 - p2c * c2p0, prob)
        c2p0 = c2p
    return prob


def _partical_detect_by_full_path(path, prob):
    next_c, next_p = 0.0, 1.0
    for i in range(len(path) - 1):
        link = tuple(path[i : i + 2])
        if link not in prob and link[::-1] not in prob:
            continue
        p2c, _, c2p = prob[link] if link in prob else prob[link[::-1]][::-1]
        next_c = next_c * p2c + next_p * (1 - c2p)
        next_p *= c2p
    return next_p + next_c

  
def route_leak_test_by_prob(myrel, validfile, leakfile, th=TH):
    tp, fp, tn, fn = 0, 0, 0, 0
    for path, num in _read_path(validfile):
        res = _partical_detect_by_prob_mintriple(path, myrel)
        if res >=th:
            tn += num
        else:
            fp += num
    for path, num in _read_path(leakfile):
        res = _partical_detect_by_prob_mintriple(path, myrel)
        if res >=th:
            fn += num
        else:
            tp += num
    
    weigh_for_n = (tp + fn) / (tn + fp) if (tn + fp) > 0 else 1.0
    fp_weighted = fp * weigh_for_n
    tn_weighted = tn * weigh_for_n
    
    precision = tp / (tp + fp_weighted) * 100 if (tp + fp_weighted) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    fpr = fp_weighted / (fp_weighted + tn_weighted) * 100 if (fp_weighted + tn_weighted) > 0 else 0
    
    result={'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn, 
            'TPR': recall,
            'FPR': fpr,
            'precision': precision,
            'recall': recall}
    return result


def route_leak_test_by_asrel(myrel, validfile, leakfile):
    tp, fp, tn, fn = 0, 0, 0, 0
    for path, num in _read_path(validfile):
        res = _partical_detect_by_asrel(path, myrel)
        if res == "valid":
            tn += num
        elif res == "leak":
            fp += num
    for path, num in _read_path(leakfile):
        res = _partical_detect_by_asrel(path, myrel)
        if res == "valid":
            fn += num
        elif res == "leak":
            tp += num
    
    weigh_for_n = (tp + fn) / (tn + fp) if (tn + fp) > 0 else 1.0
    fp_weighted = fp * weigh_for_n
    tn_weighted = tn * weigh_for_n
    
    precision = tp / (tp + fp_weighted) * 100 if (tp + fp_weighted) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    fpr = fp_weighted / (fp_weighted + tn_weighted) * 100 if (fp_weighted + tn_weighted) > 0 else 0
    
    result={'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn, 
            'TPR': recall,
            'FPR': fpr,
            'precision': precision,
            'recall': recall}
    return result

def cloudflare_leak():
    result = {key:{'tp': [], 'fp': [], 'tn': [], 'fn': [], 'TPR': [], 'FPR': [], 'precision': [], 'recall': []} 
              for key in ['pathprob']}
    
    asrels={}
    asrels['pathprob'] = _read_prob(f"{ASREL_DIR}/pathprob.txt")
    
    for date in date_list:

        st=time.time()
        
        cloudflare_validpath = [
            f"{ROUTE_LEAK_DIR}/{date}/valid_path/{rrc}.txt"
            for rrc in rrcs
        ]
        cloudflare_leakpath = [
            f"{ROUTE_LEAK_DIR}/{date}/leak_path/{rrc}.txt" for rrc in rrcs
        ]
        
        for method,asrel in asrels.items():
            if method == 'pathprob':
                res=route_leak_test_by_prob(
                        asrel,
                        cloudflare_validpath,
                        cloudflare_leakpath,
                    )
            else:
                res=route_leak_test_by_asrel(
                        asrel,
                        cloudflare_validpath,
                        cloudflare_leakpath,
                    )
            for k,v in res.items():
                result[method][k].append(v)
        duration = time.time() - st
        print(f"[{date}] Processing completed in {duration:.2f} seconds.")
    
    for method in result.keys():
        precision_arr = np.array(result[method]['precision'])
        recall_arr = np.array(result[method]['recall'])
        fpr_arr = np.array(result[method]['FPR'])
        
        result[method]['precision_stats'] = {
            'average': float(np.mean(precision_arr)),
            'best': float(np.max(precision_arr)),
            'worst': float(np.min(precision_arr))
        }
        result[method]['recall_stats'] = {
            'average': float(np.mean(recall_arr)),
            'best': float(np.max(recall_arr)),
            'worst': float(np.min(recall_arr))
        }
        result[method]['fpr_stats'] = {
            'average': float(np.mean(fpr_arr)),
            'best': float(np.min(fpr_arr)),
            'worst': float(np.max(fpr_arr))
        }
    
    output_path = f"{RESULT_DIR}/route_leak_result.json"
    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=4)
    
    
    print("\nStatistics:")
    for method in result.keys():
        print(f"\n{method}:")
        print(f"  Precision - Average: {result[method]['precision_stats']['average']:.2f}%, "
              f"Best: {result[method]['precision_stats']['best']:.2f}%, "
              f"Worst: {result[method]['precision_stats']['worst']:.2f}%")
        print(f"  Recall - Average: {result[method]['recall_stats']['average']:.2f}%, "
              f"Best: {result[method]['recall_stats']['best']:.2f}%, "
              f"Worst: {result[method]['recall_stats']['worst']:.2f}%")
        print(f"  FPR - Average: {result[method]['fpr_stats']['average']:.2f}%, "
              f"Best: {result[method]['fpr_stats']['best']:.2f}%, "
              f"Worst: {result[method]['fpr_stats']['worst']:.2f}%")
    
        print(f"Results are saved to {output_path}.")
        
        
if __name__ == "__main__":
    cloudflare_leak()
    
