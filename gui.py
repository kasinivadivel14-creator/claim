"""Desktop GUI for the Club Expense Claim Checker.

Run with: python gui.py
The existing extraction and rule-checking functions are reused from main.py.
"""

import csv
import queue
import threading
import tkinter as tk
from collections import Counter, defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from main import (
    classify,
    decide,
    read_claims,
    read_budgets,
    write_reports,
)

BASE_DIR = Path(__file__).resolve().parent


class ClaimCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Club Expense Claim Checker")
        self.root.geometry("780x610")
        self.root.minsize(700, 540)
        self.root.configure(bg="#f4f7f2")

        self.claims_path = tk.StringVar(value=str(BASE_DIR / "claims.csv"))
        default_budget = BASE_DIR / "budgets.csv"
        if not default_budget.exists() and (BASE_DIR / "budgets(1).csv").exists():
            default_budget = BASE_DIR / "budgets(1).csv"
        self.budgets_path = tk.StringVar(value=str(default_budget))
        self.output_path = tk.StringVar(value=str(BASE_DIR / "outputs"))
        self.status_text = tk.StringVar(value="Choose your files, then click Run Checker.")
        self.result_queue = queue.Queue()
        self.run_button = None
        self.open_button = None

        self._build_ui()
        self.root.after(150, self._check_queue)

    def _build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=7, font=("Segoe UI", 10))
        style.configure("Run.TButton", padding=10, font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background="#f4f7f2", font=("Segoe UI", 10))

        header = tk.Frame(self.root, bg="#174c3c", padx=24, pady=20)
        header.pack(fill="x")
        tk.Label(
            header, text="CLUB EXPENSE CLAIM CHECKER",
            bg="#174c3c", fg="white", font=("Segoe UI", 18, "bold")
        ).pack(anchor="w")
        tk.Label(
            header, text="Select CSV files • Check claims • Generate reports",
            bg="#174c3c", fg="#e1eee6", font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))

        body = ttk.Frame(self.root, padding=22)
        body.pack(fill="both", expand=True)

        self._file_row(body, "Claims CSV", self.claims_path, self._browse_claims, 0)
        self._file_row(body, "Budgets CSV", self.budgets_path, self._browse_budgets, 1)
        self._file_row(body, "Output folder", self.output_path, self._browse_output, 2)

        actions = ttk.Frame(body)
        actions.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(22, 14))
        self.run_button = ttk.Button(
            actions, text="▶  Run Checker", style="Run.TButton", command=self.run_checker
        )
        self.run_button.pack(side="left")
        self.open_button = ttk.Button(
            actions, text="Open Output Folder", command=self.open_output, state="disabled"
        )
        self.open_button.pack(side="left", padx=10)

        ttk.Label(body, text="Processing status", font=("Segoe UI", 11, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(10, 6)
        )
        self.status_label = tk.Label(
            body, textvariable=self.status_text, bg="white", fg="#26352e",
            anchor="w", justify="left", padx=12, pady=12, wraplength=690,
            relief="solid", bd=1
        )
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="ew")

        ttk.Label(body, text="Results", font=("Segoe UI", 11, "bold")).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(18, 6)
        )
        columns = ("status", "count")
        self.table = ttk.Treeview(body, columns=columns, show="headings", height=5)
        self.table.heading("status", text="Claim status")
        self.table.heading("count", text="Number of claims")
        self.table.column("status", width=450)
        self.table.column("count", width=160, anchor="center")
        self.table.grid(row=7, column=0, columnspan=3, sticky="nsew")

        note = (
            "Important: This tool only extracts information and applies software checks. "
            "It does not authorize or transfer payments. The faculty treasurer must "
            "inspect the original bill and sign every payment."
        )
        tk.Label(
            body, text=note, bg="#e8efe8", fg="#35483d", wraplength=690,
            justify="left", padx=12, pady=10, font=("Segoe UI", 9)
        ).grid(row=8, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        body.columnconfigure(1, weight=1)
        body.rowconfigure(7, weight=1)

    def _file_row(self, parent, label, variable, browse_command, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=8, padx=(0, 12))
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=8)
        ttk.Button(parent, text="Browse...", command=browse_command).grid(
            row=row, column=2, padx=(10, 0), pady=8
        )

    def _browse_claims(self):
        path = filedialog.askopenfilename(
            title="Select claims CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.claims_path.set(path)

    def _browse_budgets(self):
        path = filedialog.askopenfilename(
            title="Select budgets CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.budgets_path.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_path.set(path)

    def run_checker(self):
        claims_file = Path(self.claims_path.get().strip())
        budgets_file = Path(self.budgets_path.get().strip())
        output_folder = Path(self.output_path.get().strip())

        if not claims_file.is_file():
            messagebox.showerror("Claims file not found", "Please select a valid claims CSV file.")
            return
        if not budgets_file.is_file():
            messagebox.showerror("Budgets file not found", "Please select a valid budgets CSV file.")
            return
        if not str(output_folder):
            messagebox.showerror("Output folder missing", "Please choose an output folder.")
            return

        self.run_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.status_text.set("Processing claims. Please wait...")
        for item in self.table.get_children():
            self.table.delete(item)

        worker = threading.Thread(
            target=self._process_files,
            args=(claims_file, budgets_file, output_folder),
            daemon=True,
        )
        worker.start()

    def _process_files(self, claims_file, budgets_file, output_folder):
        try:
            claims = read_claims(claims_file)
            budgets = read_budgets(budgets_file)

            prepared = []
            same_day_totals = defaultdict(float)
            for claim in claims:
                facts = classify(claim["note"])
                prepared.append((claim, facts))
                if facts["amount"] is not None:
                    key = (claim["club"], facts["category"], claim["date"])
                    same_day_totals[key] += facts["amount"]

            spending = defaultdict(float)
            results, payable, review = [], [], []
            status_counts = Counter()

            for claim, facts in prepared:
                status, reason = decide(
                    claim, facts, same_day_totals, spending, budgets
                )
                row = {
                    "id": claim["id"], "club": claim["club"], "date": claim["date"],
                    "note": claim["note"],
                    "amount": facts["amount"] if facts["amount"] is not None else "",
                    "category": facts["category"], "bill": facts["bill"],
                    "summary": facts["summary"], "status": status, "reason": reason,
                }
                results.append(row)
                status_counts[status] += 1

                if status == "ok_to_pay":
                    payable.append({
                        "id": claim["id"], "club": claim["club"], "date": claim["date"],
                        "amount": facts["amount"], "category": facts["category"],
                        "summary": facts["summary"], "note": claim["note"],
                    })
                    spending[(claim["club"], facts["category"])] += facts["amount"]
                else:
                    review.append({
                        "id": claim["id"], "club": claim["club"], "date": claim["date"],
                        "reason": reason, "note": claim["note"],
                        "amount": row["amount"], "category": facts["category"],
                        "bill": facts["bill"],
                    })

            write_reports(
                output_folder, results, payable, review, status_counts,
                {claim["club"] for claim in claims}, budgets, spending,
            )
            self.result_queue.put(("success", len(claims), dict(status_counts), str(output_folder)))
        except Exception as error:
            self.result_queue.put(("error", str(error)))

    def _check_queue(self):
        try:
            result = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(150, self._check_queue)
            return

        self.run_button.configure(state="normal")
        if result[0] == "success":
            _, total, counts, folder = result
            labels = [
                ("OK to pay", "ok_to_pay"),
                ("Needs a bill", "needs_bill"),
                ("Needs approval", "needs_approval"),
                ("Over budget", "over_budget"),
                ("Needs more information", "needs_more_info"),
            ]
            for label, key in labels:
                self.table.insert("", "end", values=(label, counts.get(key, 0)))
            self.status_text.set(
                f"Completed successfully! {total} claims checked.\n"
                f"Four CSV reports saved in: {folder}"
            )
            self.open_button.configure(state="normal")
            messagebox.showinfo(
                "Processing complete",
                f"{total} claims checked.\n\nFour CSV reports were saved in:\n{folder}\n\n"
                "The treasurer must still verify the bills and sign payments.",
            )
        else:
            self.status_text.set("Could not complete processing. See the error message.")
            messagebox.showerror("Processing error", result[1])

        self.root.after(150, self._check_queue)

    def open_output(self):
        folder = Path(self.output_path.get().strip())
        if folder.is_dir():
            import os
            os.startfile(folder)  # Windows
        else:
            messagebox.showwarning("Folder not found", "Run the checker first to create the output folder.")


def main():
    root = tk.Tk()
    ClaimCheckerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
