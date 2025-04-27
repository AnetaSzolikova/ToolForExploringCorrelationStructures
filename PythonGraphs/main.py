import pymongo
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import os
# --------------------------------

# Pripojenie databázy
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["local"]

print("Zadajte názov kolekcie: ")
name = input().strip()

collection_names = db.list_collection_names()
if name in collection_names:
    collection = db[name]
else:
    print("ERROR: Kolekcia sa nenašla.")
    exit()

# Načítanie dát
df = pd.DataFrame(list(collection.find()))
df.drop("_id", axis=1, inplace=True)
df.dropna(how="any", inplace=True)
df = df.select_dtypes(include=[np.number])
# -----------------------------------------

# Výpočet korelačnej matice
pearson_corr_matrix = df.corr(method='pearson').round(3)

# Vypočítanie sigma hranice
max_corr = pearson_corr_matrix.abs().max().max()
avg_corr = pearson_corr_matrix.abs().mean().mean()
sigma_limit = (max_corr + avg_corr) / 2
sigma = round(sigma_limit, 3)

# Vynulovanie diagonály
np.fill_diagonal(pearson_corr_matrix.values, 0)

# Nastavenie hodnôt menších ako sigma na nulu
sigma_corr_matrix = pearson_corr_matrix.applymap(lambda x: 0 if abs(x) < sigma else x)

# Odstránenie riadkov a stĺpcov, ktoré obsahujú iba nuly
zero_columns = sigma_corr_matrix.columns[(sigma_corr_matrix != 0).any()]
zero_rows = sigma_corr_matrix.index[(sigma_corr_matrix != 0).any(axis=1)]
sigma_corr_matrix = sigma_corr_matrix.loc[zero_rows, zero_columns]

# Spočítanie súčtu korelácií každého atribútu
sums = []
for attribute in sigma_corr_matrix.columns:
    sum_corr = round(sigma_corr_matrix[attribute].abs().sum(), 3)

    # Uloženie súčtu do zoznamu
    sums.append(sum_corr)

# Vypočítanie minimálnej a maximálnej korelácie (= súčtu korelácií)
min_sum = min(sums)
max_sum = max(sums)

# Rozdelenie na 3 skupiny
divide = max_sum / 3
weak_corr = []
medium_corr = []
strong_corr = []

for attribute, sum_corr in zip(sigma_corr_matrix.columns, sums):
    if sum_corr <= divide:
        weak_corr.append(attribute)
    elif (divide + 0.01) < sum_corr < (divide * 2 - 0.01):
        medium_corr.append(attribute)
    elif (divide * 2) < sum_corr <= max_sum:
        strong_corr.append(attribute)

# Vytvorenie novej matice -> odstránené nulové atribúty + pôvodné korelácie
def matrix_for_graph(pearson_corr_matrix: pd.DataFrame, sigma_corr_matrix: pd.DataFrame) -> pd.DataFrame:
    retained_columns = sigma_corr_matrix.columns
    retained_rows = sigma_corr_matrix.index
    graph_matrix = pearson_corr_matrix.loc[retained_rows, retained_columns]

    return graph_matrix

graph_matrix = matrix_for_graph(pearson_corr_matrix, sigma_corr_matrix)

# Uloženie matice ako CSV súbor (pre tepelnú mapu)
output_dir = "C:/Users/ASUS1/Desktop/Python 3D graf/python_outputs"
file_name = f"{name}_graph_matrix.csv"
full_path = os.path.join(output_dir, file_name)
graph_matrix.to_csv(full_path, index=True)
print(f"Matica bola úspešne uložená do: {full_path}")
# ---------------------------------------------------------------------------------------------------------

# Vytvorenie 3D grafu
# Funkcia na rozloženie bodov do kruhu
def circular_layout(attributes, z_level, radius=5):
    n = len(attributes)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    z = np.full(n, z_level)
    return x, y, z

# Generovanie súradníc pre atribúty
x_weak, y_weak, z_weak = circular_layout(weak_corr, 1)
x_medium, y_medium, z_medium = circular_layout(medium_corr, 2)
x_strong, y_strong, z_strong = circular_layout(strong_corr, 3)

# Vytvorenie 3D scatter bodov
trace_nodes = go.Scatter3d(
    x=np.concatenate([x_weak, x_medium, x_strong]),
    y=np.concatenate([y_weak, y_medium, y_strong]),
    z=np.concatenate([z_weak, z_medium, z_strong]),
    mode='text+markers',
    text=weak_corr + medium_corr + strong_corr,
    textfont=dict(size=14, color="black"),
    textposition="top center",
    marker=dict(size=8, color=['yellow']*len(weak_corr) + ['blue']*len(medium_corr) + ['green']*len(strong_corr)),
    showlegend=False
)

