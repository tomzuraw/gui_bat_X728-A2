#!/usr/bin/env python
import struct, os
import smbus
from sys import exit
import time, datetime
import RPi.GPIO as GPIO
from tkinter import *
import tkinter as tk
import tkinter.messagebox as tk_m
from idlelib.tooltip import Hovertip

# Global settings
# GPIO is 26 for x728 v2.0, GPIO is 13 for X728 v1.2/v1.3
gpio_port = 26
I2C_ADDR = 0x36

PLD_PIN = 6

GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.setup(PLD_PIN, GPIO.IN)
GPIO.setwarnings(False)

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

x_date = datetime.datetime.now()
year = x_date.year
image_temp = ''
bat_temp = ''
volt_temp = ''
i_temp = ''

v = '0.1'
program_name = 'Battery/Shutdown'
ver = f'{program_name} {v}'
ver_about = f'Copyright (c) {year}. Tomasz Zurawski\n' \
            '19kemot@gmail.com'
ver_about_comp = 'Raspberry Pi'

win_bat = tk.Tk()
win_bat.title(ver)
win_bat.iconphoto(True, PhotoImage(file=os.path.join('icon', 'battery.png')))
win_bat.option_add('*Dialog.msg.font', 'Piboto 12')
win_bat.resizable(width=False, height=False)
win_bat.configure(bg='#F0F0F0')
win_bat.tk_setPalette(background='#F0F0F0', foreground='black', activeBackground='black', activeForeground='#F0F0F0')

frm_welcome = tk.Frame(master=win_bat)
frm_welcome.grid(row=0, column=0)

frm_charge = tk.Frame(master=win_bat)
frm_charge.grid(row=3, column=0)

frm_image = tk.Frame(master=win_bat)
frm_image.grid(row=5, column=0)

frm_exit = tk.Frame(master=win_bat)
frm_exit.grid(row=10, column=0)


def read_voltage(bus_):
    address = I2C_ADDR
    read = bus_.read_word_data(address, 2)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 1.25 / 1000 / 16
    return voltage


def read_capacity(bus_):
    address = I2C_ADDR
    read = bus_.read_word_data(address, 4)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped / 256
    return capacity


def exit_gui():
    win_bat.destroy()
    exit()


def shut_down(var_):
    if var_ == 'reboot':
        if tk_m.askyesno('Exit', f'Do you want reboot!') is True:
            os.system('reboot')
    elif var_ == 'shutdown':
        if tk_m.askyesno('Exit', f'Do you want shutdown!') is True:
            os.system('poweroff')
    elif var_ == 'shutdown battery':
        if tk_m.askyesno('Exit', f'Do you want shutdown battery!') is True:
            GPIO.output(gpio_port, GPIO.HIGH)
            time.sleep(3)
            GPIO.output(gpio_port, GPIO.LOW)


def des_bottom_image(image_, hover_tip_):
    global image_temp

    if image_temp != image_:
        reset_widgets(frm_image)

        image = PhotoImage(file=image_)
        num_des = tk.Label(master=frm_image, image=image)
        Hovertip(num_des, hover_tip_)
        num_des.image = image
        num_des.grid(row=0, column=0)

    image_temp = image_


