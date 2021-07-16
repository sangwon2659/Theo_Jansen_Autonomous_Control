# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 00:03:24 2018
@author: Sangwon Lee
"""

import threading
import SocketServer
import cv2
import numpy as np
import socket
import time

mode = "No object"
class ObjectDetection(object):
    def detectTUMB(self, cascade_classifier, gray_image, image):
        mode="No object"
        cascade_obj = cascade_classifier.detectMultiScale(
            gray_image,
            scaleFactor=1.02,
            minNeighbors=5,
            minSize=(16,16),
        )
        for (x_pos, y_pos, width, height) in cascade_obj:
            if(width<=40):
                cv2.rectangle(image, (x_pos, y_pos), (x_pos+width, y_pos+height), (255, 255, 255), 2)
                cv2.putText(image, 'stopsign', (x_pos, y_pos-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                mode="stop"
        return mode

def select_white(image, white):
    lower = np.uint8([white, white, white])
    upper = np.uint8([255,255,255])
    white_mask = cv2.inRange(image,lower,upper)
    return white_mask
                  
def line_direction(image, upper_limit):
    height,width = image.shape
    height = height -1 #the result of height is 239
    center = int(width/2)
    left = 0
    right =width
    white_distance = np.zeros(width)

    valid_r=0
    valid_l=0
    for i in range(center):
        if image[height-30, center- i] > 200 and valid_l==0: # the reason height-30: casue the view which camera watches is round so throw away of bottom part
            left = center - i +10
            valid_l=1
        if image[height-30, center + i] > 200 and valid_r==0:
            right=center+i
            valid_r=1
        if valid_r==1 and valid_l==1:
            break
    left=int(left) ; right=int(right)
    center= int((left+right)/2)  
    
    c=0
    d=0 
    for i in range(left, right):
        for j in range(upper_limit):
            if image[height-j, i] > 200:
                white_distance[i] = j
                if j >= 140:
                    print(j)
                    c+=1
                break
            if j >= upper_limit-1 :
                white_distance[i]=j
                
                break
            if c>0:
                d= 'forward'
    


    result = 'forward'
    left_sum= np.sum(white_distance[left:center])
    right_sum= np.sum(white_distance[center:right])
    forward_sum = np.sum(white_distance[center-10:center+10])
    print(left_sum,forward_sum,right_sum ) ; print(left,center,right)

    if d == 'forward':
        result = 'forward' ; print(0)
    elif center == 165  or left == 0 and left_sum > right_sum +1000 :
        result = 'turn left'
    elif left_sum == 0 or right_sum == 0 or forward_sum == 0:
        result = 'back ward'
    elif center > 200 and right == 320 and left_sum > right_sum:
        result = 'turn left'
    elif left > 80 and center > 120 or right_sum > 13000:
        result = 'turn right'
    elif forward_sum > 1900 and abs(left_sum - right_sum < 500):
        result = 'forward'
    #elif right_sum > left_sum + 1500:
    #    result = 'turn right' ; print(6)
    #elif left_sum  > right_sum + 1500:
    #    result = 'turn left' ; print(7)
    else:
        result='forward'
    return result, left_sum, right_sum, forward_sum

green = [99,98,94]
red = [45,58,96]
lower_green=np.array([98,97,93])
upper_green=np.array([100,99,95])
lower_red=np.array([44,57,95])
upper_red=np.array([46,59,97])

class VideoStreamHandler(SocketServer.StreamRequestHandler):
    obj_detection = ObjectDetection()
    stopsign_cascade=cv2.CascadeClassifier('cascade_xml/casade.xml')
    #we use what computer learned write position of the file and file name too
    def handle(self):
        stream_bytes = ' '
        try:
            valid=0
            k=0
            while True:
                global mode
                green = [99,98,94]
                red = [45,58,96]
                lower_green=np.array([98,97,93])
                upper_green=np.array([100,99,95])
                lower_red=np.array([44,57,95])
                upper_red=np.array([46,59,97])
                stream_bytes += self.rfile.read(1024)
                first = stream_bytes.find('\xff\xd8')
                last = stream_bytes.find('\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last+2]
                    stream_bytes = stream_bytes[last+2:]
                    gray = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),  cv2.IMREAD_GRAYSCALE)
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
                    '''mask = cv2.inRange(hsv, lower_green, upper_green)
                    mask1 = cv2.inRange(hsv, lower_red, upper_red)
                    print(mask)
                    print(mask[0])
                    print(len(mask[0]))
                    print(hsv[0][0][green])'''
                    x=0
                    for i in range(50,160):
                        for j in range(20,100):
                            if hsv[j][i][0] == green[0] and hsv[j][i][1] == green[1] and hsv[j][i][2] == green[2]:
                                print('a')
                            else:
                                continue
                                try:
                                    for k in range(40):
                                        q=j-k
                                        if hsv[q][i][0]==red[0] and hsv[q][i][1]==red[1] and hsv[q][i][2]==red[2]:
                                            print('b')
                                            x+=1
                                except:
                                    continue
                    masked_image=select_white(image,150)
                    a=line_direction(masked_image,100)
                    print(x)
                    if x > 1000:
                        print('Redlight')
                        mode='stop'
                    elif self.obj_detection.detectTUMB(self.stopsign_cascade, gray, image)=='stop':
                        print('a')
                        print('Stopsign')
                        mode='stop'
                    elif k > 5:
                        mode = 'forward' ; k=0 ; print('ssd')
                    elif a[0] == 'forward':
                        mode='forward' ; k=0
                    elif a[0] == 'turn left':
                        mode='turn left' ; k+=1
                    elif a[0] == 'turn right':
                        mode='turn right'; k+=1
                    elif a[0] == 'back ward':
                        mode='back ward' ; k=0
                    print(k)
                    else:
                        print('replay')
                    
                        
                    #image_h, image_w,channels = image.shape
                    
                    cv2.imshow('image', image)
                    cv2.imshow('wb', masked_image)
                    cv2.waitKey(1) & 0xFF
                    valid=1
                    time.sleep(0.09)
                if valid ==1:
                    self.request.send(mode)
                    print(mode)
                    valid=0
            cv2.destroyAllWindows()
        finally:
            print "Connection closed on thread 1"

class ThreadServer(object):
    def server_thread(host, port):
        server = SocketServer.TCPServer((host, port), VideoStreamHandler)
        server.serve_forever()
    ip=socket.gethostbyname(socket.getfqdn())
    print(ip)
    video_thread = threading.Thread(target=server_thread(ip, 8888))
    video_thread.start()

if __name__ == '__main__':
    ThreadServer()
