"""
Orchid CLI 
A command line interface for the M5Stack Cardputer
Copyright 2024 T. Morris Jr.
MIT License
See /lib/doc/license.txt for license information
Orchid is not a clever name, I just like the way it sounds
"""

# import the required libraries
import os, time, machine, gc, network
from random import randint
from machine import Pin, SPI, SDCard, ADC
from lib import keyboard
from lib import st7789py as st7789
from fonts import vga1_8x16 as vga_small
from fonts import vga1_16x32 as vga_large
from fonts import vga1_bold_16x32 as vga_bold

# set up constants for;

# display
display_height = const(135)
display_width = const(240)
default_x = const(10)
small_length = const(26) #<-- need to use this to implement word wrap
large_lenght = const(14)

# small font rows:
small_row0 = const(112)
small_row1 = const(78)
small_row2 = const(61)
small_row3 = const(44)
small_row4 = const(27)
small_row5 = const(10)

# large font rows:
large_row0 = const(92)
large_row1 = const(51)
large_row2 = const(10)

# define a bunch of colors
black = const(0x0000)
blue = const(0x001F)
red = const(0xF800)
green = const(0x07E0)
cyan = const(0x07FF)
magenta = const(0xF81F)
yellow = const(0xFFE0)
white = const(0xFFFF)
violet = const(0x897B)
purple = const(0x48CF)
smoke = const(0x6B2D)
gray = const(0x3A2A)
orange = const(0xB8A1)
lime = const(0x07E0)
pink = const(0xF9B9)
fuchsia = const(0xF81F)
orchid = const(0xDCFA)
crt = const(0x1061)

# set up some variables
home_dir = os.getcwd()
current_dir = home_dir # set the current dir to home dir to start
prompt_char = ">"      # establish the prompt character
previous_value = ""    # used in text_get()
prompt = current_dir+prompt_char # establish the prompt

# open the config file and store each line in a variable
with open("/sys/files/config.txt", "r") as f:
    lines = [lines for lines in f]
    bg_color = lines[0]  #<-- background color
    fg_color = lines[1]  #<-- text color
    hi_color = lines[2]  #<-- highlight color
    pr_color = lines[3]  #<-- prompt color
    automount = lines[4] #<-- automount the SD card?
    bt_enable = lines[5] #<-- enable Bluetooth, not yet implemented
    ssid = lines[6]      #<-- saved ssid     if ssud and pwrd are not none, 
    pwrd = lines[7]      #<-- saved pasword  we will autoconnect to wifi

# init the display driver
spi = SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None)
tft = st7789.ST7789(
    spi,
    display_height,
    display_width,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789.BGR
    )

# init the keyboard
kb = keyboard.KeyBoard()
current_keys = []
previous_keys = []

# check automount and if set to True, mount the SD card
if "sd" not in home_dir and automount == True:
    try:
        sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
        os.mount(sd, "/sd")
    except:
        tft.fill(black)
        tft.text(vga_small, prompt+"SD mount fail!", default_x, small_row0, red, black)

# after all that, let's run the garbage collector:
gc.collect()

# define our functions

# the command parser
# at some point the parser should be able to tell you that
# a proper command was given, but not the correct number of
# arguments, but that's a problem for future me.
def parser(value):

    zero_list = ['batt','clean','clear','clock','flip','history','lock',
             'mount','scan','scandump','space','system','umount']

    one_list = ['bg_color','bright','captive','chdir','env_get','exe','fg_color',
            'help','hi_color','list','mkdir','mkfile','net','rmdir',"roll",'sound',
            'speed','vol']

    two_list = ['alias','copy','env_set','ping','redir']

    value_list = value.split()           #<-- turn value into a list
    command = value_list[0].lower()      #<-- make sure that command is lower case
    if len(value_list) == 1:             #<-- branch by length
        if command not in zero_list:
            usr_msg("Command not found!")  
        if command in zero_list:         
            eval("o_"+command+"()")
    if len(value_list) == 2:
        param1 = value_list[1]
        if command not in one_list:
            usr_msg("Command not found!")
        if command in one_list:
            eval("o_"+command)(param1)
    if len(value_list) == 3:
        param1 = value_list[1]
        param2 = value_list[2]
        if command not in two_list:
            usr_msg("Command not found!")
        if command in two_list:
            eval("o_"+command)(param1, param2)
    if len(value_list) > 3:
        usr_msg("Too many parameters!")
    if len(value_list) == 0:
        usr_msg("No command given!")

# program functions
def usr_msg(msg, pos, color):
    tft.fill(bg_color)
    tft.text(vga_small, msg, default_x, pos, color, bg_color)
    text_get()

