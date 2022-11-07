# Utilitary functions for UPPAAL template generation
import re
import uppaalpy
import copy

from utils import AbstractTask, Capability, Effect, GoalTreeNode, MethodData, Precondition, Variable

const_end_method_name = "end_method"
const_sequential = ";"
const_fallback = "FALLBACK"
const_parallel = "#"
const_or_sequential = "OR"
const_operators = [const_sequential, const_parallel,
                   const_or_sequential, const_fallback]


def check_camel_case_regex(string: str):
    return re.match("(?:[A-Z])(?:\S?)+(?:[A-Z])(?:[a-z])+", string)


def print_nodes_from_template(template: uppaalpy.Template):
    nodes = template.graph.get_nodes()
    for i in range(len(nodes)):
        print(nodes[i].name.name)


def print_nta_declaration(nta: uppaalpy.NTA):
    print(nta.declaration.text)


def get_nodes_from_template(template: uppaalpy.Template) -> list[uppaalpy.Node]:
    return template.graph.get_nodes()


def retrieve_node_copy(template: uppaalpy.Template) -> uppaalpy.Location:
    nodes = template.graph.get_nodes()
    node_copy = copy.deepcopy(nodes[0])
    return node_copy


def add_location(template: uppaalpy.Template, id: str, pos: tuple[int, int], name: str):
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


def generate_transitions_at_template(template: uppaalpy.Template, order: list, current_method: MethodData, node_data: list[AbstractTask], nta: uppaalpy.NTA, method_name: str) -> uppaalpy.Template:
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

        if (i == 0):  # init method node
            sync_channel_str = create_channel_synch_for_transition(
                get_channel_name(method_name=method_name, finished=False), target=True)
            synch_label = uppaalpy.Label(
                kind="synchronisation", value=sync_channel_str, pos=(-705, -144))
            # Deal with preconditions here
            has_precs, prec_label, prec_neg_label = search_and_generate_preconditions_in_node(
                preconditions_list)
            if has_precs:
                constraint_label = create_precondition_label_for_transition(
                    prec_label=prec_label, context_nta=nta, pos=(-705, -158))
                trans = uppaalpy.Transition(
                    source="id0", target="id1", guard=constraint_label, synchronisation=synch_label)
                create_precondition_fail_transition(
                    template, nta, method_name, id_count, prec_neg_label)
            else:
                trans = uppaalpy.Transition(
                    source="id0", target="id1", synchronisation=synch_label)

            template.graph.add_transition(trans)

        if i == len(order) - 1:  # add last method transition with end node
            if (not check_camel_case_regex(order[i])):
                # Special case where effect is in the very last node
                has_effects, eff_label = search_and_generate_effects_in_node(
                    order=order, effects_list=effects_list, i=i)
                if has_effects:  # if there's an effect, add to transition
                    # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                    # Get location so we can use its position to place the label next to it
                    for node in template.graph.get_nodes():
                        if (node.name.name == order[i]):
                            nodePosX, nodePosY = node.pos
                    update_label = create_effect_label_for_transition(
                        eff_label=eff_label, context_nta=nta, pos=(nodePosX+30, nodePosY-20))
                    trans = uppaalpy.Transition(
                        source=source_id, target="id999", assignment=update_label)
                else:
                    # print("Connecting", source_id, "to", "id999", "in template", template.name.name)
                    trans = uppaalpy.Transition(
                        source=source_id, target="id999")
                template.graph.add_transition(trans)

        # Default case
        elif id_count < len(order):
            # print(f"i: {i}")
            # print("Current node:", order[i])
            has_capab, capab_label, capab_neg_label = search_and_generate_capabilities_in_node(
                order=order, capabilities_list=capabilities_list, i=id_count)
            if has_capab and not check_camel_case_regex(order[id_count]):
                # Get location so we can use its position to place the label next to it
                for node in template.graph.get_nodes():
                    if (node.name.name == order[i]):
                        nodePosX, nodePosY = node.pos
                guard_label = create_precondition_label_for_transition(
                    capab_label, nta, pos=(nodePosX+30, nodePosY-20))
                trans = uppaalpy.Transition(
                    source=source_id, target=target_id, guard=guard_label)
                template.graph.add_transition(trans)
                create_capability_fail_transition(
                    template, nta, method_name, id_count, capab_neg_label, pos=(nodePosX, nodePosY-120))
                continue
            has_effects, eff_label = search_and_generate_effects_in_node(
                order=order, effects_list=effects_list, i=i)
            for node in template.graph.get_nodes():
                if (node.name.name == order[i]):
                    nodePosX, nodePosY = node.pos
            # if there's an effect, add to transition
            if has_effects and not check_camel_case_regex(order[i]):
                update_label = create_effect_label_for_transition(
                    eff_label=eff_label, context_nta=nta, pos=(nodePosX+30, nodePosY-20))
                trans = uppaalpy.Transition(
                    source=source_id, target=target_id, assignment=update_label)

            # Normal transition without preconditions nor effects
            elif not check_camel_case_regex(order[i]):
                # debug
                # print("Connecting", source_id, "to", target_id, "in template", template.name.name)
                trans = uppaalpy.Transition(
                    source=source_id, target=target_id)
            template.graph.add_transition(trans)
    template = add_AT_transitions_in_template(template, node_data)
    return template


