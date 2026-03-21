import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from common import (
    create_connection,
    setup_exchange,
    create_and_bind_queue,
    publish_message
)

# -----------------------------
# CONFIG
# -----------------------------

EXCHANGE_NAME = "tracking"
CELL_SIZE = 50
PADDING = 20
AUTO_REFRESH_MS = 300

# Visual palette
BG_MAIN = "#f5f7fb"
BG_CARD = "#ffffff"
GRID_COLOR = "#d6dbe5"
TEXT_PRIMARY = "#2c3e50"
TEXT_SECONDARY = "#6c7a89"
ACCENT_BLUE = "#4a90e2"
ACCENT_GREEN = "#27ae60"
ACCENT_RED = "#e74c3c"
ACCENT_GREY = "#95a5a6"
CELL_SINGLE = "#eaf2ff"
CELL_COLLISION = "#ffeaea"


class ContactTracingGUI:
    def __init__(self, host, board_size):
        self.host = host
        self.board_size = board_size

        self.window = tk.Tk()
        self.window.title("Task 3 - Contact Tracing GUI")
        self.window.configure(bg=BG_MAIN)

        # GUI state
        self.positions = {}
        self.waiting_for_person = None
        self.last_query_person = None
        self.last_update_time = "No data yet"

        # Separate publisher connection/channel for GUI thread
        self.publish_connection, self.publish_channel = create_connection(self.host)
        setup_exchange(self.publish_channel, EXCHANGE_NAME)

        # Separate consumer connection/channel for listener thread
        self.consume_connection, self.consume_channel = create_connection(self.host)
        setup_exchange(self.consume_channel, EXCHANGE_NAME)

        self.position_queue = create_and_bind_queue(
            channel=self.consume_channel,
            exchange=EXCHANGE_NAME,
            routing_key="position"
        )

        self.response_queue = create_and_bind_queue(
            channel=self.consume_channel,
            exchange=EXCHANGE_NAME,
            routing_key="query-response"
        )

        self.build_gui()
        self.start_rabbitmq_listener()

        self.window.after(AUTO_REFRESH_MS, self.refresh_canvas)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    # -----------------------------
    # GUI BUILD
    # -----------------------------

    def build_gui(self):
        top_frame = tk.Frame(self.window, bg=BG_MAIN)
        top_frame.pack(pady=10)

        tk.Label(
            top_frame,
            text=f"Environment: {self.board_size} x {self.board_size}",
            font=("Segoe UI", 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN
        ).pack()

        self.status_label = tk.Label(
            self.window,
            text="Status: Listening for positions...",
            font=("Segoe UI", 10),
            fg=ACCENT_GREEN,
            bg=BG_MAIN
        )
        self.status_label.pack(pady=(0, 6))

        self.info_label = tk.Label(
            self.window,
            text="Active people: 0   |   Last update: No data yet",
            font=("Segoe UI", 10),
            fg=TEXT_SECONDARY,
            bg=BG_MAIN
        )
        self.info_label.pack(pady=(0, 10))

        middle_frame = tk.Frame(self.window, bg=BG_MAIN)
        middle_frame.pack(padx=10, pady=10)

        canvas_width = self.board_size * CELL_SIZE + PADDING * 2
        canvas_height = self.board_size * CELL_SIZE + PADDING * 2

        left_frame = tk.Frame(middle_frame, bg=BG_MAIN)
        left_frame.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(
            left_frame,
            width=canvas_width,
            height=canvas_height,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=GRID_COLOR
        )
        self.canvas.pack()

        legend_frame = tk.Frame(left_frame, bg=BG_MAIN)
        legend_frame.pack(pady=8)

        tk.Label(
            legend_frame,
            text="Legend:",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_MAIN
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            legend_frame,
            text="Single person = blue marker",
            font=("Segoe UI", 9),
            fg=TEXT_SECONDARY,
            bg=BG_MAIN
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            legend_frame,
            text="Collision = red marker",
            font=("Segoe UI", 9),
            fg=ACCENT_RED,
            bg=BG_MAIN
        ).pack(side=tk.LEFT, padx=5)

        right_frame = tk.Frame(
            middle_frame,
            bg=BG_CARD,
            bd=1,
            relief="solid"
        )
        right_frame.pack(side=tk.LEFT, padx=18, anchor="n", ipadx=12, ipady=10)

        tk.Label(
            right_frame,
            text="Query Person",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(pady=(4, 6))

        self.query_entry = tk.Entry(
            right_frame,
            width=22,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1
        )
        self.query_entry.pack(pady=4)
        self.query_entry.bind("<Return>", lambda event: self.send_query())

        buttons_frame = tk.Frame(right_frame, bg=BG_CARD)
        buttons_frame.pack(pady=6)

        self.query_button = tk.Button(
            buttons_frame,
            text="Search Contacts",
            width=14,
            command=self.send_query,
            bg=ACCENT_BLUE,
            fg="white",
            activebackground="#357ABD",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        )
        self.query_button.grid(row=0, column=0, padx=3, pady=3)

        self.refresh_button = tk.Button(
            buttons_frame,
            text="Refresh Now",
            width=12,
            command=self.manual_refresh,
            bg=ACCENT_GREY,
            fg="white",
            activebackground="#7f8c8d",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        )
        self.refresh_button.grid(row=0, column=1, padx=3, pady=3)

        self.clear_button = tk.Button(
            buttons_frame,
            text="Clear Results",
            width=12,
            command=self.clear_results,
            bg=ACCENT_RED,
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            relief="flat",
            cursor="hand2"
        )
        self.clear_button.grid(row=1, column=0, columnspan=2, padx=3, pady=3)

        tk.Label(
            right_frame,
            text="Contacts Found",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(pady=(14, 6))

        self.result_listbox = tk.Listbox(
            right_frame,
            width=34,
            height=14,
            font=("Segoe UI", 10),
            bg="#fafafa",
            fg=TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=GRID_COLOR,
            selectbackground=ACCENT_BLUE,
            selectforeground="white"
        )
        self.result_listbox.pack()

        tk.Label(
            right_frame,
            text="Current Positions",
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD
        ).pack(pady=(16, 6))

        self.positions_listbox = tk.Listbox(
            right_frame,
            width=26,
            height=12,
            font=("Segoe UI", 10),
            bg="#fafafa",
            fg=TEXT_PRIMARY,
            highlightthickness=1,
            highlightbackground=GRID_COLOR,
            selectbackground=ACCENT_BLUE,
            selectforeground="white"
        )
        self.positions_listbox.pack()
        self.positions_listbox.bind("<<ListboxSelect>>", self.use_selected_person)

        self.draw_grid()

    # -----------------------------
    # GRID DRAWING
    # -----------------------------

    def draw_grid(self):
        self.canvas.delete("grid")

        for i in range(self.board_size + 1):
            x = PADDING + i * CELL_SIZE
            self.canvas.create_line(
                x, PADDING,
                x, PADDING + self.board_size * CELL_SIZE,
                fill=GRID_COLOR,
                tags="grid"
            )

            y = PADDING + i * CELL_SIZE
            self.canvas.create_line(
                PADDING, y,
                PADDING + self.board_size * CELL_SIZE, y,
                fill=GRID_COLOR,
                tags="grid"
            )

        for i in range(self.board_size):
            x = PADDING + i * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(
                x,
                PADDING - 10,
                text=str(i),
                tags="grid",
                font=("Segoe UI", 9),
                fill=TEXT_SECONDARY
            )

            y = PADDING + i * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(
                PADDING - 10,
                y,
                text=str(i),
                tags="grid",
                font=("Segoe UI", 9),
                fill=TEXT_SECONDARY
            )

    def refresh_canvas(self):
        self.draw_grid()
        self.draw_people()
        self.refresh_positions_list()
        self.refresh_info_panel()
        self.window.after(AUTO_REFRESH_MS, self.refresh_canvas)

    def manual_refresh(self):
        self.draw_grid()
        self.draw_people()
        self.refresh_positions_list()
        self.refresh_info_panel()
        self.status_label.config(text="Status: Manual refresh completed", fg=ACCENT_BLUE)

    def draw_people(self):
        self.canvas.delete("people")

        cell_occupants = {}
        for person_id, (x, y) in self.positions.items():
            cell_occupants.setdefault((x, y), []).append(person_id)

        for (x, y), people in cell_occupants.items():
            left = PADDING + x * CELL_SIZE
            top = PADDING + y * CELL_SIZE
            right = left + CELL_SIZE
            bottom = top + CELL_SIZE

            if len(people) > 1:
                fill_color = CELL_COLLISION
                outline_color = ACCENT_RED
            else:
                fill_color = CELL_SINGLE
                outline_color = ACCENT_BLUE

            self.canvas.create_oval(
                left + 8, top + 8, right - 8, bottom - 8,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags="people"
            )

            label = ", ".join(people[:2])
            if len(people) > 2:
                label += "..."

            self.canvas.create_text(
                left + CELL_SIZE / 2,
                top + CELL_SIZE / 2,
                text=label,
                font=("Segoe UI", 9, "bold"),
                fill=TEXT_PRIMARY,
                tags="people"
            )

    def refresh_positions_list(self):
        self.positions_listbox.delete(0, tk.END)

        for person_id in sorted(self.positions.keys()):
            x, y = self.positions[person_id]
            self.positions_listbox.insert(tk.END, f"{person_id}: ({x}, {y})")

    def refresh_info_panel(self):
        active_count = len(self.positions)
        self.info_label.config(
            text=f"Active people: {active_count}   |   Last update: {self.last_update_time}"
        )

    # -----------------------------
    # QUERY HANDLING
    # -----------------------------

    def resolve_person_name(self, user_input):
        normalized_input = user_input.strip().lower()

        for person_id in self.positions.keys():
            if person_id.lower() == normalized_input:
                return person_id

        return None

    def use_selected_person(self, event):
        selection = self.positions_listbox.curselection()
        if not selection:
            return

        selected_text = self.positions_listbox.get(selection[0])
        person_id = selected_text.split(":")[0].strip()

        self.query_entry.delete(0, tk.END)
        self.query_entry.insert(0, person_id)

    def send_query(self):
        raw_input = self.query_entry.get().strip()

        if not raw_input:
            messagebox.showwarning("Missing Input", "Please enter a person identifier.")
            return

        resolved_person_id = self.resolve_person_name(raw_input)

        if not resolved_person_id:
            messagebox.showwarning(
                "Person Not Found",
                "That person is not currently visible in the environment.\nUse a name from the Current Positions list."
            )
            return

        self.result_listbox.delete(0, tk.END)
        self.result_listbox.insert(tk.END, "Waiting for response...")

        self.waiting_for_person = resolved_person_id
        self.last_query_person = resolved_person_id
        self.status_label.config(text=f"Status: Query sent for {resolved_person_id}", fg=ACCENT_BLUE)

        query_message = {
            "person_id": resolved_person_id
        }

        publish_message(
            channel=self.publish_channel,
            exchange=EXCHANGE_NAME,
            routing_key="query",
            message=query_message
        )

    def update_query_results(self, person_id, contact_details):
        self.result_listbox.delete(0, tk.END)

        if contact_details:
            for item in contact_details:
                contact_name = item.get("contact", "Unknown")
                timestamp = item.get("timestamp", "Unknown time")
                self.result_listbox.insert(tk.END, f"{contact_name} ({timestamp})")
        else:
            self.result_listbox.insert(tk.END, "No contacts found.")

        self.status_label.config(
            text=f"Status: Query completed for {person_id}",
            fg=ACCENT_GREEN
        )

    def clear_results(self):
        self.result_listbox.delete(0, tk.END)
        self.query_entry.delete(0, tk.END)
        self.waiting_for_person = None
        self.last_query_person = None
        self.status_label.config(text="Status: Results cleared", fg=TEXT_PRIMARY)

    # -----------------------------
    # RABBITMQ LISTENER
    # -----------------------------

    def start_rabbitmq_listener(self):
        listener_thread = threading.Thread(target=self.consume_messages, daemon=True)
        listener_thread.start()

    def consume_messages(self):
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body.decode())
                routing_key = method.routing_key

                if routing_key == "position":
                    self.window.after(0, lambda m=message: self.handle_position_message(m))

                elif routing_key == "query-response":
                    self.window.after(0, lambda m=message: self.handle_query_response(m))

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except json.JSONDecodeError:
                print("Invalid JSON received in GUI.")
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                print(f"Unexpected GUI error: {e}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        self.consume_channel.basic_consume(
            queue=self.position_queue,
            on_message_callback=callback,
            auto_ack=False
        )

        self.consume_channel.basic_consume(
            queue=self.response_queue,
            on_message_callback=callback,
            auto_ack=False
        )

        self.consume_channel.start_consuming()

    def handle_position_message(self, message):
        required_fields = ["person_id", "x", "y"]
        for field in required_fields:
            if field not in message:
                return

        person_id = message["person_id"]
        x = message["x"]
        y = message["y"]

        self.positions[person_id] = (x, y)
        self.last_update_time = datetime.now().strftime("%H:%M:%S")

    def handle_query_response(self, message):
        person_id = message.get("person_id")
        contact_details = message.get("contact_details", [])

        if self.waiting_for_person and self.waiting_for_person.lower() == person_id.lower():
            self.update_query_results(person_id, contact_details)

    # -----------------------------
    # CLOSE
    # -----------------------------

    def on_close(self):
        try:
            if self.consume_connection and self.consume_connection.is_open:
                self.consume_connection.close()
        except Exception:
            pass

        try:
            if self.publish_connection and self.publish_connection.is_open:
                self.publish_connection.close()
        except Exception:
            pass

        self.window.destroy()

    def run(self):
        self.window.mainloop()


def main():
    """
    Usage:
    python task3/contact_gui.py <middleware_endpoint> <board_size>

    Example:
    python task3/contact_gui.py localhost 10
    """
    if len(sys.argv) != 3:
        print("Usage: python task3/contact_gui.py <middleware_endpoint> <board_size>")
        sys.exit(1)

    host = sys.argv[1]

    try:
        board_size = int(sys.argv[2])
    except ValueError:
        print("Error: board_size must be an integer.")
        sys.exit(1)

    if board_size < 1 or board_size > 1000:
        print("Error: board_size must be between 1 and 1000.")
        sys.exit(1)

    if board_size > 20:
        print("Warning: very large board sizes are supported logically, but GUI display is only practical for small boards like 10-20.")

    app = ContactTracingGUI(host, board_size)
    app.run()


if __name__ == "__main__":
    main()