import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

RESULT_DIR = 'test_data/leak_detection/result'
CLOUDFLARE_RESULT_PATH = f'{RESULT_DIR}/route_leak_result.json'

def draw_line(data, x_date, xlabel, ylabel, outputfile, figsize=(8,5)):
    sns.set_context("paper")
    sns.set_style("white")
    plt.figure(figsize=figsize, dpi=600)
    plt.rcParams['font.family'] = 'DejaVu Sans'
    colors = sns.color_palette("colorblind", n_colors=len(data))
    myfontsize=28
    line_styles = ['-', '--', '-.', '-'] * (len(data)//4 + 1)
    marker_styles = ['.', 'o', 's', 'D']* (len(data)//4 + 1)
    
    y_min, y_max=0,105
    
    plt.ylim(y_min, y_max)
    
    for idx, (label_name, values) in enumerate(data.items()):
        if label_name=='Recall':
            line_style='-.'
            marker_style=''
        else:
            line_style='-'
            marker_style=marker_styles[idx]
            
        plt.plot(x_date, values,
                color=colors[idx],
                linestyle=line_style,
                linewidth=2.0,
                marker=marker_style,
                label=label_name)
        
    plt.xticks(ticks=range(len(x_date)), labels=x_date, fontsize=myfontsize)
    plt.gca().yaxis.set_major_locator(plt.FixedLocator(np.arange(0, 106, 20)))
    plt.tick_params(axis='both', which='major', labelsize=myfontsize)
    
    plt.xlabel(xlabel, fontsize=myfontsize, labelpad=8)
    plt.ylabel(ylabel, fontsize=myfontsize, labelpad=8)
    
    if ylabel == 'FPR (%)':
        plt.legend(loc='upper center',
                frameon=False,
                fontsize=myfontsize-4,
                ncol=2,
                bbox_to_anchor=(0.5, 0.93))
    else:
        plt.legend(loc='lower center',
                frameon=False,
                fontsize=myfontsize-4,
                ncol=2,
                bbox_to_anchor=(0.5, 0.0))

    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.3)

    plt.tight_layout()
    plt.savefig(outputfile, bbox_inches='tight', transparent=False)
    plt.close()

def precision_recall():
    with open(CLOUDFLARE_RESULT_PATH, 'r') as f:
        json_data = json.load(f)
    
    method2label = {
        'pathprob': 'PathProb'
    }
    
    dates = [f"Jun{d:02d}" for d in [4, 10, 16, 22, 28]]
    
    for method in json_data.keys():
        if method not in method2label:
            continue
            
        precision = np.array(json_data[method]['precision'])
        recall = np.array(json_data[method]['recall'])
        fpr = np.array(json_data[method]['FPR'])
        
        method_label = method2label[method]
        
        data = {method_label: precision}
        draw_line(data,
                [d[3:] for d in dates],
                'Date', 'Precision (%)', f'{RESULT_DIR}/precision.jpg')
        
        data = {method_label: recall}
        draw_line(data,
                [d[3:] for d in dates],
                'Date', 'Recall (%)', f'{RESULT_DIR}/recall.jpg')
        
        data = {method_label: fpr}
        draw_line(data,
                [d[3:] for d in dates],
                'Date', 'FPR (%)', f'{RESULT_DIR}/fpr.jpg')
    
    print(f"Results are saved to {RESULT_DIR}")

if __name__ == '__main__':
    precision_recall()
