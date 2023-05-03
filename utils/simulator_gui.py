import sys
import time
import threading

from command_line_gui import CMD_GUI

from PyQt5.QtCore import Qt, QObject, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QIcon, QPainter, QBrush, QPen, QColor

from battery_free_device import BatteryfreeDevice

lock = threading.Lock()

class Worker(QObject):
    def __init__(self, battery_widgets):
        super().__init__()
        self.battery_widgets = battery_widgets

    def run(self):
        while True:
            if not self.battery_widgets[0].app.pause_flag:
                self.battery_widgets[0].update_connections()

                for widget in self.battery_widgets:
                    widget.update_label()
                    widget.update_battery_level()

            time.sleep(0.1)

class BatteryWidget(QWidget):
    def __init__(self, coordinates, node, label, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(80, 120)

        self.app = app
        self.node = node
        self.label = label
        self.battery_level = 0
        self.max_battery_capacity = self.node.max_energy_per_cycle
        self.turn_on_threshold_level = int((self.node.energy_per_cycle/self.max_battery_capacity) * 100)

    @property
    def battery_level_percentage(self):
        return min(int((self.node.estored/self.max_battery_capacity) * 100), 100)
    
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        # Draw the battery casing
        qp.setPen(QPen(Qt.black, 3, Qt.SolidLine))
        qp.setBrush(QBrush(QColor(200, 200, 200)))
        qp.drawRect(10, 10, 60, 100)

        # Draw the battery contacts
        qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        qp.setBrush(QBrush(QColor(100, 100, 100)))
        qp.drawRect(5, 45, 5, 30)
        qp.drawRect(70, 45, 5, 30)

        # Draw the battery level
        qp.setBrush(QBrush(QColor(0, 255, 0)))
        qp.drawRect(12, 12 + (100 - self.battery_level), 56, self.battery_level)

        # Draw the battery turn on threshold
        qp.setPen(QPen(Qt.red, 3, Qt.DashLine))
        qp.drawLine(-100, 12 + (100 - self.turn_on_threshold_level), 150, 12 + (100 - self.turn_on_threshold_level))

    def update_battery_level(self):
        if not self.node.target_is_set: self.battery_level = 0
        else: self.battery_level = self.battery_level_percentage
        self.update()
        self.app.update()

    def update_label(self):
        if not self.node.target_is_set:
            self.label.setText("OFF")
            return
        
        self.label.setText(self.node.currState)
        if self.node.currState == "Bonito" and self.app.nodes[self.node.target_name].currState == "Bonito":
            if (self.node.name, self.node.target_name) in self.app.connections:
                self.app.connections[(self.node.name, self.node.target_name)] = Qt.blue

            else:
                self.app.connections[(self.node.target_name, self.node.name)] = Qt.blue       

        else:
            if (self.node.name, self.node.target_name) in self.app.connections:
                self.app.connections[(self.node.name, self.node.target_name)] = self.palette().color(self.backgroundRole())

            else:
                self.app.connections[(self.node.target_name, self.node.name)] = self.palette().color(self.backgroundRole()) 

    def update_connections(self):
        for k in self.app.connections:
            self.app.connections[k] = self.palette().color(self.backgroundRole())

class App(QWidget):
    def __init__(self, nodes):
        super().__init__()
        self.title = 'Bonito Network Simulator'
        self.left = 100
        self.top = 100
        # self.width = 600
        # self.height = 400
        self.width = 750
        # self.height = 610
        self.nodes = nodes
        self.n_nodes = len(nodes)
        self.battery_widgets = []
        # self.battery_coordinates = {1: (105, 125), 3: (410, 20)}

        # if len(nodes) == 2: self.battery_coordinates = dict(zip(nodes.keys(), [(22, 125), (632, 125)]))
        # elif len(nodes) == 3: self.battery_coordinates = dict(zip(nodes.keys(), [(22, 125), (632, 125), (327, 275)]))
        # elif len(nodes) == 4: self.battery_coordinates = dict(zip(nodes.keys(), [(22, 125), (327, 125), (22, 275), (327, 275)]))
        # elif len(nodes) == 5: self.battery_coordinates = dict(zip(nodes.keys(), [(22, 125), (632, 125), (327, 275), (22, 425), (632, 425)]))

        if self.n_nodes == 2: self.coordinates_arr = [(22, 125), (632, 125)]
        elif self.n_nodes == 3: self.coordinates_arr = [(327, 125), (632, 425), (22, 425)]
        elif self.n_nodes == 4: self.coordinates_arr = [(22, 125), (632, 125), (632, 425), (22, 425)]
        elif self.n_nodes == 5: self.coordinates_arr = [(22, 275), (327, 125), (632, 275), (532, 575), (122, 575)]
        elif self.n_nodes == 6: self.coordinates_arr = [(22, 275), (327, 125), (632, 275), (632, 575), (327, 725), (22, 575)]

        self.battery_coordinates = dict(zip(nodes.keys(), self.coordinates_arr))
        self.height = max(self.coordinates_arr, key=lambda item:item[1])[1] + 185

        self.connections = {}

        self.first_submit = True
        self.pause_flag = False

        self.initUI()
        
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        qp.drawRect(12, 0, 200, 60)

        qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        qp.drawRect(224, 0, 514, 90)

        qp.setPen(QPen(Qt.red, 3, Qt.DashLine))
        qp.drawLine(25, 40, 75, 40)

        for conn in self.connections.keys():
            color = self.connections[conn]
            qp.setPen(QPen(color, 5, Qt.SolidLine))

            x1 = self.battery_coordinates[conn[0]][0]
            y1 = self.battery_coordinates[conn[0]][1]

            x2 = self.battery_coordinates[conn[1]][0]
            y2 = self.battery_coordinates[conn[1]][1]

            if x1 < x2: qp.drawLine(x1 + 40, y1 + 60, x2, y2 + 60)
            else: qp.drawLine(x2 + 40, y2 + 60, x1, y1 + 60)

    def longTask(self):
        self.thread = QThread()
        self.worker = Worker(self.battery_widgets)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        legend_label = QLabel('Legend', self)
        legend_label.move(22, 5)

        turn_on_label = QLabel('Turn-On Threshold', self)
        turn_on_label.move(80, 30)

        # Create widgets
        label0 = QLabel('Node 0:', self)
        label0.move(230, 10)
        self.input0 = QLineEdit(self)
        self.input0.setFixedWidth(50)
        self.input0.move(300, 5)

        label1 = QLabel('Node 1:', self)
        label1.move(360, 10)
        self.input1 = QLineEdit(self)
        self.input1.setFixedWidth(50)
        self.input1.move(430, 5)

        label2 = QLabel('Node 2:', self)
        label2.move(490, 10)
        self.input2 = QLineEdit(self)
        self.input2.setFixedWidth(50)
        self.input2.move(560, 5)

        label3 = QLabel('Node 3:', self)
        label3.move(230, 60)
        self.input3 = QLineEdit(self)
        self.input3.setFixedWidth(50)
        self.input3.move(300, 55)

        label4 = QLabel('Node 4:', self)
        label4.move(360, 60)
        self.input4 = QLineEdit(self)
        self.input4.setFixedWidth(50)
        self.input4.move(430, 55)

        label5 = QLabel('Node 5:', self)
        label5.move(490, 60)
        self.input5 = QLineEdit(self)
        self.input5.setFixedWidth(50)
        self.input5.move(560, 55)

        start_button = QPushButton('Start', self)
        start_button.move(12, 70)
        start_button.clicked.connect(self.start)
        
        reset_button = QPushButton('Reset', self)
        reset_button.move(130, 70)
        reset_button.clicked.connect(self.reset)

        pause_button = QPushButton('Pause', self)
        pause_button.move(130, 100)
        pause_button.clicked.connect(self.pause)
        
        refresh_button = QPushButton('Refresh', self)
        refresh_button.move(635, 55)
        refresh_button.clicked.connect(self.refresh)
        
        submit_button = QPushButton('Update Targets', self)
        submit_button.move(620, 5)
        submit_button.clicked.connect(self.submit)

        for node in self.nodes.values():
            battery_label = QLabel(f'{node.name}', self)
            battery_label.move(self.battery_coordinates[node.name][0] + 15, self.battery_coordinates[node.name][1] - 25)

            state_label = QLabel(f'Bonito', self)
            # state_label.move(self.battery_coordinates[node.name][0] + 15, self.battery_coordinates[node.name][1] + 150)
            state_label.move(self.battery_coordinates[node.name][0] + 15, self.battery_coordinates[node.name][1] + 150)

            battery_widget = BatteryWidget(self.battery_coordinates[node.name], node, state_label, self, self)
            battery_widget.move(self.battery_coordinates[node.name][0], self.battery_coordinates[node.name][1])

            self.battery_widgets.append(battery_widget)

            # if node.target_is_set and not ((node.name, node.target_name) in self.connections or (node.target_name, node.name) in self.connections):
            #     self.connections[(node.name, node.target_name)] = self.palette().color(self.backgroundRole())

        # Add an icon for the window
        # self.setWindowIcon(QIcon('bonito.jpeg'))
        self.longTask()


        self.show()

    def start(self):
        lock.acquire()

        for i in range(len(self.nodes)):
            if self.nodes[f"node{i}"].target_name:
                self.nodes[f"node{i}"].target_is_set = True

        lock.release()

        if self.first_submit: self.first_submit = False
        self.pause_flag = False

    def reset(self):
        lock.acquire()

        for i in range(len(self.nodes)):
            self.nodes[f"node{i}"].target_is_set = False
            self.nodes[f"node{i}"].target_name = None
            self.nodes[f"node{i}"].iteration = 0

        lock.release()

        self.first_submit = True
        self.update()

    def pause(self):
        lock.acquire()

        for i in range(len(self.nodes)):
            self.nodes[f"node{i}"].target_is_set = False

        lock.release()
        
        self.pause_flag = True


    def refresh(self):
        self.input0.clear()
        self.input1.clear()
        self.input2.clear()
        self.input3.clear()
        self.input4.clear()
        self.input5.clear()
        self.update()

    def submit(self):
        # Get input values
        input = [None for i in range(6)]

        input[0] = self.input0.text()
        input[1] = self.input1.text()
        input[2] = self.input2.text()
        input[3] = self.input3.text()
        input[4] = self.input4.text()
        input[5] = self.input5.text()

        # for i in range(self.n_nodes):
        #     if input[i] != "":
        #         node1 = self.nodes[f"node{i}"]
        #         node2 = self.nodes[f"node{input[i]}"]

        #         lock.acquire()

        #         node1.target_is_set = False
        #         node2.target_is_set = False


        #         try: 
        #             self.nodes[node1.target_name].target_is_set = False
        #             self.nodes[node1.target_name].target_name = None
        #         except: pass

        #         try: 
        #             self.nodes[node2.target_name].target_is_set = False
        #             self.nodes[node2.target_name].target_name = None
        #         except: pass

        #         node1.target_name = None
        #         node2.target_name = None

        #         lock.release()

        for i in range(6):
            if input[i] != "":
                node1 = self.nodes[f"node{i}"]
                node2 = self.nodes[f"node{input[i]}"]

                barrier = threading.Barrier(2)

                print(f"Setting targets for Node {i} and {input[i]}")
                node1.setTarget(f"node{input[i]}", barrier)
                node2.setTarget(f"node{i}", barrier)

        self.refresh()
        if not self.first_submit: self.start()
        


if __name__ == '__main__':
        cmd_gui = CMD_GUI()

        cmd_gui.args["opt_scale_path"] = cmd_gui.args["abs_path"] + "simulator/opt_scale.csv"
        cmd_gui.args["max_offset"] = 0.000848

        Ts = 1e-5
        iteration = [0]

        cmd_gui.args['Ts'] = Ts
        cmd_gui.args['dists'] = None
        cmd_gui.args['nodes'] = None
        cmd_gui.args['fp_tchrgs'] = None
        cmd_gui.args['fp_rt_logs'] = None
        cmd_gui.args['fp_conn'] = None
        cmd_gui.args['iteration'] = None
        cmd_gui.args['times_len'] = None
        cmd_gui.args['start_time'] = None

        node_names = ['node' + str(i) for i in range(5)]

        nodes = dict(zip(node_names, [BatteryfreeDevice(node_names[i], **cmd_gui.args) for i in range(len(node_names))]))
        
        for name in node_names:
            nodes[name].currState = "Bonito"
            nodes[name].estored = nodes[name].energy_per_cycle


        app = QApplication(sys.argv)
        ex = App(nodes)
        sys.exit(app.exec_())
       

