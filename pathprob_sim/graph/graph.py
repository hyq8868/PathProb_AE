import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免 Tkinter 依赖
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os

mpl.rcParams.update(
    {
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.size": 9,  
        "axes.labelsize": 14,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "lines.linewidth": 1.5,
        "lines.markersize": 4.5,
    }
)


def load_csv_data(data_file, scenario_label, outcome_type):
    if not os.path.exists(data_file):
        print(f"File not found: {data_file}")
        return None

    df = pd.read_csv(data_file)

    filtered_data = df[
        (df["in_adopting_asns"] == "Any")
        & (df["outcome"] == outcome_type)
        & (df["propagation_round"] == 1)
        & (df["scenario_label"] == scenario_label)
    ].copy()

    if filtered_data.empty:
        print(f"No {outcome_type} data found in {data_file}")
        return None

    filtered_data = filtered_data.sort_values("percent_adopt")
    return filtered_data[["percent_adopt", "value"]].values


def get_methods_groups():
    """
    Define the order of lines and their sources.
    Also provide a "short label" for legend-only figure, avoiding too long labels.
    """
    methods = [
        {
            "label": "PathProb",
            "file": "pathprob",
            "scenario_label": "PathProb"
        },
        {
            "label": "ASPA",
            "file": "ASPA",
            "scenario_label": "PartialIssuanceASPA"
        },
    ]
    return methods


def create_single_panel(
    deployment_rate,
    outcome_type,
    save_path,
    methods,
    need_handles=False,
):

    fig, ax = plt.subplots(figsize=(3.4, 2))

    color_cycle = list(mpl.colormaps["tab10"].colors)
    marker_cycle = ["o", "s", "^", "D", "v", "P", "X", "*", ">"]

    plot_handles = []
    plot_labels = []

    ax.grid(axis="y", linestyle="--", color="#cccccc", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    for i, method_info in enumerate(methods):
        csv_file = f"pathprob_sim/data/result/partial_issuance_sim_{deployment_rate}/{method_info['file']}/data.csv"

        data = load_csv_data(csv_file, method_info['scenario_label'], outcome_type)
        if data is None:
            continue

        x_data = data[:, 0] * 100.0
        y_data = data[:, 1]

        line = ax.plot(
            x_data,
            y_data,
            label=method_info["label"],  
            color=color_cycle[i % len(color_cycle)],
            marker=marker_cycle[i % len(marker_cycle)],
            linewidth=1.5,
            markersize=4.5,
            markeredgewidth=0.5,
            markeredgecolor="#f0f0f0",  
            alpha=0.95,
        )[0]

        if need_handles:
            plot_handles.append(line)
            plot_labels.append(method_info["label"])

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("ASPA Issuance Rate (%)")

    if outcome_type == "LIR":
        ax.set_ylim(0, 20)
        ax.set_yticks([0, 5, 10, 15, 20])
        ax.set_ylabel("LIR (%)")
    elif outcome_type == "LCR":
        ax.set_ylim(75, 100)
        ax.set_yticks([75, 80, 85, 90, 95, 100])
        ax.set_ylabel("LCR (%)")

    ax.text(
        0.02,
        0.98,
        f"{deployment_rate*100:.0f}% deployment, {outcome_type}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
    )

    plt.tight_layout(pad=0.8)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close()

    if need_handles:
        return plot_handles, plot_labels
    return None, None


def save_legend_only(handles, labels, save_path):
    ncol = 3

    fig = plt.figure(figsize=(3.4, 0.8))
    fig.legend(
        handles,
        labels,
        loc="center",
        ncol=ncol,
        frameon=False,
        columnspacing=0.8,
        handlelength=2.0,
        handletextpad=0.5,
        borderaxespad=0.0,
        labelspacing=0.5,
        fontsize=20,
    )
    plt.axis("off")
    plt.tight_layout(pad=0.2)
    fig.savefig(save_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"[INFO] legend-only figure saved -> {save_path}")


def _value_at_percent(data_arr, target_fraction):
    if data_arr is None or len(data_arr) == 0:
        return None

    # Prioritize exact matching
    for p, v in data_arr:
        if abs(p - target_fraction) < 1e-9:
            return float(v)

    # Otherwise, take the nearest point
    idx = np.argmin(np.abs(data_arr[:, 0] - target_fraction))
    return float(data_arr[idx, 1])


def create_all_comparison_plots():

    deployment_rates = [0.25, 0.5, 0.75, 1.0]
    outcomes = ["LIR", "LCR"]

    methods = get_methods_groups()

    output_dir = "pathprob_sim/data/graphs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # We only need the handles/labels from the first figure to create the total legend
    legend_handles = None
    legend_labels = None

    for d in deployment_rates:
        for outcome in outcomes:
            save_path = f"{output_dir}/deploy_{d*100:.0f}_{outcome}.png"
            need_handles = legend_handles is None  # The first figure needs handles, the rest don't
            h, l = create_single_panel(
                deployment_rate=d,
                outcome_type=outcome,
                save_path=save_path,
                methods=methods,
                need_handles=need_handles,
            )
            print(f"[INFO] saved plot -> {save_path}")

            if need_handles:
                legend_handles, legend_labels = h, l

    # Export the legend figure separately
    if legend_handles is not None:
        legend_path = f"{output_dir}/legend_only.png"
        save_legend_only(legend_handles, legend_labels, legend_path)

    print(f"\n[INFO] All small figures & legend have been generated to: {output_dir}")


if __name__ == "__main__":
    create_all_comparison_plots()
