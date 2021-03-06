#!/bin/env python

import time 
import RPi.GPIO as GPIO
import bluetooth
import threading

FORWARD = 1
STOP = 3
BACKWARD = 2

LEFT = 4
RIGHT = 5
NONE = 6

def dir2string(dir):
    if dir == FORWARD:
        return "Forward"
    elif dir == BACKWARD:
        return "Backward"
    elif dir == STOP:
        return "Stop"
    else:
        return "UNKNOWN"

class MotorControl():

    def __init__(self, pin1, pin2, pin_eep=-1, braking_mode = True,
                 freq=50, verbose=False, name="DCMotorY"):
        """ init method
        """
        self.name = name
        self.pin1 = pin1
        self.pin2 = pin2

        self.verbose = verbose
        self.set_braking_mode(braking_mode)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)
        self.pwm1 = GPIO.PWM(self.pin1, freq)
        self.pwm2 = GPIO.PWM(self.pin2, freq)
        if pin_eep > 0: 
            GPIO.setup(pin_eep, GPIO.OUT)
            GPIO.output(pin_eep, True)

    def set_braking_mode(self, braking_mode):
        self.braking_mode = braking_mode

    def forward(self, speed=50):
        if self.braking_mode:
            self.pwm1.stop()
            GPIO.output(self.pin1, True)
            self.pwm2.start(100-speed)
        else:
            self.pwm2.stop()
            GPIO.output(self.pin2, False)
            self.pwm1.start(speed)

    def backward(self, speed=50):
        if self.braking_mode:
            self.pwm2.stop()
            GPIO.output(self.pin2, True)
            self.pwm1.start(100-speed)
        else:
            self.pwm1.stop()
            GPIO.output(self.pin1, False)
            self.pwm2.start(speed)

    def clean(self):
        self.pwm1.stop()
        self.pwm2.stop()



def motor_test():
    
    Motor1 = MotorControl(17, 27, -1, True, 500, False, "Moteurs de droite")
    Motor2 = MotorControl(6, 5, -1, True, 500, False, "Moteurs de gauche")

    try:
        for braking_mode in [True, False]:
            print("Braking mode = {}".format(braking_mode))
            Motor1.set_braking_mode(braking_mode)
            Motor2.set_braking_mode(braking_mode)

            for i in range(0, 101):
                print("Forward {}".format(i), end='\r')
                Motor1.forward(i)
                Motor2.forward(i)
                time.sleep(0.05)
            time.sleep(1)
            print()
            for i in range(0, 101):
                print("Backward {}".format(i), end='\r')
                Motor1.backward(i)
                Motor2.backward(i)
                time.sleep(0.05)
            time.sleep(1)
            print()
        
    except Exception as error:
            print(error)
            print("Unexpected error:")
    GPIO.cleanup()

class Blinker(threading.Thread):
    
    def __init__(self, LEDs):
        threading.Thread.__init__(self)
        self.LEDs = LEDs
        self._stop_event = threading.Event()
    
    def stop(self):
        self._stop_event.set()
        for LED in self.LEDs:
            GPIO.output(LED, False)

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        is_on = True
        while True:
            if self.stopped():
                return
            else:
                for LED in self.LEDs:
                    GPIO.output(LED, is_on)
                is_on = not is_on
                time.sleep(0.4)
            
class Car():

    def __init__(self):
        """ init method
        """
        # EEP is plugged to GPIO6 which managed by the x728 HAT, and is high only when the car is unplugged
        # This way, when we plug the car, the wheels automatically stop
        self.rightMotors = MotorControl(17, 27, -1, True, 500, False, "Moteurs de droite")
        self.leftMotors  = MotorControl(23, 24, -1, True, 500, False, "Moteurs de gauche")
        self.LEDs = [4, 18, 22, 25, 19, 16, 13, 21]
        self.current_blinker = None
        self.current_blink_dir = NONE

        for LED in self.LEDs:
            GPIO.setup(LED, GPIO.OUT)            
    
    def drive(self, dir, speed, angle):