# Funkcia na vykreslenie spojníc medzi bodmi
def draw_edges(group1, x1, y1, z1, group2, x2, y2, z2):
    edges = []
    for i, attr1 in enumerate(group1):
        for j, attr2 in enumerate(group2):
            corr_value = graph_matrix.loc[attr1, attr2]
            if corr_value != 0:
                edges.append(
                    go.Scatter3d(
                        x=[x1[i], x2[j]],
                        y=[y1[i], y2[j]],
                        z=[z1[i], z2[j]],
                        mode='lines',
                        line=dict(width=2, color='black'),
                        hoverinfo="text",
                        text=f"{attr1} ↔ {attr2}: {corr_value:.2f}",
                        showlegend=False
                    )
                )
    return edges

# Spojenia v rámci jednotlivých rovín
edges = []
edges.extend(draw_edges(weak_corr, x_weak, y_weak, z_weak, weak_corr, x_weak, y_weak, z_weak))
edges.extend(draw_edges(medium_corr, x_medium, y_medium, z_medium, medium_corr, x_medium, y_medium, z_medium))
edges.extend(draw_edges(strong_corr, x_strong, y_strong, z_strong, strong_corr, x_strong, y_strong, z_strong))

# Spojenie medzi rovinami
strongest_weak_medium = None
max_corr_weak_medium = 0

for attr1 in weak_corr:
    for attr2 in medium_corr:
        corr_value = abs(graph_matrix.loc[attr1, attr2])
        if corr_value > max_corr_weak_medium:
            max_corr_weak_medium = corr_value
            strongest_weak_medium = (attr1, attr2)

strongest_medium_strong = None
max_corr_medium_strong = 0

for attr1 in medium_corr:
    for attr2 in strong_corr:
        corr_value = abs(graph_matrix.loc[attr1, attr2])
        if corr_value > max_corr_medium_strong:
            max_corr_medium_strong = corr_value
            strongest_medium_strong = (attr1, attr2)


# Funkcia na vykreslenie spojnice medzi rovinami
def dashed_line(attr1, attr2, group1, x1, y1, z1, group2, x2, y2, z2):
    i1 = group1.index(attr1)
    i2 = group2.index(attr2)

    return go.Scatter3d(
        x=[x1[i1], x2[i2]],
        y=[y1[i1], y2[i2]],
        z=[z1[i1], z2[i2]],
        mode='lines',
        line=dict(width=2, color='red', dash='dash'),
        hoverinfo="text",
        text=f"{attr1} ↔ {attr2}: {graph_matrix.loc[attr1, attr2]:.2f}",
        showlegend=False
    )


# Pridanie najsilnejších spojení medzi rovinami
if strongest_weak_medium:
    attr1, attr2 = strongest_weak_medium
    edges.append(
        dashed_line(attr1, attr2, weak_corr, x_weak, y_weak, z_weak, medium_corr, x_medium, y_medium, z_medium))

if strongest_medium_strong:
    attr1, attr2 = strongest_medium_strong
    edges.append(
        dashed_line(attr1, attr2, medium_corr, x_medium, y_medium, z_medium, strong_corr, x_strong, y_strong, z_strong))


# Nastavenie osí
layout = go.Layout(
    scene=dict(
        xaxis_title="X",
        yaxis_title="Y",
        zaxis_title="Z",
        zaxis=dict(tickvals=[1, 2, 3], ticktext=["Slabé", "Stredné", "Silné"], backgroundcolor='rgba(0,0,0,0)', showgrid=False, zeroline=False),
        xaxis=dict(backgroundcolor='rgba(0,0,0,0)', showgrid=False, zeroline=False),
        yaxis=dict(backgroundcolor='rgba(0,0,0,0)', showgrid=False, zeroline=False),
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
)

# Vytvorenie grafu
fig = go.Figure(data=[trace_nodes] + edges, layout=layout)
# -------------------------------------------------------------------------------------------------------------

# Uloženie 3D grafu ako HTML súbor
output_file = os.path.join(output_dir, f"{name}_3d_graph.html")

# Uloženie HTML súboru
fig.write_html(output_file)

print(f"3D graf bol úspešne uložený do: {output_file}")