def multi_msg(msgs, color):
    # when calling multi_msg, something needs to be
    # passed for each line to avoid an error
    tft.fill(bg_color)
    tft.text(vga_small, msgs[0], default_x, small_row5, color, bg_color)
    tft.text(vga_small, msgs[1], default_x, small_row4, color, bg_color)
    tft.text(vga_small, msgs[2], default_x, small_row3, color, bg_color)
    tft.text(vga_small, msgs[3], default_x, small_row2, color, bg_color)
    tft.text(vga_small, msgs[4], default_x, small_row1, color, bg_color)
    tft.text(vga_small, msgs[5], default_x, small_row0, color, bg_color)
    text_get()

def charge_screen():
    # make the screen black and turn off the backlight for charging
    # or go back to the prompt
    p38 = Pin(38, Pin.OUT)
    if p38.value() == 1:
        tft.fill(bg_color)
        p38.value(0)
    else:
        p38.value(1)
        tft.fill(black)
        tft.text(vga_small, prompt+"", default_x, small_row0, fg_color, bg_color)
        text_get()

# command functions
# zero parameter functions
def o_batt():
    # display battery information - needs work
    adc = ADC(10)
    lvl = adc.read_uv()
    print(lvl)
    text_get()

def o_clean():
    # clear the screen and run garbage collection
    tft.fill(bg_color)
    tft.text(vga_small, prompt+"", default_x, small_row0, fg_color, bg_color)
    gc.collect()
    text_get()

def o_clear():
    # clear the screen
    tft.fill(bg_color)
    tft.text(vga_small, prompt+"", default_x, small_row0, fg_color, bg_color)
    text_get()

def o_clock():
    # show the date and time
    # so far, I've not come up with a clock that I like
    pass

def o_flip(): 
    # flip a coin, get heads or tails
    if randint(0,1) == 1:
        usr_msg("Heads", small_row0, fg_color)
    else:
        usr_msg("Tails", small_row0, fg_color)
    text_get()

def o_history():
    # display the command history on the screen
    # I should do this with a list and send it to multi_msg()
    pass

def o_lock():
    # make the screen black and wait for keyboard input to ask for a password
    # not sure how much I need this with the G0 button
    pass

def o_mount():
    # Check to see if the SD card is mounted. if it is, let the user know, if not mount it.
    if "sd" not in os.listdir("/"):
        sd = SDCard(slot=2, sck=Pin(40), miso=Pin(39), mosi=Pin(14), cs=Pin(12))
        os.mount(sd, "/sd")
        usr_msg("SD Mounted!", small_row0, blue)
    text_get()

def o_scan():
    # this isn't going to work very well, as it will need more room
    # than the screen can give us. Perhaps I should kill this and
    # just use the scandump function instead.
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    authmodes = ['Open', 'WEP', 'WPA-PSK' 'WPA2-PSK4', 'WPA/WPA2-PSK']
    for (ssid, bssid, channel, RSSI, authmode, hidden) in sta_if.scan():
        line0 = "* {:s}".format(ssid)
        line1 = "   - Auth: {} {}".format(authmodes[authmode], '(hidden)' if hidden else '')
        line2 = "   - Channel: {}".format(channel)
        line3 = "   - RSSI: {}".format(RSSI)
        line4 = "   - BSSID: {:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(*bssid)
        line5 = ""
    msgs = [line0, line1, line2, line3, line4, line5]
    multi_msg(msgs, yellow)

def o_scandump():
    # just like scan, but also dumps the data to a file on the SD card
    pass

def o_space():
    # get information about the SD card's total and available space
    """
    import os
    os.statvfs('/')
    (4096, 4096, 348, 329, 329, 0, 0, 0, 0, 255)

    so,
    4096 * 348 is total space in bytes
    4096 * 329 is free space in bytes
    used space = total - free"""
    pass

def o_system():
    # display useful information about the hardware and software system
    pass

def o_umount():
    # check to see if the SD card is mounted. If not, let the user know, otherwise unmount it.
    if "sd" in os.listdir("/"):
        os.umount("/sd")
        usr_msg("SD Unmounted!", small_row0, blue)
    else:
        usr_msg("SD was not mounted!", small_row0, red)
    text_get()

# single parameter functions
def o_bg_color(color):
    # accepts either a named color, or a hex color for the background color
    lines[0] = color
    usr_msg(f"bg_color={bg_color}", small_row0, color)
    text_get()

def o_bright(amount):
    # accepts a number between 0 and 100 to set the screen brightness
    pass

def o_captive(cap_ssid):
    # this will kill any wifi connection, initiate a server, and provide a web page
    # to anyone that connects with it. I plan to place the web site on the SD card
    # and use it to serve files and documentation for MicroPython, Cardputer, and 
    # other files that a user of the device might find useful.
    pass

def o_chdir(path_to_dir):
    # change the current working directory to the specified directory
    os.chdir(path_to_dir)
    text_get()

def o_env_get(env_var):
    # prints the value of the environment variable provided
    pass

def o_exe(path_to_file):
    # used to run an external python file
    # I know that exec() is considered unsafe, 
    # but a single Cardputer isn't going to be 
    # used by multiple users.
    gc.collect()
    exec(open(path_to_file).read())
    text_get()

def o_fg_color(color):
    # accepts either a named color or a hex value to set the foreground color
    lines[1] = color
    usr_msg(f"fg_color={fg_color}", small_row0, color)
    text_get()

def o_help(command):
    # displays a common usage of the given command
    # need to create a dict that contains our command and usage
    # pairs for this function and formats the usage as a multiline
    # for clear viewing
    pass

def o_hi_color(color):
    # accepts either a named color or a hex value to set the highlight color
    lines[2] = color
    usr_msg(f"hi_color={hi_color}", small_row0, color)
    text_get()

def o_list(path_to_dir):
    # expects either current or cur to get the contents of the current working directory
    # or it will accept a path to a directory and display its contents
    pass

def o_mkdir(path_to_dir):
    # make a directory at the given location
    os.mkdir(path_to_dir)
    text_get()

def o_mkfile(path_to_file):
    f = open(path_to_file, "w")
    f.close()
    text_get()
        

def o_net(action):
    # expects either connect (con), disconnect (dis), or status (stat)
    #to connect, disconnect or show the status of the network connection
    if action == "connect" or "con":
        pass
    if action == "disconnect" or "dis":
        pass
    if action == "status" or "stat":
        pass
    text_get()

def o_rmdir(path_to_dir):
    # remove the specified file or directory
    # should warn and ask for confirmation before removal
    os.rmdir(path_to_dir)
    text_get()

def o_roll(dice):
    # roll ndf, where n is the number of dice
    # d means die
    # f is the number of faces the die has
    roll_list = dice.split('d')
    die = int(roll_list[1])
    die_name = "d" + roll_list[1]
    die_list = ["d2", "d4", "d6", "d8", "d10", "d12", "d20", "d100"]
    if die_name not in die_list:
        pass
    else:
        rolls = [randint(1, die) for _ in range(int(roll_list[0]))]
    usr_msg(rolls, small_row0, green)

def o_sound(wavfile):
    # this will likely not be implemented until the next stable
    # version of MicroPython
    pass

def speed(speed):
    #expects fast (or 240) or slow (or 160)
    if speed == "fast" or "240":
        machine.freq(240000000)
    if speed == "slow" or "160":
        machine.freq(160000000)
    text_get()

def o_vol(amount):
    # like bright, accepts a number between 0 and 100 to set the system volume
    # like sound, this will likely not be implemented, yet
    pass

#double parameter functions
def o_alias(old_alias, new_alias):
    # change the command word for something into something else, will use an alias.txt file
    pass

def o_copy(origin, destination):
    # copy the origin file to the destination location
    pass

def o_env_set(env_var, param):
    # set the environment variable provided to the parameter given.
    pass

def o_ping(ip, times):
    # ping the given IP or URL the given number of times
    pass

def o_redir(old_name, new_name):
    # rename the file or directory specified
    os.rename(old_name, new_name)
    text_get()

def text_get():
    # yeah, I know we aren't really supposed to use global variables
    # but this was the only way I could get this to work reliably.
    global current_keys, previous_keys, previous_value
    current_value = previous_value
    while True:
        current_keys = kb.get_pressed_keys()
        if current_keys != previous_keys:
            if "GO" in current_keys and "GO" not in previous_keys:
                charge_screen()
                
            elif "BSPC" in current_keys and "BSPC" not in previous_keys:
                current_value = current_value[0:-1]
                tft.fill(black)
                tft.text(vga_small, prompt+current_value, 10, 112, fg_color, bg_color)
                
            elif "SPC" in current_keys and "SPC" not in previous_keys:
                current_value = current_value + ' '
                
            elif "ENT" in current_keys and "ENT" not in previous_keys:
                value = current_value
                current_value = ""
                if value == "":
                    usr_msg("Give nothing, get nothing", yellow)
                else:
                    parser(value)
                
            else:
                for key in current_keys:
                    if len(key) == 1 and key not in previous_keys:
                        current_value += key
                        tft.fill(black)
                        tft.text(vga_small, prompt+current_value, 10, 112, orchid, black)
                        
            previous_keys = current_keys
            time.sleep_ms(40) #<-- prevent repeated keys
    
text_get()