from ast import parse
import re
from typing import List
import utils
import uppaal_utils as upu
import copy
import uppaalpy

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



def open_and_parse_method_file(filename) -> List[utils.MethodData]:
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

method_data: List[utils.MethodData] = open_and_parse_method_file("method_orderings.txt")
abstract_task_data = open_and_parse_abstract_tasks_file("node_data.txt")
var_and_types_list, types_set= open_and_parse_types_and_variables_file("types_and_variables_data.txt")
predicate_dict = create_predicate_vars_for_uppaal(method_data=method_data)
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

#UPPAAL Region
# First step, create a NTA with template
# context = uppaalpy.Context()
nta_partial = uppaalpy.NTA.from_xml(path="models\empty_model.xml")
nta_partial, var_and_types_with_predicates = upu.generate_declaration_for_nta(nta_partial, predicates=predicate_dict, var_and_types_list=var_and_types_list, set_of_types=types_set)
var_and_types_with_predicates =  upu.link_variables_with_predicates_and_types(var_and_types_list_with_predicates=var_and_types_with_predicates)
# for var_and_type in var_and_types_with_predicates:
#     print(f"{var_and_type.var_name}")
#     print(f"{var_and_type.predicates_name_list}")

nta_partial = upu.generate_uppaal_methods_templates(method_data=method_data, nta=nta_partial, node_data=abstract_task_data, var_and_types_list_in_predicates=var_and_types_with_predicates)
nta_partial = upu.generate_default_verifiable_queries(nta=nta_partial)
nta_partial = upu.generate_declarations_of_variables_in_nta(nta=nta_partial, variables_set=set(var_and_types_with_predicates))
nta_partial = upu.generate_boolean_declarations_for_capabilities(method_data=method_data, nta=nta_partial)
nta_partial = upu.generate_system_declarations(nta=nta_partial, method_data=method_data)
# Add template example below
# upu.add_template(nta= nta_partial, template_name="task_1", template_to_copy=nta.templates[0], parameters=None, declaration=None)

# Debug
# for tp in nta_partial.templates:
#     upu.print_nodes_from_template(tp)

nta_partial.to_file(path='models\empty_model_new.xml')

#End UPPAAL Region
