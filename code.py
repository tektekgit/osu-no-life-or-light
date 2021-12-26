# Server/AppDaemon
import hassapi as hass
class osu_automations(hass.Hass):
    def initialize(self):
        self.log("osu! Automations by Siwat Sirichai")
        self.listen_state(self.osu_changed, "binary_sensor.osu_gamingpc")
    def osu_changed(self, entity, attribute, old, new, kwargs):
        if new == "on":
            self.speak("osu mode activated")
            self.turn_on("script.osu_mode")
        elif new == "off":
            self.call_service("cover/open_cover",entity_id="cover.laboratory_curtain_native")
            self.speak("osu mode deactivated")
            if self.isNight():
                self.turn_on("scene.laboratory_warm")
            else:
                self.turn_on("scene.laboratory_bright")
    def isNight(self) -> bool:
        if self.get_state("sun.sun") == "below_horizon":
            return 1
        return 0
    def speak(self, message: str):
        self.call_service("tts/google_cloud_say",entity_id="media_player.laboratory_display",message=message)
# Client
from multiprocessing.spawn import freeze_support
import os
import multiprocessing
import time
import subprocess
import win32gui, win32gui, win32process
import paho.mqtt.client as mqtt
import mqttauth
import psutil
 
timeout = 16
executuables = {"osuSync":"Y:\osu!\Sync.exe","tabletDriver":"Y:\OpenTabletDriver.win-x64\OpenTabletDriver.Daemon.exe"}
process = {}
 
client = mqtt.Client()
client.username_pw_set(mqttauth.username,password=mqttauth.password)
client.connect(mqttauth.server, 1883, 60)
 
# Hide Console Windows
def hide(hwnd, pid):
  if win32process.GetWindowThreadProcessId(hwnd)[1] == pid:
    # hide window
    win32gui.ShowWindow(hwnd, 0)
 
# find hwnd of parent process, which is the cmd.exe window
win32gui.EnumWindows(hide, os.getppid())
 
# This Function will check the Status of the osu! folder
# The operation may result in a program freeze so it should
#   be called using Process and timeout
# The function will terminate when the folder is connected
def checkDriveConnection():
    while not os.path.exists("Y:\osu!"):
        time.sleep(2)
 
def spawnBackgroundProc(path: str,flag):
    print("Spawning "+path)
    subprocess.Popen(path,creationflags=8,close_fds=True)
def spawnForegroundProc(path: str):
    print("Spawning "+path)
    subprocess.Popen(path,close_fds=True)
 
if __name__ == '__main__':
    freeze_support()
 
    # Initialize the Checker Process and allow it 'timeout' seconds to try to
    #   establish a connection
    process["checker"] = multiprocessing.Process(target=checkDriveConnection)
    for key in process:
        process[key].start()
    process["checker"].join(timeout)
    # If the checker process is still alive, the folder is not connected
    folder_connected = not process["checker"].is_alive()
    process = {}
    print(folder_connected)
    if folder_connected:
        # Initialize and Start Complementary Processes
        for key in executuables:
            process[key] = multiprocessing.Process(target=spawnForegroundProc,args=(executuables[key],))
            process[key].start()
        time.sleep(20)
        # Check if all process is running or not, restart the stopped process
        while True: 
            time.sleep(5)
            osu = "off"
            if "osu!.exe" in (p.name() for p in psutil.process_iter()):
                osu = "on"
            client.publish("/homeassistant/gamingpc/osu",osu)
"""             for key in process: 
                if not process[key].is_alive(): 
                    process[key].start() """
