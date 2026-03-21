import pika
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import time


class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RabbitMQ Chat")
        self.root.geometry("600x500")

        self.send_connection = None
        self.send_channel = None
        self.receive_connection = None
        self.receive_channel = None
        self.queue_name = None
        self.stop_event = threading.Event()
        self.receiver_thread = None

        self.username = ""
        self.port = 5672
        self.room_name = ""

        self.build_login_screen()

    def build_login_screen(self):
        self.clear_window()

        tk.Label(self.root, text="Username").pack(pady=5)
        self.username_entry = tk.Entry(self.root, width=30)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Port").pack(pady=5)
        self.port_entry = tk.Entry(self.root, width=30)
        self.port_entry.insert(0, "5672")
        self.port_entry.pack(pady=5)

        tk.Label(self.root, text="Room").pack(pady=5)
        self.room_entry = tk.Entry(self.root, width=30)
        self.room_entry.pack(pady=5)

        tk.Button(self.root, text="Join Chat", command=self.join_chat).pack(pady=15)

    def build_chat_screen(self):
        self.clear_window()

        header_text = f"User: {self.username} | Room: {self.room_name}"
        tk.Label(self.root, text=header_text, font=("Arial", 12, "bold")).pack(pady=5)

        self.chat_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=70, height=20, state="disabled")
        self.chat_area.pack(padx=10, pady=10)

        self.message_entry = tk.Entry(self.root, width=50)
        self.message_entry.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
        self.message_entry.bind("<Return>", lambda event: self.send_message())

        tk.Button(self.root, text="Send", command=self.send_message).pack(side=tk.LEFT, padx=5)
        tk.Button(self.root, text="Exit", command=self.exit_chat).pack(side=tk.LEFT, padx=5)

    def join_chat(self):
        self.username = self.username_entry.get().strip()
        port_text = self.port_entry.get().strip()
        self.room_name = self.room_entry.get().strip()

        if not self.username or not port_text or not self.room_name:
            messagebox.showerror("Error", "Please fill in username, port, and room.")
            return

        try:
            self.port = int(port_text)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return

        try:
            # Sending connection
            self.send_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=self.port)
            )
            self.send_channel = self.send_connection.channel()
            self.send_channel.exchange_declare(exchange=self.room_name, exchange_type="fanout")

            # Receiving connection
            self.receive_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=self.port)
            )
            self.receive_channel = self.receive_connection.channel()
            self.receive_channel.exchange_declare(exchange=self.room_name, exchange_type="fanout")

            result = self.receive_channel.queue_declare(queue="", exclusive=True)
            self.queue_name = result.method.queue
            self.receive_channel.queue_bind(exchange=self.room_name, queue=self.queue_name)

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to RabbitMQ.\n{e}")
            return

        self.build_chat_screen()

        self.stop_event.clear()
        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()

    def receive_messages(self):
        while not self.stop_event.is_set():
            try:
                method_frame, header_frame, body = self.receive_channel.basic_get(
                    queue=self.queue_name,
                    auto_ack=True
                )

                if body:
                    message = body.decode()
                    if not message.startswith(self.username + ":"):
                        self.append_message(message)

                time.sleep(0.1)

            except Exception:
                break

    def send_message(self):
        message_text = self.message_entry.get().strip()

        if not message_text:
            return

        full_message = f"{self.username}: {message_text}"

        try:
            self.send_channel.basic_publish(
                exchange=self.room_name,
                routing_key="",
                body=full_message
            )
            self.append_message(full_message)
            self.message_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Send Error", f"Could not send message.\n{e}")

    def append_message(self, message):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def exit_chat(self):
        self.stop_event.set()

        try:
            if self.receive_channel and self.receive_channel.is_open:
                self.receive_channel.close()
        except Exception:
            pass

        try:
            if self.receive_connection and self.receive_connection.is_open:
                self.receive_connection.close()
        except Exception:
            pass

        try:
            if self.send_channel and self.send_channel.is_open:
                self.send_channel.close()
        except Exception:
            pass

        try:
            if self.send_connection and self.send_connection.is_open:
                self.send_connection.close()
        except Exception:
            pass

        self.build_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_chat)
    root.mainloop()