from tkinter import *

class CMD_GUI():
    def __init__(self):
        # Dictionary for storing user input
        self.args = dict()

        # Creating tkinter window
        self.root = Tk()
        self.root.title("Battery-Free Network Simulator")
        self.root.geometry('400x550')
        
        # Misc Inputs LabelFrame
        label_frame_1 = LabelFrame(self.root, text='Misc Inputs')
        label_frame_1.pack(expand='yes', fill='both')

        label0 = Label(label_frame_1, text='Repo Absolute Path')
        label0.place(x=0, y=5)

        self.abs_path = Entry(label_frame_1)
        self.abs_path.insert(0, "/home/hrishi/Repos/")
        self.abs_path.place(x=150, y=0)

        label1 = Label(label_frame_1, text='Power Trace File')
        label1.place(x=0, y=35)

        self.trace_file = Entry(label_frame_1)
        self.trace_file.insert(0, "pwr_office.h5")
        self.trace_file.place(x=150, y=30)

        label12 = Label(label_frame_1, text='Display GUI?')
        label12.place(x=0, y=65)

        self.show_GUI = Entry(label_frame_1)
        self.show_GUI.insert(0, "Yes")
        self.show_GUI.place(x=150, y=60)

        label13 = Label(label_frame_1, text='Generate Plots?')
        label13.place(x=0, y=95)

        self.create_plots = Entry(label_frame_1)
        self.create_plots.insert(0, "Yes")
        self.create_plots.place(x=150, y=90)

        label13 = Label(label_frame_1, text='Random Seed')
        label13.place(x=0, y=125)

        self.seed = Entry(label_frame_1)
        self.seed.insert(0, "-1")
        self.seed.place(x=150, y=120)

        # Bonito Parameters LabelFrame
        label_frame_2 = LabelFrame(self.root, text='Bonito Parameters')
        label_frame_2.pack(expand='yes', fill='both')

        label2 = Label(label_frame_2, text='Slot Length (in sec)')
        label2.place(x=0, y=5)

        self.slot_length = Entry(label_frame_2)
        self.slot_length.insert(0, "1e-5")
        self.slot_length.place(x=150, y=0)

        label3 = Label(label_frame_2, text='Target Probability')
        label3.place(x=0, y=35)

        self.target_probability = Entry(label_frame_2)
        self.target_probability.insert(0, "0.99")
        self.target_probability.place(x=150, y=30)

        label4 = Label(label_frame_2, text='Max Offset (in sec)')
        label4.place(x=0, y=65)

        self.max_offset = Entry(label_frame_2)
        self.max_offset.insert(0, "0.000848")
        self.max_offset.place(x=150, y=60)

        label41 = Label(label_frame_2, text='Sim. Time (in min)')
        label41.place(x=0, y=95)

        self.sim_time = Entry(label_frame_2)
        self.sim_time.insert(0, "10")
        self.sim_time.place(x=150, y=90)

        # label5 = Label(label_frame_2, text='')
        # label5.place(x=0, y=125)

        # self.sim_time = Entry(label_frame_2)
        # self.sim_time.insert(0, "10")
        # self.sim_time.place(x=150, y=120)

        # Battery-Free Device properties LabelFrame
        label_frame_3 = LabelFrame(self.root, text='Battery-Free Device properties')
        label_frame_3.pack(expand='yes', fill='both')

        label6 = Label(label_frame_3, text='Capacity (in farad)')
        label6.place(x=0, y=5)

        self.capacity = Entry(label_frame_3)
        self.capacity.insert(0, "17e-6")
        self.capacity.place(x=150, y=0)

        label7 = Label(label_frame_3, text='V_On (in volts)')
        label7.place(x=0, y=35)

        self.von = Entry(label_frame_3)
        self.von.insert(0, "3")
        self.von.place(x=150, y=30)

        label8 = Label(label_frame_3, text='V_Off (in volts)')
        label8.place(x=0, y=65)

        self.voff = Entry(label_frame_3)
        self.voff.insert(0, "2.4")
        self.voff.place(x=150, y=60)

        label9 = Label(label_frame_3, text='V_Max (in Volts)')
        label9.place(x=0, y=95)

        self.vmax = Entry(label_frame_3)
        self.vmax.insert(0, "3.2")
        self.vmax.place(x=150, y=90)

        btn = Button(label_frame_3, text="START", command=self.callback)
        btn.place(x=150, y=120)

        # self.root.bind('<Return>', self.callback)

        mainloop()

    def callback(self):
        self.args["abs_path"] = self.abs_path.get()
        self.args["trace_file"] = self.trace_file.get()
        self.args["show_GUI"] = True if self.show_GUI.get() == "Yes" else False
        self.args["create_plots"] = True if self.create_plots.get() == "Yes" else False
        self.args["seed"] = int(self.seed.get())

        self.args["slot_length"] = float(self.slot_length.get())
        self.args["target_probability"] = float(self.target_probability.get())
        self.args["max_offset"] = float(self.max_offset.get())
        self.args["sim_time"] = float(self.sim_time.get())
        
        self.args["capacity"] = float(self.capacity.get())
        self.args["von"] = float(self.von.get())
        self.args["voff"] = float(self.voff.get())
        self.args["vmax"] = float(self.vmax.get())

        self.root.destroy()

# Main function only used for develpoment purposes
if __name__=="__main__":
    CMD_GUI()
