# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 19:49:32 2020

@author: Mahip
"""

import sys
import pandas as pd

#Cycle Time
global adder_time, mult_time
adder_time = 2
mult_time = 10

#Reservation Stations
global reservation_station, reservation_counters, reservation_init, resource_status
reservation_station = {}
reservation_counters = {'LW': 5, 'SW': 5, 'ADD': 3, 'MULT': 2, 'BNE': 2}
reservation_init = {'inst': None, 'count': None, 'src1': None, 'src2': None, 'dest': None}
resource_status = {'ADD': False, 'MULT': False, 'LW': False, 'SW': False, 'BNE': False}

#Exec stations
global execution_station, counter, done_counter, instruction_list
execution_station = {}
counter = 0
done_counter = 0
instruction_list = {}

#File variables
global instruction_history, strings, filename
instruction_history = {}
strings = []
filename = " "
branch_taken = None

def setup(branch_taken):
    global reservation_station, counter, reservation_init, strings, execution_station, instruction_list
    if branch_taken == 1:
        strings = strings * 4
    elif branch_taken == 0:
        strings = strings
    else:
        print('Wrong value of branch')
        return -1
    for i in reservation_counters:
        for j in range(0, reservation_counters[i]):
            reservation_station[i, j] = reservation_init
    
    for string in strings:
        execution_station[counter, string] = {'done': None, 'issue': None, 'exec': None, 'mem': None, 'wb': None, 'commit': None}
        instruction_list[counter] = string
        counter += 1

def get_instruction_values(inst):
    inst_type = inst.split(' ')[0]
    if inst_type in 'LW':
        inst_dest = inst.split(' ')[1]
        inst_src1 = inst.split(' ')[2]
        inst_src2 = None
        return inst_type, inst_src1, inst_src2, inst_dest
    elif inst_type in ['ADD', 'SUB', 'MULT', 'DIV']:
        inst_dest = inst.split(' ')[1]
        inst_src1 = inst.split(' ')[2]
        inst_src2 = inst.split(' ')[3]
        return inst_type, inst_src1, inst_src2, inst_dest
    elif inst_type in ['SW', 'BNE']:
        inst_dest = None
        inst_src1 = inst.split(' ')[1]
        inst_src2 = inst.split(' ')[2]
        return inst_type, inst_src1, inst_src2, inst_dest
    else:
        print('Instruction not valid')
        return

def check_free_resources(inst, inst_type, count, dest, src1, src2):
    global reservation_station
    
    available_resources = None
    if inst_type in 'LW':
        resource = 'LW'
    elif inst_type in 'SW':
        resource = 'SW'
    elif inst_type in ['ADD', 'SUB']:
        resource = 'ADD'
    elif inst_type in ['MULT', 'DIV']:
        resource = 'MULT'
    else:
        resource = 'BNE'
    
    for i in range(reservation_counters[resource]):
        if reservation_station[resource, i]['inst'] == None:
            reservation_station[resource, i] = {'inst': inst, 'count': count, 'src1': src1, 'src2': src2, 'dest': dest}
            available_resources = 1
            return available_resources
            


def check_dependency(inst, count, dest, src1, src2, history):
    busy = None
    dependency = None
    
    for instruction in history:
        if history[instruction] == None or int(instruction) == int(count):
            continue
        
        inst_type, next_src1, next_src2, next_dest = get_instruction_values(history[instruction])
        
        if int(count) > int(instruction) and ((next_dest == src1 or next_dest == src2) or inst_type == 'BNE'):
            busy = 1
            dependency = history[instruction]
    
    return busy, dependency

def memory_inst(count, inst, clock, inst_type):
    global execution_station
    execution_station[count, inst]['wb'] = clock
    execution_station[count, inst]['done'] = 1
    return

def execution_inst(count, inst, clock, inst_type):
    global execution_station, resource_status
    execution_station[count, inst]['exec'] = clock
    if inst_type in ['LW', 'SW']:
        resource_status[inst_type] = True
    return

def issue_inst(count, inst, clock):
    global execution_station, instruction_history
    execution_station[count, inst]['issue'] = clock
    instruction_history[count] = inst
    return

def free_resource(count, inst_type, inst):
    global reservation_station
    if inst_type in 'LW':
        resource = 'LW'
    elif inst_type in 'SW':
        resource = 'SW'
    elif inst_type in ['ADD', 'SUB']:
        resource = 'ADD'
    elif inst_type in ['MULT', 'DIV']:
        resource = 'MULT'
    else:
        resource = 'BNE'
    
    for i in range(reservation_counters[resource]):
        if reservation_station[resource, i]['inst'] == inst and reservation_station[resource, i]['count'] == int(count):
            reservation_station[resource, i] = reservation_init
    
def tomasulo_simulator():
    global execution_station, counter, instruction_list, done_counter, resource_status
    
    clock = 1
    count_inst = 1
    
    while True:
        not_ready = 0
        free_res = []
        
        for count in range(count_inst):
            inst = instruction_list[count]
            if execution_station[count, inst]['done'] == 1:
                continue
            inst_type, inst_src1, inst_src2, inst_dest = get_instruction_values(inst)
            
            available_resources = None
            
            if execution_station[count, inst]['issue'] == None and not_ready == 0:
                available_resources = check_free_resources(inst, inst_type, count, inst_dest, inst_src1, inst_src2)
            
            if execution_station[count, inst]['issue'] == None and available_resources == None:
                not_ready = 1
                continue
            
            not_ready_conflict = None
            dependency = None
            
            if (inst_type in ['LW', 'SW'] and execution_station[count, inst]['mem'] == None) or (inst_type not in ['LW', 'SW'] and execution_station[count, inst]['exec'] == None):
                not_ready_conflict, dependency = check_dependency(inst, count, inst_dest, inst_src1, inst_src2, instruction_history)
            
            if resource_status['BNE'] == True:
                not_ready_conflict = 1
            
            if inst_type in 'LW':
                if execution_station[count, inst]['mem'] and not_ready_conflict == None:
                    memory_inst(count, inst, clock, 'ADD')
                    done_counter += 1
                    free_res.append([count, inst_type, inst])
                elif execution_station[count, inst]['exec'] and not_ready_conflict == None:
                    execution_station[count, inst]['mem'] = clock
                    resource_status['LW'] = False
                elif execution_station[count, inst]['issue'] and resource_status['BNE'] == False and resource_status['LW'] == False and not_ready_conflict == None:
                    execution_inst(count, inst, clock, inst_type)
                elif execution_station[count, inst]['issue'] == None:
                    issue_inst(count, inst, clock)
            
            elif inst_type in 'SW':
                if execution_station[count, inst]['exec'] and not_ready_conflict == None:
                    execution_station[count, inst]['mem'] = clock
                    resource_status['SW'] = False
                    execution_station[count, inst]['done'] = 1
                    done_counter += 1
                    free_res.append([count, inst_type, inst])
                elif execution_station[count, inst]['issue'] and resource_status['BNE'] == False and resource_status['SW'] == False and not_ready_conflict == None:
                    execution_inst(count, inst, clock, 'SW')
                elif execution_station[count, inst]['issue'] == None:
                    issue_inst(count, inst, clock)
            
            if inst_type in ['ADD', 'SUB']:
                if execution_station[count, inst]['exec'] and clock - execution_station[count, inst]['exec'] == adder_time:
                    memory_inst(count, inst, clock, 'ADD')
                    done_counter += 1
                    free_res.append([count, inst_type, inst])
                elif execution_station[count, inst]['issue'] and not_ready_conflict == None and clock >= resource_status['ADD']:
                    execution_inst(count, inst, clock, 'ADD')
                    resource_status['ADD'] = clock + adder_time
                elif execution_station[count, inst]['issue'] == None:
                    issue_inst(count, inst, clock)
            
            if inst_type in ['MULT', 'DIV']:
                if execution_station[count, inst]['exec'] and clock - execution_station[count, inst]['exec'] == mult_time:
                    memory_inst(count, inst, clock, 'MULT')
                    done_counter += 1
                    free_res.append([count, inst_type, inst])
                elif execution_station[count, inst]['issue'] and not_ready_conflict == None and clock >= resource_status['MULT']:
                    execution_inst(count, inst, clock, 'MULT')
                    resource_status['MULT'] = clock + mult_time
                elif execution_station[count, inst]['issue'] == None:
                    issue_inst(count, inst, clock)
            
            if inst_type in 'BNE':
                if execution_station[count, inst]['issue'] and not_ready_conflict == None:
                    execution_station[count, inst]['exec'] = clock
                    execution_station[count, inst]['done'] = 1
                    done_counter += 1
                    free_res.append([count, inst_type, inst])
                    resource_status['BNE'] = True
                
                if execution_station[count, inst]['issue'] == None:
                    issue_inst(count, inst, clock)
        clock += 1
        
        if free_res:
            for i in range(len(free_res)):
                count = free_res[i][0]
                free_resource(free_res[i][0], free_res[i][1], free_res[i][2])
                instruction_history[int(count)] = None
        
        resource_status['BNE'] = False
        free_res = []
        
        if count_inst < counter and not_ready == 0:
            count_inst += 1
        
        if counter == done_counter:
            break
        
        if clock > 1000:
            print('Simulation too big')
            return
    
    last_value = 1
    keys = ['wb', 'mem', 'exec']
    
    for count in instruction_list.keys():
        for k in keys:
            inst = instruction_list[count]
            if execution_station[count, inst][k]:
                if last_value >= execution_station[count, inst][k] + 1:
                    execution_station[count, inst]['commit'] = last_value + 1
                    last_value = execution_station[count, inst]['commit']
                else:
                    execution_station[count, inst]['commit'] = execution_station[count, inst][k] + 1
                    last_value = execution_station[count, inst]['commit']
                break
        

def print_output():
    global execution_station
    
    data = pd.DataFrame.from_dict(execution_station, orient='index')
    data.columns = ['Done', 'Issue', 'Execution', 'Memory', 'Write Back', 'Commit']
    data.drop(['Done'], axis=1, inplace=True)
    data.fillna('-', inplace=True)
    print(data)    
       
def main():
    global filename, adder_time, mult_time, reservation_counters, reservation_station, reservation_init, strings, counter, instruction_list
    
    filename = sys.argv[1]
    adder_time = int(sys.argv[2])
    mult_time = int(sys.argv[3])
    load_buffers = int(sys.argv[4])
    adder_slots = int(sys.argv[5])
    mult_slots = int(sys.argv[6])
    branch_slots = int(sys.argv[7])
    branch_taken = int(sys.argv[8])   
    with open(filename) as f:
        for line in f:
            strings.append(line.strip('\n'))
    
    reservation_counters['LW'] = reservation_counters['SW'] = load_buffers
    reservation_counters['ADD'] = adder_slots
    reservation_counters['MULT'] = mult_slots
    reservation_counters['BNE'] = branch_slots
    
    
    a = setup(branch_taken)
    if a == -1:
        return
    tomasulo_simulator()
    print_output()
    
if __name__ == '__main__':
    main()