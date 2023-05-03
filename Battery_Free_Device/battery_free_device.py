import sys
import path
import time
import threading

# directory = path.Path(__file__).abspath() 
# sys.path.append(directory.parent.parent)

from utils.utils import *
from utils.find import Find
from utils.distributions import inverse_joint_cdf

from Battery_Free_Device.tasks import task_mapping

class BatteryfreeDevice(object):
    """Simple simulation model of a battery-free device.

    Args:
        name (str):               name of the node
        capacity (float):           energy storage capacity (in farad)
        v_on (float):               turn-on threshold (in volts)
        v_off (float):              turn-off threshold (in volts)
        v_max (float):              maximum voltage before converter goes into overvoltage protection mode (in volts)
        Ts (float):                 length of time step of the simulation (in secs)
        slot_length (float):        'Find' - slot length value (in secs)
        opt_scale_path (str):     path to the opt_sacle.csv file containing optimized scale values for 'Find'
        max_offset (float):         length of the listening window of a node (after packet transmission for establishing connection with another node) (in secs)
        target_probability (float): 'Bonito' - degree of accuracy required in the connection intervals generated
        times_len (int):          length of the power trace array

    """

    def __init__(self, name, **kwargs):
        # Constants
        self._capacity = kwargs['capacity']
        self._von = kwargs['von']
        self._voff = kwargs['voff']
        self._vmax = kwargs['vmax']

        self.energy_per_cycle = 0.5 * self._capacity * (self._von**2 - self._voff**2)       # Energy Threshold for node to wake up
        self.max_energy_per_cycle = 0.5 * self._capacity * (self._vmax**2 - self._voff**2)  # Max Energy limit
        
        self.Ts = kwargs['Ts']
        self.name = name
        self.slot_length = kwargs['slot_length']
        self.opt_scale_path = kwargs['opt_scale_path']
        self.max_offset = kwargs['max_offset']
        # self._wait_slots = secs_to_slots(self.max_offset, self.Ts) * 10
        self._wait_slots = secs_to_slots(self.max_offset, self.Ts)  # Converting wait time in secs to simulation time steps (or slots)
        self.target_probability = kwargs['target_probability']
        self.times_len = kwargs['times_len']
        self.lock = threading.Lock()

        # State Variables
        self.currState = "Find"     # Current state of the node - Either 'Find' or 'Bonito'
        self.iteration = 0          # Current iteration the node is in (while iterating on the power array to simulation incoming power)
        self.prev_tchrg = 0         # Latest charging time of the node in secs.
        self.curr_conn_no = 0       # Variable to keep track of Bonito connections in the node logs
        self.target_is_set = False  # Keeps tarck of whether the current node has a target defined

        # Metadata
        self.wakeup_cnt = 0         # No. of times the current node wakes up
        self.bonito_wakeup_cnt = 0  # No. of times the current node wakes up in 'Bonito' state
        self.connection_success = 0 # No. of successful connections
        self.conn_ints = [0]        # List of connection intervals generated
        self.bonito_tchrgs = []     # Charging time corresponding to the generated connection interval (i.e. time taken by the current node to charge when the corresponding connection interval time was generated)

        # Variables modified by external environment
        self.target_name = None     # Name of the target node
        self.target_node = None     # 'BatteryfreeDevice' object of the target node
        self.target_dist = None     # Charging time distribution of the target node
        self.barrier = None         # threading.Barrier object shared between the current and target node

    def setup(self, pwr, dists, nodes, fp_rt_logs, events):
        """Store global variables and log file pointer.

        Args:
            pwr (dict):             Dictionary of power array of all nodes             
            dists (dict):           Dictionary of charging time distribution of all nodes
            nodes (dict):           Dictionary of 'BatteryfreeDevice' objects assciated with all nodes in the environment
            fp_rt_logs (pointer):   Pointer of the log file of the current node
            events (dict):          Dictionary of the awake status (event - boolean variable) of all nodes
        """

        # Constants
        self.pwr = pwr[self.name]               # power array of the current node
        self.dist = dists[self.name]            # charging time distribution of the current node
        self.fp_rt_logs = fp_rt_logs[self.name]
        self.awake = events[self.name]          # awake status of the current node

        # Global quantities
        self.dists = dists
        self.nodes = nodes
        self.events = events

        self.reset()

        print(f'{self.name} setup Done!')

    def setTarget(self, target_name, barrier):
        """Set the target for the current node to establish Bonito connections with. Semaphores are used here since values that may be modified by other threads are being accessed.

        Args:
            target_name (string): Name of the target node
            barrier (threading.Barrier): A synchronization obejct provided by the threading module used here as a means of simulating the event of a connection being established between two nodes (See threading.Barrier docs for more reference) 
        """

        self.curr_conn_no = 0

        self.lock.acquire()

        try:
            self.target_node.target_is_set = False
            self.target_node.target_name = None
            self.target_node.target_node = None
        except: pass 

        self.target_name = target_name
        self.target_node = self.nodes[target_name]
        self.target_dist = self.dists[target_name]
        self.target_awake = self.events[target_name]

        # Common Barrier for current and target Node
        self.barrier = barrier

        self.lock.release()

    def task(self):
        """Task to be performed by the node. This will vary with the specific use case. All tasks must be defined in the tasks.py file. Calls the task for the current node from the task.py file passing itself as the argument.
        """

        task_mapping.get(self.name)(self)

    @property
    def charged(self):
        """Compares the current energy stored in the node with the threshold to wake up.

        Returns:
            (boolean): Charging status of the node (whether above or below threshold)
        """

        return self.estored >= self.energy_per_cycle
    
    @property
    def max_charged(self):
        """Compares the current energy stored in the node with the max threshold to prevent further charging.

        Returns:
            (boolean): Charging status of the node (whether max limit reached)
        """

        return self.estored >= self.max_energy_per_cycle
    
    def find(self):
        """Defines the FIND protocol. This function is executed when the node is in the 'Find' state.

        1. Sets the node to sleep till wake up energy threshold is reached.
        2. Checks if the target node is awake - If Yes, sets the state to 'Bonito' and returns.
        3. If No, samples random sleep time according to Find.
        4. Sets the node to sleep for sampled amount of time.
        5. Waits for (max offset) time for the target node to wake up.
        6. If the 'wait' function returns 'True', sets the state to 'Bonito' and returns.
        7. Else, runs the dedicated task function, drains out energy till the turn-off threshold is reached and then resets.  
        """

        # Sleep till wake up energy threshold is reached
        self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} set to sleep for charging\n")            
        self.sleep()

        # Check if the target node is awake
        if self.target_awake.is_set():
            self.currState = "Bonito"
            self.bonito_wakeup_cnt += 1
            return

        # If target node is not awake, sample random sleep time according to Find
        t_chr_slots = secs_to_slots(self.prev_tchrg, self.slot_length)
        sleep_time_slots = Find(self.opt_scale_path, t_chr_slots)
        sleep_time_secs = slots_to_secs(sleep_time_slots, self.slot_length, self.Ts) * 10 
        # sleep_time_secs = slots_to_secs(sleep_time_slots, self.slot_length, self.Ts)
        sleep_time_slots = secs_to_slots(sleep_time_secs, self.slot_length)

        # Sleep for sampled amount of random sleep time
        self._sleep_till_iteration = self.iteration + sleep_time_slots
        self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} set to sleep by Find till {self._sleep_till_iteration} ({sleep_time_secs: .6f}s)\n")
        self.sleep()

        # Wait for (max offset) time for the target node to wake up
        self._wait_till_iteration = self.iteration + self._wait_slots
        self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} waiting for Find discovery till {self._wait_till_iteration} ({self.max_offset}s)\n")

        # Waiting
        if self.wait():
            self.currState = "Bonito"
            self.bonito_wakeup_cnt += 1
            return 

        # Target node did not wake up within the time limit. The node runs its dedicated function, drains out energy to the turn-off threshold and then resets
        self.task()
        self.reset()
        self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} reset by Find\n")

    
    def bonito(self):
        """Defines the BONITO protocol. This function is executed when the node is in the 'Bonito' state.

        1. Waits for (max offset) time for the target node to wake up.
        2. If the 'wait' function returns 'True', tries to establish connection with the target node (Runs the Bonito logic).
        3. If the 'wait function returns 'False' or the connection failed, sets the state to 'Find', runs the dedicated task function, drains out energy till the turn-off threshold is reached and then resets. 
        """

        # Wait for (max offset) time for the target node to wake up
        self._wait_till_iteration = self.iteration + self._wait_slots
        self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} waiting for Bonito discovery till {self._wait_till_iteration} ({self.max_offset}s)\n")

        # Waiting
        if self.wait():
            try:
                # Barrier placed here so that this current node code execution will only proceed with the Bonito connection code if the target node code execution reaches this point of code too (an abstract way of simulating the establishing of connection). Else the connection will fail and the state will go back to Find.
                self.barrier.wait(1) # The max wait time for the barrier is 1 sec here after which it will throw an BrokenBarrierError.
                # self.barrier.wait(0.1)
                self.barrier.reset()

                # If execution reaches this point, that means current node has established connection with target node successfully (in any other case it will go into the except block)
                # self.fp_rt_logs.write(f"{self.target_awake.is_set()}\n")
                self.curr_conn_no += 1
                self.connection_success += 1
                self.fp_rt_logs.write(f"Iteration {self.iteration} :{self.curr_conn_no} - Connected to {self.target_name}!\n")

                # Compute the next connection interval
                conn_int = inverse_joint_cdf((self.dist, self.target_dist), self.target_probability)
                self.conn_ints.append(conn_int)
                self.bonito_tchrgs.append(self.prev_tchrg)
                
                # The node runs its dedicated function, drains out energy to the turn-off threshold and then resets
                self.task()
                self.reset()

                # Sleep for connection interval amount of time
                self._sleep_till_iteration = self.iteration + secs_to_slots(conn_int, self.Ts)
                self.fp_rt_logs.write(f"Iteration {self.iteration}: {self.name} reset and set to sleep by Bonito till {self._sleep_till_iteration} ({conn_int}s)\n")
                self.sleep()
                
                return # Return placed here to indicate that the node sucessfully established connection with the target node

            except:
                # Nodes discovered each other but could not establish connnection
                self.barrier.reset() 
                self.fp_rt_logs.write(f"Barrier Broken Error\n")

        # If current node code execution reaches this point means that connection could not be established. Switch state to Find
        self.currState = "Find"

        # The node runs its dedicated function, drains out energy to the turn-off threshold and then resets
        self.task()
        self.reset()
        self.fp_rt_logs.write(f"Iteration {self.iteration}: Connection with {self.target_name} lost! {self.name} reset by Bonito\n")

    def sleep(self):
        """Defines the sleep activity cycle for the node

        1. Sets the awake status of current node to False.
        2. Goes into a low power sleep state till the sleep conditions are met (and harvests energy meanwhile).
        3. Wakes up after the sleep conditions are satisfied.
        4. Logs latest charging time details
        5. Sets the awake status of current node to True.
        """

        self.iteration += 1
        self.awake.clear() # Set the awake status of current node to False

        # Specifies the sleeping condition according to various scenarios
        while (self.iteration < self.times_len) and ((not self.charged) or (self.iteration < self._sleep_till_iteration)):
            # Harvest energy from incoming power
            self.harvest(self.Ts * self.pwr[self.iteration], self.Ts)
            self.iteration += 1

        # Node woke up
        woke_up_msg = f"Iteration {self.iteration}: {self.name} woke up!"

        if not self.latest_tchrg_flag:
            self.fp_rt_logs.write(woke_up_msg + f" Charging time: {self.latest_tchrg: .6f}s\n")

            self.wakeup_cnt += 1
            if self.currState == "Bonito": self.bonito_wakeup_cnt += 1
            self.dist.sgd_update(self.latest_tchrg)
            self.prev_tchrg = self.latest_tchrg
            self.latest_tchrg_flag = True

        else:
            self.fp_rt_logs.write(woke_up_msg + "\n")

        self.awake.set() # Set the awake status of current node to True

    def wait(self):
        """Defines the waiting for discovery cycle for the node

        1. Waits till either wait time elapses or target node is discovered. Harvested energy is immediately consumed while waiting.
        2. If target node is discovered, return True.
        3. Else, return False.

        Returns:
            (boolean): Whether the current node discovered the target node (Yes - True, No - False)
        """
        
        currState = self.currState

        # Wait till either wait time elapses or target node is discovered
        while (not self.target_awake.is_set()) and self.iteration <= self._wait_till_iteration:
            self.fp_rt_logs.write(f"{currState} - Waiting for Discovery\n")
            self.iteration += 1

        # self.fp_rt_logs.write(f"{self.target_awake.is_set()}\n")

        if self.iteration <= self._wait_till_iteration: return True # Target node found
        return False # Target node not found


    def harvest(self, energy, duration):
        """Charges the capacitor by given amount of energy, in the given duration of time.

        Args:
            energy (float): Amount of energy harvested
            duration (float): Time taken for that amount of energy to be harvested
        """
        if not self.max_charged:
            self.estored += energy
            
        if not self.charged:
            self.latest_tchrg += duration

    def reset(self):
        """Deplete all energy of the node.
        Every device starts off with min energy corresponding to turn off voltage and every reset also brings it back to turn off voltage (voltage of the device never goes below turn off voltage). So we do not add that amount of energy in the self.estored and consider it as starting from 0 instead of starting from self.estored = 0.5 * self._capacity * (self._voff**2)
        """

        self.latest_tchrg = 0
        self.latest_tchrg_flag = False
        self.waiting = False
        self._sleep_till_iteration = 0
        self._wait_till_iteration = 0
        self.estored = 0
        self.awake.clear() # Set the awake status of current node to False
    
    def switchOn(self):
        """Heart of the node. This is the function that gives this node life. Called by a dedicated thread for this node from the simulator code to enable parallel execution of all the nodes in the given power trace file.
        """

        # try:
        #     self.barrier.wait(10)
        #     self.barrier.reset()
        
        # except: pass

        self.fp_rt_logs.write(f'{self.name} started at {time.time(): .6f}!\n')

        while self.iteration < self.times_len:
            if not self.target_is_set:
                # If target node is not set yet, stall the iteration on the power trace till there is a target set.
                self.reset()
                time.sleep(1)
                        
            elif self.currState == "Find":
                self.find()

            else:
                self.bonito()

        # Iteration on the power trace completed. Marks the end of simulation for the current node. Reset it and change state to Find for GUI purposes.
        self.reset()
        self.currState = "Done"
        print(f"{self.name} done at {time.time()}")