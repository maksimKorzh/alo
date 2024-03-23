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

# Find the dominant frequency
def dominant_frequency(data):
  fft_data = np.fft.fft(data)
  power_spectrum = np.abs(fft_data)
  freqs = np.fft.fftfreq(len(data), 1.0/48000)
  dominant_index = np.argmax(power_spectrum[1:]) + 1  # Exclude DC component
  dominant_freq = freqs[dominant_index]
  return dominant_freq

# Map frequency to lamp index
def map_frequency_to_lamp(frequency, num_lamps, min_freq, max_freq):
  freq_range = max_freq - min_freq
  normalized_freq = (frequency - min_freq) / freq_range
  mapped_index = int(normalized_freq * num_lamps)
  return min(mapped_index, num_lamps - 1)

# Get amplitude of given frequency
def get_amplitude(data, freq):
  fft_data = np.fft.fft(data)
  freqs = np.fft.fftfreq(len(fft_data), 1/48000)
  idx = np.argmin(np.abs(freqs - freq))
  return np.abs(fft_data[idx])

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
    min_freq = int(selected_frequency_min.get())
    max_freq = int(selected_frequency_max.get())
    while visled_running:
      data = np.frombuffer(stream.read(1024), dtype=np.int16)
      frequency = dominant_frequency(data)
      lamp_index = map_frequency_to_lamp(frequency, 8, min_freq, max_freq)
      
      # Light up lamps
      #for i in range(8):
      #  if i == lamp_index:
      #    pin = bytes('abcdefgh'[i], 'utf-8')
      #    arduino.write(pin) 
      #  else:
      #    pin = bytes('ABCDEFGH'[i], 'utf-8')
      #    arduino.write(pin)
      for i in range(8):
        for y in range(8):
          freqs = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]
          amplitude = get_amplitude(data, freqs[y])
          if amplitude > 1200000 and i == y: arduino.write(bytes('abcdefgh'[i], 'utf-8'))
          else: arduino.write(bytes('ABCDEFGH'[i], 'utf-8'))

      pin = bytes(b'H')
      arduino.write(pin) 

  except Exception as e:
    messagebox.showerror('Error', 'Failed reading audio stream!\n' + str(e))
    status_label['text'] = 'Not running'
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
root.title('Arduino Light Organ')

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
audio_device_label = ttk.Label(root, text='Input:')
audio_device_label.grid(row=1, column=0, padx=5, pady=5)
audio_devices = [d['name'] for d in list_audio_devices()]
selected_device = tk.StringVar()
audio_option = ttk.Combobox(root, textvariable=selected_device, values=audio_devices, state='readonly')
selected_device.set('default')
audio_option.grid(row=1, column=1, padx=5, pady=5)

# Frequency
frequency_range = [
  '100', '200', '300', '400', '500', '600', '700', '800', '900', '1000',
  '1100', '1200', '1300', '1500', '1600', '1700', '1800', '1900', '2000'
]
frequency_min_label = ttk.Label(root, text='Min:')
frequency_min_label.grid(row=2, column=0, padx=5, pady=5)
selected_frequency_min = tk.StringVar()
frequency_min_option = ttk.Combobox(root, textvariable=selected_frequency_min, values=frequency_range)
selected_frequency_min.set('500')
frequency_min_option.grid(row=2, column=1, padx=5, pady=5)
frequency_max_label = ttk.Label(root, text='Max:')
frequency_max_label.grid(row=3, column=0, padx=5, pady=5)
selected_frequency_max = tk.StringVar()
frequency_max_option = ttk.Combobox(root, textvariable=selected_frequency_max, values=frequency_range)
selected_frequency_max.set('1000')
frequency_max_option.grid(row=3, column=1, padx=5, pady=5)

# Start/stop
start_button = ttk.Button(root, text='Start', command=start)
start_button.grid(row=9, column=0, padx=5, pady=5)
status_label = ttk.Label(root, text='Port:')
status_label.grid(row=9, column=1, padx=5, pady=5)
status_label['text'] = 'Not running'
stop_button = ttk.Button(root, text='Stop', command=stop)
stop_button.grid(row=9, column=2, padx=5, pady=5)

# Run app
root.mainloop()
