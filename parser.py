from typing import List
import utils

# Constants used throughout parsing
const_method_name = "Method name:"
const_precondition = "__method_precondition_"
const_predicate_arg = "_argument_"


class FileMethodData:
    def __init__(self, name, order):
        self.method_name = name
        self.order = order

def parse_method_name(method_line):
    name = method_line.split(const_method_name)[1]
    # Debug
    # print(name)
    return name

def parse_precondition(line_prec):
    # Let's use destructuring to make the code a little cleaner
    predicate_name, predicate_type = line_prec.split(const_predicate_arg)[0], line_prec.split(const_predicate_arg)[1]
    
    predicate_name, predicate_value = predicate_name.split("_")[0], predicate_name.split("_")[1]
    print("predicate name:", predicate_name)
    print("predicate value:", predicate_value)
    print("predicate type: ", predicate_type)
    return utils.Precondition(name=predicate_name, type=predicate_type, value=predicate_value)



def parse_method_ordering(method_name:str, ordering_line: str):
    # First we split the line by whitespaces, which is the separator used for some things
    words = ordering_line.split(" ")
    for i in range(len(words)):
        # An ordering always starts with a precondition method, so we check if
        # 1) It exists and if it does we parse the condition and the
        if(words[i].startswith(const_precondition)):
            # Debug 
            # print("Prec print:", words[i+1])
            prec = parse_precondition(words[i+1])
            # This may change later
            prec.tied_to = method_name
        print(words[i])
    return words



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
                parsed_data.append(
                    FileMethodData(
                        name=method_name_parsed, 
                        order=parse_method_ordering(
                            method_name=method_name_parsed, 
                            ordering_line=method_ordering_line)))
            if not method_ordering_line: 
                break  # EOF/
    return parsed_data
    # Debug
    for line in data:
        print(line)

method_ordering_data = open_file("method_orderings.txt")
    
# create a data structure where first line parsed is the name of the method and the second is the sequence
# for data in method_ordering_data:
    # print(data.)
