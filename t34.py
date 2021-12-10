# Adam Kraus
# T34 Emulator

import sys
import re

memory = [0]*65536
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
    print("{:04X} {:02X}".format(loc, memory[loc]))
    return

def displayMemRange(start, end):
    chunked = list(chunks(memory[start:end+1], 8))
    for chunk in chunked:
        print("{:04X}".format(start), end=' ')
        for num in chunk:
            if isinstance(num, str):
                print(num, end=' ')
            else:
                print("{:02X}".format(num), end=' ')
        start += 8
        print("")
    return

def editMem(loc, newMem):
    for mem in newMem:
        memory[loc] = int(mem, 16)
        loc += 1
    return

def runProg(loc):
    global pc
    global ac
    global x
    global y
    global sr
    global sp
    pc = loc
    ac = 0
    x = 0
    y = 0
    sr = 32
    sp = 255
    print(" PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC")
    while not check_bit(sr, 4): # while break bit is not set
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
    global pc
    
    opc = "{:02X}".format(memory[pc])
    ins = "???"
    amod = "----"
    oprnd1 = "--"
    oprnd2 = "--"
    hi = opc[0]
    lo = opc[1]
    change = 1
    newpc = 0

    if lo == "0":
        if hi == "0": # brk impl
            ins = "BRK"
            amod = "impl"

            sr = set_bit(sr, 2)
            sr = set_bit(sr, 4)
            memory[sp+256] = (pc+2) >> 8
            memory[sp+256-1] = (pc+2) % 256
            memory[sp+256-2] = sr
            sp-=3
        elif hi == "1": # bpl rel
            ins = "BPL"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if not check_bit(sr, 7):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "2": # jsr abs
            ins = "JSR"
            amod = "abs"
            change = 0

            memory[sp+256] = (pc+2) >> 8
            memory[sp+256-1] = (pc+2) % 256
            sp -= 2

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            newpc = (val2 << 8) + val1
        elif hi == "3": # bmi rel
            ins = "BMI"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if check_bit(sr, 7):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "4": # rti impl
            ins = "RTI"
            amod = "impl"
            change = 0

            sr = memory[sp+256+1]
            pcl = memory[sp+256+2]
            pch = memory[sp+256+3]
            sp += 3
            newpc = (pch << 8) + pcl
        elif hi == "5": # bvc rel
            ins = "BVC"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if not check_bit(sr, 6):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "6": # rts impl
            ins = "RTS"
            amod = "impl"
            change = 0
            
            pcl = memory[sp+256+1]
            pch = memory[sp+256+2]
            sp += 2
            newpc = (pch << 8) + pcl
            newpc += 1
        elif hi == "7": # bvs rel
            ins = "BVS"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if check_bit(sr, 6):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "9": # bcc rel
            ins = "BCC"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if not check_bit(sr, 0):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "A": # ldy #
            ins = "LDY"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            y = val

            if check_bit(y, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if y == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "B": # bcs rel
            ins = "BCS"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if check_bit(sr, 0):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "C": # cpy #
            ins = "CPY"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            result = y - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "D": # bne rel
            ins = "BNE"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if not check_bit(sr, 0):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
        elif hi == "E": # cpx #
            ins = "CPX"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            result = x - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "F": # beq rel
            ins = "BEQ"
            amod = "rel"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            if check_bit(sr, 1):
                if check_bit(val, 7):
                    val ^= 255
                    val += 1
                    val *= -1
                change += val
    elif lo == "2":
        if hi == "A": # ldx #
            ins = "LDX"
            amod = "#"
            change = 2

            x = memory[pc+1]
            oprnd1 = "{:02X}".format(x)

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
    elif lo == "4":
        if hi == "2": # bit zpg
            ins = "BIT"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            result = ac & val

            if result == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if check_bit(val, 6):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
        elif hi == "8": # sty zpg
            ins = "STY"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)

            memory[loc] = y
        elif hi == "A": # ldy zpg
            ins = "LDY"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)

            y = memory[loc]

            if check_bit(y, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if y == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # cpy zpg
            ins = "CPY"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            result = y - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "E": # cpx zpg
            ins = "CPX"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            result = x - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
    elif lo == "5":
        if hi == "0": # ora zpg
            ins = "ORA"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            ac |= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # and zpg
            ins = "AND"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            ac &= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # eor zpg
            ins = "EOR"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            ac ^= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # adc zpg
            ins = "ADC"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            ac += val
            if check_bit(sr, 0):
                ac += 1
            
            if check_bit(ac, 8):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            sr %= 256

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "8": # sta zpg
            ins = "STA"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)

            memory[loc] = ac
        elif hi == "A": # lda zpg
            ins = "LDA"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            ac = memory[loc]

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # cmp zpg
            ins = "CMP"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            result = ac - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "E": # sbc zpg
            ins = "SBC"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            old_ac = ac
            ac -= val + 1
            if check_bit(sr, 0):
                ac += 1

            if ac < 0:
                ac += 256
            
            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(ac, 7) != check_bit(old_ac, 7):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
    elif lo == "6":
        if hi == "0": # asl zpg
            ins = "ASL"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]
            val <<= 1

            if check_bit(val, 8):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            val %= 256

            memory[loc] = val

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # rol zpg
            ins = "ROL"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]
            val <<= 1

            if check_bit(val, 8):
                sr = set_bit(sr, 0)
                val = clear_bit(val, 8)
                val = set_bit(val, 0)
            else:
                sr = clear_bit(sr, 0)

            memory[loc] = val

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # lsr zpg
            ins = "LSR"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            if check_bit(val, 0):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            val >>= 1
            memory[loc] = val

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # ror zpg
            ins = "ROR"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]

            if check_bit(val, 0):
                sr = set_bit(sr, 0)
                val += 256
            else:
                sr = clear_bit(sr, 0)
            val >>= 1
            memory[loc] = val

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "8": # stx zpg
            ins = "STX"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            memory[loc] = x
        elif hi == "A": # ldx zpg
            ins = "LDX"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            x = memory[loc]

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "C": # dec zpg
            ins = "DEC"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)
            val = memory[loc]
            val -= 1
            if val < 0:
                val += 256
            memory[loc] = val
            
            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "E": # inc zpg
            ins = "INC"
            amod = "zpg"
            change = 2

            loc = memory[pc+1]
            oprnd1 = "{:02X}".format(loc)

            val = memory[loc]
            val += 1
            if val > 255:
                val -= 256
            memory[loc] = val

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
    elif lo == "8":
        amod = "impl"
        if hi == "0": # php impl
            ins = "PHP"

            memory[sp+256] = sr
            sp-=1
        elif hi == "1": # clc impl
            ins = "CLC"

            sr = clear_bit(sr, 0)
        elif hi == "2": # plp impl
            ins = "PLP"

            sp+=1
            sr = memory[sp+256]
        elif hi == "3": # sec impl
            ins = "SEC"

            sr = set_bit(sr, 0)
        elif hi == "4": # pha impl
            ins = "PHA"

            memory[sp+256] = ac
            sp-=1
        elif hi == "5": # cli impl
            ins = "CLI"

            sr = clear_bit(sr, 2)
        elif hi == "6": # pla impl
            ins = "PLA"

            sp+=1
            ac = memory[sp+256]

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(ac, 7):
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

            if check_bit(y, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if y == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "9": # tya impl
            ins = "TYA"

            ac = y
            
            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
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
            
            if check_bit(y, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if y == 0:
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
        
            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)
            
            if x == 0:
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
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            ac |= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # and #
            ins = "AND"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            ac &= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # eor #
            ins = "EOR"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            ac ^= val

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # adc #
            ins = "ADC"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            ac += val
            if check_bit(sr, 0):
                ac += 1
            
            if check_bit(ac, 8):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            ac %= 256

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "A": # lda #
            ins = "LDA"
            amod = "#"
            change = 2

            ac = memory[pc+1]
            oprnd1 = "{:02X}".format(ac)

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # cmp #
            ins = "CMP"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            result = ac - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "E": # sbc #
            ins = "SBC"
            amod = "#"
            change = 2

            val = memory[pc+1]
            oprnd1 = "{:02X}".format(val)

            old_ac = ac
            ac -= val + 1
            if check_bit(sr, 0):
                ac += 1

            if ac < 0:
                ac += 256
            
            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(ac, 7) != check_bit(old_ac, 7):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
    elif lo == "A":
        if hi == "0": # asl A
            ins = "ASL"
            amod = "A"

            if check_bit(ac, 7):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            ac <<= 1
            ac %= 256

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # rol A
            ins = "ROL"
            amod = "A"

            ac <<= 1

            if check_bit(ac, 8):
                sr = set_bit(sr, 0)
                ac = clear_bit(ac, 8)
                ac = set_bit(ac, 0)
            else:
                sr = clear_bit(sr, 0)

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # lsr A
            ins = "LSR"
            amod = "A"
            
            if check_bit(ac, 0):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            ac >>= 1

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # ror A
            ins = "ROR"
            amod = "A"

            if check_bit(ac, 0):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            ac >>= 1

            if check_bit(sr, 0):
                ac = set_bit(ac, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "8": # txa impl
            ins = "TXA"
            amod = "impl"

            ac = x

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "9": # txs impl
            ins = "TXS"
            amod = "impl"

            sp = x
        elif hi == "A": # tax impl
            ins = "TAX"
            amod = "impl"

            x = ac

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "B": # tsx impl
            ins = "TSX"
            amod = "impl"

            x = sp

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "C": # dex impl
            ins = "DEX"
            amod = "impl"

            x -= 1
            if x < 0:
                x += 256

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
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
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            result = ac & val

            if result == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if check_bit(val, 6):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
        elif hi == "4": # jmp abs
            ins = "JMP"
            amod = "abs"
            change = 0

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            newpc = (val2 << 8) + val1
        elif hi == "6": # jmp ind
            ins = "JMP"
            amod = "ind"
            change = 0

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            pcl = memory[loc]
            pch = memory[loc+1]
            newpc = (pch << 8) + pcl
        elif hi == "8": # sty abs
            ins = "STY"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            memory[loc] = y
        elif hi == "A": # ldy abs
            ins = "LDY"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            y = memory[loc]

            if check_bit(y, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if y == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # cpy abs
            ins = "CPY"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            result = y - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "E": # cpx abs
            ins = "CPX"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            result = x - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
    elif lo == "D":
        if hi == "0": # ora abs
            ins = "ORA"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            ac |= memory[loc]

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # and abs
            ins = "AND"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            ac &= memory[loc]

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # eor abs
            ins = "EOR"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            ac ^= memory[loc]

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # adc abs
            ins = "ADC"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            old_ac = ac
            ac += memory[loc]
            if check_bit(sr, 0):
                ac += 1

            if check_bit(ac, 8):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            ac %= 256

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
            
            if check_bit(ac, 7) != check_bit(old_ac, 7):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
        elif hi == "8": # sta abs
            ins = "STA"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            memory[loc] = ac
        elif hi == "A": # lda abs
            ins = "LDA"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            ac = memory[loc]

            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # cmp abs
            ins = "CMP"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            result = ac - val

            if result == 0:
                sr = set_bit(sr, 1)
                sr = clear_bit(sr, 7)
            else:
                sr = clear_bit(sr, 1)
                if check_bit(result, 7):
                    sr = set_bit(sr, 7)
                else:
                    sr = clear_bit(sr, 7)
            
            if result >= 0:
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
        elif hi == "E": # sbc abs
            ins = "SBC"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            old_ac = ac
            ac -= val + 1
            if check_bit(sr, 0):
                ac += 1

            if ac < 0:
                ac += 256
            
            if check_bit(ac, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if ac == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)

            if check_bit(ac, 7) != check_bit(old_ac, 7):
                sr = set_bit(sr, 6)
            else:
                sr = clear_bit(sr, 6)
    elif lo == "E":
        if hi == "0": # asl abs
            ins = "ASL"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            if check_bit(val, 7):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)

            val = clear_bit(val, 7)
            val <<= 1
            memory[loc] = val

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "2": # rol abs
            ins = "ROL"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]
            val <<= 1

            if check_bit(val, 8):
                sr = set_bit(sr, 0)
                val = clear_bit(val, 8)
                val = set_bit(val, 0)
            else:
                sr = clear_bit(sr, 0)

            memory[loc] = val

            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "4": # lsr abs
            ins = "LSR"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            if check_bit(val, 0):
                sr = set_bit(sr, 0)
            else:
                sr = clear_bit(sr, 0)
            val >>= 1
            memory[loc] = val

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "6": # ror abs
            ins = "ROR"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            if check_bit(sr, 0):
                val = set_bit(val, 8)
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if check_bit(val, 0):
                sr = set_bit(sr, 0)
                val = set_bit(val, 8)
            else:
                sr = clear_bit(sr, 0)

            val >>= 1
            memory[loc] = val
            
            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "8": # stx abs
            ins = "STX"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            memory[loc] = x
        elif hi == "A": # ldx abs
            ins = "LDX"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1

            x = memory[loc]

            if check_bit(x, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if x == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "C": # dec abs
            ins = "DEC"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            val -= 1
            if val < 0:
                val += 256

            memory[loc] = val
            
            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
        elif hi == "E": # inc abs
            ins = "INC"
            amod = "abs"
            change = 3

            val1 = memory[pc+1]
            val2 = memory[pc+2]
            oprnd1 = "{:02X}".format(val1)
            oprnd2 = "{:02X}".format(val2)
            loc = (val2 << 8) + val1
            val = memory[loc]

            val += 1
            if val > 255:
                val -= 256

            memory[loc] = val
            
            if check_bit(val, 7):
                sr = set_bit(sr, 7)
            else:
                sr = clear_bit(sr, 7)

            if val == 0:
                sr = set_bit(sr, 1)
            else:
                sr = clear_bit(sr, 1)
    # PC  OPC  INS   AMOD OPRND  AC XR YR SP NV-BDIZC
    output = "{:4X}  {}  {}  {:>5} {} {}  {:02X} {:02X} {:02X} {:02X} {:08b}"
    print(output.format(pc, opc, ins, amod, oprnd1, oprnd2, ac, x, y, sp, sr))
    if change == 0:
        pc = newpc
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
                print("{:02X}".format(checksum_calc))
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