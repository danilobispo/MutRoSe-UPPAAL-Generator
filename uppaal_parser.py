from array import array
import utils
import copy


# Constants used throughout parsing
const_possible_precs = "Possible orderings for method"
const_method_name = "Method name:"
const_precondition = "__method_precondition_"
const_argument = "_argument_"
const_task_effect = "__task_effect"
const_capability_req = "__method_capability"
const_var_name = "Variable name: "
const_type_name = "Variable type: "

const_AT_name = "Name:"

const_dash_sep = "-->"

def parse_method_name(method_line):
    name = method_line.split(const_method_name)[1].replace("\n", "").replace(" ","").replace("-","_")
    # Debug
    # print(name)
    return name

def parse_precondition(line_prec):
    # Let's use destructuring to make the code a little cleaner
    predicate_name, predicate_type = line_prec.split(const_argument)[0].replace("\n", ""), line_prec.split(const_argument)[1].replace("\n", "").replace("?","")
    predicate_name, predicate_value = predicate_name.split("_")[0].replace("\n", ""), predicate_name.split("_")[1].replace("\n", "")
    # debug
    # print("precondition predicate name:", predicate_name)
    # print("precondition predicate value:", predicate_value)
    # print("precondition predicate type: ", predicate_type)
    return utils.Precondition(name=predicate_name, type=predicate_type, value=predicate_value)


def parse_effect(line_prec):
    # Let's use destructuring to make the code a little cleaner
    predicate_name, predicate_value = line_prec.split("_")[0].replace("\n", ""), line_prec.split("_")[1].replace("\n", "")
    predicate_type = line_prec.split(const_argument)[1].replace("\n", "").replace("?", "")
    # debug
    # print("effect predicate name:", predicate_name)
    # print("effect predicate value:", predicate_value)
    # print("effect predicate type: ", predicate_type)
    return utils.Effect(name=predicate_name, type=predicate_type, value=predicate_value)

def parse_capability(line_prec):
    # Let's use destructuring to make the code a little cleaner
    capability_name = line_prec.split(const_argument)[1].replace("\n", "").replace("-", "_")
    # debug
    # print("effect predicate name:", predicate_name)
    # print("effect predicate value:", predicate_value)
    # print("effect predicate type: ", predicate_type)
    return utils.Capability(name=capability_name, value=True)

def parse_method_ordering(method_name:str, ordering_line: str):
    # First we split the line by whitespaces, which is the separator used for some things
    # print("Method name:", method_name)
    words = ordering_line.split(" ")
    prec_list = []
    effect_list = []
    capabilities_list = []
    task_method_list = []
    for i in range(len(words)):
        # precondition region
        # Skip this line because we have already parsed the precondition
        if(words[i].find(const_argument) >= 0 or words[i] == "\n" ): 
            # print("Ignored line:", words[i])
            continue
        # An ordering always starts with a precondition method, so we check if
        # 1) It exists and 
        # 2) if it does we parse the value, the type and its name
        if(words[i].startswith(const_precondition)):
            i_copy = i
            # Debug 
            # print("Prec print:", words[i+1])
            while(words[i_copy+1].find(const_argument) >= 0):
                prec = parse_precondition(words[i_copy+1])
                prec.tied_to = method_name
                prec_list.append(prec)
                i_copy = i_copy + 1
            # I still have to send that precondition somewhere
        # end precondition region

        # effect region
        elif(words[i].startswith(const_task_effect)):
            i_copy = i
            while(words[i_copy+1].find(const_argument) >= 0):
                effect = parse_effect(words[i_copy+1])
                effect.tied_to = task_method_list[-1]
                effect_list.append(effect)
                i_copy = i_copy + 1
            # I still have to send that precondition somewhere
        # end effect region

        #Capabilities region: #
        elif(words[i].startswith(const_capability_req)):
            i_copy = i
            while(words[i_copy+1].find(const_argument) >= 0):
                capability = parse_capability(words[i_copy+1])
                capability.tied_to = task_method_list[-1]
                # Debug
                # print(f"capability {capability} found!")
                capabilities_list.append(capability)
                i_copy = i_copy + 1
        #End capabilities region#

        # Now they're definitely tasks or methods. This also represents the order of the tasks
        else:
            task_method_list.append(words[i].replace("\n", "").replace("-","_"))
    # print("Task order: ", task_method_list)
    # for preco in prec_list:
        # print("Precondition:", preco.name, "\n\tType:", preco.type, "\n\tvalue: ", preco.value)
    # for effect in effect_list:
        # print("Effect:", effect.name, "\n\tType:", effect.type, "\n\tvalue: ", effect.value, "\n\tTied to: ", effect.tied_to)
    return prec_list, effect_list, task_method_list, capabilities_list



