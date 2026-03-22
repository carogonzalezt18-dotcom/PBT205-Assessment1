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

        self.chat_area = None
        self.message_entry = None
        self.username_entry = None
        self.port_entry = None
        self.room_entry = None

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

        join_button = tk.Button(self.root, text="Join Chat", command=self.join_chat)
        join_button.pack(pady=15)

        self.username_entry.bind("<Return>", lambda event: self.join_chat())
        self.port_entry.bind("<Return>", lambda event: self.join_chat())
        self.room_entry.bind("<Return>", lambda event: self.join_chat())

        self.username_entry.focus_set()

    def build_chat_screen(self):
        self.clear_window()

        header_text = f"User: {self.username} | Room: {self.room_name}"
        tk.Label(self.root, text=header_text, font=("Arial", 12, "bold")).pack(pady=5)

        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            width=70,
            height=20,
            state="disabled"
        )
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.message_entry = tk.Entry(bottom_frame)
        self.message_entry.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.message_entry.focus_set()

        tk.Button(bottom_frame, text="Send", command=self.send_message).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Exit", command=self.exit_chat).pack(side=tk.LEFT, padx=5)

    def join_chat(self):
        username = self.username_entry.get().strip()
        port_text = self.port_entry.get().strip()
        room_name = self.room_entry.get().strip()

        if not username or not port_text or not room_name:
            messagebox.showerror("Error", "Please fill in username, port, and room.")
            return

        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Port must be a valid number between 1 and 65535.")
            return

        self.cleanup_connections()

        self.username = username
        self.port = port
        self.room_name = room_name
        self.stop_event.clear()

        try:
            self.send_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=self.port)
            )
            self.send_channel = self.send_connection.channel()
            self.send_channel.exchange_declare(exchange=self.room_name, exchange_type="fanout")

            self.receive_connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="localhost", port=self.port)
            )
            self.receive_channel = self.receive_connection.channel()
            self.receive_channel.exchange_declare(exchange=self.room_name, exchange_type="fanout")

            result = self.receive_channel.queue_declare(queue="", exclusive=True)
            self.queue_name = result.method.queue
            self.receive_channel.queue_bind(exchange=self.room_name, queue=self.queue_name)

        except Exception as e:
            self.cleanup_connections()
            messagebox.showerror("Connection Error", f"Could not connect to RabbitMQ.\n{e}")
            return

        self.build_chat_screen()

        self.receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receiver_thread.start()

    def receive_messages(self):
        while not self.stop_event.is_set():
            try:
                if not self.receive_channel or not getattr(self.receive_channel, "is_open", False):
                    break

                method_frame, header_frame, body = self.receive_channel.basic_get(
                    queue=self.queue_name,
                    auto_ack=True
                )

                if body:
                    message = body.decode()
                    if not message.startswith(f"{self.username}:"):
                        self.root.after(0, self.append_message, message)

                time.sleep(0.1)

            except Exception:
                break

    def send_message(self):
        if not self.message_entry:
            return

        message_text = self.message_entry.get().strip()
        if not message_text:
            return

        full_message = f"{self.username}: {message_text}"

        try:
            if not self.send_channel or not getattr(self.send_channel, "is_open", False):
                messagebox.showerror("Send Error", "The send channel is not available.")
                return

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
        if not self.chat_area:
            return

        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def cleanup_connections(self):
        self.stop_event.set()

        try:
            if self.receive_channel and self.receive_channel.is_open:
                self.receive_channel.close()
        except Exception:
            pass
        finally:
            self.receive_channel = None

        try:
            if self.receive_connection and self.receive_connection.is_open:
                self.receive_connection.close()
        except Exception:
            pass
        finally:
            self.receive_connection = None

        try:
            if self.send_channel and self.send_channel.is_open:
                self.send_channel.close()
        except Exception:
            pass
        finally:
            self.send_channel = None

        try:
            if self.send_connection and self.send_connection.is_open:
                self.send_connection.close()
        except Exception:
            pass
        finally:
            self.send_connection = None

        self.queue_name = None
        self.receiver_thread = None

    def exit_chat(self):
        self.cleanup_connections()
        self.build_login_screen()

    def close_app(self):
        self.cleanup_connections()
        self.root.destroy()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.close_app)
    root.mainloop()