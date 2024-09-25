# COM Port Mirror Client

This tool mirrors data from an input COM port to multiple output COM ports, with options to log the data or replay from a file. It supports two modes: 
- **Receive Mode**: Mirror data from an input port and optionally log the data.
- **Replay Mode**: Replay data from a log file to output ports.

## Features
- Mirror data from an input COM port to multiple output COM ports.
- Log received data in a text file.
- Replay data from a log file to COM ports.
- Configurable baud rate, parity, stop bits, and byte size.
- Graceful shutdown via keyboard interrupt.

## Requirements

- Python 3.x
- `pyserial` library

### Install `pyserial`
You can install `pyserial` using `pip`:

```bash
pip install pyserial
```

## Usage

To start using the COM Port Mirror Client, run the script with the appropriate arguments. Here's an overview of the available options:

### Command Line Arguments

| Argument              | Type      | Description |
|-----------------------|-----------|-------------|
| `-i, --input_port`     | `str`     | Input COM port (e.g., `COM1`). |
| `-o, --output_ports`   | `str[]`   | Output COM ports (e.g., `COM2 COM3`). **Required**. |
| `-b, --baud_rate`      | `int`     | Baud rate (default: `19200`). |
| `-m, --mode`           | `str`     | Operation mode, either `receive` or `replay` (default: `receive`). |
| `-r, --replay_file`    | `str`     | Log file to replay (required for `replay` mode). |
| `-p, --parity`         | `str`     | Parity bit (choices: `N`, `E`, `O`, `M`, `S`), default: `E`. |
| `-s, --stopbits`       | `float`   | Stop bits (choices: `1`, `1.5`, `2`), default: `2`. |
| `-z, --bytesize`       | `int`     | Byte size (choices: `5`, `6`, `7`, `8`), default: `7`. |

### Example Commands

1. **Receive Mode**: Mirror data from `COM1` to `COM2` and `COM3`, with a baud rate of 19200.

   ```bash
   python ComportMirrorClient.py -i COM1 -o COM2 COM3 -b 19200
   ```

2. **Replay Mode**: Replay data from a log file to `COM2` and `COM3`.

   ```bash
   python ComportMirrorClient.py -m replay -r serial_log_20230915.txt -o COM2 COM3
   ```

3. **Custom Configuration**: Receive data on `COM1`, output to `COM2` and `COM3`, with 9600 baud rate, no parity, 1 stop bit, and 8 data bits.

   ```bash
   python ComportMirrorClient.py -i COM1 -o COM2 COM3 -b 9600 -p N -s 1 -z 8
   ```

### Stopping the Program

To gracefully stop the program, press `Ctrl+C`. The program will handle the keyboard interrupt and stop mirroring.

## Logging

- When running in **Receive Mode**, the program automatically creates a log file named `serial_log_<timestamp>.txt`, where `<timestamp>` is the current date and time.
- The log file records each message's timestamp and data in hexadecimal format.

## Replay Mode

In **Replay Mode**, the program reads a log file and sends the recorded data to the specified output COM ports at the same intervals as in the log.

## Error Handling

- If the input port cannot be opened, the program will retry every second.
- The program will output any exceptions that occur during execution.

## License

This project is licensed under the MIT License.