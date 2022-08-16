# Utilitary functions for UPPAAL template generation
from typing import List, Tuple
import uppaalpy
import copy

from utils import MethodData

const_end_method_name = "end_method"


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


def add_location(template: uppaalpy.Template, id: str, pos: Tuple[int, int], name: str):
    nc = retrieve_node_copy(template)
    nc.id = id  # e.g idX(switch X for a)
    nc.pos = pos
    nc.name.name = name
    # print(pos[0], pos[1])
    nc.name.pos = (pos[0]-14, pos[1] - 31)
    template.graph.add_location(nc)


def retrieve_transition_copy(template: uppaalpy.Template) -> uppaalpy.Transition:
    transitions = template.graph._transitions
    trans_copy = copy.deepcopy(transitions[0])
    return trans_copy


def add_transition(template: uppaalpy.Template, source: str, target: str):
    tc = retrieve_transition_copy(template)
    tc.source = source  # e.g idX(switch X for a)
    tc.target = target  # e.g idX(switch X for a)
    template.graph.add_transition(tc)


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

def generate_declaration_for_nta(nta:uppaalpy.NTA, predicates) -> uppaalpy.NTA:
    for prec in predicates:
        print()
    # Create a simple declaration
    new_declaration = uppaalpy.Declaration(text="")

    nta.declaration.text

def generate_uppaal_methods_templates(method_data: List[MethodData], nta: uppaalpy.NTA) -> uppaalpy.NTA:
    for m in method_data:
        template_name = "temp_" + m.method_name
        add_template(nta=nta, template_name=template_name, template_to_copy=nta.templates[0],
                     parameters=None,
                     declaration=None)

        # After the templates are added, let's create the variables for preconditions, effects and capabilities
        # this is done in declarations
        # then set in parameters for each of the predicates and its respective types 


        for temp in nta.templates:
            posX = -572
            posY = -113
            if(temp.name.name == template_name):
                id_count = 1
                for i in range(len(m.order)):

                    id_str = "id"+str(id_count)
                    add_location(template=temp, id=id_str,
                                 pos=(posX, posY), name=m.order[i])
                    id_count = id_count + 1
                    posX = posX + 150
                    # posY = posY + 100
                    if i == len(m.order)-1:
                        # Add end location, end of method that goes back to initial node
                        temp.graph.add_location(uppaalpy.Location(id="id999",
                                                                  pos=(
                                                                      posX + 150, posY),
                                                                  name=uppaalpy.Name(
                                                                      name=const_end_method_name,
                                                                      pos=(posX+134, posY-31))))
                        # Create connection of endtask to beginning
                        temp.graph.add_transition(
                            uppaalpy.Transition(source="id999", target="id0"))
                        # and last action with end node
                        temp.graph.add_transition(
                            uppaalpy.Transition(source=id_str, target="id999"))

                # Add the connections between methods
                for i in range(len(m.order)):
                    if(i+1 <= len(m.order)):
                        source_id, target_id = "id"+str(i), "id"+str(i+1)
                        # debug
                        print("Connecting", source_id, "to",
                              target_id, "in template", temp.name.name)
                        trans = uppaalpy.Transition(source=source_id, target=target_id)
                        temp.graph.add_transition(trans)

                        # Add precondition if existing, then create a location for precondition not being met
                        # same must be done to capabilities, but i gotta think how
                        # if i == 0 and len(m.preconditions): # i.e has preconditions and it is the first node
                        #     for prec in m.preconditions:
                        #         print(prec)
                        #         if prec.value == "true":
                        #             exprstr = prec.type + "." + prec.name + "==" + prec.value  
                        #         else: 
                        #             exprstr = prec.type + "." + prec.name + "!=" + prec.value
                        #         trans.create_constraint_label(uppaalpy.ConstraintExpression(exprstr=exprstr, ctx=nta.context))

                        
    return nta


# def generate_transition(method_data, temp: uppaalpy.Template):
#     for m in method_data:
