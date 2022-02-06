# ToMasulator
A simple visual simulator developed fully in Python and based on the Tomasulo algorithm as described in the book "Computer Architecture: A Quantitative Approach":
https://www.amazon.com/gp/product/0128119055/ref=dbs_a_def_rwt_bibl_vppi_i1

It only supports 6 instructions, but this is enough to showcase the scheduling of instructions.

# How to run
If you have all the required packages (such as PyQt5) then just use the following in your command line, or run main.py in your IDE of choice:

python main.py

The simulator has been tested on Windows 10 with Python 3.6


# Simulator's main window
Below is an image of the simulator's window showing the editor, the instruction queue, different reservation stations, and the instruction timing table. The number of latency cycles of different units is adjustable. 

There are 3 buttons allwoing to load the assembly program, step through the code, and execute the code fully, respectively.

![](images/sample_window.gif)

