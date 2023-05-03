import os
import sys
import time
import json
import threading
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication

from utils.utils import *
from utils.simulator_gui import App
from utils.command_line_gui import CMD_GUI
from Battery_Free_Device.battery_free_device import BatteryfreeDevice

from utils.distributions import NormalDistribution
from utils.distributions import ExponentialDistribution
from utils.distributions import GaussianMixtureModel

lock = threading.Lock() # Semaphore for reading and updating data used by various threads

model_map = {"norm": NormalDistribution, "exp": ExponentialDistribution, "gmm": GaussianMixtureModel}

# Random Seed
n = np.random.randint(0, 1000)

# Global dictionary containing the 'BatteryfreeDevice' objects of all the Battery-Free devices in the simulation environment 
nodes = {}

def simulate(args):
    """Master thread of the simulation environment.

    1. Defines all the global variables.
    2. Creates the log folder and files and stores the file pointers.
    3. Reads the data from the trace file, creates 'BatteryfreeDevice' objects for all the nodes and initializes all the variables.
    4. Assigns a separate thread for each node.
    5. Starts all the threads simultaneously and waits for them to finish execution.
    6. Collects the results and logs them in a master log file.
    7. Generates plots based on the results.

    Args:
        args (dict): dictionary containing all the input arguments taken from the command line GUI
    """
    start = time.time()

    global nodes

    pwr = {}
    dists = {}
    fp_rt_logs = {}
    events = {}
    threads = {} 
    
    now = str(datetime.now()).replace(" ", "__")[:-7]

    args["output_path"] = args["abs_path"] + "battery-free-network-simulator/logs/" + args["trace_file"].split('.')[0][4:] + "_dataset/"
    args["input_path"] = args["abs_path"] + "battery-free-network-simulator/data/" + args["trace_file"]
    args["opt_scale_path"] = args["abs_path"] + "battery-free-network-simulator/utils/opt_scale.csv"
    
    try: os.mkdir(args["output_path"])
    except: pass

    sim_time = args["sim_time"]
    args["output_dir"] = args["output_path"] + f"{sim_time}_mins_" + now

    try: os.mkdir(args["output_dir"])
    except: pass
    
    metadata_file = args["output_dir"] + "/" + "metadata_"
    rt_logs_file = args["output_dir"] + "/" + "runtime_logs_"

    dr = DataReader(args['input_path'])

    times_len = min(int(60 * args['sim_time'] * 1e5), int(36e7))

    # Sampling interval is constant
    Ts = 1e-5
    iteration = [None]
    
    args['Ts'] = Ts
    args['iteration'] = iteration
    args['times_len'] = times_len
    args['start_time'] = start

    node_names = dr.nodes
    # node_names = [dr.nodes[1], dr.nodes[3]]

    for node in node_names:
        node_pwr = dr[int(node[-1])]
        node_dist_cls = model_map[dr.get_dist_model(node)]
        node_cls = BatteryfreeDevice(node, **args)
        node_fp_rt_logs = open(rt_logs_file + f"node{node[-1]}.txt", 'w')
        event = threading.Event()

        pwr[node] = node_pwr
        dists[node] = node_dist_cls()
        nodes[node] = node_cls
        fp_rt_logs[node] = node_fp_rt_logs
        events[node] = event

    for node in nodes.values():
        node.setup(pwr, dists, nodes, fp_rt_logs, events)
        threads[node.name] = threading.Thread(target=node.switchOn)

    ''' Example to Set targets internally via master thread

    barrier1 = threading.Barrier(2)
    barrier2 = threading.Barrier(2)

    nodes['node0'].setTarget("node2", barrier1)
    nodes['node2'].setTarget("node0", barrier1)
    nodes['node3'].setTarget("node4", barrier2)
    nodes['node4'].setTarget("node3", barrier2)
    '''

    print('Simulation started!')
    
    for thread in threads.values():
        thread.start()

    ''' Example to Update targets internally via master thread

    time.sleep(10)

    barrier3 = threading.Barrier(2)
    barrier4 = threading.Barrier(2)

    nodes['node0'].setTarget("node3", barrier3)
    nodes['node2'].setTarget("node4", barrier3)
    nodes['node3'].setTarget("node0", barrier4)
    nodes['node4'].setTarget("node2", barrier4)
    '''

    for thread in threads.values():        
        thread.join()
        
    for file_pointer in fp_rt_logs.values(): file_pointer.close()
    args['fp'] = None
    args['fp_rt_logs'] = None
    args['fp_conn'] = None
    args['iteration'] = None

    succ = {}
    wakeup_count = {}
    conn_ints_arr = {}
    bonito_tchrgs_arr = {}
    bonito_wakeup_count = {}
    
    for node in nodes.values(): 
        succ[node.name] = node.connection_success
        wakeup_count[node.name] = node.wakeup_cnt
        conn_ints_arr[node.name] = node.conn_ints
        bonito_tchrgs_arr[node.name] = node.bonito_tchrgs
        bonito_wakeup_count[node.name] = node.bonito_wakeup_cnt


    for name in node_names:
        fp = open(metadata_file + f"{name}.txt", 'w')

        node_succ = succ[name]
        node_wakeup_count = wakeup_count[name]
        node_conn_ints_arr = conn_ints_arr[name]
        node_bonito_tchrgs_arr = bonito_tchrgs_arr[name]
        node_bonito_wakeup_count = bonito_wakeup_count[name]

        delay = np.median(node_conn_ints_arr)
        n_wakeups = node_wakeup_count
        n_bonito_wakeups = node_bonito_wakeup_count
        try: success_rate = node_succ / n_bonito_wakeups
        except: success_rate = "Undefined"

        
        fp.write("---------------------\n")
        fp.write("Simulation Parameters\n")
        fp.write("---------------------\n")
        # fp.write(json.dumps(args))
        fp.write(f"\nRandom Seed: {n if args['seed'] == -1 else args['seed']}")
        fp.write("\n\n")
        fp.write("-------\n")
        fp.write("Results\n")
        fp.write("-------\n")
        fp.write(f"Total simulation time: {sim_time} mins\n")
        fp.write(f"Total no. of wakeups: {n_wakeups}\n")
        fp.write(f"No. of wakeups in 'Bonito' state: {n_bonito_wakeups}\n")
        fp.write(f"No. of successful connections: {node_succ}\n")
        if success_rate == "Undefined": fp.write(f"Success Rate: {success_rate}%\n")
        else: fp.write(f"Success Rate: {success_rate*100:.2f}%\n")
        fp.write(f"Delay: {delay:.3f}s\n")

        fp.close()      

        if args["create_plots"]:
            ax = args["ax"]
            ax.plot(node_conn_ints_arr, color="green", label="connection interval bonito")
            ax.plot(node_bonito_tchrgs_arr, color="red", label="charging time")
            ax.legend()
            plt.savefig(args["output_dir"] + f"/{name}_plot.png")
            ax.get_legend().remove()
            plt.cla()

    end = time.time()
    print(f"Total Runtime: {end - start} s")

if __name__ == "__main__":
    while True:
        cmd_gui = CMD_GUI()

        # if args is empty then quit
        if not bool(cmd_gui.args): quit()

        fig, ax = plt.subplots()
        cmd_gui.args["quit"] = False
        cmd_gui.args["ax"] = ax
        

        try:
            # Set the random seed before performing any computation
            if cmd_gui.args["seed"] != -1: np.random.seed(cmd_gui.args["seed"])
            else: 
                cmd_gui.args["seed"] = n
                np.random.seed(n)
                print(f"Seed: {n}")
        except: pass
                
        t1 = threading.Thread(target=simulate, args=(cmd_gui.args,))
        t1.start()


        time.sleep(1)
        
        try:
            if cmd_gui.args["show_GUI"]:
                if not QApplication.instance():
                    app = QApplication(sys.argv)
                else:
                    app = QApplication.instance()

                ex = App(nodes)
                app.exec_()
                for node in nodes.values():
                    lock.acquire()
                    node.iteration = cmd_gui.args["times_len"]
                    lock.release()
        except: pass

        t1.join()


