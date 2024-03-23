###################################
#
#  Arduino Light Organ (frontend)
#
###################################

# Packages
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import serial
import threading
import pyaudio
import numpy as np
import os, time
import serial

# Thread state
visled_thread = None
visled_running = False

###################################
#
#       GUI control module
#
###################################

# List COM ports
def get_available_ports():
  available_ports = []
  for port in serial.tools.list_ports.comports():
    available_ports.append(port.device)
  return available_ports

# Refresh ports
def update_ports():
  com_ports = get_available_ports()
  com_ports = com_ports if len(com_ports) else ['No device found']
  com_port_option['values'] = com_ports
  selected_port.set(com_ports[0])

# Execute visled in background
def start():
  global visled_thread, visled_running
  visled_running = True
  visled_thread = threading.Thread(target=visled)
  visled_thread.start()

# Stop visled execution
def stop():
  global visled_thread, visled_running
  visled_running = False
  status_label['text'] = 'Not running'
  if visled_thread and visled_thread.is_alive():
    visled_thread.join()
    status_label['text'] = 'Not running'

def list_audio_devices():
  p = pyaudio.PyAudio()
  num_devices = p.get_device_count()
  devices = []
  for index in range(num_devices):
      device_info = p.get_device_info_by_index(index)
      devices.append({
        'index': device_info['index'],
        'name': device_info['name']
      })

  p.terminate()
  return devices

###################################
#
#    Visual LED control module
#
###################################

# Function to find the dominant frequency
def dominant_frequency(data):
  fft_data = np.fft.fft(data)
  power_spectrum = np.abs(fft_data)
  freqs = np.fft.fftfreq(len(data), 1.0/48000)
  dominant_index = np.argmax(power_spectrum[1:]) + 1  # Exclude DC component
  dominant_freq = freqs[dominant_index]
  return dominant_freq

# Function to map frequency to lamp index
def map_frequency_to_lamp(frequency, num_lamps):
  min_freq = 500
  max_freq = 2000
  freq_range = max_freq - min_freq
  normalized_freq = (frequency - min_freq) / freq_range
  mapped_index = int(normalized_freq * num_lamps)
  return min(mapped_index, num_lamps - 1)


# Light organ logic
def visled():
  global visled_running
  
  # Start serial communication
  try:
    arduino = serial.Serial(port=selected_port.get(), baudrate=115200, timeout=.1)
    status_label['text'] = 'Connecting to serial port...'
  except:
    messagebox.showerror('Error', 'Port ' + selected_port.get() + ' does not exist!')
    status_label['text'] = 'Not running'
    return
  try:
    device = [d for d in list_audio_devices() if d['name'] == selected_device.get()][0]
    status_label['text'] = 'Loading audio device...'
  except:
    messagebox.showerror('Error', 'Audio device does not exist!')
    status_label['text'] = 'Not running'
    return

  # Wait for serial connection to start
  time.sleep(3)
  
  # Listen to audio stream
  try:
    # Initialize audio stream
    audio = pyaudio.PyAudio()
    stream = audio.open(
      format=pyaudio.paInt16,
      channels=2,
      rate=48000,
      input=True,
      input_device_index=device['index'],
      frames_per_buffer=1024
    )

    status_label['text'] = 'Listening to input stream...'
    while visled_running:
      data = np.frombuffer(stream.read(1024), dtype=np.int16)
      frequency = dominant_frequency(data)
      lamp_index = map_frequency_to_lamp(frequency, 8)
      
      # Light up lamps
      for i in range(8):
        if i == lamp_index:
          pin = bytes('abcdefgh'[i], 'utf-8')
          arduino.write(pin) 
        else:
          pin = bytes('ABCDEFGH'[i], 'utf-8')
          arduino.write(pin) 
      pin = bytes(b'H')
      arduino.write(pin) 

  except Exception as e:
    messagebox.showerror('Error', 'Failed reading audio stream!\n' + str(e))
    status_label['text'] = 'Not running'
    stream.stop_stream()
    stream.close()
    audio.terminate()
    arduino.close()

  finally:
    stream.stop_stream()
    stream.close()
    audio.terminate()
    arduino.close()

####################################
#
#              Main
#
###################################

# Create UI
root = tk.Tk()
root.title('Serial Communication App')

# List serial port
com_port_label = ttk.Label(root, text='Port:')
com_port_label.grid(row=0, column=0, padx=5, pady=5)
selected_port = tk.StringVar()
com_ports = get_available_ports()
com_ports = com_ports if len(com_ports) else ['No device found']
com_port_option = ttk.Combobox(root, textvariable=selected_port, values=get_available_ports())
com_port_option.grid(row=0, column=1, padx=5, pady=5)
selected_port.set(com_ports[0])
update_button = tk.Button(root, text="  Update ", command=update_ports)
update_button.grid(row=0, column=2, padx=5, pady=5)

# List audio devices
audio_devices = [d['name'] for d in list_audio_devices()]
selected_device = tk.StringVar()
audio_option = ttk.Combobox(root, textvariable=selected_device, values=audio_devices)
selected_device.set('default')
audio_option.grid(row=1, column=1, padx=5, pady=5)

# Start button
start_button = ttk.Button(root, text='Start', command=start)
start_button.grid(row=9, column=0, padx=5, pady=5)

# Status label
status_label = ttk.Label(root, text='Port:')
status_label.grid(row=9, column=1, padx=5, pady=5)
status_label['text'] = 'Not running'

# Stop button
stop_button = ttk.Button(root, text='Stop', command=stop)
stop_button.grid(row=9, column=2, padx=5, pady=5)

# Run app
root.mainloop()
