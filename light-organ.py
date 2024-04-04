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
import random
import time

# Thread state
visled_thread = None
visled_running = False

# Frequencies
frequency_range = [
  '100', '200', '300', '400', '500', '600', '700', '800', '900', '1000',
  '1100', '1200', '1300', '1500', '1600', '1700', '1800', '1900', '2000'
]

# Thresholds
amplitudes = [
  '100',
  '500',
  '1000',
  '10000',
  '100000',
  '200000',
  '300000',
  '400000',
  '500000',
  '600000',
  '800000',
  '1000000',
  '1200000',
  '1400000',
  '1600000',
  '1800000',
  '2000000'
]

# Play modes
modes = [
  'Dominant frequency',
  'Amplitude threshold',
  'Random'
]

# Delays
delays = [
  '0.01',
  '0.05',
  '0.1',
  '0.5',
  '1'
]

###################################
#
#       GUI control module
#
###################################

# Close app
def on_window_close():
  stop()
  root.destroy()

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
def sync():
  stop()
  global visled_thread, visled_running
  if visled_running: return
  visled_running = True
  visled_thread = threading.Thread(target=visled)
  visled_thread.start()

# Stop visled execution
def stop():
  global visled_thread, visled_running
  visled_running = False
  status_state['text'] = 'Not running'
  if visled_thread and visled_thread.is_alive():
    visled_thread.join()
    status_state['text'] = 'Not running'

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

# Get amplitudes for all frequencies
def get_amplitudes(stream, min_freq, max_freq):
      data = np.frombuffer(stream.read(1024), dtype=np.int16)
      amplitudes = []
      for i in range(8):
        freqs = list(range(min_freq, max_freq + int(max_freq/min_freq),int ((max_freq - min_freq) / 7)))
        amplitudes.append(get_amplitude(data, freqs[i]))
      return amplitudes

# Light organ logic
def visled():
  global visled_running
  
  # Start serial communication
  try:
    arduino = serial.Serial(port=selected_port.get(), baudrate=115200, timeout=.1)
  except:
    messagebox.showerror('Error', 'Port ' + selected_port.get() + ' does not exist!')
    status_state['text'] = 'Not running'
    visled_running = False
    return
  try:
    device = [d for d in list_audio_devices() if d['name'] == selected_device.get()][0]
    status_state['text'] = 'Connecting...'
  except:
    messagebox.showerror('Error', 'Audio device does not exist!')
    status_state['text'] = 'Not running'
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

    # Fetch user settings
    status_state['text'] = 'Synced, no sound'
    min_freq = int(selected_frequency_min.get())
    max_freq = int(selected_frequency_max.get())
    threshold = int(selected_amplitude.get())
    pause = float(selected_delay.get())
    mode = selected_mode.get()

    # Handle inversion
    if max_freq <= min_freq: max_freq = min_freq + 2000
    if selected_inversion.get() == 'True':
      light_up = 'abcdefgh'
      light_down = 'ABCDEFGH'
    else:
      light_up = 'ABCDEFGH'
      light_down = 'abcdefgh'

    # Light loop
    while visled_running:
      # Read sound data
      amplitudes = get_amplitudes(stream, min_freq, max_freq)
      
      # Process idling
      if amplitudes[0] < 1000:
        status_state['text'] = 'Idling...'
        for i in range(8):
          arduino.write(bytes(light_up[i], 'utf-8'))
          time.sleep(pause)
          if get_amplitudes(stream, min_freq, max_freq)[0] > threshold: break
          arduino.write(bytes(light_down[i], 'utf-8'))

      else:
        status_state['text'] = 'Playing...'

      # Process sound
      if mode == 'Dominant frequency':
        frequency = dominant_frequency(data)
        lamp_index = map_frequency_to_lamp(frequency, 8, min_freq, max_freq)
        for i in range(8):
          amplitude = get_amplitude(data, min_freq)
          if amplitude > threshold and i == abs(lamp_index):
            arduino.write( bytes(light_up[i], 'utf-8')) 
            time.sleep(pause)
          else: arduino.write(bytes(light_down[i], 'utf-8'))
      
      elif mode == 'Amplitude threshold':
        for i in range(8):
          if amplitudes[i] > threshold:
            arduino.write(bytes(light_up[i], 'utf-8'))
        
        time.sleep(pause)
        for i in range(8):
          arduino.write(bytes(light_down[i], 'utf-8'))

      elif mode == 'Random':
        for i in range(8):
          amplitude = get_amplitude(data, min_freq)
          if amplitude > threshold:
            random_combination = ''.join(random.choice((str.upper, str.lower))(c) for c in light_up[:8])
            for c in random_combination: arduino.write(bytes(c, 'utf-8'))
        time.sleep(pause)
        for i in range(8):
          for c in light_down: arduino.write(bytes(c, 'utf-8'))

  except Exception as e:
    messagebox.showerror('Error', 'Failed reading audio stream!\n' + str(e))
    status_state['text'] = 'Not running'
    visled_running = False
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
root.title('Light Organ')

