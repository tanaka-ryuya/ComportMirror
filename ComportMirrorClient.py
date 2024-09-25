import serial
import threading
import argparse
import sys
import time
import os
from datetime import datetime


class ArgumentParserWithError(argparse.ArgumentParser):
    def error(self, message):
        """カスタムエラーメッセージとUSAGE表示"""
        sys.stderr.write(f"Error: {message}\n")
        self.print_help()
        sys.exit(2)

class ComPortMirrorClient:
    def __init__(self, input_port, output_ports, baud_rate=19200, mode='receive', replay_file=None,
                 parity=serial.PARITY_EVEN, stopbits=2, bytesize=7):
        self.input_port = input_port
        self.output_ports = output_ports
        self.baud_rate = baud_rate
        self.mode = mode
        self.replay_file = replay_file
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.stop_event = threading.Event()
        self.start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stop_event.clear()

    def start_mirroring(self):
        if self.mode == 'receive':
            self.receive_mode()
        elif self.mode == 'replay':
            self.replay_mode()

    def receive_mode(self):
        log_filename = f"serial_log_{self.start_time}.txt"
        while not self.stop_event.is_set():
            print(f"Trying to open serial port {self.input_port}...")
            try:
                with serial.Serial(self.input_port, self.baud_rate, timeout=2,
                                   parity=self.parity, stopbits=self.stopbits, bytesize=self.bytesize) as input_serial:
                    output_serials = [serial.Serial(port, self.baud_rate, timeout=2, write_timeout=0,
                                                    parity=self.parity, stopbits=self.stopbits, bytesize=self.bytesize)
                                      for port in self.output_ports]

                    print(f"Mirroring data from {self.input_port} to {', '.join(self.output_ports)} and logging to {log_filename}...")

                    with open(log_filename, 'a') as log_file:
                        while not self.stop_event.is_set():
                            data = input_serial.read(88)
                            if data:
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                                hex_data = data.hex().upper()
                                log_file.write(f"{timestamp},{hex_data}\n")
                                log_file.flush()
                                print(f"Received at {timestamp}: {hex_data}")

                                for output_serial in output_serials:
                                    output_serial.write(data)

            except serial.SerialException as e:
                print(f"Error: Could not open serial port {self.input_port}. Retrying in 1 second... {e}")
                time.sleep(1)

            except Exception as e:
                print(f"Unexpected error occurred: {e}")
                break

            print("Exiting receive mode...")

    def replay_mode(self):
        if not self.replay_file or not os.path.exists(self.replay_file):
            print(f"Error: Replay file {self.replay_file} not found.")
            return

        with open(self.replay_file, 'r') as log_file:
            log_lines = log_file.readlines()

        output_serials = [serial.Serial(port, self.baud_rate, timeout=1,
                                        parity=self.parity, stopbits=self.stopbits, bytesize=self.bytesize)
                          for port in self.output_ports]

        print(f"Replaying data from {self.replay_file} to {', '.join(self.output_ports)}...")

        base_time = datetime.strptime(log_lines[0].split(',')[0], "%Y-%m-%d %H:%M:%S.%f")
        start_replay_time = time.time()

        for line in log_lines:
            if self.stop_event.is_set():
                break

            timestamp_str, hex_data = line.strip().split(',')
            data = bytes.fromhex(hex_data)
            log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
            elapsed_time = (log_time - base_time).total_seconds()
            time_to_wait = start_replay_time + elapsed_time - time.time()

            if time_to_wait > 0:
                time.sleep(time_to_wait)

            for output_serial in output_serials:
                output_serial.write(data)

            print(f"Replayed at {timestamp_str}: {hex_data}")

    def stop_mirroring(self):
        self.stop_event.set()

def main():
    parser = ArgumentParserWithError(description='Mirror data from one input COM port to multiple output COM ports.')
    parser.add_argument('-i', '--input_port', type=str, help='Input COM port (e.g., COM1)')
    parser.add_argument('-o', '--output_ports', type=str, nargs='+', required=True, help='Output COM ports (e.g., COM2 COM3)')
    parser.add_argument('-b', '--baud_rate', type=int, default=19200, help='Baud rate (default: 19200)')
    parser.add_argument('-m', '--mode', type=str, choices=['receive', 'replay'], default='receive', help='Operation mode (receive or replay)')
    parser.add_argument('-r', '--replay_file', type=str, help='Replay file for replay mode')
    parser.add_argument('-p', '--parity', type=str, choices=['N', 'E', 'O', 'M', 'S'], default='E', help='Parity (N=None, E=Even, O=Odd, M=Mark, S=Space)')
    parser.add_argument('-s', '--stopbits', type=float, choices=[1, 1.5, 2], default=2, help='Stop bits (1, 1.5, or 2)')
    parser.add_argument('-z', '--bytesize', type=int, choices=[5, 6, 7, 8], default=7, help='Byte size (5, 6, 7, or 8)')

    args = parser.parse_args()

    parity_dict = {
        'N': serial.PARITY_NONE,
        'E': serial.PARITY_EVEN,
        'O': serial.PARITY_ODD,
        'M': serial.PARITY_MARK,
        'S': serial.PARITY_SPACE
    }

    client = ComPortMirrorClient(
        args.input_port,
        args.output_ports,
        args.baud_rate,
        args.mode,
        args.replay_file,
        parity=parity_dict[args.parity],
        stopbits=args.stopbits,
        bytesize=args.bytesize
    )

    thread = threading.Thread(target=client.start_mirroring)
    thread.daemon = True
    thread.start()

    try:
        while thread.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping mirroring...")
        client.stop_mirroring()

    print("Mirroring stopped.")

if __name__ == "__main__":
    main()
