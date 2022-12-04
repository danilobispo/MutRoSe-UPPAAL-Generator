# Utilitary functions for UPPAAL template generation
import re
import uppaalpy
import copy

from utils import AbstractTask, AbstractTaskWithId, Capability, Effect, GoalInfo, GoalTreeNode, MethodData, Precondition, TasksRequiringLinking, Variable

const_end_method_name = "end_method"
const_sequential = ";"
const_fallback = "FALLBACK"
const_parallel = "#"
const_or_sequential = "OR"
const_operators = [const_sequential, const_parallel,
                   const_or_sequential, const_fallback]

const_mission_complete_var = "mission_complete"
const_mission_failed_var = "mission_failed"
const_start_mission_var = "startMission()"

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


def generate_failed_boolean_transition_guard(method_name: str, is_true: bool) -> str:
    if is_true:
        return f"{method_name}_failed == true"
    else:
        return f"{method_name}_failed == false"


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
    # Goal model template section
    nta.system.text += f"var_goal_model_template = goal_model_template();\n"  
    nta.system.text += "system "
    for i, temp in enumerate(nta.templates):
        nta.system.text += f"var_{temp.name.name}"
        if i != len(nta.templates)-1:
            nta.system.text += ","
    nta.system.text += ";"
    return nta


def generate_start_mission_function_definition(nta: uppaalpy.NTA, variables_set: set[Variable]):
    
    nta.declaration.text += "\nvoid startMission() {\n"
    nta.declaration.text += "// starts mission with following values, you may change the values to your liking\n"
    nta.declaration.text += f"\t{const_mission_complete_var} = false;\n"
    nta.declaration.text += f"\t{const_mission_failed_var} = false;\n"
    for var in variables_set:
        for i, predicate in enumerate(var.predicates_name_list):
            nta.declaration.text += f"\t{var.var_name}.{predicate} = false;\n"
    nta.declaration.text += "\r}\n\n"

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

def is_finish_task_node(node: str):
    return True if (node.find("finish_AT") != -1) else False


def get_list_of_tasks(goal_orderings: list[GoalTreeNode]):
    # Go through the whole list one time to get all children that are tasks, we'll put them on a list
    # Next, we'll check for their parents, each time the iteration ends, we check if any child contains a related parent
    # If so, we can then proceed to execute, parent by parent, the model transformation
    tasks_list: list = []
    for goal in goal_orderings:
        if goal.isTask:
            tasks_list.append(goal.name)
    return tasks_list


def find_node_and_add_to_list(task, goal_orderings: list[GoalTreeNode], index: int, backwards_list: list):
    for i in range(index, -1, -1):
        for child in goal_orderings[i].children:
            if child == task:
                backwards_list.append(goal_orderings[i].name)
                next_iter_pos = i-1
                find_node_and_add_to_list(
                    goal_orderings[i].name, goal_orderings, next_iter_pos, backwards_list)


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


def find_childrens_tasks(goal: str, goal_orderings: list[GoalTreeNode], children_task_list: list):
    for node in goal_orderings:
        if node.name == goal:
            for child in node.children:
                if is_gm_task(child):
                    children_task_list.append(child)
                else:
                    find_childrens_tasks(
                        child, goal_orderings, children_task_list)


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


def find_common_goal_ancestor(task_ordering_lists) -> str:
    common_goal_list = list(set.intersection(*map(set, task_ordering_lists)))
    print("The common elements from N lists : " + str(common_goal_list))
    common_goal_list.sort(key=lambda x: int(x[1:x.find("_")]))
    return str(common_goal_list[-1])


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


def remove_whitespaces(string: str):
    return string.replace(" ", "")


def link_tasks_and_method_names(goal_properties_list: list[GoalInfo], abstract_task_data: list[AbstractTask]) -> list[AbstractTaskWithId]:
    # First we create a list with all tasks present in the mission
    task_list: list = []
    # Another list will be created with each entry for each task and their respective methods
    task_and_methods_name_list: list = []
    for goal in goal_properties_list:
        if is_gm_task(goal.node_id):
            task_list.append(
                [goal.node_id, remove_whitespaces(goal.node_name)])
    for task in task_list:
        for abstract_task in abstract_task_data:
            if task[1] == abstract_task.name:
                print(f"{task[1]} equals to {abstract_task.name}")
                task_and_methods_name_list.append(AbstractTaskWithId(
                    task[0], abstract_task.name, abstract_task.methods))
    return task_and_methods_name_list

    # for task in abstract_task_data:
    # print(task.name)
    # print(task_list)