def open_and_parse_method_file(filename) -> list[utils.MethodData]:
    with open(filename) as file:
        lines = list(file.readlines())
        parsed_data  = []
        
        for i in range(len(lines)):
            if lines[i] == "": 
                break
            else: 
                if lines[i].startswith(const_method_name):
                    method_name_parsed=parse_method_name(method_line=lines[i])
                    i_copy = i+1
                    if(i_copy in range(len(lines))):
                        i_method_count = 0
                        while(not lines[i_copy].startswith(const_method_name)):
                            preconditions, effects, order, capabilities=parse_method_ordering(
                                    method_name=method_name_parsed+"_"+str(i_method_count), 
                                    ordering_line=lines[i_copy])
                            parsed_data.append(utils.MethodData(name=method_name_parsed+"_"+str(i_method_count), 
                            preconditions= preconditions, effects= effects, order=order, capabilities=capabilities))
                            if(i_copy + 1 == len(lines)): break
                            else: i_copy = i_copy + 1
                            i_method_count = i_method_count + 1
        # now we will extract the repeated methods
        # let's make a shallow copy
        parsed_data_cp = copy.copy(parsed_data)
        for obj in parsed_data:
            for ele in parsed_data_cp:
                if obj.method_name == ele.method_name and obj.order == ele.order:
                    if obj is not ele:
                        parsed_data.remove(ele)

    # Debug
    # for obj in parsed_data:
    #     print(obj.method_name)
    return parsed_data

def open_and_parse_abstract_tasks_file(filename: str):
    at_list = []
    with open(filename) as file:
        lines = file.readlines()
        for i in range(len(lines)):
            at_methods = []
            if lines[i].startswith(const_AT_name) :
                at_name = lines[i].split(const_AT_name)[1].replace('\n', "").replace(" ", "")
                i_copy = i+1
                if(i_copy in range(len(lines))):
                    while(not lines[i_copy].startswith(const_AT_name) and i_copy < len(lines)):
                        at_methods.append(lines[i_copy].replace("\n", "").replace(" ", "").replace("-","_"))
                        if(i_copy + 1 == len(lines)): break
                        else: i_copy = i_copy + 1
                at_list.append(utils.AbstractTask(name=at_name, methods=at_methods))
    at_list_cp = copy.copy(at_list)
    for obj in at_list:
        for ele in at_list_cp:
            if obj.name == ele.name and obj.methods == ele.methods:
                if obj is not ele:
                    at_list.remove(ele)
    return at_list

def open_and_parse_types_and_variables_file(filename:str):
    variables_and_types= set[utils.Variable]()
    set_of_types = set()
    with open(filename) as file:
        lines = file.readlines()
        for i in range(len(lines)):
            variable_name, variable_type = lines[i].split(" ")[2].replace("?", ""), lines[i].split(" ")[5].replace("\n", "")
            variables_and_types.add(utils.Variable(variable_name, variable_type))
        for varia in variables_and_types:
            set_of_types.add(varia.type_name)
        return variables_and_types, set_of_types

def extract_predicate_names_and_types(method_data):
    predicate_dict = dict()
    for method in method_data:
        for prec in method.preconditions:
            if(prec.name not in predicate_dict):
                predicate_dict[prec.name] = prec.type
        for effect in method.effects:
            if(effect.name not in predicate_dict):
                predicate_dict[effect.name] = effect.type
    return predicate_dict

