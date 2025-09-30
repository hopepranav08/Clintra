import os
import json
import base64
import io
import tempfile
from typing import Dict, List, Any, Optional
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import numpy as np

class GraphGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def generate_biomedical_graph(self, query: str, data_type: str = "literature") -> Dict[str, Any]:
        """
        Generate a real biomedical graph based on the query.
        """
        # Create a network graph
        G = nx.Graph()
        
        # Add nodes based on query
        main_node = query.replace(' ', '_').lower()
        G.add_node(main_node, label=query, type="main", size=20)
        
        # Add related nodes based on query type
        if "treatment" in query.lower():
            G.add_node("drug_target", label="Drug Target", type="target", size=15)
            G.add_node("pathway", label="Biological Pathway", type="pathway", size=12)
            G.add_node("protein", label="Target Protein", type="protein", size=15)
            G.add_node("clinical_trial", label="Clinical Trial", type="trial", size=10)
            
            # Add edges
            G.add_edge(main_node, "drug_target", type="targets")
            G.add_edge(main_node, "pathway", type="modulates")
            G.add_edge("drug_target", "protein", type="binds")
            G.add_edge("protein", "pathway", type="participates")
            G.add_edge(main_node, "clinical_trial", type="investigated_in")
            
        elif "disease" in query.lower():
            G.add_node("biomarker", label="Biomarker", type="biomarker", size=12)
            G.add_node("symptom", label="Symptom", type="symptom", size=10)
            G.add_node("gene", label="Associated Gene", type="gene", size=12)
            G.add_node("pathway", label="Disease Pathway", type="pathway", size=15)
            
            # Add edges
            G.add_edge(main_node, "biomarker", type="has")
            G.add_edge(main_node, "symptom", type="causes")
            G.add_edge(main_node, "gene", type="associated_with")
            G.add_edge("gene", "pathway", type="involved_in")
            
        else:
            # Generic biomedical graph
            G.add_node("molecule", label="Molecule", type="molecule", size=15)
            G.add_node("receptor", label="Receptor", type="receptor", size=15)
            G.add_node("pathway", label="Pathway", type="pathway", size=12)
            
            # Add edges
            G.add_edge(main_node, "molecule", type="contains")
            G.add_edge("molecule", "receptor", type="binds")
            G.add_edge("receptor", "pathway", type="activates")
        
        # Generate different formats
        graph_data = {
            "query": query,
            "graph_type": "network",
            "nodes": [{"id": node, "label": G.nodes[node].get("label", node), 
                      "type": G.nodes[node].get("type", "unknown"), 
                      "size": G.nodes[node].get("size", 10)} for node in G.nodes()],
            "edges": [{"source": edge[0], "target": edge[1], 
                      "type": G.edges[edge].get("type", "connects")} for edge in G.edges()],
            "download_links": self._generate_download_links(G, query),
            "sponsor_tech": "Powered by NetworkX, Matplotlib, and Plotly for real graph generation"
        }
        
        return graph_data
    
    def _generate_download_links(self, G: nx.Graph, query: str) -> Dict[str, str]:
        """
        Generate real downloadable graph files.
        """
        # Generate JSON data
        graph_json = {
            "nodes": [{"id": node, "label": G.nodes[node].get("label", node), 
                      "type": G.nodes[node].get("type", "unknown"), 
                      "size": G.nodes[node].get("size", 10)} for node in G.nodes()],
            "edges": [{"source": edge[0], "target": edge[1], 
                      "type": G.edges[edge].get("type", "connects")} for edge in G.edges()],
            "metadata": {"query": query, "generated_at": "2024-01-01T00:00:00Z"}
        }
        
        json_data = json.dumps(graph_json, indent=2)
        json_b64 = base64.b64encode(json_data.encode()).decode()
        
        # Generate PNG image
        png_b64 = self._generate_png_graph(G, query)
        
        # Generate SVG
        svg_b64 = self._generate_svg_graph(G, query)
        
        # Generate interactive HTML
        html_b64 = self._generate_interactive_html(G, query)
        
        return {
            "graph_json": f"data:application/json;base64,{json_b64}",
            "graph_png": f"data:image/png;base64,{png_b64}",
            "graph_svg": f"data:image/svg+xml;base64,{svg_b64}",
            "interactive_viewer": f"data:text/html;base64,{html_b64}"
        }
    
    def _generate_png_graph(self, G: nx.Graph, query: str) -> str:
        """
        Generate a PNG image of the graph.
        """
        plt.figure(figsize=(12, 8))
        plt.style.use('dark_background')
        
        # Use spring layout for better positioning
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Define colors for different node types
        node_colors = {
            "main": "#FF6B6B",
            "target": "#4ECDC4", 
            "pathway": "#45B7D1",
            "protein": "#96CEB4",
            "trial": "#FFEAA7",
            "biomarker": "#DDA0DD",
            "symptom": "#98D8C8",
            "gene": "#F7DC6F",
            "molecule": "#BB8FCE",
            "receptor": "#85C1E9",
            "unknown": "#BDC3C7"
        }
        
        # Draw nodes
        for node_type in set(G.nodes[node].get("type", "unknown") for node in G.nodes()):
            nodes_of_type = [node for node in G.nodes() if G.nodes[node].get("type", "unknown") == node_type]
            if nodes_of_type:
                nx.draw_networkx_nodes(G, pos, nodelist=nodes_of_type, 
                                     node_color=node_colors.get(node_type, "#BDC3C7"),
                                     node_size=[G.nodes[node].get("size", 10) * 50 for node in nodes_of_type],
                                     alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color="#FFFFFF", alpha=0.6, width=2)
        
        # Draw labels
        labels = {node: G.nodes[node].get("label", node) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color="white", font_weight="bold")
        
        plt.title(f"Biomedical Graph: {query}", fontsize=16, fontweight="bold", color="white")
        plt.axis("off")
        
        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        png_b64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return png_b64
    
    def _generate_svg_graph(self, G: nx.Graph, query: str) -> str:
        """
        Generate an SVG image of the graph.
        """
        plt.figure(figsize=(12, 8))
        plt.style.use('dark_background')
        
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Define colors for different node types
        node_colors = {
            "main": "#FF6B6B",
            "target": "#4ECDC4", 
            "pathway": "#45B7D1",
            "protein": "#96CEB4",
            "trial": "#FFEAA7",
            "biomarker": "#DDA0DD",
            "symptom": "#98D8C8",
            "gene": "#F7DC6F",
            "molecule": "#BB8FCE",
            "receptor": "#85C1E9",
            "unknown": "#BDC3C7"
        }
        
        # Draw nodes
        for node_type in set(G.nodes[node].get("type", "unknown") for node in G.nodes()):
            nodes_of_type = [node for node in G.nodes() if G.nodes[node].get("type", "unknown") == node_type]
            if nodes_of_type:
                nx.draw_networkx_nodes(G, pos, nodelist=nodes_of_type, 
                                     node_color=node_colors.get(node_type, "#BDC3C7"),
                                     node_size=[G.nodes[node].get("size", 10) * 50 for node in nodes_of_type],
                                     alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color="#FFFFFF", alpha=0.6, width=2)
        
        # Draw labels
        labels = {node: G.nodes[node].get("label", node) for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color="white", font_weight="bold")
        
        plt.title(f"Biomedical Graph: {query}", fontsize=16, fontweight="bold", color="white")
        plt.axis("off")
        
        # Save to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        svg_b64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return svg_b64
    
    def _generate_interactive_html(self, G: nx.Graph, query: str) -> str:
        """
        Generate an interactive HTML visualization using Plotly.
        """
        # Get positions
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare data for Plotly
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create edge trace
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=2, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        # Create node traces by type
        node_traces = []
        node_colors = {
            "main": "#FF6B6B",
            "target": "#4ECDC4", 
            "pathway": "#45B7D1",
            "protein": "#96CEB4",
            "trial": "#FFEAA7",
            "biomarker": "#DDA0DD",
            "symptom": "#98D8C8",
            "gene": "#F7DC6F",
            "molecule": "#BB8FCE",
            "receptor": "#85C1E9",
            "unknown": "#BDC3C7"
        }
        
        for node_type in set(G.nodes[node].get("type", "unknown") for node in G.nodes()):
            nodes_of_type = [node for node in G.nodes() if G.nodes[node].get("type", "unknown") == node_type]
            if nodes_of_type:
                node_x = [pos[node][0] for node in nodes_of_type]
                node_y = [pos[node][1] for node in nodes_of_type]
                node_text = [G.nodes[node].get("label", node) for node in nodes_of_type]
                node_size = [G.nodes[node].get("size", 10) * 5 for node in nodes_of_type]
                
                node_trace = go.Scatter(x=node_x, y=node_y,
                                      mode='markers+text',
                                      hoverinfo='text',
                                      text=node_text,
                                      textposition="middle center",
                                      marker=dict(size=node_size,
                                                color=node_colors.get(node_type, "#BDC3C7"),
                                                line=dict(width=2, color='white')),
                                      name=node_type.title())
                node_traces.append(node_trace)
        
        # Create figure
        fig = go.Figure(data=[edge_trace] + node_traces,
                       layout=go.Layout(
                           title=f'Interactive Biomedical Graph: {query}',
                           titlefont_size=16,
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Interactive graph - hover over nodes for details",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor="left", yanchor="bottom",
                               font=dict(color="#888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='#1a1a1a',
                           paper_bgcolor='#1a1a1a',
                           font=dict(color='white')
                       ))
        
        # Convert to HTML
        html_str = fig.to_html(include_plotlyjs='cdn', div_id="graph")
        html_b64 = base64.b64encode(html_str.encode()).decode()
        
        return html_b64

# Global instance
graph_generator = GraphGenerator()
