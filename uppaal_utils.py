# Utilitary functions for UPPAAL template generation
import graphlib
import re
from typing import List, Tuple
import uppaalpy
import copy

from utils import AbstractTask, MethodData, Variable

const_end_method_name = "end_method"

def check_camel_case_regex(string: str):
    return re.match("(?:[A-Z])(?:\S?)+(?:[A-Z])(?:[a-z])+", string)

def print_nodes_from_template(template: uppaalpy.Template):
    nodes = template.graph.get_nodes()
    for i in range(len(nodes)):
        print(nodes[i].name.name)

def print_nta_declaration(nta: uppaalpy.NTA):
    print(nta.declaration.text)


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

def generate_transitions_at_template(template: uppaalpy.Template, order: list, node_data: List[AbstractTask], nta: uppaalpy.NTA) -> uppaalpy.Template:
    # Add the connections between methods
    j = 0 # Counter for AT Methods
    add_transition_on_next_iteration = True
    for i in range(len(order)):    
        if(i+1 <= len(order)):
            source_id, target_id = "id"+str(i), "id"+str(i+1)
            # debug
            # print("Connecting", source_id, "to",
            #   target_id, "in template", temp.name.name)
            if add_transition_on_next_iteration:
                trans = uppaalpy.Transition(
                    source=source_id, target=target_id)
                template.graph.add_transition(trans)

            if not check_camel_case_regex(order[i]):
                add_transition_on_next_iteration = True
            else:
                add_transition_on_next_iteration = False

    template = add_AT_transitions_in_template(template, node_data, nta)

            
            



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
    return template

def add_AT_transitions_in_template(template: uppaalpy.Template, node_data: List[AbstractTask], nta: uppaalpy.NTA):
    locations = template.graph.get_nodes()
    for i in range(len(locations)):
        if(check_camel_case_regex(locations[i].name.name)):
            for node in node_data:
                j = 0
                if(locations[i].name.name == node.name):
                    posX, posY = locations[i].pos
                    posY -= 100
                    for method in node.methods:
                        add_declaration_for_channels_in_nta(channel_name=method, nta=nta)
                        print_nta_declaration(nta)
                        location_method_name = "exec_" + method
                        location_method_id = "id"+str(800+j)
                        # Create location for each method and add a Transition to it from the AT Task
                        add_location(template=template,
                        id=location_method_id, 
                        name=location_method_name, 
                        pos=(posX, posY))
                        # Adding transition
                        template.graph.add_transition(uppaalpy.Transition(source=locations[i].id, target=location_method_id))
                        j+=1
                        posX += 100
                        posY -= 100
                        # now locate the next node and a Transition to it
                        if i+1 in range(len(locations)):
                            target_id = locations[i+1].id
                            template.graph.add_transition(uppaalpy.Transition(source=location_method_id, target=target_id))
                            
    return template

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


def generate_declaration_for_nta(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: List[Variable], set_of_types: set[str]) -> uppaalpy.NTA:
    nta = generate_structs_for_types(nta, predicates, var_and_types_list, set_of_types)
    return nta

def generate_structs_for_types(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: List[Variable], set_of_types: set[str]) -> uppaalpy.NTA:
    # For each of the types in the set we gotta create a struct, so the types can have specific predicates
    nta.declaration.text += "\n"
    flag = 0
    for tp in set_of_types:
        struct_start = "typedef struct {\n"
        nta.declaration.text += struct_start
        # print("partial text: ")
        # print(nta.declaration.text)
        for tvar in var_and_types_list:
            # print(predicates.values)
            if(tvar.type_name == tp):
                # print("tvar.type", tvar.type_name, "equals to", "tp", tp)
                for predicate_name in predicates.keys():
                    predicate_type = predicates.get(predicate_name)
                    if(predicate_type == tvar.var_name):
                        # print("prec_value", predicate_type, "equals to",
                        #         "tvar.name", tvar.var_name)
                        nta.declaration.text += "bool " + predicate_name + ";"
                        nta.declaration.text += "\n"
                        flag = 1
        # Delete the struct declaration, since no predicate was found for that struct
        if flag != 1:
            startIndex = nta.declaration.text.rindex(struct_start)
            nta.declaration.text = nta.declaration.text[0: startIndex]
        else:
            struct_end = "} "+tp.title()+";\n"
            nta.declaration.text += struct_end
        flag = 0
    return nta

def generate_uppaal_methods_templates(method_data: List[MethodData], nta: uppaalpy.NTA, node_data: List[AbstractTask]) -> uppaalpy.NTA:
    for m in method_data:
        template_name = "temp_" + m.method_name
        add_template(nta=nta, template_name=template_name, template_to_copy=nta.templates[0],
                     parameters=None,
                     declaration=None)

        for temp in nta.templates:
            posX = -552
            posY = -150
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
                                                                  pos=(posX + 150, posY),
                                                                  name=uppaalpy.Name(
                                                                      name=const_end_method_name,
                                                                      pos=(posX+134, posY-31))))
                        # Create connection of endtask to beginning
                        temp.graph.add_transition(
                            uppaalpy.Transition(source="id999", target="id0"))
                        # and last action with end node
                        temp.graph.add_transition(
                            uppaalpy.Transition(source=id_str, target="id999"))

                temp = generate_transitions_at_template(template=temp, order=m.order, node_data=node_data, nta=nta)

    return nta

def add_declaration_for_channels_in_nta(channel_name: str, nta: uppaalpy.NTA) -> uppaalpy.NTA:
    # Always do a line skip before beginning to write in a file that already contains written lines
    if(check_for_duplicate_channel(channel_name=channel_name, nta=nta)):
        nta.declaration.text += "\n"
        nta.declaration.text += f"broadcast chan start_{channel_name};\n"
        nta.declaration.text += f"broadcast chan finish_{channel_name};\n"
    return nta

def check_for_duplicate_channel(channel_name: str, nta: uppaalpy.NTA) -> bool:
    if(nta.declaration.text.find(f"broadcast chan start_{channel_name};") != -1 or
    nta.declaration.text.find(f"broadcast chan start_{channel_name};") != -1):
        return False
    else:
        return True



# def generate_transition(method_data, temp: uppaalpy.Template):
#     for m in method_data:
