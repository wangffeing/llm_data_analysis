# -*- coding: utf-8 -*-
import json
from typing import Any, Dict, Optional, Tuple, List, Union
from taskweaver.plugin import Plugin, register_plugin

# Maximum allowed nodes for diagram generation
MAX_NODES = 50

def json_converter(o: Any) -> Any:
    """JSON serialization helper"""
    if hasattr(o, 'isoformat'):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

@register_plugin
class gpt_vis_diagram(Plugin):
    def __call__(
            self,
            diagram_type: str,
            nodes: Optional[List[Dict]] = None,
            edges: Optional[List[Dict]] = None,
            mind_data: Optional[Dict] = None,
            title: Optional[str] = None,
    ) -> str:
        
        # Validate diagram type
        supported_types = ['flow-diagram', 'mind-map']
        if diagram_type not in supported_types:
            raise ValueError(f"Unsupported diagram type: {diagram_type}. Supported types: {supported_types}")
        
        # Validate input data based on diagram type
        if diagram_type == 'flow-diagram':
            if not nodes or not edges:
                raise ValueError("Flow diagram requires both 'nodes' and 'edges' parameters.")
            
            # Check nodes limit
            if len(nodes) > MAX_NODES:
                raise ValueError(
                    f"Number of nodes ({len(nodes)}) exceeds maximum limit ({MAX_NODES}). "
                    f"Please reduce the number of nodes for better performance."
                )
            
            # Validate nodes structure
            for i, node in enumerate(nodes):
                if not isinstance(node, dict) or 'name' not in node:
                    raise ValueError(f"Node {i} must be a dictionary with 'name' field.")
            
            # Validate edges structure
            for i, edge in enumerate(edges):
                if not isinstance(edge, dict) or 'source' not in edge or 'target' not in edge:
                    raise ValueError(f"Edge {i} must be a dictionary with 'source' and 'target' fields.")
            
            processed_data = self._process_flow_diagram_data(nodes, edges)
        
        elif diagram_type == 'mind-map':
            if not mind_data:
                raise ValueError("Mind map requires 'mind_data' parameter.")
            
            # Validate mind map structure
            if not isinstance(mind_data, dict) or 'name' not in mind_data:
                raise ValueError("Mind map data must be a dictionary with 'name' field.")
            
            # Count total nodes in mind map
            node_count = self._count_mind_map_nodes(mind_data)
            if node_count > MAX_NODES:
                raise ValueError(
                    f"Number of mind map nodes ({node_count}) exceeds maximum limit ({MAX_NODES}). "
                    f"Please simplify the mind map structure."
                )
            
            processed_data = mind_data
        
        # Build diagram configuration
        diagram_config = {
            "type": diagram_type,
            "data": processed_data
        }
        
        # Add optional parameters
        if title:
            diagram_config["title"] = title
        
        # Generate output
        filename = f'''vis-diagram_{diagram_type}_{title or "untitled"}.vis'''
        markdown_content = self._generate_markdown(diagram_config, filename)
        
        return markdown_content
    
    def _process_flow_diagram_data(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """Process flow diagram data to GPT-Vis format"""
        # Ensure nodes have required structure
        processed_nodes = []
        for node in nodes:
            processed_node = {"name": node["name"]}
            if "label" in node:
                processed_node["label"] = node["label"]
            processed_nodes.append(processed_node)
        
        # Ensure edges have required structure
        processed_edges = []
        for edge in edges:
            processed_edge = {
                "source": edge["source"],
                "target": edge["target"]
            }
            if "name" in edge:
                processed_edge["name"] = edge["name"]
            if "label" in edge:
                processed_edge["label"] = edge["label"]
            processed_edges.append(processed_edge)
        
        return {
            "nodes": processed_nodes,
            "edges": processed_edges
        }
    
    def _count_mind_map_nodes(self, data: Dict) -> int:
        """Count total nodes in mind map recursively"""
        count = 1  # Count current node
        if "children" in data and isinstance(data["children"], list):
            for child in data["children"]:
                count += self._count_mind_map_nodes(child)
        return count
    
    def _generate_markdown(self, diagram_config: Dict[str, Any], filename: str) -> str:
        """Generate markdown content"""
        diagram_json = json.dumps(diagram_config, ensure_ascii=False, default=json_converter, indent=2)
        json_content = f"```vis-chart\n{diagram_json}\n```"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(json_content)
        except Exception as e:
            print(f"Warning: Could not write to file {filename}: {e}")
        
        return json_content