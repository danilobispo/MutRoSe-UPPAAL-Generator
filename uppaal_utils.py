# Utilitary functions for UPPAAL template generation
from typing import Tuple
import uppaalpy
import copy


def print_nodes_from_template(template: uppaalpy.Template):
    nodes = template.graph.get_nodes()
    for i in range(len(nodes)):
        print(nodes[i].name.name)

def retrieve_node_copy(template: uppaalpy.Template) -> uppaalpy.Location:
    nodes = template.graph.get_nodes()
    node_copy = copy.deepcopy(nodes[0])
    return node_copy

def add_location(template: uppaalpy.Template, id:str, pos: Tuple[int, int], name: str):
    nc = retrieve_node_copy(template)
    nc.id = id #e.g idX(switch X for a)
    nc.pos = pos
    nc.name.name = name
    template.graph.add_location(nc)

def add_template(
    nta: uppaalpy.NTA, 
    template_to_copy: uppaalpy.Template, 
    template_name: str, 
    parameters: uppaalpy.Parameter | None, 
    declaration: uppaalpy.Declaration | None):
    
    tp_copy = copy.deepcopy(template_to_copy)
    tp_copy.name.name = template_name
    tp_copy.parameter = parameters
    tp_copy.declaration = declaration

    nta.templates.append(tp_copy)
    return nta
    