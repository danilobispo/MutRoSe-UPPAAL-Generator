# Utilitary functions for UPPAAL template generation
import re
from turtle import update
from typing import List, Tuple
import uppaalpy
import copy

from utils import AbstractTask, Capability, Effect, MethodData, Precondition, Variable

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

def generate_transitions_at_template(template: uppaalpy.Template, order: list, current_method: MethodData, node_data: List[AbstractTask], nta: uppaalpy.NTA, method_name:str) -> uppaalpy.Template:
    preconditions_list: list[Precondition] = current_method.preconditions
    effects_list: list[Effect] = current_method.effects
    capabilities_list: list[Capability] = current_method.capabilities
    # Add the connections between methods
    eff_label = None
    has_effects = False
    prec_label = None
    has_precs = False
    has_capab = False
    capab_label = None
    for i in range(len(order)):
        id_count = i+1
        source_id, target_id = "id"+str(id_count), "id"+str(id_count+1)
        
        if(i == 0): # init method node
            sync_channel_str = create_channel_synch_for_transition(get_channel_name(method_name=method_name, finished=False),target=True)
            synch_label = uppaalpy.Label(kind="synchronisation", value=sync_channel_str, pos=(250, 250))
            # Deal with preconditions here
            has_precs, prec_label, prec_neg_label =  search_and_generate_preconditions_in_node(preconditions_list)
            if has_precs:
                constraint_label = create_precondition_label_for_transition(prec_label=prec_label, context_nta=nta)
                trans = uppaalpy.Transition(source="id0", target="id1", guard=constraint_label, synchronisation=synch_label)
                create_precondition_fail_transition(template, nta, method_name, id_count, prec_neg_label)
            else:
                trans=uppaalpy.Transition(source="id0", target="id1", synchronisation=synch_label)

            template.graph.add_transition(trans)
            


        if i == len(order) - 1: # add last method transition with end node
            if(not check_camel_case_regex(order[i])):
                # Special case where effect is in the very last node
                has_effects, eff_label = search_and_generate_effects_in_node(order=order, effects_list=effects_list, i=i) 
                if has_effects: # if there's an effect, add to transition
                    # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                    update_label = create_effect_label_for_transition(eff_label=eff_label, context_nta=nta)
                    trans = uppaalpy.Transition(source=source_id, target="id999", assignment=update_label)
                else: 
                    # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                    trans = uppaalpy.Transition(source=source_id, target="id999")
                template.graph.add_transition(trans)

        # Default case
        elif id_count < len(order):
            # print(f"i: {i}")
            # print("Current node:", order[i])
            has_capab, capab_label = search_and_generate_capabilities_in_node(order=order, capabilities_list=capabilities_list, i=id_count)
            if has_capab and not check_camel_case_regex(order[id_count]):
                guard_label = create_precondition_label_for_transition(capab_label, nta)
                trans = uppaalpy.Transition(source=source_id, target=target_id, guard=guard_label)
                template.graph.add_transition(trans)
                continue
            has_effects, eff_label = search_and_generate_effects_in_node(order=order, effects_list=effects_list, i=i) 
            if has_effects and not check_camel_case_regex(order[i]): # if there's an effect, add to transition
                update_label = create_effect_label_for_transition(eff_label=eff_label, context_nta=nta)
                trans = uppaalpy.Transition(source=source_id, target=target_id, assignment=update_label)

            # Normal transition without preconditions nor effects
            elif not check_camel_case_regex(order[i]):
                    # debug
                    # print("Connecting", source_id, "to", target_id, "in template", template.name.name)
                    trans = uppaalpy.Transition(source=source_id, target=target_id)
            template.graph.add_transition(trans)
    template = add_AT_transitions_in_template(template, node_data)
    return template

