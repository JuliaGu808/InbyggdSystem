import RPi.GPIO as GPIO
import time
from picamera import PiCamera
import os
import yagmail

PIR_PIN = 4
RED_PIN = 17
BLUE_PIN = 27
LOG_FILE_NAME = "/home/pi/camera/photo_logs.txt"

def take_photo(camera):
    file_name = "/home/pi/camera/img_" + str(time.time()) + ".jpg"
    camera.capture(file_name)
    return file_name

def update_photo_log_file(photo_file_name):
    with open(LOG_FILE_NAME, "a") as f:
        f.write(photo_file_name)
        f.write("\n")

def send_email_with_photo(yagmail_client, file_name):
    yagmail_client.send(to="test+t1@test.com",
                        subject="Movement detected!",
                        contents="Here's a photo taken by your Raspberry Pi",
                        attachments=file_name)

# Setup camera
camera = PiCamera()
camera.resolution = (720, 480)
camera.rotation = 180
print("Waiting 2 seconds to init the camera...")
time.sleep(2)
print("Camera setup OK.")

# Remove log file
if os.path.exists(LOG_FILE_NAME):
    os.remove(LOG_FILE_NAME)
    print("Log file removed.")

# Setup yagmail
password = ""
with open("/home/pi/.local/share/.email_password", "r") as f:
    password = f.read()
yag = yagmail.SMTP("test@test.com", password)
print("Email sender setup OK.")

# Setup GPIOs
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.output(RED_PIN, GPIO.LOW)
GPIO.setup(BLUE_PIN, GPIO.OUT)
GPIO.output(BLUE_PIN, GPIO.LOW)
print("GPIOs setup OK.")

MOV_DETECT_TRESHOLD = 3.0
last_pir_state = GPIO.input(PIR_PIN)
movement_timer = time.time()
current_timer = time.time()
LOOP_DURATION = 0.01
MIN_DURATION_BETWEEN_2_PHOTOS = 30.0
last_time_photo_taken = 0

print("Everything has been setup.")

try:
    while True:
        if time.time() - current_timer > LOOP_DURATION:
            current_timer = time.time()
            pir_state = GPIO.input(PIR_PIN)
            if pir_state == GPIO.HIGH:
                GPIO.output(RED_PIN, GPIO.HIGH) # check 3 sec led on
            else:
                GPIO.output(RED_PIN, GPIO.LOW)
            if last_pir_state == GPIO.LOW and pir_state == GPIO.HIGH: # begin move
                movement_timer = time.time()
            if last_pir_state == GPIO.HIGH and pir_state == GPIO.HIGH: # moving for 3 sec
                if time.time() - movement_timer > MOV_DETECT_TRESHOLD:
                    if time.time() - last_time_photo_taken > MIN_DURATION_BETWEEN_2_PHOTOS:
                        GPIO.output(BLUE_PIN, GPIO.HIGH)
                        print("Take photo and send it by email")
                        photo_file_name = take_photo(camera)
                        update_photo_log_file(photo_file_name)
                        send_email_with_photo(yag, photo_file_name)
                        GPIO.output(BLUE_PIN, GPIO.LOW)
                        last_time_photo_taken = time.time()
            last_pir_state = pir_state
except KeyboardInterrupt:
    GPIO.cleanup()
