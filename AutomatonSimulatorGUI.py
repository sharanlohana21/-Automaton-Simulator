import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import math
import time
from PIL import ImageGrab

class AutomatonSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Automaton Simulator")
        self.root.state('zoomed')
        self.root.configure(bg="#f0f2f5")

        self.title_font = ("Segoe UI", 16, "bold")
        self.label_font = ("Segoe UI", 10)
        self.input_font = ("Segoe UI", 10)
        self.button_font = ("Segoe UI", 10, "bold")
        self.accent_color = "#4a90e2"
        self.bg_main = "#f0f2f5"
        self.bg_sidebar = "#ffffff"
        self.bg_button = self.accent_color
        self.fg_button = "#ffffff"

        self.sidebar = tk.Frame(root, bg=self.bg_sidebar, width=340, padx=20, pady=20)
        self.sidebar.pack(side="left", fill="y")

        self.main_area = tk.Frame(root, bg="#ffffff")
        self.main_area.pack(side="right", fill="both", expand=True)

        self.output_canvas_frame = tk.Frame(self.main_area, bg="#ffffff")
        self.output_canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.right_output_frame = tk.Frame(self.output_canvas_frame, bg="#ffffff", height=150)
        self.right_output_frame.pack(fill="x", side="top")
        tk.Label(self.right_output_frame, text="Output:", font=self.label_font, bg="#ffffff").pack(anchor="w")
        self.output_text = tk.Text(self.right_output_frame, height=8, font=self.input_font, bg="#f4f4f4", relief=tk.FLAT)
        self.output_text.pack(fill="x", pady=(0, 10))

        self.canvas = tk.Canvas(self.output_canvas_frame, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.create_sidebar()
        self.transitions = {}
        self.state_positions = {}

    def create_sidebar(self):
        tk.Label(self.sidebar, text="🧠 Automaton Simulator", bg=self.bg_sidebar, fg=self.accent_color, font=self.title_font).pack(anchor="w", pady=(0, 20))
        tk.Label(self.sidebar, text="Automaton Type:", font=self.label_font, bg=self.bg_sidebar).pack(anchor="w")
        self.mode_var = tk.StringVar(value="DFA")
        opt = tk.OptionMenu(self.sidebar, self.mode_var, "DFA", "NFA")
        opt.config(font=self.input_font, bg="#f9f9f9", relief=tk.FLAT)
        opt["menu"].config(font=self.input_font)
        opt.pack(fill="x", pady=(0, 10))

        self.states_entry = self.add_entry("Number of States:", "")
        self.alpha_entry = self.add_entry("Alphabet (comma-separated):", "")
        self.start_entry = self.add_entry("Start State (e.g., q0):", "")
        self.final_entry = self.add_entry("Final States (comma-separated, e.g., q1,q2):", "")
        self.input_entry = self.add_entry("Input String:", "")

        self.add_button("🔄 Enter Transitions", self.get_transitions)
        self.add_button("▶️ Simulate", self.simulate)
        self.add_button("📸 Export Diagram as Image", self.export_image)
        self.add_button("🧹 Clear All", self.clear_all)

    def add_entry(self, label_text, placeholder):
        frame = tk.Frame(self.sidebar, bg=self.bg_sidebar)
        frame.pack(fill="x", pady=(5, 10))
        tk.Label(frame, text=label_text, font=self.label_font, bg=self.bg_sidebar).pack(anchor="w")
        entry = tk.Entry(frame, font=self.input_font, relief=tk.FLAT, bg="#f9f9f9")
        entry.insert(0, placeholder)
        entry.pack(fill="x", ipady=5)
        return entry

    def add_button(self, text, command):
        btn = tk.Button(self.sidebar, text=text, font=self.button_font, bg=self.bg_button,
                        fg=self.fg_button, activebackground="#357ab7", activeforeground="#fff",
                        relief=tk.FLAT, command=command)
        btn.pack(fill="x", pady=6, ipady=6)

    def parse_state(self, state_str):
        if not state_str.startswith("q") or not state_str[1:].isdigit():
            raise ValueError(f"Invalid state format: '{state_str}' (expected format: q0, q1, ...)")
        return int(state_str[1:])

    def get_transitions(self):
        try:
            self.states = int(self.states_entry.get())
            self.alphabet = [s.strip() for s in self.alpha_entry.get().split(",") if s.strip()]
            self.start_state = self.parse_state(self.start_entry.get().strip())
            self.final_states = [self.parse_state(s.strip()) for s in self.final_entry.get().split(",") if s.strip()]
            if self.start_state >= self.states or any(s >= self.states for s in self.final_states):
                raise ValueError("State index out of range.")
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.transitions.clear()
        is_dfa = self.mode_var.get() == "DFA"
        all_symbols = self.alphabet + (["ε"] if not is_dfa else [])

        for state in range(self.states):
            for symbol in all_symbols:
                prompt = f"State q{state} on '{symbol}' → "
                val = simpledialog.askstring("Transition Input", prompt)
                if val is None:
                    return
                try:
                    val = val.strip()
                    if is_dfa:
                        st = self.parse_state(val)
                        if st >= self.states:
                            raise ValueError(f"Target state q{st} out of bounds.")
                        self.transitions[(state, symbol)] = {st}
                    else:
                        if not val:
                            continue
                        next_states = set()
                        for x in val.split(","):
                            x = x.strip()
                            if not x:
                                continue
                            st = self.parse_state(x)
                            if st >= self.states:
                                raise ValueError(f"Target state q{st} out of bounds.")
                            next_states.add(st)
                        self.transitions.setdefault((state, symbol), set()).update(next_states)
                except Exception as e:
                    messagebox.showerror("Input Error", str(e))
                    return

        self.draw_automaton()
        messagebox.showinfo("Done", f"{self.mode_var.get()} transitions recorded.")

    def draw_automaton(self):
        self.canvas.delete("all")
        radius = 25
        cx, cy, r = 350, 250, 180
        self.state_positions.clear()

        for i in range(self.states):
            angle = 2 * math.pi * i / self.states
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            self.state_positions[i] = (x, y)

        edge_labels = {}
        for (src, symbol), targets in self.transitions.items():
            for tgt in targets:
                edge_labels.setdefault((src, tgt), []).append(symbol)

        for (src, tgt), symbols in edge_labels.items():
            x1, y1 = self.state_positions[src]
            x2, y2 = self.state_positions[tgt]
            label = ",".join(symbols)
            if src == tgt:
                self.canvas.create_arc(x1 - 40, y1 - 60, x1 + 40, y1, start=0, extent=270, style='arc', width=2)
                self.canvas.create_text(x1, y1 - 65, text=label, font=("Arial", 10))
            else:
                dx, dy = x2 - x1, y2 - y1
                dist = math.hypot(dx, dy)
                ux, uy = dx / dist, dy / dist
                sx, sy = x1 + radius * ux, y1 + radius * uy
                ex, ey = x2 - radius * ux, y2 - radius * uy
                offset = 15 if (tgt, src) in edge_labels else 0
                if offset:
                    perp_x, perp_y = -uy * offset, ux * offset
                    sx += perp_x
                    sy += perp_y
                    ex += perp_x
                    ey += perp_y
                    mx, my = (sx + ex) / 2 + perp_x, (sy + ey) / 2 + perp_y
                else:
                    mx, my = (sx + ex) / 2, (sy + ey) / 2
                self.canvas.create_line(sx, sy, ex, ey, arrow=tk.LAST, width=2)
                self.canvas.create_text(mx + 5, my + 5, text=label, font=("Arial", 10))

        for state, (x, y) in self.state_positions.items():
            color = "lightgreen" if state == self.start_state else "white"
            self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, width=2)
            self.canvas.create_text(x, y, text=f"q{state}", font=("Arial", 14))
            if state in self.final_states:
                self.canvas.create_oval(x - radius + 5, y - radius + 5, x + radius - 5, y + radius - 5, outline="blue", width=2)

    def simulate(self):
        input_str = self.input_entry.get().strip()
        if self.mode_var.get() == "NFA":
            input_str = input_str.replace(" ", "ε")
        invalid_symbols = [ch for ch in input_str if ch not in self.alphabet + (["ε"] if self.mode_var.get() == "NFA" else [])]
        if invalid_symbols:
            messagebox.showerror("Error", f"Invalid symbols in input: {', '.join(invalid_symbols)}")
            return

        self.output_text.delete(1.0, tk.END)
        if self.mode_var.get() == "DFA":
            self.simulate_dfa(input_str)
        else:
            self.simulate_nfa(input_str)

    def simulate_dfa(self, input_str):
        state = self.start_state
        self.output_text.insert(tk.END, f"Start at state q{state}\n")
        for ch in input_str:
            self.highlight_state(state)
            key = (state, ch)
            if key not in self.transitions:
                self.output_text.insert(tk.END, f"No transition for (q{state}, '{ch}')\n❌ Rejected\n")
                return
            next_state = list(self.transitions[key])[0]
            self.output_text.insert(tk.END, f"Read '{ch}' → q{next_state}\n")
            self.animate_transition(state, next_state)
            state = next_state
        self.highlight_state(state)
        if state in self.final_states:
            self.output_text.insert(tk.END, "✅ Accepted\n")
        else:
            self.output_text.insert(tk.END, "❌ Rejected\n")

    def simulate_nfa(self, input_str):
        results = []
        self._simulate_nfa_step({self.start_state}, input_str, 0, [f"q{self.start_state}"], results)
        if results:
            self.output_text.insert(tk.END, f"\n✅ Accepted ({len(results)} path(s))\n")
            for path in results:
                self.output_text.insert(tk.END, f"Path: {path}\n")
        else:
            self.output_text.insert(tk.END, "❌ Rejected\n")

    def _simulate_nfa_step(self, current_states, string, index, path, results):
        current_states = self.epsilon_closure(current_states)

        for state in current_states:
            self.highlight_state(state)
            self.root.update()
            time.sleep(0.3)

        if index == len(string):
            if any(s in self.final_states for s in current_states):
                results.append(" → ".join(path))
            return

        symbol = string[index]
        for state in current_states:
            next_states = self.transitions.get((state, symbol), set())
            for next_state in next_states:
                self.output_text.insert(tk.END, f"Read '{symbol}': q{state} → q{next_state}\n")
                self.output_text.see(tk.END)

                self.highlight_state(state)
                self.root.update()
                time.sleep(0.3)

                self.animate_transition(state, next_state)

                self._simulate_nfa_step({next_state}, string, index + 1, path + [f"q{next_state}"], results)

    def epsilon_closure(self, states):
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for next_state in self.transitions.get((state, "ε"), set()):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    def animate_transition(self, from_state, to_state):
        x1, y1 = self.state_positions[from_state]
        r = 25
        if from_state == to_state:
            steps = 30
            radius = 40
            center_x, center_y = x1, y1 - radius // 2
            for i in range(steps + 1):
                t = i / steps
                angle = math.radians(270 * t)
                dot_x = center_x + radius * math.cos(angle)
                dot_y = center_y + radius * math.sin(angle)
                dot = self.canvas.create_oval(dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4, fill="red")
                self.root.update()
                time.sleep(0.015)
                self.canvas.delete(dot)
            return

        x2, y2 = self.state_positions[to_state]
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        sx, sy = x1 + r * ux, y1 + r * uy
        ex, ey = x2 - r * ux, y2 - r * uy
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            dot_x = sx + (ex - sx) * t
            dot_y = sy + (ey - sy) * t
            dot = self.canvas.create_oval(dot_x - 6, dot_y - 6, dot_x + 6, dot_y + 6, fill="red")
            self.root.update()
            time.sleep(0.015)
            self.canvas.delete(dot)

    def highlight_state(self, state):
        self.draw_automaton()
        if state in self.state_positions:
            x, y = self.state_positions[state]
            r = 25
            self.canvas.create_oval(x - r, y - r, x + r, y + r, outline="red", width=4)

    def clear_all(self):
        self.states_entry.delete(0, tk.END)
        self.alpha_entry.delete(0, tk.END)
        self.start_entry.delete(0, tk.END)
        self.final_entry.delete(0, tk.END)
        self.input_entry.delete(0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.transitions.clear()
        self.state_positions.clear()
        self.canvas.delete("all")

  
    def export_image(self):
        try:
            self.canvas.update()
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png")],
                title="Save Canvas as Image"
            )
            if not filepath:
                return

            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            img.save(filepath)
            messagebox.showinfo("Success", f"Diagram saved as {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")




if __name__ == "__main__":
    root = tk.Tk()
    app = AutomatonSimulator(root)
    root.mainloop()