def create_precondition_fail_transition(template, nta, method_name, id_count, prec_neg_label):
    # Generate precondition location transition to where it would fail and another transition back to the initial node:
    # First we create a location
    # number 700+ ids are restricted to locations like these
    failed_location_id = "id70"+str(id_count)
    add_location(template=template, id=failed_location_id, name="failed_precondition", pos=(80, 169))
                # Then a negation condition for the precondition, along with the transition
    constraint_neg_label = create_precondition_label_for_transition(prec_label=prec_neg_label, context_nta=nta)
                # Adding a nail so it is easily identifiable in the graph
    additional_trans_list = []
    additional_trans_nail = uppaalpy.Nail(x=-552, y=8)
    additional_trans_list.append(additional_trans_nail)
                # Add a transition channel since we do not want it to execute when it is not the correct time yet
    additional_trans_channel_name = create_channel_synch_for_transition(get_channel_name(method_name=method_name, finished=False),target=True)
    additional_trans_channel_label = uppaalpy.Label(kind="synchronisation", value=additional_trans_channel_name, pos=(300, 250))
                # Create the first transition, that begins from the first node to the last             
    additional_trans = uppaalpy.Transition(source="id0", target=failed_location_id, guard=constraint_neg_label, nails=additional_trans_list, 
                synchronisation=additional_trans_channel_label)
                # #finally, we create a synch channel, showing that 
    end_synch = create_channel_synch_for_transition(get_channel_name(method_name=method_name, finished=True),target=False)
    end_synch_label = uppaalpy.Label(kind="synchronisation", value=end_synch, pos=(300, 250))
                # Also we're adding a boolean variable that is triggered by mission failure
    method_fail_update_str = f"{method_name}_failed = true"
    update_label_for_failed_trans = uppaalpy.UpdateLabel(kind="assignment", value=method_fail_update_str, pos=(320, 250), ctx=template.context)
    trans_to_init_node = uppaalpy.Transition(source=failed_location_id, target="id0", synchronisation=end_synch_label, assignment=update_label_for_failed_trans)
    template.graph.add_transition(additional_trans)
    template.graph.add_transition(trans_to_init_node)

def add_AT_transitions_in_template(template: uppaalpy.Template, node_data: List[AbstractTask]):
    locations = template.graph.get_nodes()
    for i in range(len(locations)):
        if(check_camel_case_regex(locations[i].name.name)):
            for node in node_data:
                j = 0
                if(locations[i].name.name == node.name):
                    posX, posY = locations[i].pos
                    posY -= 100
                    for method in node.methods:
                        # Create location for each method and add a Transition to it from the AT Task
                        location_method_name = "exec_" + method
                        location_method_id = "id"+str(800+j)
                        add_location(template=template, id=location_method_id, name=location_method_name, pos=(posX, posY))
                        # Create channel message:
                            # Since the template can only be one, we'll call the first instance, if there's more than one, that will not be executed
                            # because we do not know which instance of the task must be executed, but we know there's at least one of it
                        method_name = method+str("_0")
                        method_channel_sync_str = create_channel_synch_for_transition(get_channel_name(method_name=method_name))
                        synch_label = uppaalpy.Label(kind="synchronisation", value=method_channel_sync_str, pos=(posX-100, posY+55))
                        # Adding transition
                        trans = uppaalpy.Transition(source=locations[i].id, target=location_method_id, synchronisation=synch_label)
                        template.graph.add_transition(trans)
                        # now locate the next node and a Transition to it
                        if i+1 in range(len(locations)):
                            target_id = locations[i+1].id
                            # Add channel to go back to this template when the execution of the subtask is
                            method_channel_sync_str = create_channel_synch_for_transition(get_channel_name(method_name=method_name, finished=True), target=True)
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


def generate_declaration_for_nta(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: List[Variable], set_of_types: set[str]):
    var_and_types_with_predicates: list[Variable] = []
    nta, var_and_types_with_predicates = generate_structs_for_types(nta, predicates, var_and_types_list, set_of_types)
    return nta, var_and_types_with_predicates

def generate_structs_for_types(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: List[Variable], set_of_types: set[str]):
    # For each of the types in the set we gotta create a struct, so the types can have specific predicates
    var_and_types_with_predicates:list[Variable] = []
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
                for predicate_name in predicates.keys():
                    predicate_type = predicates.get(predicate_name)
                    if(predicate_type == tvar.var_name):
                        # print(f"{predicate_name} found for {tvar.var_name} with type {predicate_type}")
                        nta.declaration.text += "bool " + predicate_name + ";"
                        nta.declaration.text += "\n"
                        flag = 1
                        tvar.predicates_name_list.append(predicate_name)
                        var_and_types_with_predicates.append(tvar)
        # Delete the struct declaration, since no predicate was found for that struct
        if flag != 1:
            startIndex = nta.declaration.text.rindex(struct_start)
            nta.declaration.text = nta.declaration.text[0: startIndex]
        else:
            struct_end = "} "+tp.title()+";\n"
            nta.declaration.text += struct_end
        flag = 0
        
    # add remaining variables with same type (e.g robot r1, r2, r3, etc or patient p1, p2, etc)
    for tvar in var_and_types_list:
        for tv in var_and_types_with_predicates:
            if tvar.type_name == tv.type_name and tvar not in var_and_types_with_predicates:
                var_and_types_with_predicates.append(tvar)

    return nta, var_and_types_with_predicates

