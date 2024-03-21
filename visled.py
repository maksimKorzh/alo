import pyaudio
import numpy as np
import os, time
import serial

# Open the serial port

arduino = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=.1) 

time.sleep(3)

#   Index 0: HDA Intel PCH: ALC255 Analog (hw:0,0)
#   Index 1: HDA Intel PCH: HDMI 0 (hw:0,3)
#   Index 2: HDA Intel PCH: HDMI 1 (hw:0,7)
#   Index 3: HDA Intel PCH: HDMI 2 (hw:0,8)
#   Index 4: HDA Intel PCH: HDMI 3 (hw:0,9)
#   Index 5: HDA Intel PCH: HDMI 4 (hw:0,10)
#   Index 6: HDA Intel PCH: HDMI 5 (hw:0,11)
#   Index 7: HDA Intel PCH: HDMI 6 (hw:0,12)
#   Index 8: sysdefault
#   Index 9: hdmi
#   Index 10: samplerate
#   Index 11: speexrate
#   Index 12: pulse
#   Index 13: upmix
#   Index 14: vdownmix
#   Index 15: default

# Constants for audio processing
CHUNK = 1024
FORMAT = pyaudio.paInt16
DEVICE = 15
CHANNELS = 2
RATE = 44100

def list_audio_devices():
    p = pyaudio.PyAudio()
    num_devices = p.get_device_count()

    print("Available audio devices:")
    for index in range(num_devices):
        device_info = p.get_device_info_by_index(index)
        device_name = device_info["name"]
        print(f"Index {index}: {device_name}")

    p.terminate()

list_audio_devices()
#import sys
#sys.exit(0)

# Function to find the dominant frequency
def dominant_frequency(data):
    # Perform FFT and get the power spectrum
    fft_data = np.fft.fft(data)
    power_spectrum = np.abs(fft_data)
    
    # Find the dominant frequency bin
    freqs = np.fft.fftfreq(len(data), 1.0/RATE)
    dominant_index = np.argmax(power_spectrum[1:]) + 1  # Exclude DC component
    dominant_freq = freqs[dominant_index]
    
    return dominant_freq

# Function to map frequency to lamp index
def map_frequency_to_lamp(frequency, num_lamps):
    min_freq = 500  # Minimum frequency detectable
    max_freq = 2000  # Maximum frequency detectable
    freq_range = max_freq - min_freq
    normalized_freq = (frequency - min_freq) / freq_range
    mapped_index = int(normalized_freq * num_lamps)
    return min(mapped_index, num_lamps - 1)

# Initialize audio stream
audio = pyaudio.PyAudio()
stream = audio.open(
  format=FORMAT,
  channels=CHANNELS,
  rate=RATE,
  input=True,
  input_device_index=DEVICE,
  frames_per_buffer=CHUNK
)

try:
    print("Listening... (Press Ctrl+C to exit)")
    while True:
        data = np.frombuffer(stream.read(CHUNK), dtype=np.int16)
        frequency = dominant_frequency(data)
        lamp_index = map_frequency_to_lamp(frequency, 8)
        
        # Clear the terminal
        #os.system('clear')
        
        # Print the lamps
        for i in range(8):
            if i == lamp_index:
                pin = bytes('abcdefgh'[i], 'utf-8')
                arduino.write(pin) 
            else:
                pin = bytes('ABCDEFGH'[i], 'utf-8')
                arduino.write(pin) 
        pin = bytes(b'H')
        arduino.write(pin) 
        
except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close audio stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Close the serial port
    arduino.close()