def get_parent_operation(goal_orderings: list[GoalTreeNode], node: GoalTreeNode):
    if node.name.find("_") != -1:  # if it has a _ in its name, it means it has an operation
        return separate_goal_operator(node.name)
    else:  # let's find the parent goal
        for item in goal_orderings:
            for child in item.children:
                if child == node.name:
                    if item.name.find("_") != -1:
                        return item, separate_goal_operator(item.name)
                    else:
                        get_parent_operation(
                            goal_orderings, find_node_by_name(item.name, goal_orderings))


def is_inside_fallback(goal_orderings: list[GoalTreeNode], node: GoalTreeNode) -> bool:
    if(node == None):
        return False
    if node.name.find("_FALLBACK") != -1:  # if it has a _ in its name, it means it has an operation
        return True
    else:  # let's find the parent goal
        for item in goal_orderings:
            for child in item.children:
                if child == node.name:
                    if item.name.find("_FALLBACK") != -1:
                        return True
                    else:
                        return is_inside_fallback(
                            goal_orderings, find_node_by_name(item.name, goal_orderings))

def get_immediate_parent(goal_orderings: list[GoalTreeNode], node: GoalTreeNode):
    for item in goal_orderings:
        for child in item.children:
            if child == node.name:
                return item, separate_goal_operator(item.name)


def find_node_by_name(name: str, goal_orderings: list[GoalTreeNode]) -> GoalTreeNode:
    for node in goal_orderings:
        if node.name == name:
            return node


def has_children(goal: GoalTreeNode) -> str:
    if goal.children != None:
        return True
    else:
        return False

def create_update_for_mission_end(nta: uppaalpy.NTA, completedOrFailed: bool, pos = None) -> uppaalpy.Label:
    if pos is not None:
        if completedOrFailed:
            return uppaalpy.UpdateLabel(kind="assignment",ctx =nta.context, pos=pos,value=f"{const_mission_complete_var} = true")
        else:
            return uppaalpy.UpdateLabel(kind="assignment", ctx=nta.context, pos=pos,value=f"{const_mission_failed_var} = true")
    else:
        if completedOrFailed:
            return uppaalpy.UpdateLabel(kind="assignment", ctx=nta.context, pos=(500, 300),value=f"{const_mission_complete_var} = true")
        else:
            return uppaalpy.UpdateLabel(kind="assignment", ctx=nta.context, pos=(500, 300),value=f"{const_mission_failed_var} = true")


def create_nta_declaration_for_mission_end(nta: uppaalpy.NTA):
    nta.declaration.text += f"\nbool {const_mission_complete_var} = false;\n"
    nta.declaration.text += f"bool {const_mission_failed_var} = false;\n"

def get_goal_children(goal_orderings: list[GoalTreeNode], node: str):
    for goal_node in goal_orderings:
        if goal_node.name == node:
            if has_children(goal_node):
                return goal_node.children
            else:
                return None


def recursive_get_goal_children_tasks(goal_orderings: list[GoalTreeNode], node: str, child_list: list):
    for goal_node in goal_orderings:
        if goal_node.name == node:
            if has_children(goal_node):
                for child in goal_node.children:
                    if is_gm_task(child):
                        child_list.append(child)
                    recursive_get_goal_children_tasks(
                        goal_orderings, child, child_list)


def trim_useless_goals_from_order(task_ordering_lists):
    for task_list in task_ordering_lists:
        for node in task_list:
            # Then it is a goal without operation
            if not is_gm_task(node) and separate_goal_operator(node) is None:
                task_list.remove(node)


def reverse_tasks_list(task_ordering_lists):
    for task_list in task_ordering_lists:
        task_list.reverse()


def has_path_to_children_task(goal_orderings: list[GoalTreeNode], node: GoalTreeNode) -> bool:
    has_child_task: bool = None
    for item in goal_orderings:
        if item.name == node.name:
            if has_children(item):
                # Debug
                # print(f"Current node: {item}")
                for child in item.children:
                    if is_gm_task(child):
                        has_child_task = True or has_child_task
                    else:
                        has_child_task = has_path_to_children_task(
                            goal_orderings, find_node_by_name(child, goal_orderings))
    return has_child_task


def get_available_methods_for_task_id(task_id: str, tasks_names: list[AbstractTaskWithId]):
    for task in tasks_names:
        if task_id == task.id:
            return task.methods

def get_tasks_transitions(template: uppaalpy.Template):
    nodes: list[uppaalpy.Location] = template.graph.get_nodes()
    task_nodes_list: list[uppaalpy.Location] = []
    transition_list = template.graph._transitions
    for node in nodes:
        # Get all tasks nodes
        if is_finish_task_node(node.name.name):
            task_nodes_list.append(node)
    return template, task_nodes_list, transition_list
    

def add_remaining_transition_for_general_tasks(template, task_nodes_list, transition_list):
    for node in task_nodes_list:
        transition_count = 0
        node_transition_list: list[uppaalpy.Transition] = []
        for transition in transition_list:
            if node.id == transition.source:
                transition_count += 1
                node_transition_list.append(transition)
        # By checking the connections the node has, it is possible to infer if its connected with the last node
        if transition_count == 1: # Only one connection stems from this node, it should be 2 normally
            if node_transition_list[0].target == "id777": #If the only connection is with the error node, made by default
                # We'll add another, with the connection to the end node
                template.graph.add_transition(uppaalpy.Transition(source=node.id, target="id9000"))

def add_remaining_transitions_for_fallback_tasks(template: uppaalpy.Template, fb_tasks_requiring_linking: list[TasksRequiringLinking], tasks_names: list[AbstractTaskWithId], method_data: list[MethodData]):
    node_list = template.graph.get_nodes()
    tasks_names: list[AbstractTaskWithId]
    for task in fb_tasks_requiring_linking:
        available_methods = get_available_methods_for_task_id(task.id, tasks_names)
        for node in node_list:
            # First, get task node in graph
            if node.name.name.__contains__("finish_"+task.id):
                task_node = node            
        if task.sibling is not None:
            goal_name = separate_goal_name(task.sibling.name)
            for node in node_list:
                # if there's a sibling, we need to get its target node where the transition shall occur
                if node.name.name.__contains__("goal_"+goal_name):
                    target_node = node
        else: # if there's no sibling, then straight to mission complete!
            target_node = None
        for method in available_methods:
            for m in method_data:
                if m.method_name.__contains__(method):    
                    grd_lbl_x, grd_lbl_y = task_node.pos
                    guard = uppaalpy.ConstraintLabel(
                        kind="guard", 
                    value=generate_failed_boolean_transition_guard(m.method_name, False),
                    pos=(grd_lbl_x, grd_lbl_y), 
                    ctx=template.context)
                    if target_node is not None:
                        trans = uppaalpy.Transition(source=task_node.id, target=target_node.id, guard=guard)
                    else: # transition to mission complete node directly
                        trans = uppaalpy.Transition(source=task_node.id, target="id9000", guard=guard)
                    template.graph.add_transition(trans)
        
    # Create the mission_failed linking 
    tasks_names_id = [task.id for task in tasks_names] # Get all tasks id's in list of all tasks
    task_id = [task.id for task in fb_tasks_requiring_linking] # Get all tasks id's in list of tasks that require linking
    tasks_not_linked = [task for task in tasks_names_id if task not in task_id] # Find the difference between them
    if tasks_not_linked is not None: 
        for task in tasks_not_linked:
            available_methods = get_available_methods_for_task_id(task, tasks_names)
            for node in node_list:
                if node.name.name.__contains__("finish_"+task):
                    task_node = node
            for method in available_methods:
                for m in method_data:
                    if m.method_name.__contains__(method):    
                        fail_transition = uppaalpy.Transition(
                                    source=task_node.id, 
                                    target="id777", 
                                    guard=
                                        uppaalpy.ConstraintLabel(kind="guard", 
                                        value=generate_failed_boolean_transition_guard(m.method_name, True), 
                                        pos=task_node.pos,
                                        ctx=template.context))
                        template.graph.add_transition(fail_transition)
                

def generate_goal_model_template(goal_orderings: list[GoalTreeNode], nta: uppaalpy.NTA, tasks_names: list[AbstractTaskWithId], method_data: list[MethodData]) -> uppaalpy.NTA:
    tasks_list = get_list_of_tasks(goal_orderings)
    task_ordering_lists = []
    for node in tasks_list:
        backwards_list = []
        backwards_list.append(node)
        find_node_and_add_to_list(node, goal_orderings, len(
            goal_orderings)-1, backwards_list)
        task_ordering_lists.append(backwards_list)
    # Debug
    print(task_ordering_lists)
    goal_model_template = create_goal_model_initial_template(nta)
    reverse_tasks_list(task_ordering_lists)
    # trim_useless_goals_from_order(task_ordering_lists)
    node = find_common_goal_ancestor(task_ordering_lists)
    # First create the Location for the goal
    goal_model_template.graph.add_location(uppaalpy.Location(
        id="id1",
        pos=(600, 500),
        name=uppaalpy.Name(name="goal_"+separate_goal_name(node), pos=(600, 470))))
    
    start_mission_str = "startMission()"
    # add the startMission task method call
    start_mission_label = uppaalpy.Label(kind="assignment", pos=(467,501),value=f"{const_start_mission_var}")
    # Then add a transition for the initial node

    goal_model_template.graph.add_transition(
        uppaalpy.Transition(source="id0", target="id1", assignment=start_mission_label))

    # First, we'll check what operation we must do with the common ancestor
    node_op = separate_goal_operator(node)
    # Sequential implies doing all operations sequentially
    # Parallel means we can treat the same as a sequential (i guess)
    # (if it's an OR, all transitions stem from the same node)
    # if fallback, we'll use that pattern of generation

    # Debug
    print(
        f"Common ancestor of all tasks {separate_goal_name(node)} operation is {node_op}")

    initial_pos_x, initial_pos_y = 720, 500
    or_children: list[str] = []
    fb_tasks_requiring_linking: list[TasksRequiringLinking] = []
    generate_subsequent_goals_for_child_node(
        goal_orderings, node, goal_model_template, initial_pos_x, initial_pos_y, tasks_names, method_data, or_children, fb_tasks_requiring_linking)
    # Add remaining connections to the end of the task and trigger the variables which declare missionFailed or missionCompleted
    template, task_nodes_list, transition_list = get_tasks_transitions(goal_model_template)
    print(fb_tasks_requiring_linking)
    if len(fb_tasks_requiring_linking) is not 0:
        add_remaining_transitions_for_fallback_tasks(template, fb_tasks_requiring_linking, tasks_names, method_data)
    add_remaining_transition_for_general_tasks(template, task_nodes_list, transition_list)
    return nta