def generate_uppaal_methods_templates(method_data: List[MethodData], nta: uppaalpy.NTA, node_data: List[AbstractTask], var_and_types_list_in_predicates: list[Variable]) -> uppaalpy.NTA:
    for m in method_data:
        m = trim_method_predicates(method=m, var_and_types_list_in_predicates=var_and_types_list_in_predicates)
    for m in method_data:
        template_name = create_template(method=m, nta=nta)
        add_declaration_for_channels_in_nta(channel_name=m.method_name, nta=nta)
        add_failed_channels_booleans_in_nta(method_name=m.method_name, nta=nta)
        for temp in nta.templates:
            posX = -552
            posY = -150
            if(temp.name.name == template_name):
                id_count = 1
                m.order = rename_tasks_with_same_name(m.order)
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
                        # Channel for end method
                        sync_channel_str = create_channel_synch_for_transition(get_channel_name(method_name=m.method_name, finished=True),target=False)
                        synch_label = uppaalpy.Label(kind="synchronisation", value=sync_channel_str, pos=(190, 250))
                        # Create connection of endtask to beginning
                        temp.graph.add_transition(uppaalpy.Transition(source="id999", target="id0", synchronisation=synch_label))
                temp = generate_transitions_at_template(template=temp, order=m.order, current_method=m, node_data=node_data, nta=nta, method_name=m.method_name)
                # TODO: Generate parameters for each of the templates
                add_precondition_and_effects_parameter_types_in_template(
                    effect_list=m.effects, precondition_list=m.preconditions, var_and_types_list=var_and_types_list_in_predicates, temp=temp)
    nta.templates.remove(nta.templates[0]) # Remove _method template, since it was just a placeholder           
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
        return f"{effect_type}.{effect_name} = true" 
    else:
        return f"{effect_type}.{effect_name} = false"

def generate_precondition_for_transition_guard(prec_name:str, prec_type: str, is_true: bool) -> str:
    if is_true:
        return f"{prec_type}.{prec_name} == true"
    else:
        return f"{prec_type}.{prec_name} == false"

def generate_capability_for_transition_guard(prec_name:str) -> str:
    return f"{prec_name} == true"

def search_and_generate_effects_in_node(order: list, effects_list: list[Effect], i: int):
    has_effects = False
    eff_label: list[str] = []
    for effect in effects_list:
        if effect.tied_to == order[i]:
            # Debug
            # print(f"effect {effect.name} is tied to {order[i]}")
            eff_label.append(generate_effect_for_transition_update(
                    effect_name=effect.name, 
                    is_true=True if effect.value == "true" else False, 
                    effect_type=effect.type))
            # Let's create the label and send it to the trans object with the transition
            has_effects = True
    return has_effects, eff_label

def create_effect_label_for_transition(eff_label: list[str], context_nta:uppaalpy.NTA):
    update_value = ""
    update_label = None
    for i in range(len(eff_label)):
        if i != len(eff_label)-1:
            update_value += eff_label[i] + ", " 
        else:
            update_value += eff_label[i]
    # print(f"update_value: {update_value}")
    update_label = uppaalpy.UpdateLabel(
                kind="assignment", 
                value=update_value,
                pos=(20, 90),
                ctx=context_nta.context)
    return update_label

def search_and_generate_preconditions_in_node(preconditions_list: list[Precondition]):
    prec_label: list[str] = []
    prec_neg_label: list[str] = []
    has_precs = False
    if len(preconditions_list) > 0: 
        for prec in preconditions_list:
            prec_label.append(generate_precondition_for_transition_guard(
                    prec_name=prec.name, 
                    is_true=True if prec.value == "true" else False, 
                    prec_type=prec.type))
            prec_neg_label.append(generate_precondition_for_transition_guard(
                prec_name=prec.name,
                is_true=False if prec.value == "true" else True,
                prec_type=prec.type
            ))
            # Let's create the label and send it to the trans object with the transition
            has_precs = True
    return has_precs, prec_label, prec_neg_label
            
def create_precondition_label_for_transition(prec_label: list[str], context_nta:uppaalpy.NTA):
    guard_value = ""
    constraint_label = None
    # Debug precondition
    # print("Connecting", source_id, "to", target_id, "in template", template.name.name, "with precondition", prec_label.value)
    for i in range(len(prec_label)):
        if i != len(prec_label)-1:
            guard_value += prec_label[i] + " && " 
        else:
            guard_value += prec_label[i]
            
    # print(f"guard_value: {guard_value}")
    constraint_label = uppaalpy.ConstraintLabel(kind="guard", value=guard_value, pos=(20, 90), ctx=context_nta.context)
    return constraint_label

