import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'ml', 'iot_dataset.csv')
    plots_dir = os.path.join(base_dir, 'plots')
    
    # Create plots directory if it doesn't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {data_path}")
        return
        
    print(f"Dataset loaded with shape: {df.shape}")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Set the style
    sns.set_theme(style="whitegrid")
    
    # 1. Distribution of Risk Labels
    print("Generating Risk Label Distribution chart...")
    plt.figure(figsize=(8, 6))
    risk_order = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    # Filter the order to only include categories that exist in the data to avoid visual issues
    existing_risks = [r for r in risk_order if r in df['risk_label'].unique()]
    
    ax = sns.countplot(data=df, x='risk_label', order=existing_risks, palette='viridis')
    plt.title('Distribution of Risk Labels across Devices', fontsize=14, pad=15)
    plt.xlabel('Risk Level', fontsize=12)
    plt.ylabel('Number of Devices', fontsize=12)
    
    # Add count labels on top of bars
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=10, xytext=(0, 5), textcoords='offset points')
                    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, '1_risk_label_distribution.png'), dpi=300)
    plt.close()
    
    # 2. Encryption Algorithm Usage
    print("Generating Encryption Algorithm Usage chart...")
    plt.figure(figsize=(12, 8))
    algo_counts = df['encryption_algorithm'].value_counts()
    
    sns.barplot(x=algo_counts.values, y=algo_counts.index, palette='magma')
    plt.title('Usage frequency of Encryption Algorithms', fontsize=14, pad=15)
    plt.xlabel('Number of Devices', fontsize=12)
    plt.ylabel('Encryption Algorithm', fontsize=12)
    
    # Add percentage labels
    total = len(df)
    for i, v in enumerate(algo_counts.values):
        plt.text(v + (total*0.005), i, f'{v} ({(v/total)*100:.1f}%)', va='center')
        
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, '2_encryption_algorithms.png'), dpi=300)
    plt.close()
    
    # 3. CPU vs RAM grouped by Risk Label
    print("Generating CPU vs RAM scatter plot...")
    plt.figure(figsize=(10, 8))
    
    sns.scatterplot(data=df, x='cpu_mhz', y='ram_kb', hue='risk_label', alpha=0.7, 
                    hue_order=existing_risks, palette='coolwarm', s=60)
    plt.title('Device Resources: CPU vs RAM by Risk Level', fontsize=14, pad=15)
    plt.xlabel('CPU (MHz)', fontsize=12)
    plt.ylabel('RAM (KB) [Log Scale]', fontsize=12)
    plt.yscale('log')
    # Using log scale for RAM usually helps since embedded devices vary greatly (kb to mb/gb)
    
    # Move legend outside
    plt.legend(title='Risk Label', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, '3_cpu_vs_ram_risk.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Correlation Heatmap
    print("Generating Correlation Heatmap...")
    plt.figure(figsize=(14, 12))
    
    # Select only numeric columns for correlation (drop IDs)
    numeric_df = df.select_dtypes(include=['int64', 'float64'])
    if 'device_id' in numeric_df.columns:
        numeric_df = numeric_df.drop('device_id', axis=1)
        
    corr = numeric_df.corr()
    
    # Create mask for upper triangle
    import numpy as np
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, annot=True, cmap='RdBu_r', fmt='.2f', 
                linewidths=0.5, annot_kws={"size": 9}, vmin=-1, vmax=1, center=0)
    plt.title('Correlation Heatmap of Numerical Features', fontsize=16, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, '4_correlation_heatmap.png'), dpi=300)
    plt.close()
    
    # 5. Data Sensitivity vs Key Rotation Days
    print("Generating Data Sensitivity vs Key Rotation Days plot...")
    plt.figure(figsize=(10, 6))
    
    sns.boxplot(data=df, x='data_sensitivity', y='key_rotation_days', palette='Set3', showfliers=False)
    plt.title('Key Rotation Practices based on Data Sensitivity', fontsize=14, pad=15)
    plt.xlabel('Data Sensitivity Level', fontsize=12)
    plt.ylabel('Key Rotation (Days)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, '5_sensitivity_vs_key_rotation.png'), dpi=300)
    plt.close()

    print(f"\n✅ Success! Analysis complete.")
    print(f"📁 5 charts have been generated and saved to: {plots_dir}")

if __name__ == "__main__":
    main()