def create_precondition_fail_transition(template, nta, method_name, id_count, prec_neg_label):
    # Generate precondition location transition to where it would fail and another transition back to the initial node:
    # First we create a location
    # number 700+ ids are restricted to locations like these
    failed_location_id = "id70"+str(id_count)
    add_location(template=template, id=failed_location_id,
                 name="failed_precondition", pos=(-59, 17))
    # Then a negation condition for the precondition, along with the transition
    constraint_neg_label = create_precondition_label_for_transition(
        prec_label=prec_neg_label, context_nta=nta, pos=(-552, 17))
    # Adding a nail so it is easily identifiable in the graph
    additional_trans_list = []
    additional_trans_nail = uppaalpy.Nail(x=-552, y=8)
    additional_trans_list.append(additional_trans_nail)
    # Add a transition channel since we do not want it to execute when it is not the correct time yet
    additional_trans_channel_name = create_channel_synch_for_transition(
        get_channel_name(method_name=method_name, finished=False), target=True)
    additional_trans_channel_label = uppaalpy.Label(
        kind="synchronisation", value=additional_trans_channel_name, pos=(-561, 34))
    # Create the first transition, that begins from the first node to the last
    additional_trans = uppaalpy.Transition(source="id0", target=failed_location_id, guard=constraint_neg_label, nails=additional_trans_list,
                                           synchronisation=additional_trans_channel_label)

    end_synch = create_channel_synch_for_transition(
        get_channel_name(method_name=method_name, finished=True), target=False)
    end_synch_label = uppaalpy.Label(
        kind="synchronisation", value=end_synch, pos=(-306, -67))
    # Also we're adding a boolean variable that is triggered by mission failure
    method_fail_update_str = f"{method_name}_failed = true"
    update_label_for_failed_trans = uppaalpy.UpdateLabel(
        kind="assignment", value=method_fail_update_str, pos=(-306, -52), ctx=template.context)
    trans_to_init_node = uppaalpy.Transition(
        source=failed_location_id, target="id0", synchronisation=end_synch_label, assignment=update_label_for_failed_trans)
    template.graph.add_transition(additional_trans)
    template.graph.add_transition(trans_to_init_node)


def create_capability_fail_transition(template, nta, method_name, id_count, capab_neg_label, pos=None):
    failed_location_id = "id70"+str(id_count)
    if pos != None:
        add_location(template=template, id=failed_location_id,
                     name="failed_capability", pos=pos)
    else:
        add_location(template=template, id=failed_location_id,
                     name="failed_capability", pos=(-246, -331))
    # Then a negation condition for the precondition, along with the transition
    constraint_neg_label = create_precondition_label_for_transition(
        prec_label=capab_neg_label, context_nta=nta, pos=(-442, -280))

    # Create the first transition, that begins from the first node to the last
    additional_trans = uppaalpy.Transition(
        source='id'+str(id_count), target=failed_location_id, guard=constraint_neg_label)
    # #finally, we create a synch channel, showing that
    end_synch = create_channel_synch_for_transition(
        get_channel_name(method_name=method_name, finished=True), target=False)
    end_synch_label = uppaalpy.Label(
        kind="synchronisation", value=end_synch, pos=(-612, -382))
    # Also we're adding a boolean variable that is triggered by mission failure
    method_fail_update_str = f"{method_name}_failed = true"
    update_label_for_failed_trans = uppaalpy.UpdateLabel(
        kind="assignment", value=method_fail_update_str, pos=(-629, -365), ctx=template.context)
    # Adding a nail so it is easily identifiable in the graph
    additional_trans_list = [uppaalpy.Nail(
        x=-824, y=-340), uppaalpy.Nail(-824, -93)]
    trans_to_init_node = uppaalpy.Transition(source=failed_location_id, target="id0", synchronisation=end_synch_label,
                                             assignment=update_label_for_failed_trans, nails=additional_trans_list)
    template.graph.add_transition(additional_trans)
    template.graph.add_transition(trans_to_init_node)


