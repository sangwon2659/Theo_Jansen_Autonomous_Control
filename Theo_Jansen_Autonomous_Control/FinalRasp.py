# -*- coding: utf-8 -*-
"""
Created on Mon Dec 10 09:34:32 2018

@author: Sangwon Lee
"""

import io
import socket
import struct
import time
import picamera
import argparse
import cv2
import numpy as np
import RPi.GPIO as GPIO
parser = argparse.ArgumentParser(description='Press IP adress and Port number')
parser.add_argument('-ip', type=str ,default = '165.132.138.161')
parser.add_argument('-port', type=int, default = 8888)

motor1A=16
motor1B=18
motor2A=13
motor2B=15
GPIO_TRIGGER = 38
GPIO_ECHO    = 40

GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_TRIGGER,GPIO.OUT)
GPIO.setup(GPIO_ECHO,GPIO.IN)
GPIO.setup(motor1A,GPIO.OUT)
GPIO.setup(motor1B,GPIO.OUT)
GPIO.setup(motor2A,GPIO.OUT)
GPIO.setup(motor2B,GPIO.OUT)

"""GPIO.PWM : motor 1A, 600Hz"""
p1A = GPIO.PWM(motor1A,600)
p1A.start(0)
p1B = GPIO.PWM(motor1B,600)
p1B.start(0)
p2A = GPIO.PWM(motor2A,600)
p2A.start(0)
p2B = GPIO.PWM(motor2B,600)
p2B.start(0)

a = parser.parse_args()
ip = a.ip
port = a.port
# create socket and bind host
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client_socket.connect(('165.132.138.161', 9999))
client_socket.connect((ip, port))
connection = client_socket.makefile('wb')

def measure():
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start=time.time()
    while GPIO.input(GPIO_ECHO)==0:
        start=time.time()
    while GPIO.input(GPIO_ECHO)==1:
        stop=time.time()
    elapsed=stop-start
    distance=(elapsed*34300)/2
    print(distance)
    return distance

try:
    with picamera.PiCamera() as camera:
        camera.resolution = (320, 240)
        camera.vflip = True
        camera.hflip = True
        camera.framerate = 10
        time.sleep(2)
        start = time.time()
        stream = io.BytesIO()
        # send jpeg format video stream
        count=0
        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port = True):
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            stream.seek(0)
            image_bytes=stream.read()
            connection.write(image_bytes)
			

            if time.time() - start > 600:
                break
            stream.seek(0)
            #read image from stream data
            stream.truncate()
            connection.write(struct.pack('<L', 0))
            if count>=5:	
                data = client_socket.recv(1024)
                print(data)
              	try:				
					distance = measure()
                except:
                    continue
                if distance < 5:
                    p1A.ChangeDutyCycle(0)
                    p1B.ChangeDutyCycle(0)
                    p2A.ChangeDutyCycle(0)
                    p2B.ChangeDutyCycle(0)
                    
                if data=="stop":
                    p1A.ChangeDutyCycle(0)
                    p1B.ChangeDutyCycle(0)
                    p2A.ChangeDutyCycle(0)
                    p2B.ChangeDutyCycle(0)
                    
                elif data=="forward":
                    p1A.ChangeDutyCycle(0)#which leg?left
                    p1B.ChangeDutyCycle(78)#straight
                    p2A.ChangeDutyCycle(100)#which leg?right/straight
                    p2B.ChangeDutyCycle(0)
                    
                elif data=="turn left":
                    p1A.ChangeDutyCycle(60)
                    p1B.ChangeDutyCycle(0)#left straight
                    p2A.ChangeDutyCycle(73)#right straight
                    p2B.ChangeDutyCycle(0)
                        
                elif data=="turn right":
                    p1A.ChangeDutyCycle(0)
                    p1B.ChangeDutyCycle(95)#left straight
                    p2A.ChangeDutyCycle(75)#right straight
                    p2B.ChangeDutyCycle(0)
                        
                elif data=='back ward':
                    p1A.ChangeDutyCycle(78)
                    p1B.ChangeDutyCycle(0)#left straight
                    p2A.ChangeDutyCycle(0)#right straight
                    p2B.ChangeDutyCycle(100)
                else :
                    data = client_socket.recv(1024)
                    p1A.ChangeDutyCycle(0)
                    p1B.ChangeDutyCycle(0)
                    p2A.ChangeDutyCycle(0)
                    p2B.ChangeDutyCycle(0)
                time.sleep(0.025)
            count+=1

            image = cv2.imdecode(np.fromstring(image_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            #cv2.imshow('image', image)
            cv2.waitKey(1) & 0xff

finally:
    connection.close()
    client_socket.close()