def search_and_generate_capabilities_in_node(order, capabilities_list: list[Capability], i: int):
    capab_label: list[str] = []
    has_capab = False
    for capab in capabilities_list:
        if capab.tied_to == order[i]:
            capab_label.append(generate_capability_for_transition_guard(prec_name=capab.name))
            # Let's create the label and send it to the trans object with the transition
            has_capab = True
    return has_capab, capab_label

def insert_parameter_in_template(template: uppaalpy.Template, parameter_name: str, parameter_type: str):
    
    added = False
    if template.parameter == None:
        # print("if template.parameter == None:")
        # print(f"Added {parameter_type.title()} {parameter_name}")
        template.parameter = uppaalpy.Parameter(text=f"{parameter_type.title()} &{parameter_name} ") 
        added = True
    else:
        search_str = f"{parameter_type.title()} &{parameter_name}"
        search_str = r"\b" + search_str + r"\b"
        # print(f"search_str: {search_str}")
        if(re.search(search_str, template.parameter.text) is None):
            # print("else:")
            # print(f"Added {parameter_type.title()} {parameter_name}")
            template.parameter.text += f"{parameter_type.title()} &{parameter_name} "
            added = True
        else:
            # print(f"not adding {parameter_type.title()} {parameter_name} due to repetition")
            added = False
    return added

def add_precondition_and_effects_parameter_types_in_template(precondition_list, effect_list, var_and_types_list, temp: uppaalpy.Template):
    # if(temp.name.name == "temp_fetch_meal_with_robot_0"):
    # print(f"in template {temp.name.name}")
    # print(precondition_list)
    # print(effect_list)
    # if temp.name.name == "template temp_pick_dishes_two_robots_at_location_0":
    #     print(precondition_list,"\n",effect_list)

    if len(precondition_list) > 0:
        for i in range(len(precondition_list)):
            for j in range(len(var_and_types_list)):
                if var_and_types_list[j].var_name == precondition_list[i].type:
                    is_param_added = insert_parameter_in_template(
                        template=temp, 
                        parameter_name=var_and_types_list[j].
                        var_name, parameter_type=var_and_types_list[j].type_name)
                    if i != len(precondition_list) - 1 and is_param_added:
                        temp.parameter.text += ", "
    if len(effect_list) > 0:
        if(len(precondition_list) == 1):
            temp.parameter.text += ", "  
        for i in range(len(effect_list)):
            for j in range(len(var_and_types_list)):
                if var_and_types_list[j].var_name == effect_list[i].type:
                    # print(f"var_name: {var_and_types_list[i].var_name} is equal to type {eff.type}")
                    is_param_added = insert_parameter_in_template(
                        template=temp, 
                        parameter_name=var_and_types_list[j].var_name, parameter_type=var_and_types_list[j].type_name)
                    if i != len(effect_list) - 1 and is_param_added:
                        temp.parameter.text += ", "

    if temp.parameter is not None:
        if temp.parameter.text[-2:] == ", ":
            temp.parameter.text = temp.parameter.text[:-2]
            # print(f"temp.parameter.text: {temp.parameter.text}")
            # print("\n")

def trim_method_predicates(method: MethodData, var_and_types_list_in_predicates:list[Variable]) -> list[MethodData]:
    effs: list[Effect] = method.effects
    precs: list[Precondition] = method.preconditions

    # Loop for effects
    len_effs = range(len(effs))
    i = 0
    while i in len_effs:
        j = 0
        while j < len(var_and_types_list_in_predicates):
            if(var_and_types_list_in_predicates[j].var_name == effs[i].type):
                # print(f"Found {effs[i].type}")
                break                
            #Last index and still not found? then it is not in the list
            elif var_and_types_list_in_predicates[j].var_name != effs[i].type and j == len(var_and_types_list_in_predicates)-1:
                # print(f"Removing {effs[i].type}")
                effs.pop(i)
            j += 1
        i += 1
        len_effs = range(len(effs))

    # Loop for preconditions
    i = 0
    len_precs = range(len(precs))
    while i in len_precs:
        j = 0
        while j < len(var_and_types_list_in_predicates):
            if(var_and_types_list_in_predicates[j].var_name == precs[i].type):
                # print(f"Found {precs[i].type}")
                break                
            #Last index and still not found? then it is not in the list
            elif var_and_types_list_in_predicates[j].var_name != precs[i].type and j == len(var_and_types_list_in_predicates)-1: 
                # print(f"Removing {precs[i].type}")
                precs.pop(i)
            j += 1
        i += 1
        len_precs = range(len(precs))

    return method