def add_AT_transitions_in_template(template: uppaalpy.Template, node_data: list[AbstractTask]):
    locations = template.graph.get_nodes()
    for i in range(len(locations)):
        if (check_camel_case_regex(locations[i].name.name)):
            for node in node_data:
                j = 0
                if (locations[i].name.name == node.name):
                    posX, posY = locations[i].pos
                    posY -= 100
                    for method in node.methods:
                        # Create location for each method and add a Transition to it from the AT Task
                        location_method_name = "exec_" + method
                        location_method_id = "id"+str(800+j)
                        add_location(template=template, id=location_method_id,
                                     name=location_method_name, pos=(posX, posY))
                        # Create channel message:
                    # Since the template can only be one, we'll call the first instance, if there's more than one, that will not be executed
                    # because we do not know which instance of the task must be executed, but we know there's at least one of it
                        method_name = method+str("_0")
                        method_channel_sync_str = create_channel_synch_for_transition(
                            get_channel_name(method_name=method_name))
                        synch_label = uppaalpy.Label(
                            kind="synchronisation", value=method_channel_sync_str, pos=(posX-100, posY+55))
                        # Adding transition
                        trans = uppaalpy.Transition(
                            source=locations[i].id, target=location_method_id, synchronisation=synch_label)
                        template.graph.add_transition(trans)
                        # now locate the next node and a Transition to it
                        if i+1 in range(len(locations)):
                            target_id = locations[i+1].id
                            # Add channel to go back to this template when the execution of the subtask is
                            method_channel_sync_str = create_channel_synch_for_transition(
                                get_channel_name(method_name=method_name, finished=True), target=True)
                            synch_label = uppaalpy.Label(
                                kind="synchronisation", value=method_channel_sync_str, pos=(posX+100, posY+55))

                            template.graph.add_transition(uppaalpy.Transition(
                                source=location_method_id, target=target_id, synchronisation=synch_label))
                        j += 1
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

    if (not flag_repeated_template):
        tp_copy = copy.deepcopy(template_to_copy)
        tp_copy.name.name = template_name
        tp_copy.parameter = parameters
        tp_copy.declaration = declaration

        nta.templates.append(tp_copy)


def generate_declaration_for_nta(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: list[Variable], set_of_types: set[str]):
    var_and_types_with_predicates: list[Variable] = []
    nta, var_and_types_with_predicates = generate_structs_for_types(
        nta, predicates, var_and_types_list, set_of_types)
    return nta, var_and_types_with_predicates


def generate_structs_for_types(nta: uppaalpy.NTA, predicates: dict[str], var_and_types_list: list[Variable], set_of_types: set[str]):
    # For each of the types in the set we gotta create a struct, so the types can have specific predicates
    var_and_types_with_predicates: list[Variable] = []
    nta.declaration.text += "\n"
    flag = 0
    for tp in set_of_types:
        struct_start = "typedef struct {\n"
        nta.declaration.text += struct_start
        # print("partial text: ")
        # print(nta.declaration.text)
        for tvar in var_and_types_list:
            # print(predicates.values)
            if (tvar.type_name == tp):
                for predicate_name in predicates.keys():
                    predicate_type = predicates.get(predicate_name)
                    if (predicate_type == tvar.var_name):
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


