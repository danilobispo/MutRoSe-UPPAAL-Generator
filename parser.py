from operator import index
from pprint import pprint
from typing import List
import utils

# Constants used throughout parsing
const_method_name = "Method name:"
const_precondition = "__method_precondition_"
const_predicate_arg = "_argument_"
const_task_effect = "__task_effect"


class FileMethodData:
    def __init__(self, name, order, effects, preconditions):
        self.method_name = name
        self.order = order
        self.effects = effects
        self.preconditions = preconditions
    def __repr__(self) -> str:
        return f'MethodData: ("{self.method_name}","{self.order}", "{self.effects}", "{self.preconditions}")'


def parse_method_name(method_line):
    name = method_line.split(const_method_name)[1]
    # Debug
    # print(name)
    return name

def parse_precondition(line_prec):
    # Let's use destructuring to make the code a little cleaner
    predicate_name, predicate_type = line_prec.split(const_predicate_arg)[0], line_prec.split(const_predicate_arg)[1]
    predicate_name, predicate_value = predicate_name.split("_")[0], predicate_name.split("_")[1]
    # debug
    # print("precondition predicate name:", predicate_name)
    # print("precondition predicate value:", predicate_value)
    # print("precondition predicate type: ", predicate_type)
    return utils.Precondition(name=predicate_name, type=predicate_type, value=predicate_value)


def parse_effect(line_prec):
    # Let's use destructuring to make the code a little cleaner
    predicate_name, predicate_value = line_prec.split("_")[0], line_prec.split("_")[1]
    predicate_type = line_prec.split(const_predicate_arg)[1]
    # debug
    # print("effect predicate name:", predicate_name)
    # print("effect predicate value:", predicate_value)
    # print("effect predicate type: ", predicate_type)
    return utils.Effect(name=predicate_name, type=predicate_type, value=predicate_value)



def parse_method_ordering(method_name:str, ordering_line: str):
    # First we split the line by whitespaces, which is the separator used for some things
    print("Method name:", method_name)
    words = ordering_line.split(" ")
    prec_list = []
    effect_list = []
    task_method_list = []
    for i in range(len(words)):
        # precondition region
        # Skip this line because we have already parsed the precondition
        if(words[i].find(const_predicate_arg) >= 0 or words[i] == "\n" ): 
            print("Ignored line:", words[i])
            continue
        # An ordering always starts with a precondition method, so we check if
        # 1) It exists and 
        # 2) if it does we parse the value, the type and its name
        if(words[i].startswith(const_precondition)):
            i_copy = i
            # Debug 
            # print("Prec print:", words[i+1])
            while(words[i_copy+1].find(const_predicate_arg) >= 0):
                prec = parse_precondition(words[i_copy+1])
                prec.tied_to = method_name
                prec_list.append(prec)
                i_copy = i_copy + 1
            # I still have to send that precondition somewhere
        # end precondition region

        # effect region
        elif(words[i].startswith(const_task_effect)):
            i_copy = i
            while(words[i_copy+1].find(const_predicate_arg) >= 0):
                effect = parse_effect(words[i_copy+1])
                effect.tied_to = task_method_list[-1]
                effect_list.append(effect)
                i_copy = i_copy + 1
            # I still have to send that precondition somewhere
        # end effect region

        # Now they're definitely tasks or methods. This also represents the order of the tasks
        else:
            task_method_list.append(words[i])
    print("Task order: ", task_method_list)
    for preco in prec_list:
        print("Precondition:", preco.name, "\n\tType:", preco.type, "\n\tvalue: ", preco.value)
    for effect in effect_list:
        print("Effect:", effect.name, "\n\tType:", effect.type, "\n\tvalue: ", effect.value, "\n\tTied to: ", effect.tied_to)
    return prec_list, effect_list, task_method_list



def open_file(filename) -> List[FileMethodData]:
    with open(filename) as file:
        # data = list(file.readlines())
        parsed_data  = []
        
        while True:
            method_name_line = file.readline()
            method_ordering_line = file.readline()
            if method_ordering_line == "" or method_name_line == "": 
                break
            else:
                method_name_parsed=parse_method_name(method_line=method_name_line)
                preconditions, effects, order = parse_method_ordering(
                            method_name=method_name_parsed, 
                            ordering_line=method_ordering_line)
                parsed_data.append(FileMethodData(name=method_name_parsed, 
                preconditions= preconditions, effects= effects, order=order))
            if not method_ordering_line: 
                break  # EOF/
    # Debug
    for obj in parsed_data:
        print(repr(obj))
    return parsed_data

method_ordering_data = open_file("method_orderings.txt")
    
# create a data structure where first line parsed is the name of the method and the second is the sequence
# for data in method_ordering_data:
    # print(data.)