def label_volt():
    global bat_temp,volt_temp, i_temp

    i = GPIO.input(PLD_PIN)

    volt = "Voltage:%5.2fV" % read_voltage(bus)
    batt = "Battery:%5i%%" % read_capacity(bus)

    welcome_bat_stat = f' {volt} \n' \
                       f' {batt}'

    if bat_temp != batt or volt_temp != volt:

        reset_widgets(frm_welcome)
        welcome = tk.Label(master=frm_welcome, text=welcome_bat_stat)
        welcome.grid(row=0, column=0)

    bat_temp = batt
    volt_temp = volt

    if i_temp != i:

        reset_widgets(frm_charge)

        if i == 0:
            charge = tk.Label(master=frm_charge, text="AC Power OK")
            charge.grid(row=0, column=0)
            des_bottom_image(os.path.join('icon', 'battery_charge.png'), 'Battery: Charge')

        elif i == 1:
            charge = tk.Label(master=frm_charge, text="AC Power Lost")
            charge.grid(row=0, column=0)
    i_temp = i

    if i == 1:

        if read_capacity(bus) >= 75:

            des_bottom_image(os.path.join('icon', 'battery_100.png'), 'Battery: 75% - 100%')

        elif 75 > read_capacity(bus) >= 50:

            des_bottom_image(os.path.join('icon', 'battery_75.png'), 'Battery: 50% - 75%')

        elif 50 > read_capacity(bus) >= 25:

            des_bottom_image(os.path.join('icon', 'battery_50.png'), 'Battery: 25% - 50%')

        elif 25 > read_capacity(bus) >= 10:

            des_bottom_image(os.path.join('icon', 'battery_25.png'), 'Battery: 10% - 25%')

        elif 10 > read_capacity(bus) >= 5:

            des_bottom_image(os.path.join('icon', 'battery_10.png'), 'Battery: 5% - 10%')

        elif 5 > read_capacity(bus) >= 3:

            des_bottom_image(os.path.join('icon', 'battery_5.png'), 'Battery: 3% - 5%')

        elif read_capacity(bus) < 3:

            if read_voltage(bus) >= 3.01:
                des_bottom_image(os.path.join('icon', 'battery_3.png'), 'Battery: 0% - 3%\n'
                                                                        'If voltage low then 3.00V\n'
                                                                        'Shutdown 30s !')
            else:
                des_bottom_image(os.path.join('icon', 'battery_0.png'), 'Battery: 0%\n'
                                                                        'Shutdown 30s !')

                reset_widgets(frm_charge)
                charge = tk.Label(master=frm_charge, text=f"Shutdown: ~30s")
                charge.grid(row=0, column=0)
                i_temp = ''

                if read_voltage(bus) < 3.00:
                    time.sleep(30)

                    if read_voltage(bus) < 3.00:
                        GPIO.output(gpio_port, GPIO.HIGH)
                        time.sleep(3)
                        GPIO.output(gpio_port, GPIO.LOW)

    win_bat.after(10000, label_volt)


def reset_widgets(var_):
    for widget in var_.winfo_children():
        widget.destroy()


btn_exit = tk.Button(master=frm_exit, text='Reboot', command=lambda: shut_down('reboot'), width=17)
btn_exit.grid(row=5, column=1, padx=5, pady=2)

btn_exit = tk.Button(master=frm_exit, text='Shutdown', command=lambda: shut_down('shutdown'), width=17)
btn_exit.grid(row=6, column=1, padx=5, pady=2)

btn_exit = tk.Button(master=frm_exit, text='Shutdown Battery', command=lambda: shut_down('shutdown battery'), width=17)
btn_exit.grid(row=7, column=1, padx=5, pady=2)

btn_exit = tk.Button(master=frm_exit, text='Exit', command=exit_gui, width=17)
btn_exit.grid(row=8, column=1, padx=5, pady=2)

'''
while True:
     print("******************")
     print("Voltage:%5.2fV" % read_voltage(bus))
     print("Battery:%5i%%" % read_capacity(bus))
     if read_capacity(bus) == 100:
        print("Battery FULL")
     if read_capacity(bus) < 20:
        print("Battery Low")
        #Set battery low voltage to shut down, you can modify the 3.00 to other value
     if read_voltage(bus) < 3.00:
        print("Battery LOW!!!")
        print("Shutdown in 10 seconds")
        time.sleep(10)
        GPIO.output(GPIO_PORT, GPIO.HIGH)
        time.sleep(3)
        GPIO.output(GPIO_PORT, GPIO.LOW)
     time.sleep(2)'''

win_bat.after(1000, label_volt)

win_bat.mainloop()