def create_exec_tasks_location_template(task: str, template: uppaalpy.Template, tasks_names: list[AbstractTaskWithId], method_data: list[MethodData], parent_operation: str, goal_orderings: list[GoalTreeNode]):
    nodes = template.graph.get_nodes()
    last_node: uppaalpy.Node = nodes[-1]
    (updated_x_position, updated_y_position) = last_node.pos
    updated_y_position -= 100
    exec_location_id_number = separate_number_from_id_and_get_number(
        last_node.id) + 1
    finish_location_id_number = separate_number_from_id_and_get_number(
        last_node.id) + 2
    exec_location_id = "id"+str(exec_location_id_number)
    finish_location_id = "id"+str(finish_location_id_number)

    # Exec Location
    exec_location = uppaalpy.Location(
        id=exec_location_id,
        pos=(updated_x_position, updated_y_position),
        name=uppaalpy.Name(name="exec_"+task, pos=(updated_x_position, updated_y_position-30)))

    updated_y_position -= 100

    # Finish location
    finish_location = uppaalpy.Location(
        id=finish_location_id,
        pos=(updated_x_position, updated_y_position),
        name=uppaalpy.Name(name="finish_"+task, pos=(updated_x_position, updated_y_position-30)))

    methods = get_available_methods_for_task_id(task, tasks_names)
    for method in methods:
        for m in method_data:
            if m.method_name.__contains__(method):
                # Last goal to task transition
                # I must add the start channel to this transition
                exec_sync_channel_str = create_channel_synch_for_transition(
                    get_channel_name(method_name=m.method_name, finished=False), target=False)
                exec_synch_label = uppaalpy.Label(
                    kind="synchronisation", value=exec_sync_channel_str, pos=(updated_x_position, updated_y_position+150))
                goal_to_task_transition = uppaalpy.Transition(
                    source=last_node.id, target=exec_location_id, synchronisation=exec_synch_label)

                # Exec to finish location transition
                # I must add the finish channel to this transition
                finish_sync_channel_str = create_channel_synch_for_transition(
                    get_channel_name(method_name=m.method_name, finished=True), target=True)
                finish_synch_label = uppaalpy.Label(
                    kind="synchronisation", value=finish_sync_channel_str, pos=(updated_x_position, updated_y_position+50))
                exec_location_transition = uppaalpy.Transition(
                    source=exec_location_id, target=finish_location_id, synchronisation=finish_synch_label)

                # Add transition to failure node with guard condition
                # by definition, the failed node is "id777"
                fail_transition = uppaalpy.Transition(
                    source=finish_location_id, 
                    target="id777", 
                    guard=
                        uppaalpy.ConstraintLabel(kind="guard", 
                        value=generate_failed_boolean_transition_guard(m.method_name, True), 
                        pos=(updated_x_position-140, updated_y_position-80),
                        ctx=template.context))
                template.graph.add_transition(goal_to_task_transition)
                template.graph.add_location(exec_location)
                template.graph.add_transition(exec_location_transition)
                template.graph.add_location(finish_location)
                if(parent_operation != const_fallback and not is_inside_fallback(goal_orderings, find_node_by_name(task, goal_orderings))):
                    template.graph.add_transition(fail_transition)

def or_insertion_function(goal_orderings, initial_pos_x, initial_pos_y, child, node_list, last_node_id_plus_one):
    goal_location = uppaalpy.Location(
                    id=last_node_id_plus_one,
                    pos=(initial_pos_x, initial_pos_y+60),
                    name=uppaalpy.Name(
                        name="goal_" +
                        str(separate_goal_name(child)),
                        pos=(initial_pos_x, initial_pos_y+30)))
    or_parent, or_parent_operation = get_immediate_parent(goal_orderings, find_node_by_name(child, goal_orderings))
    for goal_node in node_list:
        if goal_node.name.name.endswith(separate_goal_name(or_parent.name)):
            or_node_parent_id = goal_node.id
    trans = uppaalpy.Transition(source=or_node_parent_id, target=last_node_id_plus_one)
    return goal_location, trans

def is_second_operand_of_fallback(goal: str, goal_orderings: list[GoalTreeNode]) -> bool:
    parent, operator = get_immediate_parent(goal_orderings, find_node_by_name(goal, goal_orderings))
    if operator == const_fallback:
        children = get_goal_children(goal_orderings, parent.name)
        # Debug
        # print(f"Children of {parent.name}")
        # for child in children:
        #     print(f"{child}")
        if(children[1] == goal):
            return True

def is_first_operand_of_fallback(goal: str, goal_orderings: list[GoalTreeNode]) -> bool:
    parent, operator = get_immediate_parent(goal_orderings, find_node_by_name(goal, goal_orderings))
    if operator == const_fallback:
        children = get_goal_children(goal_orderings, parent.name)
        # Debug
        # print(f"Children of {parent.name}")
        # for child in children:
        #     print(f"{child}")
        if(children[0] == goal):
            return True

