HOW TO RUN THE DESKTOP GUI

1. Keep gui.py in the same folder as main.py, claims.csv, and your budgets CSV.
2. Make sure your .env file (if using the OpenAI API) is in the project folder.
3. Open the project folder in VS Code: File > Open Folder.
4. Open Terminal > New Terminal.
5. Install the packages once:
   python -m pip install -r requirements.txt
6. Start the GUI:
   python gui.py
7. In the app, use Browse to select claims.csv and your budgets CSV.
8. Choose an output folder and click Run Checker.
9. The app creates results.csv, payable.csv, review.csv, and summary.csv in that folder.

If the command says gui.py cannot be found, make sure the VS Code terminal is
in the same folder as gui.py. You can also right-click gui.py in the Explorer
and choose Run Python File in Terminal.

Tkinter is included with most standard Windows Python installations. If Python
reports that tkinter is missing, reinstall Python from python.org and ensure
that the Tcl/Tk support option is included.

SECURITY: Keep your .env file private. Never share your API key or commit .env
to GitHub. The treasurer must inspect supporting documents and approve payments.
