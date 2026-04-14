import re
import pandas as pd
import matplotlib.pyplot as plt

def parse_combined_logs(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by any variation of the Run header
    runs = re.split(r'(?=## .*Run — )', content)
    data = []

    for run in runs:
        if not run.strip(): continue
            
        # 1. Flexible Run ID Extraction
        # Captures: 2026-04-07T13:44:51 OR (7/4/2026)Run — (14:40)
        run_id_match = re.search(r'## (?:.*?)Run — ([\d\-\:T\(\)\/]+)', run)
        run_label = run_id_match.group(1) if run_id_match else "Unknown"

        # 2. Extract Total Latency
        # Finds the 'Totals' table and grabs the value in the 'total_s' column
        # Logic: find 'total_s', then skip to the next row and grab the 4th column
        latency_search = re.search(r'total_s\s*\|\s*batches\s*\|\n\|.*?\|.*?\|.*?\|.*?\|\s*([\d\.]+)\s*\|', run, re.DOTALL)
        
        # 3. Extract Total Cost
        cost_match = re.search(r'Total run cost: \$([\d\.]+)', run)
        
        # 4. Extract Thinking Tokens
        thinking_tok_match = re.search(r'thinking\s*\|\s*(\d+)\s*\|', run)

        # 5. Extract totals row values for msgs_in and batches
        totals_match = re.search(
            r'\*\*Totals\*\*.*?\n\|[^\n]*\n\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*([\d\.]+)\s*\|\s*(\d+)\s*\|',
            run,
            re.DOTALL,
        )

        msgs_in = int(float(totals_match.group(1))) if totals_match else 0
        batches = int(totals_match.group(5)) if totals_match else 0

        if run_id_match:
            data.append({
                "Run": run_label,
                "Cost ($)": float(cost_match.group(1)) if cost_match else 0,
                "Latency (s)": float(latency_search.group(1)) if latency_search else 0,
                "Thinking Tokens": int(thinking_tok_match.group(1)) if thinking_tok_match else 0,
                "Messages": msgs_in,
                "Batches": batches,
            })

    return pd.DataFrame(data)

def plot_performance(df):
    if df.empty:
        print("No data found. Ensure the Markdown file is saved correctly.")
        return

    # Clean up the labels for the X-axis (extract just the time)
    df['Label'] = df['Run'].apply(lambda x: re.findall(r'(\d{2}:\d{2})', x)[-1] if ":" in x else x)
    
    fig, axes = plt.subplots(5, 1, figsize=(10, 16), sharex=True)
    plt.subplots_adjust(hspace=0.4)
    
    metrics = [
        ("Cost ($)", "#2ecc71", "Efficiency"),
        ("Latency (s)", "#e74c3c", "Speed"),
        ("Thinking Tokens", "#3498db", "Model Reasoning"),
        ("Batches", "#9b59b6", "Batch Count"),
        ("Messages", "#f39c12", "Message Count"),
    ]

    for i, (col, color, title) in enumerate(metrics):
        axes[i].plot(df["Label"], df[col], marker='o', ls='-', color=color, lw=2, markersize=8)
        axes[i].set_title(f"{title} ({col})", fontsize=12, fontweight='bold')
        axes[i].grid(axis='y', linestyle='--', alpha=0.6)
        
        # Annotate values on the dots
        for x, y in zip(df["Label"], df[col]):
            axes[i].annotate(
                f'{y:.4f}' if "Cost" in col else f'{int(y)}',
                xy=(x, y), textcoords="offset points", xytext=(0,10), ha='center'
            )

    plt.xticks(rotation=0)
    plt.xlabel("Run Time")
    plt.show()

if __name__ == "__main__":
    df = parse_combined_logs("Big_Analysis.md")
    plot_performance(df)
