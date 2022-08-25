# Utilitary functions for UPPAAL template generation
import graphlib
import re
from typing import List, Tuple
import uppaalpy
import copy

from utils import AbstractTask, Effect, MethodData, Precondition, Variable

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

def generate_transitions_at_template(template: uppaalpy.Template, order: list, current_method: MethodData, node_data: List[AbstractTask], nta: uppaalpy.NTA) -> uppaalpy.Template:
    preconditions_list: list[Precondition] = current_method.preconditions
    effects_list: list[Effect] = current_method.effects
    # Add the connections between methods
    eff_label = None
    has_effects = False
    prec_label = None
    has_precs = False
    print(f"len order: {len(order)}")
    for i in range(len(order)):
        id_count = i+1
        source_id, target_id = "id"+str(id_count), "id"+str(id_count+1)
        
        if(i == 0):
        # TODO: Deal with preconditions here
            has_precs, prec_label =  search_and_generate_preconditions_in_node(order, preconditions_list, i, nta.context)
            if has_precs:
                insert_precondition_in_location(source_id="id0", target_id="id1", template=template, prec_label=prec_label)
            else:
                template.graph.add_transition(uppaalpy.Transition(source="id0", target="id1"))


        if i == len(order) - 1: # add last method transition with end node
            # debug
            has_effects, eff_label = search_and_generate_effects_in_node(order=order, effects_list=effects_list, i=i, context_nta=nta) 
            if has_effects: # if there's an effect, add to transition
                # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                insert_effect_in_location(source_id=source_id, target_id="id999", template=template, eff_label=eff_label)
            else: 
                # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                template.graph.add_transition(
                    uppaalpy.Transition(source=source_id, target="id999"))

        elif id_count < len(order):
            # print(f"i: {i}")
            # print("Current node:", order[i])

            has_effects, eff_label = search_and_generate_effects_in_node(order=order, effects_list=effects_list, i=i, context_nta=nta) 
            if has_effects: # if there's an effect, add to transition
                insert_effect_in_location(source_id=source_id,target_id=target_id, template=template, eff_label=eff_label)

            elif not check_camel_case_regex(order[i]):
                    # debug
                    print("Connecting", source_id, "to",
                      target_id, "in template", template.name.name)
                    trans = uppaalpy.Transition(
                        source=source_id, 
                        target=target_id)
                    template.graph.add_transition(trans)
            # Check for preconditions and effects on current node
            # if it contains an effect, we must add a transition update on the transition made before
            # if it contains a precondition, we must add a transition guard on the transition that 
            # print(effects_list)
            # print(preconditions_list)
    
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
    # template = add_AT_transitions_in_template(template, node_data, nta)
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
                        # Create location for each method and add a Transition to it from the AT Task
                        location_method_name = "exec_" + method
                        location_method_id = "id"+str(800+j)
                        add_location(template=template,
                        id=location_method_id, 
                        name=location_method_name, 
                        pos=(posX, posY))
                        # Create channel message:
                        method_channel_sync_str = create_channel_synch_for_transition(get_channel_name(method_name=method))
                        synch_label = uppaalpy.Label(kind="synchronisation", value=method_channel_sync_str, pos=(posX-100, posY+55))
                        # Adding transition
                        trans = uppaalpy.Transition(source=locations[i].id, target=location_method_id, synchronisation=synch_label)
                        template.graph.add_transition(trans)
                        # now locate the next node and a Transition to it
                        if i+1 in range(len(locations)):
                            target_id = locations[i+1].id
                            # Add channel to go back to this template when the execution of the subtask is
                            method_channel_sync_str = create_channel_synch_for_transition(get_channel_name(method_name=method, finished=True), target=True)
                            synch_label = uppaalpy.Label(kind="synchronisation", value=method_channel_sync_str, pos=(posX+100, posY+55))
                            template.graph.add_transition(uppaalpy.Transition(source=location_method_id, target=target_id, synchronisation=synch_label))
                        j+=1
                        posX += 100
                        posY -= 100
                            
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
                        

                temp = generate_transitions_at_template(template=temp, order=m.order, current_method=m, node_data=node_data, nta=nta)

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

def get_channel_name(method_name: str, finished: bool = False) -> str:
    if finished:
        return f"finish_{method_name}"
    else:
        return f"start_{method_name}"

def create_channel_synch_for_transition(channel_name: str, target: bool = False) -> str:
    if target: #if the channel receives the synch or not
        return f"{channel_name}?"
    else:
        return f"{channel_name}!"

def generate_effect_for_transition_update(effect_name: str, effect_type:str, is_true: bool) -> str:
    if is_true:
        return f"{effect_type}.{effect_name} := true" 
    else:
        return f"{effect_type}.{effect_name} := false"

def generate_precondition_for_transition_guard(prec_name:str, prec_type: str, is_true: bool) -> str:
    if is_true:
        return f"{prec_type}.{prec_name} == true"
    else:
        return f"{prec_type}.{prec_name} == false"

def search_and_generate_effects_in_node(order: list, effects_list: list[Effect], i: int, context_nta:uppaalpy.NTA):
    has_effects = False
    eff_label = None
    for effect in effects_list:
        if effect.tied_to == order[i]:
            # Debug
            # print(f"effect {effect.name} is tied to {order[i]}")
            eff_value = generate_effect_for_transition_update(
                    effect_name=effect.name, 
                    is_true=True if effect.value == "true" else False, 
                    effect_type=effect.type)
            # Let's create the label and send it to the trans object with the transition
            eff_label = uppaalpy.UpdateLabel(
                kind="assignment", 
                value=eff_value,
                pos=(20, 90),
                ctx=context_nta.context)
            has_effects = True
    return has_effects, eff_label

def insert_effect_in_location(source_id: str, target_id:str, template: uppaalpy.Template, eff_label: uppaalpy.UpdateLabel):
    # Debug effect
    print("Connecting", source_id, "to", target_id, "in template", template.name.name, "with effect", eff_label.value)
    trans = uppaalpy.Transition(
        source=source_id, 
        target=target_id, 
        assignment=eff_label)
    template.graph.add_transition(trans)

def search_and_generate_preconditions_in_node(order: list, preconditions_list: list[Precondition], i: int, context_nta:uppaalpy.NTA):
    prec_label = None
    has_precs = False
    if len(preconditions_list) > 0:    
        prec_label = None
        for prec in preconditions_list:
            # Debug
            print(f"prec {prec.name} is tied to {order[i]}")
            prec_value = generate_precondition_for_transition_guard(
                    prec_name=prec.name, 
                    is_true=True if prec.value == "true" else False, 
                    prec_type=prec.type)
            # Let's create the label and send it to the trans object with the transition
            prec_label = uppaalpy.ConstraintLabel(
                kind="guard", 
                value=prec_value,
                pos=(20, 90),
                ctx=context_nta)
            has_precs = True
    return has_precs, prec_label
            
def insert_precondition_in_location(source_id: str, target_id:str, template: uppaalpy.Template, prec_label: uppaalpy.Label):
    # Debug precondition
    print("Connecting", source_id, "to", target_id, "in template", template.name.name, "with precondition", prec_label.value)
    trans = uppaalpy.Transition(
        source=source_id, 
        target=target_id, 
        guard=prec_label)
    template.graph.add_transition(trans)


# def generate_transition(method_data, temp: uppaalpy.Template):
#     for m in method_data:
