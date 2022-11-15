import uppaalpy
import uppaal_utils as upu

#UPPAAL Region
def execute_generator(method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_orderings, goal_properties_list):
    # First step, create a NTA with template
    # context = uppaalpy.Context()
    nta_partial = uppaalpy.NTA.from_xml(path="models\empty_model.xml")
    nta_partial, var_and_types_with_predicates = upu.generate_declaration_for_nta(nta_partial, predicates=predicate_dict, var_and_types_list=var_and_types_list, set_of_types=types_set)
    var_and_types_with_predicates =  upu.link_variables_with_predicates_and_types(var_and_types_list_with_predicates=var_and_types_with_predicates)
    tasks_names = upu.link_tasks_and_method_names(goal_properties_list, abstract_task_data)

    nta_partial = upu.generate_goal_model_template(goal_orderings, nta_partial, tasks_names, method_data)
    nta_partial = upu.generate_uppaal_methods_templates(method_data=method_data, nta=nta_partial, node_data=abstract_task_data, var_and_types_list_in_predicates=var_and_types_with_predicates)
    nta_partial = upu.generate_default_verifiable_queries(nta=nta_partial)
    nta_partial = upu.generate_declarations_of_struct_variables_in_nta(nta=nta_partial, variables_set=set(var_and_types_with_predicates))
    upu.generate_start_mission_function_definition(nta_partial, set(var_and_types_with_predicates))
    nta_partial = upu.generate_boolean_declarations_for_capabilities(method_data=method_data, nta=nta_partial)
    nta_partial = upu.generate_system_declarations(nta=nta_partial, method_data=method_data)

    # Debug
    # for tp in nta_partial.templates:
    #     upu.print_nodes_from_template(tp)

    nta_partial.to_file(path='models\empty_model_new.xml')

    #End UPPAAL Region