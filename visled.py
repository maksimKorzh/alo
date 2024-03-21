import pyaudio
import numpy as np
import os, time
import serial

# Open the serial port

arduino = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=.1) 

time.sleep(3)

# Constants for audio processing
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

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
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

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
