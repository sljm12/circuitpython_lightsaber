import board
import busio
import adafruit_lsm303_accel
import adafruit_lsm303dlh_mag
import time
from digitalio import DigitalInOut, Direction, Pull
from adafruit_debouncer import Debouncer

class LightSaber:
    POWERDOWN_STATE = 0
    ON_STATE = 1
    TURN_OFF_STATE = 2
    HUM_STATE = 3
    PLAYING_HUM_STATE = 4
    SWING_STATE = 5
    CLASH_STATE = 6
    
    def __init__(self, uart, accel, busypin,on_off_pin):
        self.uart = uart
        self.accel = accel
        self.pre_accel = accel.acceleration
        self.state= self.POWERDOWN_STATE
        self.busy_pin = DigitalInOut(busypin)
        self.busy_pin.direction = Direction.INPUT
        self.prev_state = self.POWERDOWN_STATE
        
        self.on_off_pin = DigitalInOut(on_off_pin)
        self.on_off_pin.direction=Direction.INPUT
        self.on_off_pin.pull=Pull.UP
        self.on_off = Debouncer(self.on_off_pin)
        self.on_off_state = False
        
        self.pre_accel=self.accel.acceleration
        self.current_accel = None
        self.swinging = False
        self.swing_counter = 0
        
    def switch_on(self):
        #self.play_track(2)
        self.state = self.ON_STATE
    
    def play_track(self,num):
        self.write_data(0x03,num)
        return ls.read()
    
    def repeat_play(self):
        self.write_data(0x11,1)
        return ls.read()
    
    def stop_repeat_play(self):
        self.write_data(0x11,1)
        return ls.read()
    '''
    def is_playing(self):
        return True if self.busy_pin.value
    '''     
    def write_data(self, cmd, dataL=0, dataH=0):
        self.uart.write(b'\x7E')        # Start
        self.uart.write(b'\xFF')        # Firmware version
        self.uart.write(b'\x06')        # Command length
        self.uart.write(bytes([cmd]))   # Command word
        self.uart.write(b'\x00')        # Feedback flag
        self.uart.write(bytes([dataH])) # DataH
        self.uart.write(bytes([dataL])) # DataL
        self.uart.write(b'\xEF')        # Stop

    def read(self):
        n = self.uart.in_waiting
        if n > 0:
            return self.uart.read(n)
        else:
            return None
    
    def check_on_button(self):
        self.on_off.update()
        if self.on_off.fell:
            if self.on_off_state is False:
                self.on_off_state = True
                self.state = self.ON_STATE
            else:
                self.state=self.TURN_OFF_STATE
                self.on_off_state = False
    
    def swing(self):
        self.current_accel = self.accel.acceleration
        (x1,y1,z1) = self.pre_accel
        (x2,y2,z2) = self.current_accel
        
        r=[i for i in [abs(x1-x2), abs(y1-y2), abs(z1-z2)] if i > 6]
        self.pre_accel = self.accel.acceleration
        
        if len(r) > 1:
            print(r)
        is_swinging = True if len(r) >=1 else False
        if self.swinging is False and is_swinging:
            self.swinging = True
            self.swing_counter=0
            return is_swinging
        elif self.swinging is True:
            self.swing_counter = self.swing_counter + 1
            if self.swing_counter > 50:
                print("End Swing")
                self.swinging = False
                self.swing_counter = 0
            return False
        else:
            return False
    
    def update_swing(self):
        if self.state == self.POWERDOWN_STATE:
            pass
        else:
            if self.swing():
                print("Swing")
                self.state=self.SWING_STATE
    
    def update_loop(self):
        self.check_on_button()
        self.update_swing()
        if self.accel.tapped and self.state != self.CLASH_STATE:
            print("Tapped!\n")
            self.state=self.CLASH_STATE
            
        #print(self.prev_state,self.state, self.busy_pin.value)
        if self.state == self.ON_STATE:
            print("Play on track")
            self.play_track(2)
            self.prev_state = self.ON_STATE
            time.sleep(2)
            self.state=self.HUM_STATE
        elif self.state==self.HUM_STATE:
            #print("HUM state")
            #self.state=self.PLAYING_HUM_STATE
            pass
        elif self.state==self.PLAYING_HUM_STATE and self.busy_pin.value is True:
            print("Playing HUM state")
            self.play_track(3)
            time.sleep(0.2)
        elif self.state == self.TURN_OFF_STATE:
            print("Turn Off")
            self.play_track(2)
            time.sleep(2)
            self.state=self.POWERDOWN_STATE
        elif self.state == self.CLASH_STATE:
            self.play_track(4)
            time.sleep(1)
            #self.state=self.PLAYING_HUM_STATE
            self.state=self.HUM_STATE
        elif self.state==self.SWING_STATE:
            self.play_track(1)
            time.sleep(1)
            self.state=self.HUM_STATE
        #time.sleep(0.1)

def swing(pre, current):
    (x1,y1,z1) = pre
    (x2,y2,z2) = current
    r=[i for i in [abs(x1-x2), abs(y1-y2), abs(z1-z2)] if i > 1]
    return True if len(r) >=1 else False

#--- Init LSM303
i2c = board.I2C()
#i2c = busio.I2C(board.GP17, board.GP16)
mag = adafruit_lsm303dlh_mag.LSM303DLH_Mag(i2c)
accel = adafruit_lsm303_accel.LSM303_Accel(i2c)
accel.range = adafruit_lsm303_accel.Range.RANGE_8G
accel.set_tap(1, 30)
previous =accel.acceleration
swing_state = False
swing_counter = 0

#--- Init MP3
uart = busio.UART(board.TX,board.RX,baudrate=9600)
ls=LightSaber(uart, accel,board.D9, board.D10)
time.sleep(2)
print("play humming")
#ls.write_data(0x09) # Use
#ls.read()
#ls.switch_on()
#time.sleep(2)
#ls.play_track(3)
while True:
    ls.update_loop()
'''
print(ls.play_track(3))
while True:
    if accel.tapped:
        print("Tapped!\n")
    current = accel.acceleration
    if swing_state is False:
        if swing(previous, current) is True:
            swing_state=True
            swing_counter=0
            print("Swing")
            ls.play_track(1)
    if swing_state is True:
        if swing_counter > 10:
            swing_counter = 0
            swing_state = False
            print("End Swing")
        else:
            swing_counter=swing_counter+1
    previous = current
    time.sleep(0.1)
'''
'''
while True:
    print("Acceleration (m/s^2): X=%0.3f Y=%0.3f Z=%0.3f"%accel.acceleration)
    print("Magnetometer (micro-Teslas)): X=%0.3f Y=%0.3f Z=%0.3f"%mag.magnetic)
    time.sleep(0.1)
'''