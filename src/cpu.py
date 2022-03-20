import pygame
from pygame.locals import *
import keyboard
import random
from enum import Enum
import time

class Display():
    def __init__(self):
        pygame.init()
        self.grid = [0] * 2048

        self.screen = pygame.display.set_mode((640, 320));
        self.screen.fill((0, 0, 0))


    def clear_display(self):
        self.display = [0] * 2048
        self.update_display()

    def update_display(self):
        for x in range(64):
            for y in range(32):
                if self.grid[x * 32 + y] == 1:
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
        val = self.stack[self.sp]
        self.sp -= 1
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
        
        # clear display
        if inst == 0x00e0:
            pass
        # return from subroutine
        elif inst == 0x00ee:
            self.pc = self.pop_stack()
        elif opcode == 0x1000:
            self.pc = inst & 0x0fff
        elif opcode == 0x2000:
            self.push_stack(self.pc)
            self.pc = inst & 0x0fff
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
            self.regfile[x] = self.regfile[x] + (inst & 0x00ff)
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
            self.regfile[x] = self.regfile[x] & self.regfile[y]
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
            if self.regfile[x] > self.regfile[y]:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = self.regfile[x] - self.regfile[y]
        elif inst & 0xf00f == 0x8006:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[x] & 0xf == 1:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = self.regfile[x] >> 1
        elif inst & 0xf00f == 0x8007:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if self.regfile[y] > self.regfile[x]:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
        elif inst & 0xf00f == 0x800e:
            x = (inst & 0x0f00) >> 8
            y = (inst & 0x00f0) >> 4
            if (self.regfile[x] & 0xf0) >> 4 == 1:
                self.regfile[0xf] = 1
            else:
                self.regfile[0xf] = 0
            self.regfile[x] = self.regfile[x] << 1
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
                while row != 0:
                    print(xcoord, ycoord)
                    if xcoord > 64:
                        break
                    if row & 1 == 1:
                        if self.display.grid[ycoord * 64 + xcoord] == 1:
                            self.display.grid[ycoord * 64 + xcoord] = 0
                            # self.display.clear_pixel(xcoord, ycoord)
                            self.regfile[0xf] = 1
                        else:
                            self.display.grid[ycoord * 64 + xcoord] = 1
                            # self.display.draw_pixel(xcoord, ycoord)
                    row = row >> 1
                    xcoord += 1
                ycoord += 1
            #pygame.display.update()
            self.display.update_display()
        elif inst & 0xf0ff == 0xe09e:
            x = (inst & 0x0f00) >> 8
            if keyboard.read_key() == self.regfile[x]:
                self.pc += 2
        elif inst & 0xf0ff == 0xe0a1:
            x = (inst & 0x0f00) >> 8
            if keyboard.read_key() != self.regfile[x]:
                self.pc += 2
        elif inst & 0xf0ff == 0xf007:
            x = (inst & 0x0f00) >> 8
            self.regfile[x] = self.dt
        elif inst & 0xf0ff == 0xf00a:
            x = (inst & 0x0f00) >> 8
            # TODO get keypress
            while True:
                if keyboard.is_pressed('q'):
                    break
        elif inst & 0xf0ff == 0xf015:
            x = (inst & 0x0f00) >> 8
            self.dt = self.regfile[x]
        elif inst & 0xf0ff == 0xf018:
            x = (inst & 0x0f00) >> 8
            self.st = self.regfile[x]
        elif inst & 0xf0ff == 0xf01e:
            x = (inst & 0x0f00) >> 8
            self.I = self.I + self.regfile[x]

    def dump(self):
        pp = []
        for i in range(len(self.regfile)):
            pp.append("0x" + str(i) + ": " + str(self.regfile[i]) + " ")
        print(''.join(pp))



if __name__ == '__main__':
    display = Display()
    c8 = chip8(display)
    # pygame.draw.rect(screen, (255, 255, 255), Rect(10, 10, 10, 10))
    instructions = open('../tests/printa.txt', 'r')
    lines = instructions.readlines()

    j = 0x200
    for i in range(0x200, 0x200 + len(lines)):
        op = int("0x" + lines[i - 0x200], 16)
        print(((op & 0xff00) >> 8).to_bytes(1, byteorder='big'))
        print((op & 0xff).to_bytes(1, byteorder='big'))
        c8.wr((op & 0xff00) >> 8, j, 1)
        c8.wr((op & 0xff), j + 1, 1)
        j += 2


    while True:
        c8.step()
        c8.dump()
        
        print('step')
        while True:
            if keyboard.is_pressed('q'):
                break
        display.draw_pixel(0, 0)
        display.draw_pixel(1, 1)
        display.draw_pixel(2, 2)
        display.draw_pixel(3, 3)
        display.draw_pixel(4, 4)
        pygame.display.update()
        time.sleep(0.1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break;
    quit()
