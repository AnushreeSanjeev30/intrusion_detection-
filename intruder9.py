import socket
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

SERVER_IP = '127.0.0.1'  # Change to server's IP if needed
CONTROL_PORT = 9000
DATA_PORT = 9001
CLIENT_ID = "psycho"  # Must match server's authorized_clients

response_label = None
msg_display = None
msg_entry = None
data_socket = None

def connect_to_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock

def control_channel():
    global response_label
    try:
        conn = connect_to_server(SERVER_IP, CONTROL_PORT)
        conn.send(CLIENT_ID.encode())
        response = conn.recv(1024).decode('utf-8')
        response_label.config(text=f"Server: {response.strip()}")
        
        if "BLOCKED" in response or "INTRUSION" in response:
            return False
        return True
    except Exception as e:
        response_label.config(text=f"Control Error: {str(e)}")
        return False

def receive_messages():
    global data_socket
    while True:
        try:
            msg = data_socket.recv(1024).decode('utf-8')
            if msg:
                msg_display.insert(tk.END, f"{msg}\n")
                msg_display.see(tk.END)
        except Exception as e:
            msg_display.insert(tk.END, f"[ERROR] Connection lost: {str(e)}\n")
            break

def data_channel():
    global data_socket
    try:
        data_socket = connect_to_server(SERVER_IP, DATA_PORT)
        data_socket.send(CLIENT_ID.encode())  # Critical: Re-send ID
        threading.Thread(target=receive_messages, daemon=True).start()
    except Exception as e:
        response_label.config(text=f"Data Error: {str(e)}")

def send_message():
    msg = msg_entry.get()
    if data_socket and msg:
        try:
            data_socket.send(msg.encode())
            msg_display.insert(tk.END, f"You: {msg}\n")
            msg_entry.delete(0, tk.END)
        except Exception as e:
            msg_display.insert(tk.END, f"[ERROR] Send failed: {str(e)}\n")

def launch_gui():
    global response_label, msg_display, msg_entry

    window = tk.Tk()
    window.title("Chat Client")

    tk.Label(window, text=f"Client ID: {CLIENT_ID}", font=("Arial", 12)).pack()

    response_label = tk.Label(window, text="", fg="blue")
    response_label.pack()

    msg_display = ScrolledText(window, height=15, width=60)
    msg_display.pack()

    msg_entry = tk.Entry(window, width=50)
    msg_entry.pack(pady=5)
    tk.Button(window, text="Send", command=send_message).pack()

    if control_channel():
        data_channel()
    else:
        msg_entry.config(state=tk.DISABLED)

    window.mainloop()

if __name__ == "__main__":
    launch_gui()