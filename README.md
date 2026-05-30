# Game Time Manager

<img width="1024" height="1024" alt="Program_icoon" src="https://github.com/user-attachments/assets/887cc011-d8f0-4e4b-bf43-96b85e23fcf3" />


Game Time Manager is a lightweight, local desktop application built in Python designed to help you track and manage the time you spend playing different games. It acts as an advanced stopwatch that saves your sessions to a database, allowing you to categorize your playtime with custom tags and view your complete gaming history. This is a vibe coded program what started as a joke to a AI to make a stopwatch what turned into motivation to replace my current tracker.

## Features Overview

* **Integrated Pre-Game Tracker:** Launch the app with a game name to be greeted by a quick prompt to select tags and start tracking immediately—perfect for integration with game launchers or shortcuts.
* **Live Time Tracking:** Start, stop, and reset a real-time stopwatch directly from the graphical interface.
* **Game Names & Custom Tags:** Attach a specific game name to your sessions. Use the built-in "Settings" menu to create, edit, and delete custom tags (e.g., "Ranked", "Casual", "Co-op") and assign them to your entries.
* **Persistent History Log:** All finished sessions are automatically saved to a local SQLite database (`Game Time.db`) and displayed in a neat table within the app.
* **Manual Entry Management:** Forgot to start the timer? You can manually add past sessions, or edit existing ones. The app will automatically calculate the total time between your start and end dates.
* **Export Functionality:** Export your entire gaming history to a clean, readable text file (`Game_Time_Export.txt`) with a single click.
* **Command Line Interface (CLI) Support:** Control your timer without opening the window! You can start and stop the tracker via terminal commands.
* **Pizza Button:** A very important, dedicated button to send a Pizza Hawaii to Nicolaï.

## Requirements

To run the Game Time Manager just run it...

To run the Game Time Manager source files, you only need the following:

* **Python 3.x** installed on your system.
* **customtkinter** to draw and show the windows

## How to Run

### 1. Graphical Interface (GUI)
Simply double-click the `GameTimeManager.exe`, or run the following command in your terminal:
```bash
GameTimeManager
```

### 2. Integrated Launcher (Pre-Game Tracker)
To use the app as a prompt when launching a game, run:
```bash
GameTimeManager "Your Game Name"
```
This will open a small "Pre-Game Tracker" window asking if you want to track time for that game.

### 3. Command Line (CLI) Usage
You can start and stop the timer using your terminal (CMD, PowerShell, etc.). If the app is already open, the terminal will silently communicate with it!

To start the timer immediately:
```bash
GameTimeManager start "game name" "Tag1, Tag2"
```

To stop and save the current timer:
```bash
GameTimeManager stop
```

## Disclaimer

This program/project was written entirely using AI. No warranties are provided regarding its functionality or performance. I am a solo person with little to no coding experience, driven by a passion for "100%ing" games and tracking playtime.