def create_predicate_vars_for_uppaal(method_data):
    predicate_name_list = extract_predicate_names_and_types(method_data)
    return predicate_name_list

def open_and_parse_goal_orderings(filename: str):
    tree_node_list = []
    with open(filename) as file:
        lines = file.readlines()
        for line in lines:
            # Debug
            # print(line)
            if(len(line.rstrip()) > 0):
                source, targets = line.split(sep=const_dash_sep)[0].strip(), line.split(sep=const_dash_sep)[1]
                if source[:2] == "AT":
                    source = trim_tasks_names(source)
                targets = targets.split(sep=" ")[1:]
                for target in targets:
                    if target == "\n":
                        targets.remove(target)
                    if target[:2] == "AT" :
                        index = targets.index(target)
                        targets[index] = trim_tasks_names(target)
                tree_node = utils.GoalTreeNode(source, targets, is_task=check_if_node_is_task(source))
                tree_node_list.append(tree_node)
                # Debug
                # print(f"Source: {source}")
                # print(f"Targets: {targets}")
    return tree_node_list

def check_if_node_is_task(node: str): 
    if(node[:1] == "G"):
        return False
    elif(node[:2] == "AT"):
        return True

def trim_tasks_names(task_name: str):
    # We're going to remove characters starting from the _ character, so we find its index and
    # delete all the string from then on
    return task_name[0:task_name.find("_")]

def open_and_parse_goal_properties(filename:str):
    goal_properties_list = []
    with open(filename) as fp:
        lines = fp.readlines()
        # If the line is empty, then close the loop
        # stop criteria is that if the line is empty, then we can create a new data structure
        i = 0
        const_node_line = "Node:"
        const_context_line = "Context:"
        const_group_line = "Group?"
        const_divisible_line = "Divisible?"
        while i < len(lines):
            if lines[i] == "\n":
                goal_info = utils.GoalInfo(node_id, node_name, node_context, node_group, node_divisible)
                goal_properties_list.append(goal_info)
            else:
                # If it starts with 
                if lines[i].startswith(const_node_line):
                    first_line = lines[i].split(sep=":")
                    node_id, node_name = first_line[1].strip(), first_line[2].split(sep="[")[0].strip()
                # If it starts with "Context: "
                elif lines[i].startswith(const_context_line):
                    node_context = lines[i].split(sep=":")[1].strip()
                # If it starts with "Group? "
                elif lines[i].startswith(const_group_line):
                    node_group = True if lines[i].split(sep="?")[1].strip() == "1" else False
                elif lines[i].startswith(const_divisible_line):
                    node_divisible = True if lines[i].split(sep="?")[1].strip() == "1" else False
            i += 1
    return goal_properties_list


def execute_parser():
    method_data: list[utils.MethodData] = open_and_parse_method_file("method_orderings.txt")
    abstract_task_data = open_and_parse_abstract_tasks_file("node_data.txt")
    var_and_types_list, types_set= open_and_parse_types_and_variables_file("types_and_variables_data.txt")
    predicate_dict = create_predicate_vars_for_uppaal(method_data=method_data)
    goal_orderings = open_and_parse_goal_orderings("general_annot_orderings.txt")
    goal_properties_list = open_and_parse_goal_properties("goal_nodes_info.txt")

    # Debug
    for goal in goal_properties_list:
        print(goal)

    # print(goal_node_info)
    # for data in method_data:
    #     print(data)
        # print("Order:", data.order)

    # for var_and_type in var_and_types_list:
    #     print(f"var_and_type.var_name: {var_and_type.var_name}")
    #     print(f"var_and_type.type_name: {var_and_type.type_name}")

    # Clean file content before running the program again
    f = open('models\empty_model_new.xml', 'r+')
    f.truncate(0) # need '0' when using r+
    f.close()

    return method_data, abstract_task_data, var_and_types_list, types_set, predicate_dict, goal_orderings, goal_properties_list
