import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import serial
import serial.tools.list_ports
import winreg
from ComPortMirrorClient import ComPortMirrorClient


def get_all_com_ports():
    ports = set()

    # pyserialから取得（シンボリックリンク含む）
    try:
        ports.update(
            [port.device for port in serial.tools.list_ports.comports(include_links=True)]
        )
    except:
        pass

    # レジストリから取得（仮想ポート含む）
    try:
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
        i = 0
        while True:
            try:
                val = winreg.EnumValue(reg, i)
                ports.add(val[1])
                i += 1
            except OSError:
                break
    except:
        pass

    return sorted(ports)


class MirrorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("COMポートミラーリング")
        self.client = None
        self.thread = None

        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)

        # 入力ポート
        ttk.Label(frm, text="入力ポート:").grid(column=0, row=0, sticky="e", pady=2)
        self.input_port = ttk.Combobox(frm, values=get_all_com_ports(), width=20)
        self.input_port.grid(column=1, row=0, sticky="w", pady=2)

        # 出力ポート
        ttk.Label(frm, text="出力ポート（複数選択）:").grid(column=0, row=1, sticky="ne", pady=2)
        output_frame = ttk.Frame(frm)
        output_frame.grid(column=1, row=1, sticky="w", pady=2)
        self.output_ports = tk.Listbox(output_frame, selectmode=tk.MULTIPLE, height=5, width=20)
        for p in get_all_com_ports():
            self.output_ports.insert(tk.END, p)
        self.output_ports.pack()

        # ボーレート
        ttk.Label(frm, text="ボーレート:").grid(column=0, row=2, sticky="e", pady=2)
        self.baud_rate = ttk.Combobox(frm, values=["9600", "19200", "38400", "57600", "115200"], width=20)
        self.baud_rate.set("19200")
        self.baud_rate.grid(column=1, row=2, sticky="w", pady=2)

        # パリティ
        ttk.Label(frm, text="パリティ (N/E/O/M/S):").grid(column=0, row=3, sticky="e", pady=2)
        self.parity = ttk.Combobox(frm, values=["N", "E", "O", "M", "S"], width=20)
        self.parity.set("E")
        self.parity.grid(column=1, row=3, sticky="w", pady=2)

        # ストップビット
        ttk.Label(frm, text="ストップビット (1 / 1.5 / 2):").grid(column=0, row=4, sticky="e", pady=2)
        self.stopbits = ttk.Combobox(frm, values=["1", "1.5", "2"], width=20)
        self.stopbits.set("2")
        self.stopbits.grid(column=1, row=4, sticky="w", pady=2)

        # バイトサイズ
        ttk.Label(frm, text="バイトサイズ (5〜8):").grid(column=0, row=5, sticky="e", pady=2)
        self.bytesize = ttk.Combobox(frm, values=["5", "6", "7", "8"], width=20)
        self.bytesize.set("7")
        self.bytesize.grid(column=1, row=5, sticky="w", pady=2)

        # モード
        ttk.Label(frm, text="モード:").grid(column=0, row=6, sticky="e", pady=2)
        self.mode = ttk.Combobox(frm, values=["receive", "replay"], width=18)
        self.mode.set("receive")
        self.mode.grid(column=1, row=6, sticky="w", pady=2)
        self.mode.bind("<<ComboboxSelected>>", self.toggle_replay_file)

        # リプレイファイル
        ttk.Label(frm, text="リプレイファイル:").grid(column=0, row=7, sticky="e", pady=2)
        file_frame = ttk.Frame(frm)
        file_frame.grid(column=1, row=7, sticky="w", pady=2)
        self.replay_file = ttk.Entry(file_frame, width=20)
        self.replay_file.pack(side=tk.LEFT)
        ttk.Button(file_frame, text="参照", command=self.browse_file).pack(side=tk.LEFT, padx=5)

        # 開始・停止ボタン
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(column=0, row=8, columnspan=2, pady=10)
        self.start_button = ttk.Button(btn_frame, text="開始", command=self.start_mirroring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(btn_frame, text="停止", command=self.stop_mirroring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.replay_file.delete(0, tk.END)
            self.replay_file.insert(0, file_path)

    def toggle_replay_file(self, event=None):
        if self.mode.get() == "replay":
            self.replay_file.config(state=tk.NORMAL)
        else:
            self.replay_file.config(state=tk.DISABLED)

    def start_mirroring(self):
        input_port = self.input_port.get()
        output_ports = [self.output_ports.get(i) for i in self.output_ports.curselection()]
        mode = self.mode.get()
        replay_file = self.replay_file.get() if mode == "replay" else None

        try:
            baud_rate = int(self.baud_rate.get().strip())
            parity_code = self.parity.get().strip().upper()
            parity_dict = {
                'N': serial.PARITY_NONE,
                'E': serial.PARITY_EVEN,
                'O': serial.PARITY_ODD,
                'M': serial.PARITY_MARK,
                'S': serial.PARITY_SPACE
            }
            parity = parity_dict[parity_code]
            stopbits = float(self.stopbits.get().strip())
            bytesize = int(self.bytesize.get().strip())
        except Exception as e:
            messagebox.showerror("エラー", f"シリアル設定が不正です: {e}")
            return

        if not input_port and mode == "receive":
            messagebox.showerror("エラー", "入力ポートを選択してください。")
            return
        if not output_ports:
            messagebox.showerror("エラー", "出力ポートを選択してください。")
            return

        self.client = ComPortMirrorClient(
            input_port=input_port,
            output_ports=output_ports,
            baud_rate=baud_rate,
            mode=mode,
            replay_file=replay_file,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize
        )

        self.thread = threading.Thread(target=self.client.start_mirroring)
        self.thread.daemon = True
        self.thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_mirroring(self):
        if self.client:
            self.client.stop_mirroring()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = MirrorApp(root)
    root.mainloop()

