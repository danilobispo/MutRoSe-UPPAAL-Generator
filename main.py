from uppaal_generator import execute_generator
from uppaal_parser import execute_parser
# uncomment these to profile in cmd line with
# python -m cProfile -o .\program.prof .\main.py
# import cProfile
# import re
# cProfile.run('main()')

def main():
    method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_orderings, goal_properties_list = execute_parser()
    execute_generator(method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_orderings, goal_properties_list)
    

if __name__ == "__main__":
    main()