#speed angle  left right
#    0 0   -> -100  100
#    0 90  ->    0    0
#    0 180 ->  100 -100
#  255 0   ->    0  100
#  255 90  ->  100  100
#  255 180 ->  100    0
# -255 0   -> -100    0
# -255 90  -> -100 -100
# -255 180 ->    0 -100

        rel_speed = speed
        rel_angle = angle
        if dir == BACKWARD:
            rel_speed = -speed
            rel_angle = 180-angle

        rel_speed = rel_speed * 100 / 255
        rel_angle = (rel_angle - 90) * 100 / 90

        left_speed  = int(min(max( rel_angle + rel_speed, -100), 100))
        right_speed = int(min(max(-rel_angle + rel_speed, -100), 100))

        # print("-> left={:+03d} right={:+03d}".format(left_speed, right_speed))
        
        if left_speed < 0:
            self.leftMotors.backward(-left_speed)
        else:
            self.leftMotors.forward(left_speed)
        if right_speed < 0:
            self.rightMotors.backward(-right_speed)
        else:
            self.rightMotors.forward(right_speed)


        if angle != 90:
            if angle < 90:
                self.blink(LEFT)
            else:
                self.blink(RIGHT)
        else:
            self.blink(NONE)


    def stop(self):
        GPIO.setmode(GPIO.BCM)
        self.drive(STOP, 0, 90)

    def set_front_lights(self, are_on):
        GPIO.output(self.LEDs[5], are_on)
        GPIO.output(self.LEDs[6], are_on)

    def set_rear_lights(self, are_on):
        GPIO.output(self.LEDs[1], are_on)
        GPIO.output(self.LEDs[3], are_on)

    def blink(self, DIR):
        if self.current_blink_dir != DIR:
            self.current_blink_dir = DIR
        else:
            return

        if self.current_blinker:
            self.current_blinker.stop()
        if DIR == NONE:
            return
        LEDs = None
        if DIR == RIGHT:
            LEDs = [self.LEDs[0], self.LEDs[4]]
        elif DIR == LEFT:
            LEDs = [self.LEDs[2], self.LEDs[7]]

        self.current_blinker = Blinker(LEDs)
        self.current_blinker.start()


car = Car()


def connection_lost():
    print("Connection Lost: stopping car")
    car.stop()

def main():
    while 1:
        car.stop()
        connection_lost_timer = threading.Timer(1, connection_lost)
        try:
            print("create server socket")
            server_socket=bluetooth.BluetoothSocket( bluetooth.RFCOMM ) 
            port = 1
            print("bind")
            server_socket.bind(("",port))
            print("listen")
            server_socket.listen(1)
            
            print("accept")
            client_socket,address = server_socket.accept()
            print ("Accepted connection from {}".format(address))

            previous_time = 0
            while 1:
                data = client_socket.recv(1024)
                current_time = time.time()
                connection_lost_timer.cancel()
                connection_lost_timer = threading.Timer(1, connection_lost)
                connection_lost_timer.start()
                # for byte in data[:4]:
                #     print("{} ".format(bin(byte)), end='')
                # print("delay = {}".format(current_time - previous_time))
                direction = data[0] & 3
                speed = data[1]
                angle = data[2]
                blue = (data[3] & 0b10000000) > 0
                red  = (data[3] & 0b1000000) > 0
                horn = (data[3] & 0b100000) > 0
                a    = (data[3] & 0b10000) > 0
                b    = (data[3] & 0b1000) > 0
                c    = (data[3] & 0b100) > 0
                # print("{:8s} speed={:03d} angle={:03d} delay={:.2f} {} {} {} {} {} {}".format(
                #   dir2string(direction), speed, angle, 
                #   current_time - previous_time,
                #   blue, red, horn, a, b, c))
                car.drive(direction, speed, angle)
                car.set_front_lights(blue)
                car.set_rear_lights(red)
                previous_time = current_time
                
            client_socket.close()
            server_socket.close()
        except bluetooth.btcommon.BluetoothError as btErr:
            #connection_lost_timer.cancel()
            print("Bluetooth disconnected")
            print(btErr)


if __name__ == '__main__':
    try:
        
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        # while True:
        #     for pin in [4, 18, 22, 25, 12, 16, 26, 21]:
        #         GPIO.setup(pin, GPIO.OUT)
        #         GPIO.output(pin, True)
        #         time.sleep(0.5)
        #         GPIO.output(pin, False)
        main()
    except KeyboardInterrupt:
        print("CTRL-C: Terminating program.")

    print("just before exiting")

    car.stop()
    # GPIO.cleanup()
    exit()