# List serial port
com_port_label = ttk.Label(root, text='     Port:')
com_port_label.grid(row=1, column=0, padx=5, pady=5)
selected_port = tk.StringVar()
com_ports = get_available_ports()
com_ports = com_ports if len(com_ports) else ['No device found']
com_port_option = ttk.Combobox(root, textvariable=selected_port, values=get_available_ports())
com_port_option.grid(row=1, column=1, padx=5, pady=5)
selected_port.set(com_ports[0])

# List audio devices
audio_device_label = ttk.Label(root, text='    Input:')
audio_device_label.grid(row=2, column=0, padx=5, pady=5)
audio_devices = [d['name'] for d in list_audio_devices()]
selected_device = tk.StringVar()
audio_option = ttk.Combobox(root, textvariable=selected_device, values=audio_devices, state='readonly')
selected_device.set('Microsoft Sound Mapper - Input')
audio_option.grid(row=2, column=1, padx=5, pady=5)

# Frequency
frequency_min_label = ttk.Label(root, text='       Min:')
frequency_min_label.grid(row=3, column=0, padx=5, pady=5)
selected_frequency_min = tk.StringVar()
selected_frequency_min.set('200')
frequency_min_option = ttk.Combobox(root, textvariable=selected_frequency_min, values=frequency_range)
frequency_min_option.grid(row=3, column=1, padx=5, pady=5)
frequency_max_label = ttk.Label(root, text='       Max:')
frequency_max_label.grid(row=4, column=0, padx=5, pady=5)
selected_frequency_max = tk.StringVar()
selected_frequency_max.set('600')
frequency_max_option = ttk.Combobox(root, textvariable=selected_frequency_max, values=frequency_range)
frequency_max_option.grid(row=4, column=1, padx=5, pady=5)

# Amplitude
amplitude_label = ttk.Label(root, text='Threshold:')
amplitude_label.grid(row=5, column=0, padx=5, pady=5)
selected_amplitude = tk.StringVar()
selected_amplitude.set('200000')
amplitude_option = ttk.Combobox(root, textvariable=selected_amplitude, values=amplitudes)
amplitude_option.grid(row=5, column=1, padx=5, pady=5)

# Delay
delay_label = ttk.Label(root, text='      Delay:')
delay_label.grid(row=6, column=0, padx=5, pady=5)
selected_delay = tk.StringVar()
selected_delay.set('0.05')
delay_option = ttk.Combobox(root, textvariable=selected_delay, values=delays)
delay_option.grid(row=6, column=1, padx=5, pady=5)

# Inversion
inversion_label = ttk.Label(root, text='Inversion:')
inversion_label.grid(row=7, column=0, padx=5, pady=5)
selected_inversion = tk.StringVar()
selected_inversion.set('True')
inversion_option = ttk.Combobox(root, textvariable=selected_inversion, values=['True', 'False'], state='readonly')
inversion_option.grid(row=7, column=1, padx=5, pady=5)

# Mode
mode_label = ttk.Label(root, text='      Mode:')
mode_label.grid(row=8, column=0, padx=5, pady=5)
selected_mode = tk.StringVar()
selected_mode.set('Amplitude threshold')
mode_option = ttk.Combobox(root, textvariable=selected_mode, values=modes, state='readonly')
mode_option.grid(row=8, column=1, padx=5, pady=5)

# Sync
sync_button = ttk.Button(root, text='Sync', command=sync)
sync_button.grid(row=100, column=0, padx=5, pady=5)
status_state = ttk.Label(root, text='Not running')
status_state.grid(row=100, column=1, padx=5, pady=5)
time.sleep(0.5)

# On app close
root.protocol("WM_DELETE_WINDOW", on_window_close)

# Run app
root.mainloop()
