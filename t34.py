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
    print(str(loc).zfill(4), hex(memory[int(loc, 16)])[2:].zfill(2).upper(), sep=' ')
    return

def displayMemRange(start, end):
    sub_list = memory[int(start, 16):int(end, 16)+1]
    sections = list(chunks(sub_list, 8))
    i = int(start, 16)
    for section in sections:
        print(hex(i)[2:].zfill(4).upper(), end=' ')
        for no in section:
            print(hex(no)[2:].zfill(2).upper(), end=' ')
        i += 8
        print("")
    return

def editMem(loc, newMem):
    # print(loc)
    # print(newMem, sep=' ')
    i = int(loc, 16)
    for mem in newMem:
        memory[i] = int(mem, 16)
        i += 1
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
            runProg(monitor[:-1])
        elif "." in monitor:
            # display memory range
            split = monitor.split(".")
            displayMemRange(split[0], split[1])
        elif ":" in monitor:
            # edit memory locations
            split = monitor.split()
            editMem(split[0][:-1], split[1:])    
        else:
            displayMem(monitor)

        monitor = input("> ")

if __name__ == "__main__":
    main()