def get_sibling_of_fallback_node(goal: str, goal_orderings: list[GoalTreeNode]):
    fallback_node, operator = get_immediate_parent(goal_orderings, find_node_by_name(goal, goal_orderings))
    if operator == const_fallback:
        fallback_parent, fallback_parent_op = get_immediate_parent(goal_orderings, find_node_by_name(fallback_node.name, goal_orderings) )
        children = get_goal_children(goal_orderings, fallback_parent.name)
        print(f"Children of {fallback_parent.name}")
        for i, child in enumerate(children):
            if child == fallback_node.name:
                # Debug
                # for child in children:
                if i+1 in range(len(children)):
                    print(f"{children[i+1]} is the sibling of {fallback_node.name}")
                    return find_node_by_name(children[i+1], goal_orderings)
                else:
                    print(f"No sibling found for goal {goal}")
                    return None


def generate_subsequent_goals_for_child_node(
        goal_orderings: list[GoalTreeNode],
        node: str,
        goal_model_template: uppaalpy.Template,
        initial_pos_x: int,
        initial_pos_y: int,
        tasks_names: list[AbstractTaskWithId],
        method_data: list[MethodData],
        or_children: list[str],
        fb_tasks_requiring_linking: list[TasksRequiringLinking]):
    children=get_goal_children(goal_orderings=goal_orderings, node=node)
    # print(f"children: {children}")
    # no children, so it is the last node
    if len(children) == 0 and not is_gm_task(node):
        print(f"node {node} has no children!")

    for child in children:        
        if is_gm_task(child):  # is Task?
            parent, parent_operation=get_parent_operation(
                goal_orderings, find_node_by_name(node, goal_orderings))
            # First, gather all possible operands from the parent
            # child_task_list: list[str]=[]
            print(f"parent: {parent}")
            # recursive_get_goal_children_tasks(
                # goal_orderings, parent.name, child_task_list)
            # print(f"child List: {child_task_list}")
            # Find parent and perform operation on node
            print(f"is task {child}")
            print(f"parent_operation: {parent_operation}")
            # Perform operation if its not already performed
            create_exec_tasks_location_template(
                    child, goal_model_template, tasks_names, method_data, parent_operation, goal_orderings)
        else:  # is Goal?
            # If it's a goal, check if goal leads to a task, otherwise its dismissible
            print(f"it is goal {child}")
            
            has_path=has_path_to_children_task(
                goal_orderings=goal_orderings, node=find_node_by_name(child, goal_orderings))
            # Debug
            print(f"child {child} has path to children tasks? {has_path}")
            if has_path:  # Means that goal is not dismissable and must be put into the goal model template
                already_added_trans = False
                child_operator = separate_goal_operator(child)
                node_list: list[uppaalpy.Location] = goal_model_template.graph.get_nodes()
                last_node: uppaalpy.Node=node_list[-1]
                last_node_id_plus_one="id" + \
                    str(separate_number_from_id_and_get_number(
                        last_node.id)+1)
                last_node_pos_x, last_node_pos_y = last_node.pos
                # Due to bug in tasks generation, where tasks would overlap each other
                # may not be necessary at the end
                if (last_node_pos_x == initial_pos_x):
                    initial_pos_x += 150
                # elif last_node_pos_y == initial_pos_y:
                #     initial_pos_y += 20
                
                for n in node_list:
                    x_pos, y_pos = n.pos
                    if x_pos == initial_pos_x:
                        initial_pos_y -= 100

                goal_location = uppaalpy.Location(
                    id=last_node_id_plus_one,
                    pos=(initial_pos_x, initial_pos_y),
                    name=uppaalpy.Name(
                        name="goal_" +
                        str(separate_goal_name(child)),
                        pos=(initial_pos_x, initial_pos_y-30)))
                

                # Specific loop of OR children
                if child in or_children:
                    goal_location, trans = or_insertion_function(goal_orderings, initial_pos_x, initial_pos_y, child, node_list, last_node_id_plus_one)
                # Specific loop of FALLBACK
                # If it's the second operand, then the order changes, as it must contain a failure node linked directly
                elif is_second_operand_of_fallback(goal=child, goal_orderings=goal_orderings):
                    print(f"Goal {child} is second operand of FALLBACK")
                    # Add the failed condition for last task executed
                    task_id = separate_goal_operator(last_node.name.name)
                    methods = get_available_methods_for_task_id(task_id, tasks_names)
                    for method in methods:
                        for m in method_data:
                            if m.method_name.__contains__(method):
                                fall_trans = uppaalpy.Transition(
                                source=last_node.id, 
                                target=last_node_id_plus_one, 
                                guard=uppaalpy.ConstraintLabel(kind="guard", 
                                value=generate_failed_boolean_transition_guard(m.method_name, True), 
                                pos=(initial_pos_x-100, initial_pos_y-80),
                                ctx=goal_model_template.context))
                                # added early due to iteration
                                goal_model_template.graph.add_transition(fall_trans)
                                already_added_trans = True
                
                else:
                    trans = uppaalpy.Transition(source=last_node.id, target=last_node_id_plus_one)
                
                if is_first_operand_of_fallback(child, goal_orderings):
                    # Whitelist the task as one that must contain 
                    # two transitions in its task final node, in order
                    # to avoid deadlocks
                    print(f"{child} is first operand of fallback")
                    sibling = get_sibling_of_fallback_node(child, goal_orderings)
                    first_operands_tasks = []
                    find_childrens_tasks(goal=child, goal_orderings=goal_orderings, children_task_list=first_operands_tasks)
                    if first_operands_tasks is not None:
                        for task in first_operands_tasks:
                            new_task = TasksRequiringLinking(task, sibling)
                            fb_tasks_requiring_linking.append(new_task)    
                
                goal_model_template.graph.add_location(goal_location)
                if trans is not None and already_added_trans is not True:
                    goal_model_template.graph.add_transition(trans)
                    # Decomposition for goals without children
                if child_operator is not None:
                    # Case ; (SEQUENTIAL)
                    if child_operator == const_sequential:
                        print("it is sequential!")
                    if child_operator == const_or_sequential:
                        or_children = get_goal_children(goal_orderings, child)
                initial_pos_x += 100
        generate_subsequent_goals_for_child_node(
            goal_orderings, child, goal_model_template, initial_pos_x, initial_pos_y, tasks_names, method_data, or_children, fb_tasks_requiring_linking)