def generate_uppaal_methods_templates(method_data: list[MethodData], nta: uppaalpy.NTA, node_data: list[AbstractTask], var_and_types_list_in_predicates: list[Variable]) -> uppaalpy.NTA:
    for m in method_data:
        m = trim_method_predicates(
            method=m, var_and_types_list_in_predicates=var_and_types_list_in_predicates)
    for m in method_data:
        template_name = create_template(method=m, nta=nta)
        add_declaration_for_channels_in_nta(
            channel_name=m.method_name, nta=nta)
        add_failed_channels_booleans_in_nta(method_name=m.method_name, nta=nta)
        for temp in nta.templates:
            posX = -552
            posY = -220
            if (temp.name.name == template_name):
                id_count = 1
                m.order = rename_tasks_with_same_name(m.order)
                for i in range(len(m.order)):
                    id_str = "id"+str(id_count)
                    add_location(template=temp, id=id_str,
                                 pos=(posX, posY), name=m.order[i])
                    id_count = id_count + 1
                    posX = posX + 225
                    # posY = posY + 100
                    if i == len(m.order)-1:
                        # Add end location, end of method that goes back to initial node
                        temp.graph.add_location(uppaalpy.Location(id="id999",
                                                                  pos=(
                                                                      posX + 150, posY),
                                                                  name=uppaalpy.Name(
                                                                      name=const_end_method_name,
                                                                      pos=(posX+134, posY-31))))
                        # Channel for end method
                        sync_channel_str = create_channel_synch_for_transition(
                            get_channel_name(method_name=m.method_name, finished=True), target=False)
                        synch_label = uppaalpy.Label(
                            kind="synchronisation", value=sync_channel_str, pos=(posX-100, -115))
                        # Create connection of endtask to beginning
                        # Add an additional nail here so the transition looks better on the template
                        nail = uppaalpy.Nail(posX+150, -93)
                        nail_list: list[uppaalpy.Nail] = []
                        nail_list.append(nail)
                        temp.graph.add_transition(uppaalpy.Transition(
                            source="id999", target="id0", synchronisation=synch_label, nails=nail_list))
                temp = generate_transitions_at_template(
                    template=temp, order=m.order, current_method=m, node_data=node_data, nta=nta, method_name=m.method_name)
                # TODO: Generate parameters for each of the templates
                add_precondition_and_effects_parameter_types_in_template(
                    effect_list=m.effects, precondition_list=m.preconditions, var_and_types_list=var_and_types_list_in_predicates, temp=temp)
    # Remove _method template, since it was just a placeholder
    nta.templates.remove(nta.templates[0])
    return nta


def add_declaration_for_channels_in_nta(channel_name: str, nta: uppaalpy.NTA) -> uppaalpy.NTA:
    # Always do a line skip before beginning to write in a file that already contains written lines
    if (check_for_duplicate_channel(channel_name=channel_name, nta=nta)):
        nta.declaration.text += "\n"
        nta.declaration.text += f"broadcast chan start_{channel_name};\n"
        nta.declaration.text += f"broadcast chan finish_{channel_name};\n"
    return nta