def create_template(method: MethodData, nta: uppaalpy.NTA) -> str:
    template_name = "temp_" + method.method_name
    add_template(nta=nta, template_name=template_name, template_to_copy=nta.templates[0], parameters=None, declaration=None)
    return template_name

def generate_default_verifiable_queries(nta: uppaalpy.NTA) -> uppaalpy.NTA:
    query = uppaalpy.Query("A[] not deadlock", comment="Basic formula query to verify absence of deadlocks")
    nta.queries.append(query)
    return nta

def rename_tasks_with_same_name(nodes_names: list[str]):
    names_list: list[str] = []
    names_list = nodes_names[:]
    for i, name in enumerate(names_list):
        if names_list.count(name) > 1:
            j=0
            while j in range(names_list.count(name)):
                name = name + "_" + str(j)
                names_list[i] = name
                j+=1
    # In theory, lists should be about the same size, so...
    for i in range(len(nodes_names)):
        nodes_names[i]= names_list[i]

    return nodes_names

def generate_system_declarations(nta: uppaalpy.NTA, method_data: list[MethodData]):
    # Later on, when i parsed GM annotations, I will only instantiate the methods that are actually used,
    # but first, we cannot know for sure which ones are going to be used, so we call them all
    # Empty default system declaration text
    nta.system.text = ""
    for temp in nta.templates:
        for m in method_data:
            if temp.name.name.find(m.method_name) > 0:
                predicates: set[Precondition] = m.effects + m.preconditions
                nta.system.text+=f"var_{temp.name.name} = {temp.name.name}("
                added_types = []
                if temp.parameter is not None:
                    comma_positions = temp.parameter.text.split(",")

                    for j, com in enumerate(comma_positions):
                        for i, prec in enumerate(predicates):
                            # print(temp.name.name)
                            # print(com.split(" ")[0])
                            com = com.strip(' ') # Trim whitespaces
                            type = com.split(" ")[1].replace("&","")
                            # print(prec.type)
                            # print(str(type))
                            # print(prec.type == str(type))
                            if prec.type == str(type) and prec.type not in added_types:
                                nta.system.text += f"{prec.type}"
                                added_types.append(prec.type)
                                if j != len(comma_positions)-1:
                                    nta.system.text += ","
                    # Remove an unnecessary comma at the end of the string                            
                    if(nta.system.text[-1:] == ","):
                        nta.system.text = nta.system.text[:-1]
                    nta.system.text+=");\n"
                else:
                    nta.system.text+=");\n"
    nta.system.text += "system "
    for i, temp in enumerate(nta.templates):
        nta.system.text += f"var_{temp.name.name}"
        if i != len(nta.templates)-1:
            nta.system.text += ","
    nta.system.text += ";"
    return nta

def generate_declarations_of_struct_variables_in_nta(nta: uppaalpy.NTA, variables_set: set[Variable]) -> uppaalpy.NTA:
    nta.declaration.text += "\n"
    for var in variables_set:
        nta.declaration.text += f"{var.type_name.title()} {var.var_name}"
        nta.declaration.text += " = {"
        for i in range(len(var.predicates_name_list)):
            if i == len(var.predicates_name_list) - 1: #Last element
                nta.declaration.text += "false};"
            else:
                nta.declaration.text += "false,"

        nta.declaration.text += "\n"
    
    return nta

        
def link_variables_with_predicates_and_types(var_and_types_list_with_predicates: List[Variable]):
    # Adds remaining predicates to variables still without them
    aux_var_and_types_list_with_predicates = copy.deepcopy(var_and_types_list_with_predicates)
    
    for tvar in var_and_types_list_with_predicates:
        for aux in aux_var_and_types_list_with_predicates:
            if aux.type_name == tvar.type_name:
                for in_list in aux.predicates_name_list:
                    if in_list not in tvar.predicates_name_list:
                        tvar.predicates_name_list.append(in_list)

    return var_and_types_list_with_predicates
    
def generate_boolean_declarations_for_capabilities(method_data: list[MethodData], nta: uppaalpy.NTA):
    cap_list = []
    for m in method_data:
        if len(m.capabilities) > 0:
            for cap in m.capabilities:
                cap_list.append(cap)
    # After obtaining all capabilities, let's create a set to store all the different ones
    cap_set: set[Capability] = set(cap_list)
    # and write then on a file as boolean variables
    nta.declaration.text += "\n"
    for cap in cap_set:
        value = "true" if str(cap.value) == "True" else "false"
        nta.declaration.text += f"bool {cap.name} = {value};\n"

    return nta

def add_failed_channels_booleans_in_nta(method_name: str, nta: uppaalpy.NTA):
    nta.declaration.text += f"bool {method_name}_failed = false;\n"