def create_goal_model_initial_template(nta: uppaalpy.NTA) -> uppaalpy.Template:
    goal_model_template: uppaalpy.Template=uppaalpy.Template(nta.context)
    print(goal_model_template)
    # Defining name
    goal_model_template.name=uppaalpy.Name("goal_model_template", (0, 0))
    # Initial location
    goal_model_template.graph.initial_location="id0"
    goal_model_template.graph.add_location(uppaalpy.Location(
        id="id0",
        pos=(420, 500),
        name=uppaalpy.Name("beginMissionNode", pos=(420, 470))
    ))

    create_nta_declaration_for_mission_end(nta = nta)
    mission_complete_label = create_update_for_mission_end(nta=nta, completedOrFailed=True, pos=(450, 720))
    mission_failed_label = create_update_for_mission_end(nta=nta, completedOrFailed=False, pos=(280, 272))

    # mission failed location
    mission_failed_id="id777"
    goal_model_template.graph.add_location(uppaalpy.Location(
        id=mission_failed_id,
        pos=(420, 100),
        name=uppaalpy.Name("missionFailed", pos=(420, 70))
    ))
    # mission failed transition back to initial node
    goal_model_template.graph.add_transition(uppaalpy.Transition(
        source=mission_failed_id, target=goal_model_template.graph.initial_location, assignment=mission_failed_label))

    # mission complete location
    mission_complete_id="id9000"
    goal_model_template.graph.add_location(uppaalpy.Location(
        id=mission_complete_id,
        pos=(1500, 750),
        name=uppaalpy.Name("missionComplete", pos=(1500, 720))
    ))
    # mission complete transition back to initial node
    goal_model_template.graph.add_transition(uppaalpy.Transition(
        source=mission_complete_id, target=goal_model_template.graph.initial_location, nails=[uppaalpy.Nail(420, 740)], assignment=mission_complete_label))

    nta.templates.append(goal_model_template)
    return goal_model_template