def check_for_duplicate_channel(channel_name: str, nta: uppaalpy.NTA) -> bool:
    if (nta.declaration.text.find(f"broadcast chan start_{channel_name};") != -1 or
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
    if target:  # if the channel receives the synch or not
        return f"{channel_name}?"
    else:
        return f"{channel_name}!"


def generate_effect_for_transition_update(effect_name: str, effect_type: str, is_true: bool) -> str:
    if is_true:
        return f"{effect_type}.{effect_name} = true"
    else:
        return f"{effect_type}.{effect_name} = false"


def generate_precondition_for_transition_guard(prec_name: str, prec_type: str, is_true: bool) -> str:
    if is_true:
        return f"{prec_type}.{prec_name} == true"
    else:
        return f"{prec_type}.{prec_name} == false"


def generate_capability_for_transition_guard(capab_name: str, is_true: bool) -> str:
    if is_true:
        return f"{capab_name} == true"
    else:
        return f"{capab_name} == false"


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


def create_effect_label_for_transition(eff_label: list[str], context_nta: uppaalpy.NTA, pos=None):
    update_value = ""
    update_label = None
    for i in range(len(eff_label)):
        if i != len(eff_label)-1:
            update_value += eff_label[i] + ", "
        else:
            update_value += eff_label[i]
    # print(f"update_value: {update_value}")

    if (pos == None):
        update_label = uppaalpy.UpdateLabel(
            kind="assignment", value=update_value, pos=(20, 90), ctx=context_nta.context)
    else:
        update_label = uppaalpy.UpdateLabel(
            kind="assignment", value=update_value, pos=pos, ctx=context_nta.context)
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


def create_precondition_label_for_transition(prec_label: list[str], context_nta: uppaalpy.NTA, pos=None):
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
    if pos != None:
        constraint_label = uppaalpy.ConstraintLabel(
            kind="guard", value=guard_value, pos=pos, ctx=context_nta.context)
    else:
        constraint_label = uppaalpy.ConstraintLabel(
            kind="guard", value=guard_value, pos=(20, 90), ctx=context_nta.context)
    return constraint_label


def search_and_generate_capabilities_in_node(order, capabilities_list: list[Capability], i: int):
    capab_label: list[str] = []
    capab_neg_label: list[str] = []
    has_capab = False
    for capab in capabilities_list:
        if capab.tied_to == order[i]:
            capab_label.append(generate_capability_for_transition_guard(
                capab_name=capab.name, is_true=True))
            capab_neg_label.append(generate_capability_for_transition_guard(
                capab_name=capab.name, is_true=False))
            # Let's create the label and send it to the trans object with the transition
            has_capab = True
    return has_capab, capab_label, capab_neg_label


def insert_parameter_in_template(template: uppaalpy.Template, parameter_name: str, parameter_type: str):

    added = False
    if template.parameter == None:
        # print("if template.parameter == None:")
        # print(f"Added {parameter_type.title()} {parameter_name}")
        template.parameter = uppaalpy.Parameter(
            text=f"{parameter_type.title()} &{parameter_name} ")
        added = True
    else:
        search_str = f"{parameter_type.title()} &{parameter_name}"
        search_str = r"\b" + search_str + r"\b"
        # print(f"search_str: {search_str}")
        if (re.search(search_str, template.parameter.text) is None):
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
        if (len(precondition_list) == 1):
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


def trim_method_predicates(method: MethodData, var_and_types_list_in_predicates: list[Variable]) -> list[MethodData]:
    effs: list[Effect] = method.effects
    precs: list[Precondition] = method.preconditions

    # Loop for effects
    len_effs = range(len(effs))
    i = 0
    while i in len_effs:
        j = 0
        while j < len(var_and_types_list_in_predicates):
            if (var_and_types_list_in_predicates[j].var_name == effs[i].type):
                # print(f"Found {effs[i].type}")
                break
            # Last index and still not found? then it is not in the list
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
            if (var_and_types_list_in_predicates[j].var_name == precs[i].type):
                # print(f"Found {precs[i].type}")
                break
            # Last index and still not found? then it is not in the list
            elif var_and_types_list_in_predicates[j].var_name != precs[i].type and j == len(var_and_types_list_in_predicates)-1:
                # print(f"Removing {precs[i].type}")
                precs.pop(i)
            j += 1
        i += 1
        len_precs = range(len(precs))

    return method


def create_template(method: MethodData, nta: uppaalpy.NTA) -> str:
    template_name = "temp_" + method.method_name
    add_template(nta=nta, template_name=template_name,
                 template_to_copy=nta.templates[0], parameters=None, declaration=None)
    return template_name


def generate_default_verifiable_queries(nta: uppaalpy.NTA) -> uppaalpy.NTA:
    query = uppaalpy.Query(
        "A[] not deadlock", comment="Basic formula query to verify absence of deadlocks")
    nta.queries.append(query)
    return nta


def rename_tasks_with_same_name(nodes_names: list[str]):
    names_list: list[str] = []
    names_list = nodes_names[:]
    for i, name in enumerate(names_list):
        if names_list.count(name) > 1:
            j = 0
            while j in range(names_list.count(name)):
                name = name + "_" + str(j)
                names_list[i] = name
                j += 1
    # In theory, lists should be about the same size, so...
    for i in range(len(nodes_names)):
        nodes_names[i] = names_list[i]

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
                nta.system.text += f"var_{temp.name.name} = {temp.name.name}("
                added_types = []
                if temp.parameter is not None:
                    comma_positions = temp.parameter.text.split(",")

                    for j, com in enumerate(comma_positions):
                        for i, prec in enumerate(predicates):
                            # print(temp.name.name)
                            # print(com.split(" ")[0])
                            com = com.strip(' ')  # Trim whitespaces
                            type = com.split(" ")[1].replace("&", "")
                            # print(prec.type)
                            # print(str(type))
                            # print(prec.type == str(type))
                            if prec.type == str(type) and prec.type not in added_types:
                                nta.system.text += f"{prec.type}"
                                added_types.append(prec.type)
                                if j != len(comma_positions)-1:
                                    nta.system.text += ","
                    # Remove an unnecessary comma at the end of the string
                    if (nta.system.text[-1:] == ","):
                        nta.system.text = nta.system.text[:-1]
                    nta.system.text += ");\n"
                else:
                    nta.system.text += ");\n"
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
            if i == len(var.predicates_name_list) - 1:  # Last element
                nta.declaration.text += "false};"
            else:
                nta.declaration.text += "false,"

        nta.declaration.text += "\n"

    return nta


def link_variables_with_predicates_and_types(var_and_types_list_with_predicates: list[Variable]):
    # Adds remaining predicates to variables still without them
    aux_var_and_types_list_with_predicates = copy.deepcopy(
        var_and_types_list_with_predicates)

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


def is_gm_task(node: str):
    return True if (node.startswith("AT")) else False


def get_list_of_tasks(goal_nodes_info: list[GoalTreeNode]):
    # Go through the whole list one time to get all children that are tasks, we'll put them on a list
    # Next, we'll check for their parents, each time the iteration ends, we check if any child contains a related parent
    # If so, we can then proceed to execute, parent by parent, the model transformation
    tasks_list: list = []
    for goal in goal_nodes_info:
        if goal.isTask:
            tasks_list.append(goal.name)
    return tasks_list


def find_node_and_add_to_list(task, goal_nodes_info: list[GoalTreeNode], index: int, backwards_list: list):
    for i in range(index, -1, -1):
        for child in goal_nodes_info[i].children:
            if child == task:
                backwards_list.append(goal_nodes_info[i].name)
                next_iter_pos = i-1
                find_node_and_add_to_list(
                    goal_nodes_info[i].name, goal_nodes_info, next_iter_pos, backwards_list)


def create_sequential_template_for_tasks(operands_list,  goal_model_template: uppaalpy.Template, completed_operands: list):
    # First, we'll start with generating a local node where the execution begins
    # and then other where the execution ends
    # first we'll create a connection from the last_node
    node_list = goal_model_template.graph.get_nodes()

    last_node: uppaalpy.Node = node_list[-1]
    last_node_id = last_node.id

    fixed_y = 490
    fixed_y_text = 503

    x = 550
    next_id = separate_number_from_id_and_get_number(last_node.id) + 1

    # We'll need this extra variable for transitions

    # First, we'll start with generating a local node where the execution begins
    for operand in operands_list:
        print(f"operand {operand}")
        exec_location: uppaalpy.Location = uppaalpy.Location(
            id="id"+str(next_id),
            pos=(x, fixed_y),
            name=uppaalpy.Name("exec_"+operand, pos=(x, fixed_y_text))
        )
        goal_model_template.graph.add_location(exec_location)

        next_id += 1
        x += 100

        end_location: uppaalpy.Location = uppaalpy.Location(
            id="id"+str(next_id),
            pos=(x, fixed_y),
            name=uppaalpy.Name("finished_"+operand, pos=(x, fixed_y_text))
        )
        goal_model_template.graph.add_location(end_location)

        # Now i gotta add two transitions, the first one is to the exec_location, trigerring its execution,
        # TODO: Get name of task and trigger channel execution
        exec_location_transition = uppaalpy.Transition(
            source=last_node.id, target=exec_location.id)
        end_location_transition = uppaalpy.Transition(
            source=exec_location.id, target=end_location.id)

        goal_model_template.graph.add_transition(exec_location_transition)
        goal_model_template.graph.add_transition(end_location_transition)

        next_id += 1
        x += 100
        completed_operands.append(operand)

        node_list = goal_model_template.graph.get_nodes()
        last_node: uppaalpy.Node = node_list[-1]

    # the second one is the end_location where i must ask if the task has finished
    # In order to do so, i need another function telling me what are the names of each method
    # In goal model, they are in CamelCase, but i need them in snake_case
    # And then i'll add the synch channels for ending and starting the channel connection


def separate_number_from_id_and_get_number(id: str) -> int:
    # The first two characters are "i" and "d", we just want the number so we get the result after these two lines
    return int(id[2:])


def goal_has_operator(goal_name: str) -> bool:
    has_operator = goal_name.find("_")
    if has_operator == -1:
        return False
    else:
        return True


def separate_goal_operator(goal: str) -> str | None:
    return goal[goal.find("_") + 1:] if goal_has_operator(goal) else None


def separate_goal_name(goal: str) -> str:
    return goal[0:goal.find("_")] if goal_has_operator(goal) else goal


def find_childrens_tasks(goal: str, goal_nodes_info: list[GoalTreeNode], children_task_list: list):
    for node in goal_nodes_info:
        if node.name == goal:
            childrenList = [item for child in node.children for item in child]
            for child in childrenList:
                if is_gm_task(child):
                    children_task_list.append(child)
                else:
                    find_childrens_tasks(
                        child, goal_nodes_info, children_task_list)


def is_operand_completed(operands_list, completed_operands):
    result: bool = False
    for operand in operands_list:
        if operand in completed_operands:
            result = True
        else:
            result = False
    return result


def add_remaining_tasks_to_operand_list(operands_list, task_children):
    for task in task_children:
        if task not in operands_list:
            operands_list.append(task)


def generate_goal_model_task_template(task_list: list, goal_model_template: uppaalpy.Template,
                                      goal_nodes_info: list[GoalTreeNode],
                                      completed_operands: list = [],
                                      completed_operators: list = []):
    operator_list: list = []
    operands_list: list = []
    for node in task_list:  # is operand and not goal
        if node not in const_operators and is_gm_task(node):
            operands_list.append(node)
        # is operator or goal
        elif node not in const_operators and not is_gm_task(node):
            operator = separate_goal_operator(node)
            print(f"Found new operator: {operator}")
            if operator is not None and operator in const_operators:  # Is operator
                operator_list.append(operator)
                task_children: list = []
                find_childrens_tasks(node, goal_nodes_info, task_children)
                add_remaining_tasks_to_operand_list(
                    operands_list, task_children)

                if not is_operand_completed(operands_list, completed_operands):
                    if operator_list[-1] in const_operators:
                        if operator == const_sequential:  # CASE ";"
                            print(
                                f"Executing case {const_sequential} for operand {operator} in goal {separate_goal_name(node)}")
                            create_sequential_template_for_tasks(
                                operands_list, goal_model_template, completed_operands)
                            if len(operands_list) > 0:
                                # Pops the last operand, so operation won't be done again in same operand
                                operands_list.pop(-1)

                        elif operator == const_parallel:  # CASE "#" (parallel)
                            print(
                                f"Executing case {const_parallel} for operand {operator}")
                        elif operator == const_fallback:  # CASE "FALLBACK"
                            print(
                                f"Executing case {const_fallback} for operand {operator}")
                        elif operator == const_or_sequential:  # CASE "OR"
                            print(
                                f"Executing case {const_or_sequential} for operand {operator}")
                            create_OR_template_for_tasks(
                                operands_list, goal_model_template, completed_operands)

                        # After every operation, we must remove the operator and add it to a completed operands list
                    print(f"operator {operator_list[-1]} completed operation")
                    operator_list.pop(-1)
            completed_operands.append(node)
            completed_operators.append(operator)


def find_common_goal_ancestor(task_ordering_lists) -> str:
    res = list(set.intersection(*map(set, task_ordering_lists)))
    print("The common elements from N lists : " + str(res))
    # We return the first one, since the last one is normally the root goal
    return str(res[0])


def create_OR_template_for_tasks(operands_list,  goal_model_template: uppaalpy.Template, completed_operands: list):
    # First, we'll start with generating a local node where the execution begins
    # and then other where the execution ends
    # first we'll create a connection from the last_node
    node_list = goal_model_template.graph.get_nodes()

    last_node: uppaalpy.Node = node_list[-1]
    last_node_id = last_node.id

    fixed_y = 490
    fixed_y_text = 503

    x = 550
    next_id = separate_number_from_id_and_get_number(last_node.id) + 1

    # We'll need this extra variable for transitions

    # First, we'll start with generating a local node where the execution begins
    for operand in operands_list:
        print(f"operand {operand}")
        exec_location: uppaalpy.Location = uppaalpy.Location(
            id="id"+str(next_id),
            pos=(x, fixed_y),
            name=uppaalpy.Name("exec_"+operand, pos=(x, fixed_y_text))
        )
        goal_model_template.graph.add_location(exec_location)

        next_id += 1
        x += 100

        end_location: uppaalpy.Location = uppaalpy.Location(
            id="id"+str(next_id),
            pos=(x, fixed_y),
            name=uppaalpy.Name("finished_"+operand, pos=(x, fixed_y_text))
        )
        goal_model_template.graph.add_location(end_location)

        # Now i gotta add two transitions, the first one is to the exec_location, trigerring its execution,
        # TODO: Get name of task and trigger channel execution
        exec_location_transition = uppaalpy.Transition(
            source=last_node.id, target=exec_location.id)
        end_location_transition = uppaalpy.Transition(
            source=exec_location.id, target=end_location.id)

        goal_model_template.graph.add_transition(exec_location_transition)
        goal_model_template.graph.add_transition(end_location_transition)

        next_id += 1
        x += 100
        completed_operands.append(operand)

        # In this case, the sequential OR last node is not updated, since it is a XOR
        # decomposition, it must only execute one of the following operands, so lines below are commented
        # node_list = goal_model_template.graph.get_nodes()
        # last_node: uppaalpy.Node = node_list[-1]

    # the second one is the end_location where i must ask if the task has finished
    # In order to do so, i need another function telling me what are the names of each method
    # In goal model, they are in CamelCase, but i need them in snake_case
    # And then i'll add the synch channels for ending and starting the channel connection


def generate_goal_model_template(goal_nodes_info: list[GoalTreeNode], nta: uppaalpy.NTA) -> uppaalpy.NTA:
    tasks_list = get_list_of_tasks(goal_nodes_info)
    task_ordering_lists = []
    for node in tasks_list:
        backwards_list = []
        backwards_list.append(node)
        find_node_and_add_to_list(node, goal_nodes_info, len(
            goal_nodes_info)-1, backwards_list)
        task_ordering_lists.append(backwards_list)
    # Debug
    print(task_ordering_lists)
    goal_model_template = create_goal_model_initial_template(nta)
    reverse_tasks_list(task_ordering_lists)
    # trim_useless_goals_from_order(task_ordering_lists)
    common_ancestor = find_common_goal_ancestor(task_ordering_lists)
    # First create the Location for the goal
    goal_model_template.graph.add_location(uppaalpy.Location(
        id="id1",
        pos=(600, 500),
        name=uppaalpy.Name(name="goal_"+separate_goal_name(common_ancestor), pos=(600, 470))))
    # Then add a transition for the initial node
    goal_model_template.graph.add_transition(
        uppaalpy.Transition(source="id0", target="id1"))

    # First, we'll check what operation we must do with the common ancestor 
    common_ancestor_op = separate_goal_operator(common_ancestor)
    # Sequential implies doing all operations sequentially
    # Parallel means we can treat the same as a sequential (i guess)
    # (if it's an OR, all transitions stem from the same node)
    # if fallback, we'll use that pattern of generation

    # Debug
    print(f"Common ancestor of all tasks {separate_goal_name(common_ancestor)} operation is {common_ancestor_op}")
    if common_ancestor_op == const_sequential:
        print("Sequential treatment")
        children = get_goal_children(goal_nodes_info=goal_nodes_info, node=common_ancestor)


    initial_pos_x, initial_pos_y = 680, 470
    # for task_list in task_ordering_lists:
    #     for i, node in enumerate(task_list):
    #         node_operator = separate_goal_operator(node)
    #         if i+1 in range(len(task_list)) and not is_gm_task(task_list[i+1]):
    #             print(f"node {node} doesn't have an immediate children task!")
    #             if node_operator == const_sequential:  # CASE ";"
    #                 # All children must be performed first, so what do we do?
    #                 # for each children in the sequential, we must unwind its whole tree along with its operations
    #                 # then go to the next one
                    
    #                 children = get_goal_children(goal_nodes_info, node)[0]
    #                 if children is not None:                        
    #                     for i, child in enumerate(children):
    #                         node_list = goal_model_template.graph.get_nodes()
    #                         last_node: uppaalpy.Node = node_list[-1]
    #                         last_node_id_plus_one = "id" + str(separate_number_from_id_and_get_number(last_node.id)+1)
    #                         goal_model_template.graph.add_location(uppaalpy.Location(
    #                             id=last_node_id_plus_one,
    #                             pos=(initial_pos_x, initial_pos_y),
    #                             name=uppaalpy.Name(
    #                                 name="goal_" + str(separate_goal_name(child)),
    #                                 pos=(initial_pos_x, initial_pos_y-24))))
    #                         goal_model_template.graph.add_transition(
    #                             uppaalpy.Transition(source=last_node.id, target=last_node_id_plus_one))
    #                         initial_pos_x += 70
                        

    #     completed_operands: list = []
    #     completed_operators: list = []

    #     generate_goal_model_task_template(
    #         task_list, goal_model_template, goal_nodes_info, completed_operands, completed_operators)
    return nta

def has_children(goal: GoalTreeNode) -> str:
    if goal.children != None:
        return True
    else:
        return False

def get_goal_children(goal_nodes_info: list[GoalTreeNode], node: str):
    for goal_node in goal_nodes_info:
        if goal_node.name == node:
            if has_children(goal_node):
                return goal_node.children
            else:
                return None


def trim_useless_goals_from_order(task_ordering_lists):
    for task_list in task_ordering_lists:
        for node in task_list:
            # Then it is a goal without operation
            if not is_gm_task(node) and separate_goal_operator(node) is None:
                task_list.remove(node)


def reverse_tasks_list(task_ordering_lists):
    for task_list in task_ordering_lists:
        task_list.reverse()


def create_goal_model_initial_template(nta: uppaalpy.NTA) -> uppaalpy.Template:
    goal_model_template: uppaalpy.Template = uppaalpy.Template(nta.context)
    print(goal_model_template)
    # Defining name
    goal_model_template.name = uppaalpy.Name("goal_model_template", (0, 0))

    # Initial location
    goal_model_template.graph.initial_location = "id0"

    goal_model_template.graph.add_location(uppaalpy.Location(
        id="id0",
        pos=(490, 490),
        name=uppaalpy.Name("beginMissionNode", pos=(490, 470))
    ))
    nta.templates.append(goal_model_template)
    return goal_model_template
