import pygame
from pygame.locals import *
from pynput import keyboard
import random
from enum import Enum
import time
import sys

class Display():
    def __init__(self):
        pygame.init()
        self.grid = [0] * 2048

        self.screen = pygame.display.set_mode((640, 320));
        self.screen.fill((0, 0, 0))

    def print_display(self):
        pp = []
        for j in range(32):
            for i in range(64):
                pp += "" + str(self.grid[j * 64 + i])
            pp += '\n'

    def clear_display(self):
        self.grid = [0] * 2048
        self.update_display()

    def update_display(self):
        for x in range(64):
            for y in range(32):
                if self.grid[y * 64 + x] == 1:
                    self.draw_pixel(x, y)
                else:
                    self.clear_pixel(x, y)
                
        pygame.display.update()

    def draw_pixel(self, x, y):
        pygame.draw.rect(self.screen, (255, 255, 255), Rect((x % 64) * 10, (y % 64) * 10, 10, 10))

    def clear_pixel(self, x, y):
        pygame.draw.rect(self.screen, (0, 0, 0), Rect((x % 64) * 10, (y % 64) * 10, 10, 10))


class chip8():
    def __init__(self, display):
        self.mem = b'\x00' * 0x1000
        self.regfile = [0] * 16
        self.stack = [0] * 16
        self.sp = 0
        self.pc = 0x200
        self.I = 0x0000
        self.dt = 0x00
        self.st = 0x00
        self.display = display
        self.currentkey = set()

        self.keyboardmap = {
            "1": "1",
            "2": "2",
            "3": "3",
            "4": "C",
            "q": "4",
            "w": "5",
            "e": "6",
            "r": "D",
            "a": "7",
            "s": "8",
            "d": "9",
            "f": "e",
            "z": "a",
            "x": "0",
            "c": "b",
            "v": "f",
        }

        sprites = [
                0xf0, 0x90, 0x90, 0x90, 0xf0,
                0x20, 0x60, 0x20, 0x20, 0x70,
                0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
                0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
                0x90, 0x90, 0xF0, 0x10, 0x10, # 4
                0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
                0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
                0xF0, 0x10, 0x20, 0x40, 0x40, # 7
                0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
                0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
                0xF0, 0x90, 0xF0, 0x90, 0x90, # A
                0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
                0xF0, 0x80, 0x80, 0x80, 0xF0, # C
                0xE0, 0x90, 0x90, 0x90, 0xE0, # D
                0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
                0xF0, 0x80, 0xF0, 0x80, 0x80, # F
        ]

        for i in range(len(sprites)):
            self.wr(sprites[i], i)

    def on_press(self, key):
        try:
            if key.char in self.keyboardmap.keys():
                self.currentkey.add(self.keyboardmap[key.char])
        except AttributeError:
            if key in self.keyboardmap.keys():
                self.currentkey.add(self.keyboardmap[key])

    def on_release(self, key):
        try:
            self.currentkey.discard(self.keyboardmap[key.char])
        except AttributeError:
            self.currentkey.add(self.keyboardmap[key])

    def wr(self, dat, addr, size = 1):
        dat = dat.to_bytes(size, byteorder='big')
        self.mem = self.mem[:addr] + dat + self.mem[addr + size:]
    
    def push_stack(self, num):
        if self.sp == 16:
            raise Exception("Stack overflow")
        self.stack[self.sp] = num
        self.sp += 1
    
    def pop_stack(self):
        if self.sp == 0:
            raise Exception("Stack is empty")
        self.sp -= 1
        val = self.stack[self.sp]
        return val

    def step(self):
        # fetch
        instruction = int.from_bytes(self.mem[self.pc:self.pc + 2], byteorder='big')
        self.pc += 2
        
        # decrement timer
        if self.dt != 0:
            self.dt -= 1

        # decode
        self.decode(instruction)


    def decode(self, inst):
        opcode = int(inst) & 0xf000
        
        if inst == 0x00e0:
            self.display.clear_display()
        elif inst == 0x00ee:
            self.pc = self.pop_stack()
        elif opcode == 0x1000:
            self.pc = inst & 0x0fff
        elif opcode == 0x2000:
            self.push_stack(self.pc)
            self.pc = (inst & 0x0fff)
        elif opcode == 0x3000:
            if self.regfile[(inst & 0x0f00) >> 8] == (inst & 0x00ff):
                self.pc += 2
        elif opcode == 0x4000:
            if self.regfile[(inst & 0x0f00) >> 8] != (inst & 0x00ff):
                self.pc += 2
        elif opcode == 0x5000:
            if self.regfile[(inst & 0x0f00) >> 8] == self.regfile[(inst & 0x00f0) >> 4]:
                self.pc += 2
        elif opcode == 0x6000:
            x = (inst & 0x0f00) >> 8
            self.regfile[x] = (inst & 0x00ff)
        elif opcode == 0x7000:
            x = (inst & 0x0f00) >> 8
            self.regfile[x] = (self.regfile[x] + (inst & 0x00ff)) % 256
        elif inst & 0xf00f == 0x8000:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            self.regfile[x] = self.regfile[y]
        elif inst & 0xf00f == 0x8001:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            self.regfile[x] = self.regfile[x] | self.regfile[y]
        elif inst & 0xf00f == 0x8002:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            self.regfile[x] = self.regfile[x] & self.regfile[y]
        elif inst & 0xf00f == 0x8003:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            self.regfile[x] = self.regfile[x] ^ self.regfile[y]
        elif inst & 0xf00f == 0x8004:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            val = self.regfile[x] + self.regfile[y]
            if val > 255:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = val & 0xff
        elif inst & 0xf00f == 0x8005:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[x] >= self.regfile[y]:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            result = self.regfile[x] + (~self.regfile[y] + 1)
            if result < 0:
                result += 256
            self.regfile[x] = result
        elif inst & 0xf00f == 0x8006:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[x] & 1 == 1:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = self.regfile[x] // 2
        elif inst & 0xf00f == 0x8007:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[y] >= self.regfile[x]:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            result = self.regfile[y] - self.regfile[x]
            if result < 0:
                result += 256
            self.regfile[y] = result
        elif inst & 0xf00f == 0x800e:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if ((self.regfile[x]) >> 8) & 1 == 1:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = (self.regfile[x] * 2) % 256
        elif inst & 0xf00f == 0x9000:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[x] != self.regfile[y]:
                self.pc += 2
        elif inst & 0xf000 == 0xa000:
            self.I = inst & 0x0fff
        elif inst & 0xf000 == 0xb000:
            self.pc = (inst & 0x0fff) + self.regfile[0x0]
        elif inst & 0xf000 == 0xc000:
            x = (inst & 0x0f00) >> 8
            k = (inst & 0x00ff)
            self.regfile[x] = random.randint(0, 255) & k
        elif inst & 0xf000 == 0xd000:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            n = (inst & 0x000f)
            xcoord = self.regfile[x] % 64
            ycoord = self.regfile[y] % 32
            self.regfile[0xf] = 0
            for i in range(n):
                if ycoord > 32:
                    break
                row = int.from_bytes(self.mem[self.I + i:self.I + i + 1], byteorder='big')
                xcoord = self.regfile[x] % 64
                xcoord += 8
                while row != 0:
                    if xcoord < 64:
                        if row & 1 == 1:
                            if self.display.grid[ycoord * 64 + xcoord - 1] == 1:
                                self.display.grid[ycoord * 64 + xcoord - 1] = 0
                                self.regfile[0xf] = 1
                            else:
                                self.display.grid[ycoord * 64 + xcoord - 1] = 1
                    row = row >> 1
                    xcoord -= 1
                ycoord += 1
            self.display.update_display()
        elif inst & 0xf0ff == 0xe09e:
            x = (inst & 0x0f00) >> 8
            if ("%1x" % self.regfile[x]) in self.currentkey:
                self.pc += 2
        elif inst & 0xf0ff == 0xe0a1:
            x = (inst & 0x0f00) >> 8
            if ("%1x" % self.regfile[x]) not in self.currentkey:
                self.pc += 2
        elif inst & 0xf0ff == 0xf007:
            x = (inst & 0x0f00) >> 8
            self.regfile[x] = self.dt
        elif inst & 0xf0ff == 0xf00a:
            x = (inst & 0x0f00) >> 8
            # TODO get keypress
            while self.currentkey == '':
                if self.currentkey != '':
                    self.regfile[x] = self.currentkey
        elif inst & 0xf0ff == 0xf015:
            x = (inst & 0x0f00) >> 8
            self.dt = self.regfile[x]
        elif inst & 0xf0ff == 0xf018:
            x = (inst & 0x0f00) >> 8
            self.st = self.regfile[x]
        elif inst & 0xf0ff == 0xf01e:
            x = (inst & 0x0f00) >> 8
            self.I = self.I + self.regfile[x]
        elif inst & 0xf0ff == 0xf029:
            x = (inst & 0x0f00) >> 8
            self.I = self.regfile[x] * 5
        elif inst & 0xf0ff == 0xf033:
            x = (inst & 0x0f00) >> 8
            self.wr(self.regfile[x] % 10, self.I + 2)
            self.wr((self.regfile[x] // 10) % 10, self.I + 1)
            self.wr((self.regfile[x] // 100) % 10, self.I)
        elif inst & 0xf0ff == 0xf055:
            x = (inst & 0x0f00) >> 8
            for i in range(x + 1):
                print(i)
                self.wr(self.regfile[i], self.I + i)
        elif inst & 0xf0ff == 0xf065:
            x = (inst & 0x0f00) >> 8
            for i in range(x + 1):
                self.regfile[i] = self.mem[self.I + i]

    def dump(self):
        pp = []
        for i in range(16):
            if i != 0 and i % 8 == 0:
                pp += "\n"
            pp += " %3s: %08x" % ("x%x" % i, self.regfile[i])
        pp += "\n   I: %08x" % (self.I)
        pp += "\n  PC: %08x" % (self.pc)
        pp += "\nStack:"
        if self.sp == 0:
            pp += "\n(empty)"
        else:
            for i in range(self.sp):
                pp += '\n' + str(self.stack[self.sp - i - 1])
        print(''.join(pp))


if __name__ == '__main__':
    display = Display()
    c8 = chip8(display)
    debug = False
    # pygame.draw.rect(screen, (255, 255, 255), Rect(10, 10, 10, 10))
    instructions = open('/Users/edmundxin/dev/chip-8/chip8-python/tests/printa.txt', 'r')
    with open('/Users/edmundxin/dev/chip-8/chip8-python/tests/tetris.rom', 'rb') as test_binary:
        j = 0x200
        while (byte := test_binary.read(1)):
            c8.mem = c8.mem[:j] + byte + c8.mem[j:]
            j += 1

    if len(sys.argv) > 1:
        if sys.argv[1] == "-d":
            debug = True

    commandStack = []

    steps = 0
    listener = keyboard.Listener(
        on_press=c8.on_press,
        on_release=c8.on_release)
    listener.start()
    while True:
        c8.step()
        if debug:
            while True:
                if steps > 0:
                    print(steps)
                    steps -= 1
                    break
                command = input("(debug) ")
                # if command == '':
                #     command = commandStack[-1]
                #     print()
                if command and command.split(" ")[0] == "s":
                    instruction = int.from_bytes(c8.mem[c8.pc:c8.pc + 2], byteorder='big')
                    print("Current instruction: 0x%04x" % instruction)
                    print("PC: %08x" % (c8.pc))
                    commandStack.append('s')
                    if len(command.split(" ")) != 1:
                        steps = int(command.split(" ")[1])
                        print(steps)
                    break
                elif command == "p":
                    c8.dump()
                    commandStack.append('p')
                elif command == 'h':
                    print("Just kidding, there is no help")
                    commandStack.append('h')
                elif command == "c":
                    debug = False
                    commandStack.append('c')
                    break
                elif command == "d":
                    display.print_display()
                    commandStack.append('d')
                elif command and command[0] == "x":
                    params = command.split(" ")
                    if len(params) < 2:
                        print("Please include address to inspect")
                        break
                    addr = int(params[1], 16)
                    pp = []
                    for i in range(addr, addr + 128, 2):
                        if (i - addr) != 0 and (i - addr) % 16 == 0:
                            pp += "\n"
                        if (i - addr) % 16 == 0:
                            pp += "%08x: " % i
                        if (i - addr) % 2 == 0:
                            pp += " "
                        pp += c8.mem[i:i+2].hex().upper()
                    print(''.join(pp))
                    commandStack.append('x')
                else:
                    print('Command not found. Type (h) for help.')
        # c8.dump()
        
        time.sleep(0.005)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break;
    quit()
