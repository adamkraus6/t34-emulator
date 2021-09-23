import sys
import re

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
    chunked = list(chunks(memory[start:end+1], 8))
    for chunk in chunked:
        print(format(start, "04X"), end=' ')
        for num in chunk:
            print(format(num, "02X"), end=' ')
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
    print("PC  OPC INS AMOD OPRND AC XR YR SP NV-BDIZC")
    print(format(pc, "04X"))
    return

def main():
    if len(sys.argv) > 1:
        # file argument supplied
        f = open(sys.argv[1], "r")
        # read file lines
        lines = f .readlines()
        for line in lines:
            line = line[:-1]
            byteCount = int(line[1:3], 16)
            address = int(line[3:7], 16)
            recordType = int(line[7:9], 16)
            # if data record, edit memory with opcodes
            if recordType == 0:
                data = re.findall("..?", line[9:9+2*byteCount])
                editMem(address, data)
    else:
        print("no file")

    # get input
    monitor = input("> ")
    while "exit" not in monitor:
        # check input
        if "R" in monitor: # ex: 200R
            # run program at starting address
            runProg(int(monitor[:-1], 16))
        elif "." in monitor: # ex: 200.20F
            # display memory range
            split = monitor.split(".")
            displayMemRange(int(split[0], 16), int(split[1], 16))
        elif ":" in monitor: # ex: 200: A9
            # edit memory locations
            split = monitor.split()
            editMem(int(split[0][:-1], 16), split[1:])    
        else: # ex: 200
            displayMem(int(monitor, 16))

        monitor = input("> ")

if __name__ == "__main__":
    main()