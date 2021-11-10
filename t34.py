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
        change = interpret()
        pc+=change
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
    oprnd1 = "--"
    oprnd2 = "--"
    hi = opc[0]
    lo = opc[1]
    change = 1

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
        elif hi == "1": # bpl rel
            ins = "BPL"
            amod = "rel"
        elif hi == "2": # jsr abs
            ins = "JSR"
            amod = "abs"
        elif hi == "3": # bmi rel
            ins = "BMI"
            amod = "rel"
        elif hi == "4": # rti impl
            ins = "RTI"
            amod = "impl"
        elif hi == "5": # bvc rel
            ins = "BVC"
            amod = "rel"
        elif hi == "6": # rts impl
            ins = "RTS"
            amod = "impl"
        elif hi == "7": # bvs rel
            ins = "BVS"
            amod = "rel"
        elif hi == "9": # bcc rel
            ins = "BCC"
            amod = "rel"
        elif hi == "A": # ldy #
            ins = "LDY"
            amod = "#"
        elif hi == "B": # bcs rel
            ins = "BCS"
            amod = "rel"
        elif hi == "C": # cpy #
            ins = "CPY"
            amod = "#"
        elif hi == "D": # bne rel
            ins = "BNE"
            amod = "rel"
        elif hi == "E": # cpx #
            ins = "CPX"
            amod = "#"
        elif hi == "F": # beq rel
            ins = "BEQ"
            amod = "rel"
    elif lo == "1":
        if hi == "0": # ora x,ind
            ins = "ORA"
            amod = "x,ind"
        elif hi == "1": # ora ind,y
            ins = "ORA"
            amod = "ind,y"
        elif hi == "2": # and x,ind
            ins = "AND"
            amod = "x,ind"
        elif hi == "3": # and ind,y
            ins = "AND"
            amod = "ind,y"
        elif hi == "4": # eor x,ind
            ins = "EOR"
            amod = "x,ind"
        elif hi == "5": # eor ind,y
            ins = "EOR"
            amod = "ind,y"
        elif hi == "6": # adc x,ind
            ins = "ADC"
            amod = "x,ind"
        elif hi == "7": # adc ind,y
            ins = "ADC"
            amod = "ind,y"
        elif hi == "8": # sta x,ind
            ins = "STA"
            amod = "x,ind"
        elif hi == "9": # sta ind,y
            ins = "STA"
            amod = "ind,y"
        elif hi == "A": # lda x,ind
            ins = "LDA"
            amod = "x,ind"
        elif hi == "B": # lda ind,y
            ins = "LDA"
            amod = "ind,y"
        elif hi == "C": # cmp x,ind
            ins = "CMP"
            amod = "x,ind"
        elif hi == "D": # cmp ind,y
            ins = "CMP"
            amod = "ind,y"
        elif hi == "E": # sbc x,ind
            ins = "SBC"
            amod = "x,ind"
        elif hi == "F": # sbc ind,y
            ins = "SBC"
            amod = "ind,y"
    elif lo == "2":
        if hi == "A": # ldx #
            ins = "LDX"
            amod = "#"
    elif lo == "4":
        if hi == "2": # bit zpg
            ins = "BIT"
            amod = "zpg"
        elif hi == "8": # sty zpg
            ins = "STY"
            amod = "zpg"
        elif hi == "9": # sty zpg,x
            ins = "STY"
            amod = "zpg,x"
        elif hi == "A": # ldy zpg
            ins = "LDY"
            amod = "zpg"
        elif hi == "B": # ldy zpg,x
            ins = "LDY"
            amod = "zpg,x"
        elif hi == "C": # cpy zpg
            ins = "CPY"
            amod = "zpg"
        elif hi == "E": # cpx zpg
            ins = "CPX"
            amod = "zpg"
    elif lo == "5":
        if hi == "0": # ora zpg
            ins = "ORA"
            amod = "zpg"
        elif hi == "1": # ora zpg,x
            ins = "ORA"
            amod = "zpg,x"
        elif hi == "2": # and zpg
            ins = "AND"
            amod = "zpg"
        elif hi == "3": # and zpg,x
            ins = "AND"
            amod = "zpg,x"
        elif hi == "4": # eor zpg
            ins = "EOR"
            amod = "zpg"
        elif hi == "5": # eor zpg,x
            ins = "EOR"
            amod = "zpg,x"
        elif hi == "6": # adc zpg
            ins = "ADC"
            amod = "zpg"
        elif hi == "7": # adc zpg,x
            ins = "ADC"
            amod = "zpg,x"
        elif hi == "8": # sta zpg
            ins = "STA"
            amod = "zpg"
        elif hi == "9": # sta zpg,x
            ins = "STA"
            amod = "zpg,x"
        elif hi == "A": # lda zpg
            ins = "LDA"
            amod = "zpg"
        elif hi == "B": # lda zpg,x
            ins = "LDA"
            amod = "zpg,x"
        elif hi == "C": # cmp zpg
            ins = "CMP"
            amod = "zpg"
        elif hi == "D": # cmp zpg,x
            ins = "CMP"
            amod = "zpg,x"
        elif hi == "E": # sbc zpg
            ins = "SBC"
            amod = "zpg"
        elif hi == "F": # sbc zpg,x
            ins = "SBC"
            amod = "zpg,x"
    elif lo == "6":
        if hi == "0": # asl zpg
            ins = "ASL"
            amod = "zpg"
        elif hi == "1": # asl zpg,x
            ins = "ASL"
            amod = "zpg,x"
        elif hi == "2": # rol zpg
            ins = "ROL"
            amod = "zpg"
        elif hi == "3": # rol zpg,x
            ins = "ROL"
            amod = "zpg,x"
        elif hi == "4": # lsr zpg
            ins = "LSR"
            amod = "zpg"
        elif hi == "5": # lsr zpg,x
            ins = "LSR"
            amod = "zpg,x"
        elif hi == "6": # ror zpg
            ins = "ROR"
            amod = "zpg"
        elif hi == "7": # ror zpg,x
            ins = "ROR"
            amod = "zpg,x"
        elif hi == "8": # stx zpg
            ins = "STX"
            amod = "zpg"
        elif hi == "9": # stx zpg,x
            ins = "STX"
            amod = "zpg,x"
        elif hi == "A": # ldx zpg
            ins = "LDX"
            amod = "zpg"
        elif hi == "B": # ldx zpg,x
            ins = "LDX"
            amod = "zpg,x"
        elif hi == "C": # dec zpg
            ins = "DEC"
            amod = "zpg"
        elif hi == "D": # dec zpg,x
            ins = "DEC"
            amod = "zpg,x"
        elif hi == "E": # inc zpg
            ins = "INC"
            amod = "zpg"
        elif hi == "F": # inc zpg,x
            ins = "INC"
            amod = "zpg,x"
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
    elif lo == "9":
        if hi == "0": # ora #
            ins = "ORA"
            amod = "#"
        elif hi == "1": # ora abs,y
            ins = "ORA"
            amod = "abs,y"
        elif hi == "2": # and #
            ins = "AND"
            amod = "#"
        elif hi == "3": # and abs,y
            ins = "AND"
            amod = "abs,y"
        elif hi == "4": # eor #
            ins = "EOR"
            amod = "#"
        elif hi == "5": # eor abs,y
            ins = "EOR"
            amod = "abs,y"
        elif hi == "6": # adc #
            ins = "ADC"
            amod = "#"
        elif hi == "7": # adc abs,y
            ins = "ADC"
            amod = "abs,y"
        elif hi == "9": # sta abs,y
            ins = "STA"
            amod = "abs,y"
        elif hi == "A": # lda #
            ins = "LDA"
            amod = "#"
        elif hi == "B": # lda abs,y
            ins = "LDA"
            amod = "abs,y"
        elif hi == "C": # cmp #
            ins = "CMP"
            amod = "#"
        elif hi == "D": # cmp abs,y
            ins = "CMP"
            amod = "abs,y"
        elif hi == "E": # sbc #
            ins = "SBC"
            amod = "#"
        elif hi == "F": # sbc abs,y
            ins = "SBC"
            amod = "abs,y"
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
    elif lo == "C":
        if hi == "2": # bit abs
            ins = "BIT"
            amod = "abs"
        elif hi == "4": # jmp abs
            ins = "JMP"
            amod = "abs"
        elif hi == "6": # jmp ind
            ins = "JMP"
            amod = "ind"
        elif hi == "8": # sty abs
            ins = "STY"
            amod = "abs"
        elif hi == "A": # ldy abs
            ins = "LDY"
            amod = "abs"
        elif hi == "B": # ldy abs,x
            ins = "LDY"
            amod = "abs,x"
        elif hi == "C": # cpy abs
            ins = "CPY"
            amod = "abs"
        elif hi == "E": # cpx abs
            ins = "CPX"
            amod = "abs"
    elif lo == "D":
        if hi == "0": # ora abs
            ins = "ORA"
            amod = "abs"
        elif hi == "1": # ora abs,x
            ins = "ORA"
            amod = "abs,x"
        elif hi == "2": # and abs
            ins = "AND"
            amod = "abs"
        elif hi == "3": # and abs,x
            ins = "AND"
            amod = "abs,x"
        elif hi == "4": # eor abs
            ins = "EOR"
            amod = "abs"
        elif hi == "5": # eor abs,x
            ins = "EOR"
            amod = "abs,x"
        elif hi == "6": # adc abs
            ins = "ADC"
            amod = "abs"
        elif hi == "7": # adc abs,x
            ins = "ADC"
            amod = "abs,x"
        elif hi == "8": # sta abs
            ins = "STA"
            amod = "abs"
        elif hi == "9": # sta abs,x
            ins = "STA"
            amod = "abs,x"
        elif hi == "A": # lda abs
            ins = "LDA"
            amod = "abs"
        elif hi == "B": # lda abs,x
            ins = "LDA"
            amod = "abs,x"
        elif hi == "C": # cmp abs
            ins = "CMP"
            amod = "abs"
        elif hi == "D": # cmp abs,x
            ins = "CMP"
            amod = "abs,x"
        elif hi == "E": # sbc abs
            ins = "SBC"
            amod = "abs"
        elif hi == "F": # sbc abs,x
            ins = "SBC"
            amod = "abs,x"
    elif lo == "E":
        if hi == "0": # asl abs
            ins = "ASL"
            amod = "abs"
        elif hi == "1": # asl abs,x
            ins = "ASL"
            amod = "abs,x"
        elif hi == "2": # rol abs
            ins = "ROL"
            amod = "abs"
        elif hi == "3": # rol abs,x
            ins = "ROL"
            amod = "abs,x"
        elif hi == "4": # lsr abs
            ins = "LSR"
            amod = "abs"
        elif hi == "5": # lsr abs,x
            ins = "LSR"
            amod = "abs,x"
        elif hi == "6": # ror abs
            ins = "ROR"
            amod = "abs"
        elif hi == "7": # ror abs,x
            ins = "ROR"
            amod = "abs,x"
        elif hi == "8": # stx abs
            ins = "STX"
            amod = "abs"
        elif hi == "A": # ldx abs
            ins = "LDX"
            amod = "abs"
        elif hi == "B": # ldx abs,y
            ins = "LDX"
            amod = "abs,y"
        elif hi == "C": # dec abs
            ins = "DEC"
            amod = "abs"
        elif hi == "D": # dec abs,x
            ins = "DEC"
            amod = "abs,x"
        elif hi == "E": # inc abs
            ins = "INC"
            amod = "abs"
        elif hi == "F": # inc abs,x
            ins = "INC"
            amod = "abs,x"
    # PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC
    output = " {:04X} {}  {}  {:>5} {} {}  {:02X} {:02X} {:02X} {:02X} {:08b}"
    print(output.format(pc, opc, ins, amod, oprnd1, oprnd2, ac, x, y, sp, sr))
    return change

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
    while "EXIT" not in monitor:
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