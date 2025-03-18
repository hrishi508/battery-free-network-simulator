# Battery-Free Network Simulator (HarvNet)

<p align="center">
<img width="651" alt="Screenshot 2025-03-18 at 7 34 29 AM" src="https://github.com/user-attachments/assets/8c6010e9-fdb9-4811-a812-1d67670f11df" />
</p>

[Simulation Demo](https://drive.google.com/file/d/1xVURLDKaRJLqKNzl3a4dBWNy6q_pbP3I/view?usp=sharing)

## Overview

The **Battery-Free Network Simulator** is a Python-based simulation framework designed to study computation across a network of intermittent, battery-free devices. This tool leverages the **Bonito protocol** to enable coordination of tasks across a dynamic network of energy-harvesting nodes. The simulator provides an interactive **Graphical User Interface (GUI)** for visualization and parameter tuning, along with programmatic control for detailed experimentation.

## Features

- **Bonito Protocol Implementation**: Translates the entire Bonito protocol into Python and validates it using real-world power traces.
- **Task Coordination**: Enables execution of distributed tasks across battery-free nodes.
- **Realistic Power Modeling**: Utilizes real-world power traces and various power models (Normal, Exponential, Gaussian Mixture) for accurate simulation.
- **Multi-Threaded Execution**: Simulates each node in parallel with independent energy profiles and behaviors.
- **Graphical & Command-Line Interfaces**: Provides a GUI for visualization and an interactive command-line interface (CLI) for control.
- **Customizable Simulation Parameters**: Users can modify node behavior, power models, connection strategies, and more.

## Repository Structure

```
📂 battery-free-network-simulator
├── 📂 Battery_Free_Device
│   ├── battery_free_device.py  # Core implementation of a battery-free node
├── 📂 utils
│   ├── distributions.py        # Implements power distributions (Normal, Exponential, GMM)
│   ├── simulator_gui.py        # GUI implementation for visualization
│   ├── command_line_gui.py     # CLI interface for simulation control
│   ├── utils.py                # General utility functions
│   ├── opt_scale.csv           # Optimization scale data
├── 📂 data
│   ├── power_trace_xxx.csv     # Real-world power traces used for simulation
├── 📂 logs
│   ├── runtime_logs_xxx.txt    # Logs of node activities during simulation
│   ├── metadata_xxx.txt        # Summary of simulation results
├── tasks.py                    # Defines tasks performed by each node
├── simulate.py                 # Main script to run the simulation
├── README.md                   # This file
```

## Installation & Setup

### Prerequisites

Ensure you have the following dependencies installed:

- Python 3.8+
- NumPy
- Matplotlib
- PyQt5

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/battery-free-network-simulator.git
   cd battery-free-network-simulator
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Simulation

To start the simulator, run:

```bash
python3 simulate.py
```

This launches the interactive CLI. If GUI mode is enabled, the graphical interface will open.

### Configuring Simulation Parameters

Modify `simulate.py` or use the command-line prompts to:

- Set power trace files
- Choose power models (Normal, Exponential, GMM)
- Enable/disable the GUI
- Adjust simulation duration

### Viewing Logs & Results

Simulation logs are stored in the `logs/` directory. Metadata files provide:

- Number of successful connections
- Wake-up counts
- Success rates
- Connection delays

Plots of connection intervals and charging times are saved in the output directory.

## Example Applications

- **Data Ferrying**: Nodes coordinate to transfer data intermittently across the network.
- **Network Awareness**: Nodes adapt their behavior based on power availability and network conditions.

## Future Work

- Extending the Bonito protocol to support more complex task coordination
- Integration with real-world hardware experiments
- Enhancing visualization tools for deeper analysis

## License

This project is licensed under the MIT License.

---

For any questions or suggestions, feel free to open an issue or contact [me](k.hrishi2010@gmail.com)

