import tkinter as tk
from tkinter import ttk
import pyaudio
import numpy as np
import os, time
import serial

class SerialPortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Port App")

        # Default values
        self.default_values = {
            "serial_port": "/dev/ttyUSB0",
            "device_index": "15",
            "rate": "44100",
            "channels": "2",
            "min_frequency": "200",
            "max_frequency": "2000",
        }

        # Variables to store user inputs
        self.serial_port_var = tk.StringVar(value=self.default_values["serial_port"])
        self.device_index_var = tk.StringVar(value=self.default_values["device_index"])
        self.rate_var = tk.StringVar(value=self.default_values["rate"])
        self.channels_var = tk.StringVar(value=self.default_values["channels"])
        self.min_frequency_var = tk.StringVar(value=self.default_values["min_frequency"])
        self.max_frequency_var = tk.StringVar(value=self.default_values["max_frequency"])
        self.output_var = tk.StringVar(value="Normal")
        self.mode_var = tk.StringVar(value="Dominant Frequency")

        # Create UI elements
        serial_port_label = ttk.Label(root, text="Serial Port:")
        serial_port_label.grid(row=0, column=0, padx=5, pady=5)
        self.serial_port_entry = ttk.Entry(root, textvariable=self.serial_port_var)
        self.serial_port_entry.grid(row=0, column=1, padx=5, pady=5)

        device_index_label = ttk.Label(root, text="Device Index:")
        device_index_label.grid(row=1, column=0, padx=5, pady=5)
        self.device_index_entry = ttk.Entry(root, textvariable=self.device_index_var)
        self.device_index_entry.grid(row=1, column=1, padx=5, pady=5)

        rate_label = ttk.Label(root, text="Rate:")
        rate_label.grid(row=2, column=0, padx=5, pady=5)
        self.rate_entry = ttk.Entry(root, textvariable=self.rate_var)
        self.rate_entry.grid(row=2, column=1, padx=5, pady=5)

        channels_label = ttk.Label(root, text="Channels:")
        channels_label.grid(row=3, column=0, padx=5, pady=5)
        self.channels_entry = ttk.Entry(root, textvariable=self.channels_var)
        self.channels_entry.grid(row=3, column=1, padx=5, pady=5)

        min_frequency_label = ttk.Label(root, text="Min Frequency:")
        min_frequency_label.grid(row=4, column=0, padx=5, pady=5)
        self.min_frequency_combobox = ttk.Combobox(root, values=list(range(200, 2001, 100)), textvariable=self.min_frequency_var, state="readonly")
        self.min_frequency_combobox.grid(row=4, column=1, padx=5, pady=5)

        max_frequency_label = ttk.Label(root, text="Max Frequency:")
        max_frequency_label.grid(row=5, column=0, padx=5, pady=5)
        self.max_frequency_combobox = ttk.Combobox(root, values=list(range(200, 2001, 100)), textvariable=self.max_frequency_var, state="readonly")
        self.max_frequency_combobox.grid(row=5, column=1, padx=5, pady=5)

        output_label = ttk.Label(root, text="Output:")
        output_label.grid(row=6, column=0, padx=5, pady=5)
        self.output_combobox = ttk.Combobox(root, values=["Normal", "Inverted"], textvariable=self.output_var, state="readonly")
        self.output_combobox.grid(row=6, column=1, padx=5, pady=5)

        mode_label = ttk.Label(root, text="Mode:")
        mode_label.grid(row=7, column=0, padx=5, pady=5)
        self.mode_combobox = ttk.Combobox(root, values=["Dominant Frequency", "Threshold"], textvariable=self.mode_var, state="readonly")
        self.mode_combobox.grid(row=7, column=1, padx=5, pady=5)

        start_button = ttk.Button(root, text="Start", command=self.start)
        start_button.grid(row=8, column=0, padx=5, pady=5)

        stop_button = ttk.Button(root, text="Stop", command=self.stop)
        stop_button.grid(row=8, column=1, padx=5, pady=5)

    def start(self):
        # Gather all parameters
        output = self.output_var.get()
        mode = self.mode_var.get()

        arduino = serial.Serial(port=self.serial_port_var.get(), baudrate=115200, timeout=.1) 
        time.sleep(3)

        # Function to find the dominant frequency
        def dominant_frequency(data):
            # Perform FFT and get the power spectrum
            fft_data = np.fft.fft(data)
            power_spectrum = np.abs(fft_data)

            # Find the dominant frequency bin
            freqs = np.fft.fftfreq(len(data), 1.0/int(self.rate_var.get()))
            dominant_index = np.argmax(power_spectrum[1:]) + 1  # Exclude DC component
            dominant_freq = freqs[dominant_index]

            return dominant_freq

        # Function to map frequency to lamp index
        def map_frequency_to_lamp(frequency, num_lamps):
            min_freq = int(self.min_frequency_var.get())
            max_freq = int(self.max_frequency_var.get())
            freq_range = max_freq - min_freq
            normalized_freq = (frequency - min_freq) / freq_range
            mapped_index = int(normalized_freq * num_lamps)
            return min(mapped_index, num_lamps - 1)

        # Initialize audio stream
        audio = pyaudio.PyAudio()
        stream = audio.open(
          format=pyaudio.paInt16,
          channels=int(self.channels_var.get()),
          rate=int(self.rate_var.get()),
          input=True,
          input_device_index=int(self.device_index_var.get()),
          frames_per_buffer=1024
        )

        try:
            print("Listening... (Press Ctrl+C to exit)")
            while True:
                data = np.frombuffer(stream.read(1024), dtype=np.int16)
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

    def stop(self):
        print("Stopping...")

    def scan_audio_devices(self):
        p = pyaudio.PyAudio()
        num_devices = p.get_device_count()
        audio_devices = []

        for index in range(num_devices):
            device_info = p.get_device_info_by_index(index)
            device_name = device_info["name"]
            print(device_name)
        
        p.terminate()

def main():
    root = tk.Tk()
    app = SerialPortApp(root)
    app.scan_audio_devices()
    root.mainloop()

if __name__ == "__main__":
    main()
