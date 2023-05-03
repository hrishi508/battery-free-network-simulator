import os
import sys
import json
import time
import threading
import numpy as np
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import QApplication

from utils import *
from simulator_gui import App
from command_line_gui import CMD_GUI
from battery_free_device import BatteryfreeDevice

from distributions import NormalDistribution
from distributions import ExponentialDistribution
from distributions import GaussianMixtureModel

model_map = {"norm": NormalDistribution, "exp": ExponentialDistribution, "gmm": GaussianMixtureModel}

n = np.random.randint(0, 1000)

nodes = {}

def simulate(args):
    start = time.time()

    global nodes

    pwr = {}
    dists = {}
    fp_rt_logs = {}
    events = {}
    threads = {}


    # if args is empty then return
    if not bool(args): return 
    
    now = str(datetime.now()).replace(" ", "__")[:-7]

    args["output_path"] = args["abs_path"] + "simulator1/logs/" + args["trace_file"].split('.')[0][4:] + "_dataset/"
    args["input_path"] = args["abs_path"] + "simulator1/data/" + args["trace_file"]
    args["opt_scale_path"] = args["abs_path"] + "simulator1/opt_scale.csv"

    # args["trace_file"] = None
    
    try: os.mkdir(args["output_path"])
    except: pass

    # print(args["output_path"])
    
    sim_time = args["sim_time"]
    args["output_dir"] = args["output_path"] + f"{sim_time}_mins_" + now

    try: os.mkdir(args["output_dir"])
    except: pass
    
    logs_file = args["output_dir"] + "/" + "metadata.txt"
    rt_logs_file = args["output_dir"] + "/" + "runtime_logs_"

    fp = open(logs_file, 'w')

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
    # node_names = [dr.nodes[0], dr.nodes[2]]
    # node_names = [dr.nodes[1], dr.nodes[3]]
    # print(node_names)

    for node in node_names:
        node_pwr = dr[int(node[-1])]
        node_dist_cls = model_map[dr.get_dist_model(node)]
        node_cls = BatteryfreeDevice(node, **args)
        node_fp_rt_logs = open(rt_logs_file + node[-1] + ".txt", 'w')
        event = threading.Event()

        pwr[node] = node_pwr
        dists[node] = node_dist_cls()
        nodes[node] = node_cls
        fp_rt_logs[node] = node_fp_rt_logs
        events[node] = event

    for node in nodes.values():
        node.setup(pwr, dists, nodes, fp_rt_logs, events)
        threads[node.name] = threading.Thread(target=node.switchOn)

    # barrier1 = threading.Barrier(2)
    # barrier2 = threading.Barrier(2)

    # nodes['node0'].setTarget("node2", barrier1)
    # nodes['node2'].setTarget("node0", barrier1)
    # nodes['node3'].setTarget("node4", barrier2)
    # nodes['node4'].setTarget("node3", barrier2)

    print('Simulation started!')
    
    for node in threads:
        threads[node].start()

    # time.sleep(10)

    # print("Targets Changed!!!")

    # barrier3 = threading.Barrier(2)
    # barrier4 = threading.Barrier(2)

    # nodes['node0'].setTarget("node3", barrier3)
    # nodes['node2'].setTarget("node4", barrier3)
    # nodes['node3'].setTarget("node0", barrier4)
    # nodes['node4'].setTarget("node2", barrier4)
    
    # for i in range(1, -1, -1): threads[i].start()
    for node in threads:
        threads[node].join()
        

    succ = []
    wakeup_count = []
    conn_ints_arr = []
    bonito_tchrgs_arr = []
    bonito_wakeup_count = []
    
    for node in nodes.values(): 
        succ.append(node.connection_success)
        wakeup_count.append(node.wakeup_cnt)
        conn_ints_arr.append(node.conn_ints)
        bonito_tchrgs_arr.append(node.bonito_tchrgs)
        bonito_wakeup_count.append(node.bonito_wakeup_cnt)

        
    for file_pointer in fp_rt_logs.values(): file_pointer.close()

    print(wakeup_count, bonito_wakeup_count, succ)
    
    # delay = max(np.median(conn_ints_arr[0]), np.median(conn_ints_arr[1]))
    # succ = max(succ)
    # n_wakeups = min(wakeup_count)
    # n_bonito_wakeups = min(bonito_wakeup_count)
    # success_rate = succ / n_bonito_wakeups

    # args['fp'] = None
    # args['fp_rt_logs'] = None
    # args['fp_conn'] = None
    # args['iteration'] = None
    
    # fp.write("---------------------\n")
    # fp.write("Simulation Parameters\n")
    # fp.write("---------------------\n")
    # fp.write(json.dumps(args))
    # fp.write(f"\nRandom Seed: {n if args['seed'] == -1 else args['seed']}")
    # fp.write("\n\n")
    # fp.write("-------\n")
    # fp.write("Results\n")
    # fp.write("-------\n")
    # fp.write(f"Total simulation time: {sim_time} mins\n")
    # fp.write(f"Total no. of wakeups: {n_wakeups}\n")
    # fp.write(f"No. of wakeups in 'Bonito' state: {n_bonito_wakeups}\n")
    # fp.write(f"No. of successful connections: {succ}\n")
    # fp.write(f"Success Rate: {success_rate*100:.2f}%\n")
    # fp.write(f"Delay: {delay:.3f}s\n")

    # fp.close()      

    # if args["create_plots"]:
    #     shell_file = str(Path.home()) + "/simulate_final.sh"
    #     shell_fp = open(shell_file, 'a')
    #     shell_fp.write(f"python3 plotter.py {args['output_dir']}")

    end = time.time()
    print(f"Total Runtime: {end - start} s")

if __name__ == "__main__":
    cmd_gui = CMD_GUI()

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
            app = QApplication(sys.argv)
            ex = App(nodes)
            app.exec_()

    except: pass

    t1.join()



