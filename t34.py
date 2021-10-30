# Adam Kraus
# T34 Emulator

import sys
import re

memory = [format(0, "02X")]*65536
pc = 0
ac = 0
x = 0
y = 0
sr = 32 # 0010 0000
sp = 255 # Add 256 to put in range 01FF to 0100

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def displayMem(loc):
    print("{:04X} {}".format(loc, memory[loc]))
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
        memory[loc] = mem
        loc += 1
    return

def runProg(loc):
    global pc
    pc = loc
    print(" PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC")
    while not check_bit(sr, 2): # while interrupt bit is not set
        interpret()
        pc+=1
    return

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def check_bit(value, bit):
    return value & (1<<bit)

def interpret():
    global ac
    global x
    global y
    global sr
    global sp
    
    opc = memory[pc]
    ins = "???"
    amod = "----"
    oprnd = "-- --"
    hi = opc[0]
    lo = opc[1]

    if lo == "0":
        if hi == "0": # brk impl
            ins = "BRK"
            amod = "impl"

            sr = set_bit(sr, 2) # set interrupt flag
            sr = set_bit(sr, 4) # set break flag

            # add 256 offset to get in range 01FF to 0100
            memory[sp+256] = (pc+2)>>8 # top half of pc
            memory[sp+256-1] = (pc+2)%256 # bottom half of pc
            memory[sp+256-2] = sr

            sp-=3
    elif lo == "8":
        amod = "impl"

        if hi == "0": # php impl
            ins = "PHP"

            memory[sp] = sr
            sp-=1
        elif hi == "1": # clc impl
            ins = "CLC"

            sr = clear_bit(sr, 0)
        elif hi == "2": # plp impl
            ins = "PLP"

            sp+=1
            sr = memory[sp]
        elif hi == "3": # sec impl
            ins = "SEC"
            sr = set_bit(sr, 0)
        elif hi == "4": # pha impl
            ins = "PHA"

            memory[sp] = ac
            sp-=1
        elif hi == "5": # cli impl
            ins = "CLI"

            sr = clear_bit(sr, 2)
        elif hi == "6": # pla impl
            ins = "PLA"

            sp+=1
            ac = memory[sp]

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
        elif hi == "7": # sei impl
            ins = "SEI"
            sr = set_bit(sr, 2)
        elif hi == "8": # dey impl
            ins = "DEY"

            y-=1
            if y < 0:
                y+=256

            if check_bit(y, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if y == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "9": # tya impl
            ins = "TYA"

            ac = y
            
            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "A": # tay impl
            ins = "TAY"

            y = ac
            
            if check_bit(y, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if y == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "B": # clv impl
            ins = "CLV"

            sr = clear_bit(sr, 6)
        elif hi == "C": # iny impl
            ins = "INY"

            y+=1
            if y > 255:
                y-=256
            
            if check_bit(y, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if y == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "D": # cld impl
            ins = "CLD"

            sr = clear_bit(sr, 3)
        elif hi == "E": # inx impl
            ins = "INX"

            x+=1
            if x > 255:
                x-=256
        
            if check_bit(x, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if x == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        else: # sed impl
            ins = "SED"
            sr = set_bit(sr, 3)
    elif lo == "A":
        if hi == "0": # asl A
            ins = "ASL"
            amod = "A"

            if check_bit(ac, 7): # set carry flag
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            ac=ac<<1
            if ac > 255:
                ac-=256
            
            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # rol A
            ins = "ROL"
            amod = "A"

            old_ac = ac
            ac=ac<<1
            if ac > 255:
                ac-=256

            if check_bit(old_ac, 7): # set carry flag
                ac = set_bit(ac, 0)
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # lsr A
            ins = "LSR"
            amod = "A"
            
            if check_bit(ac, 0): # set carry flag
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            
            ac=ac>>1 # shift right 1

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "6": # ror A
            ins = "ROR"
            amod = "A"

            old_ac = ac
            ac=ac>>1
            
            if check_bit(old_ac, 0): # set carry flag
                ac = set_bit(ac, 7)
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "8": # txa impl
            ins = "TXA"
            amod = "impl"

            ac = x

            if check_bit(ac, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "9": # txs impl
            ins = "TXS"
            amod = "impl"

            sp = x
        elif hi == "A": # tax impl
            ins = "TAX"
            amod = "impl"

            x = ac

            if check_bit(x, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "B": # tsx impl
            ins = "TSX"
            amod = "impl"

            x = sp

            if check_bit(x, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # dex impl
            ins = "DEX"
            amod = "impl"

            x-=1
            if x < 0:
                x+=256

            if check_bit(x, 7): # set negative flag
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if x == 0: # set zero flag
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "E": # nop impl
            ins = "NOP"
            amod = "impl"

    # PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC
    output = " {:04X} {}  {}   {:>4} {}  {:02X} {:02X} {:02X} {:02X} {:08b}"
    print(output.format(pc, opc, ins, amod, oprnd, ac, x, y, sp, sr))
    return

def file_input():
    if len(sys.argv) > 1:
        # file argument supplied
        f = open(sys.argv[1], "r")
        # read file lines
        lines = f.readlines()
        for line in lines:
            line = line[:-1]
            byteCount = int(line[1:3], 16)
            address = int(line[3:7], 16)
            recordType = int(line[7:9], 16)
            data = re.findall("..?", line[9:9+2*byteCount])
            checksum_obj = int(line[-2:], 16)
            # do checksum validaton
            checksum_calc = byteCount + int(line[3:5], 16) + int(line[5:7], 16) + recordType
            for byte in data:
                checksum_calc += int(byte, 16)

            checksum_calc = (checksum_calc % 256)^255
            checksum_calc += 1

            if recordType == 1: #EOF
                return

            if checksum_calc != checksum_obj:
                print("Format error input file: ", sys.argv[1])
                return

            # if data record, edit memory with opcodes
            if recordType == 0:
                editMem(address, data)
    return

def main():
    file_input()

    # get input
    monitor = input("> ").upper()
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

        monitor = input("> ").upper()

if __name__ == "__main__":
    main()