

import pandas as pd
import io
import unicodedata
import re
import networkx as nx
import pygraphviz # Import the Graph class
from networkx.drawing.nx_pydot import to_pydot
from IPython.display import SVG
import subprocess

# Function to convert text to a valid Python variable name
def to_variable_name(text):
    # Normalize the text to decompose accented characters
    text = unicodedata.normalize('NFKD', str(text))

    # Remove non-ASCII characters and replace with their base letters
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Remove remaining special characters and replace spaces with underscores
    text = re.sub(r'[^\w\s]', '', text)
    text = text.replace(' ', '_')

    return text

def csv_to_pd(csv_data,csv_node=""):
    # Create DataFrame A
    A = pd.read_csv(io.StringIO(csv_data))
    D = ""
       # Create DataFrame B with distinct elements from first two columns
    B_data = pd.concat([A['source'], A['target']]).drop_duplicates()
    B = pd.DataFrame({
        'texlbl': B_data,
        'name': B_data.apply(to_variable_name)
    })

    #If a node CSV is provided, update texlbl in B with node labels
    if csv_node:
        D = pd.read_csv(io.StringIO(csv_node))
        #print(D)
        #print(B)
        # Merge B with D to update texlbl
        B = B.merge(D[['name', 'texlbl']], on='name', how='left')
        #print(B)
        # Update texlbl column, keeping original if no match in D
        B['texlbl'] = B['texlbl_y'].fillna(B['texlbl_x'])

        # Drop the temporary merge columns
        B = B.drop(columns=['texlbl_x', 'texlbl_y'])
        #print(B)

    # Create DataFrame C

    # Create DataFrame C
    C = pd.DataFrame({
        'source_name': A['source'].apply(to_variable_name),
        'target_name': A['target'].apply(to_variable_name),
        'label': A['label'],
        'style': A.iloc[:, 3]
    })

    C.fillna("solid", inplace=True)
    return (B,C)

def pd_to_nx(B,C):
    # Assuming B and C DataFrames are already created from the previous code

    # Create an empty graph
    G = nx.DiGraph()  # Using DiGraph for a directed graph

    # Add nodes from table B
    # Use the 'name' column as node identifier and 'texlbl' as a node attribute
    for _, row in B.iterrows():
        G.add_node(
            row['name'],  # Use the converted variable name as node identifier
            texlbl=row['texlbl']  # Original label as a node attribute
        )

    # Add edges from table C
    for _, row in C.iterrows():
        # Add an edge using the converted source and target names
        G.add_edge(
            row['source_name'],  # Source node
            row['target_name'],  # Target node
            style=row.get('style', ''),  # Style attribute
            texlbl=row.get('label', '')  # Label attribute
        )
    return G


def nx_to_dot(G,tex_file_path="graph"):
    dot_graph = to_pydot(G)

    # Save the DOT file
    with open(tex_file_path+".dot", "w", encoding="utf-8") as f:
        f.write(dot_graph.to_string())
    return(dot_graph)


def insert_resizebox(tex_file_path):
    """Inserts \resizebox{\linewidth}{!}{ and } into a LaTeX file.

    Args:
        tex_file_path: Path to the LaTeX file.

    Returns:
        None
    """

    with open(tex_file_path, 'r') as f:
        lines = f.readlines()

    # Find the line containing \pagestyle{empty}
    for i, line in enumerate(lines):
        if r"\pagestyle{empty}" in line:
            lines.insert(i + 1, r"\resizebox{\linewidth}{!}{")
            break

    # Find the line containing \end{document}
    for i,line in enumerate(lines):
        if r"\end{document}" in line:
            lines.insert(i-1, r"}")
            break

    with open(tex_file_path, 'w') as f:
        f.writelines(lines)



def csv_to_svg(csv_data,csv_node="",tex_file_path = "graph"):
    (B,C)=csv_to_pd(csv_data,csv_node)
    G = pd_to_nx(B,C)
    nx_to_dot(G,tex_file_path)


    # Using subprocess for shell commands
    subprocess.run(f'dot2tex --docpreamble "\\usepackage[utf8]{{inputenc}} \\usepackage[T1]{{fontenc}} \\usepackage{{amssymb}}" -tmath --autosize "{tex_file_path}.dot" > "{tex_file_path}.tex"', shell=True)
    insert_resizebox(f"{tex_file_path}.tex")
    subprocess.run(f'xelatex "{tex_file_path}.tex"', shell=True)

    subprocess.run(f'pdf2svg "{tex_file_path}.pdf" "{tex_file_path}.svg"', shell=True)

    display(SVG(f"{tex_file_path}.svg"))
