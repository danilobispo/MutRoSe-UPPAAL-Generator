from uppaal_generator import execute_generator
from parser import execute_parser


def main():
    method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_node_info = execute_parser()
    execute_generator(method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_node_info)
    

if __name__ == "__main__":
    main()