import socket
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

HOST = '0.0.0.0'  
CONTROL_PORT = 9000
DATA_PORT = 9001


authorized_clients = {"anushka", "anushree"}  
blacklisted_clients = set()
active_clients = {}  


root = tk.Tk()
root.title("Server Logs")
log_area = ScrolledText(root, height=30, width=100)
log_area.pack()

def log(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)

def handle_control_connection(conn, addr):
    try:
        client_id = conn.recv(1024).decode('utf-8').strip()
        log(f"[CONTROL] Connection from {addr} | Client ID: {client_id}")

        if client_id in blacklisted_clients:
            conn.send(b"BLOCKED: You are banned.\n")
            log(f"[BLOCKED] {client_id} tried to reconnect.")
            conn.close()
            return

        if client_id not in authorized_clients:
            blacklisted_clients.add(client_id)
            conn.send(b"INTRUSION: Unauthorized access detected. You are now blocked.\n")
            log(f"[INTRUSION] Blocked {client_id} from {addr}")
            conn.close()
            return

        conn.send(b"AUTHORIZED: Welcome to the chat!\n")
        active_clients[client_id] = None  
        log(f"[AUTHORIZED] {client_id} added to active clients.")
    except Exception as e:
        log(f"[ERROR] Control handling failed: {str(e)}")
    finally:
        conn.close()

def handle_data_connection(conn, addr):
    try:
        client_id = conn.recv(1024).decode('utf-8').strip()
        if client_id in active_clients:
            active_clients[client_id] = conn  
            log(f"[DATA] {client_id} data channel established.")
            
            while True:
                msg = conn.recv(1024)
                if not msg:
                    break
                decoded_msg = msg.decode('utf-8')
                log(f"[CHAT] {client_id}: {decoded_msg}")
                
                for other_id, other_conn in active_clients.items():
                    if other_id != client_id and other_conn:
                        other_conn.send(f"{client_id}: {decoded_msg}".encode())
        else:
            conn.send(b"ERROR: Unauthorized data connection.\n")
            log(f"[REJECTED] Data connection from {addr} (invalid ID: {client_id})")
    except Exception as e:
        log(f"[ERROR] Data handling failed: {str(e)}")
    finally:
        if client_id in active_clients:
            del active_clients[client_id]
        conn.close()

def start_server():
    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    control_sock.bind((HOST, CONTROL_PORT))
    control_sock.listen(5)

    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_sock.bind((HOST, DATA_PORT))
    data_sock.listen(5)

    log(f"[SERVER] Listening on {HOST}:{CONTROL_PORT} (control) and {DATA_PORT} (data)")

    def accept_connections():
        while True:
            ctrl_conn, ctrl_addr = control_sock.accept()
            threading.Thread(target=handle_control_connection, args=(ctrl_conn, ctrl_addr)).start()
            
            data_conn, data_addr = data_sock.accept()
            threading.Thread(target=handle_data_connection, args=(data_conn, data_addr)).start()

    threading.Thread(target=accept_connections, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    start_server()
