import sys
import numpy as np

memory = [0]*65536
pc = 0
ac = 0
x = 0
y = 0
sr = 0
sp = 0

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def displayMem(loc):
    print(format(loc, "04X"), format(memory[loc], "02X"), sep=' ')
    return

def displayMemRange(start, end):
    sub_list = memory[start:end+1]
    sections = list(chunks(sub_list, 8))
    for section in sections:
        print(format(start, "04X"), end=' ')
        for no in section:
            print(format(no, "02X"), end=' ')
        start += 8
        print("")
    return

def editMem(loc, newMem):
    for mem in newMem:
        memory[loc] = int(mem, 16)
        loc += 1
    return

def runProg(loc):
    pc = loc;

    return

def main():
    # print(sys.argv[1])
    # print(len(sys.argv))

    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        # print(f.read())
        # 
    else:
        print("no file")

    # get input
    monitor = input("> ")
    while "exit" not in monitor:
        # check input
        if "R" in monitor:
            # run program at starting address
            runProg(int(monitor[:-1], 16))
        elif "." in monitor:
            # display memory range
            split = monitor.split(".")
            displayMemRange(int(split[0], 16), int(split[1], 16))
        elif ":" in monitor:
            # edit memory locations
            split = monitor.split()
            editMem(int(split[0][:-1], 16), split[1:])    
        else:
            displayMem(int(monitor, 16))

        monitor = input("> ")

if __name__ == "__main__":
    main()