import board
import busio
import adafruit_lsm303_accel
import adafruit_lsm303dlh_mag
import time
from digitalio import DigitalInOut, Direction

class LightSaber:
    OFF_STATE = 0
    ON_STATE = 1
    HUM_STATE = 2
    SWING_STATE = 3
    CLASH_STATE = 4
    
    def __init__(self, uart, accel, busypin):
        self.uart = uart
        self.accel = accel
        self.pre_accel = accel.acceleration
        self.state= self.OFF_STATE
        self.busy_pin = DigitalInOut(busypin)
        self.busy_pin.direction = Direction.INPUT
        self.prev_state = self.OFF_STATE
    
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
        
    def update_loop(self):
        print(self.prev_state,self.state, self.busy_pin.value)
        if self.state == self.ON_STATE:
            print("Play on track")
            self.play_track(2)
            self.prev_state = self.ON_STATE
            time.sleep(2)
            self.state=self.HUM_STATE
        elif self.state==self.HUM_STATE and self.busy_pin.value is True:
            print("playing Hum track busy True")
            self.play_track(3)
        time.sleep(0.1)

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
ls=LightSaber(uart, accel,board.D9)
time.sleep(2)
print("play humming")
#ls.write_data(0x09) # Use
#ls.read()
ls.switch_on()
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