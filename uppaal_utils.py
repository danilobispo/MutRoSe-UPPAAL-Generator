# Utilitary functions for UPPAAL template generation
from typing import List, Tuple
import uppaalpy
import copy


def print_nodes_from_template(template: uppaalpy.Template):
    nodes = template.graph.get_nodes()
    for i in range(len(nodes)):
        print(nodes[i].name.name)


def get_nodes_from_template(template: uppaalpy.Template) -> List[uppaalpy.Node]:
    return template.graph.get_nodes()

def retrieve_node_copy(template: uppaalpy.Template) -> uppaalpy.Location:
    nodes = template.graph.get_nodes()
    node_copy = copy.deepcopy(nodes[0])
    return node_copy

def add_location(template: uppaalpy.Template, id:str, pos: Tuple[int, int], name: str):
    nc = retrieve_node_copy(template)
    nc.id = id #e.g idX(switch X for a)
    nc.pos = pos
    nc.name.name = name
    # print(pos[0], pos[1])
    nc.name.pos = (pos[0]-14, pos[1] - 31)
    template.graph.add_location(nc)

def add_template(
    nta: uppaalpy.NTA, 
    template_to_copy: uppaalpy.Template, 
    template_name: str, 
    parameters: uppaalpy.Parameter | None, 
    declaration: uppaalpy.Declaration | None):
    """_summary_

    Args:
        nta (uppaalpy.NTA): _description_
        template_to_copy (uppaalpy.Template): _description_
        template_name (str): _description_
        parameters (uppaalpy.Parameter | None): _description_
        declaration (uppaalpy.Declaration | None): _description_
    """
    
    flag_repeated_template = False
    for temp in nta.templates:
        if template_name == temp.name.name:
            flag_repeated_template = True
            break
            
    if(not flag_repeated_template):
        tp_copy = copy.deepcopy(template_to_copy)
        tp_copy.name.name = template_name
        tp_copy.parameter = parameters
        tp_copy.declaration = declaration

        nta.templates.append(tp_copy)


def generate_uppaal_methods_templates(method_data, nta: uppaalpy.NTA) -> uppaalpy.NTA:
    for m in method_data:
        template_name = "temp_" + m.method_name
        add_template(nta= nta, template_name=template_name, template_to_copy=nta.templates[0], 
        parameters=None, 
        declaration=None)

        for temp in nta.templates:
            posX = -572
            posY = -113
            if(temp.name.name == template_name):
                id_count = 1
                for i in range(len(m.order)):
                    id_str = "id"+str(id_count)
                    add_location(template=temp, id=id_str, pos=(posX, posY), name=m.order[i])
                    id_count = id_count + 1
                    posX = posX + 150
                    # posY = posY + 100
    return nta

        