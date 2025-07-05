import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def main():
    """
    Loads the final zonal statistics results and creates a variety of advanced
    visualizations to explore the phenology trends in more depth.
    """
    # --- 1. Load Data ---
    input_csv = 'phenology_trends_by_vegetation.csv'
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: The input file '{input_csv}' was not found.")
        print("Please run 'analyze_phenology_by_veg.py' first to generate it.")
        return

    print("Successfully loaded results. Generating advanced plots...")

    # --- 2. Plot 1: Stacked Bar Chart for LOS Composition ---
    fig1, ax1 = plt.subplots(figsize=(15, 8))
    
    # We plot the NEGATIVE SOS trend because LOS = EOS - SOS.
    # So, a positive LOS trend is composed of a positive EOS trend and a negative SOS trend (advancement).
    ax1.bar(df['Vegetation_Type'], df['EOS_Trend_days_per_year'], label='EOS Trend (推后/提前)', color='firebrick')
    ax1.bar(df['Vegetation_Type'], -df['SOS_Trend_days_per_year'], label='SOS Contribution (提前/推后)', color='royalblue', bottom=df['EOS_Trend_days_per_year'])

    ax1.set_title('Composition of Growing Season Length (LOS) Trend by Vegetation Type', fontsize=16)
    ax1.set_ylabel('Trend Contribution (days/year)')
    ax1.axhline(0, color='black', linewidth=0.8)
    ax1.legend(title='Component')
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    plt.tight_layout()
    plot1_path = 'advanced_plot_1_los_composition.png'
    plt.savefig(plot1_path, dpi=300)
    print(f"  - Saved LOS Composition plot to '{plot1_path}'")

    # --- 3. Plot 2: Scatter/Bubble Plot of SOS vs EOS Trends ---
    fig2, ax2 = plt.subplots(figsize=(12, 10))
    
    # Bubble size is proportional to the magnitude of the LOS change
    bubble_size = df['LOS_Trend_days_per_year'].abs() * 200  # Multiply by a factor for visibility

    sns.scatterplot(
        data=df,
        x='SOS_Trend_days_per_year',
        y='EOS_Trend_days_per_year',
        size=bubble_size,
        hue='Vegetation_Type',
        sizes=(50, 2000),  # Min and max bubble sizes
        legend='auto',
        ax=ax2
    )

    # Add labels for each point
    for i, row in df.iterrows():
        ax2.text(row['SOS_Trend_days_per_year']+0.005, row['EOS_Trend_days_per_year'], row['Vegetation_Type'], fontsize=9)

    ax2.axhline(0, color='grey', linestyle='--', lw=1)
    ax2.axvline(0, color='grey', linestyle='--', lw=1)
    
    ax2.set_title('SOS Trend vs. EOS Trend Relationship', fontsize=16)
    ax2.set_xlabel('SOS Trend (days/year, <0 is earlier spring)')
    ax2.set_ylabel('EOS Trend (days/year, >0 is later autumn)')
    ax2.grid(True)
    ax2.legend(title='Vegetation Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Quadrant explanations
    ax2.text(0.98, 0.02, 'Earlier Spring, Earlier Autumn', transform=ax2.transAxes, ha='right', va='bottom', fontsize=10, style='italic', color='grey')
    ax2.text(0.02, 0.02, 'Later Spring, Earlier Autumn\n(Shorter Season)', transform=ax2.transAxes, ha='left', va='bottom', fontsize=10, style='italic', color='red')
    ax2.text(0.02, 0.98, 'Later Spring, Later Autumn', transform=ax2.transAxes, ha='left', va='top', fontsize=10, style='italic', color='grey')
    ax2.text(0.98, 0.98, 'Earlier Spring, Later Autumn\n(Longer Season)', transform=ax2.transAxes, ha='right', va='top', fontsize=10, style='italic', color='green')

    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend
    plot2_path = 'advanced_plot_2_trend_relationship.png'
    plt.savefig(plot2_path, dpi=300)
    print(f"  - Saved Trend Relationship plot to '{plot2_path}'")

    # --- 4. Plot 3: Horizontal Bar Chart for LOS Trend Magnitude ---
    df_sorted = df.sort_values(by='LOS_Trend_days_per_year', ascending=False)
    
    fig3, ax3 = plt.subplots(figsize=(10, 8))
    
    colors = ['green' if x > 0 else 'red' for x in df_sorted['LOS_Trend_days_per_year']]
    ax3.hlines(y=df_sorted['Vegetation_Type'], xmin=0, xmax=df_sorted['LOS_Trend_days_per_year'], color=colors, lw=2)
    ax3.plot(df_sorted['LOS_Trend_days_per_year'], df_sorted['Vegetation_Type'], "o", color='black')

    ax3.set_title('Magnitude of Growing Season Length (LOS) Change', fontsize=16)
    ax3.set_xlabel('Trend (days/year)')
    ax3.set_ylabel('Vegetation Type')
    ax3.axvline(0, color='black', linestyle='--', lw=0.8)
    ax3.grid(True, axis='x', linestyle=':')
    
    plt.tight_layout()
    plot3_path = 'advanced_plot_3_los_magnitude.png'
    plt.savefig(plot3_path, dpi=300)
    print(f"  - Saved LOS Magnitude plot to '{plot3_path}'")
    
    plt.show()

if __name__ == '__main__':
    main() 