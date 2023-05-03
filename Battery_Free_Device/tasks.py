'''
Define tasks to be performed by each node here.
The number of functions to be defined is equal to the no. of nodes existing in the power trace.
The argument of the task function of a node is the 'BatteryfreeDevice' of that node itself. This is done so as to enable easy access the data being generated or stored by that node.
'''

def task0(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

def task1(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

def task2(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

def task3(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

def task4(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

def task5(curr_node):
    curr_node.fp_rt_logs.write("Task Completed!\n")
    return

task_mapping = {
                "node0": task0, 
                "node1": task1, 
                "node2": task2, 
                "node3": task3, 
                "node4": task4, 
                "node5": task5 
                }

