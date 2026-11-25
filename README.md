# Geology Rocks

A free, open-source Android field companion for identifying rocks and minerals
— and understanding the story behind them.

- **Interactive key** with picture hints: answer questions in any order, skip
  what you can't tell, and get an honest answer at the level the evidence
  supports.
- **Explains its reasoning** at every step: what each observation tells you.
- **Local geology**: what you're standing on, how the landscape formed, where
  to see the best exposures.
- **Field notebook** with GPS, photos and export — stored only on your phone.
- **Responsible collecting** guidance built in.
- **Works offline.** No accounts, no ads, no tracking. Ever.

First region: **South West England**. More to come.

## Status

Early development. See `docs/ROADMAP.md`.

## Try the key prototype on your laptop

Before the Android app exists, the identification key can be tried in a web
browser on your own computer. It is a testing tool: the geology content is
still a draft, and the pictures are placeholders.

**You need:** Python 3.11 or newer (free) and an internet connection the
first time only. No git, no GitHub account, no other installation.

1. **Install Python** from <https://www.python.org/downloads/> if you don't
   have it. On Windows, tick **"Add python.exe to PATH"** during installation.
2. **Download this project:** click the green **Code** button at the top of
   this page, then **Download ZIP**. Unzip it somewhere easy to find, such as
   your Documents folder.
3. **Start the key:**
   - **Windows:** open the unzipped folder and double-click `run-key.bat`.
   - **Mac:** open *Terminal*, type `cd ` (with a space), drag the unzipped
     folder onto the Terminal window and press Enter. Then type `bash run-key`
     and press Enter.
   - **Linux:** open a terminal in the folder and type `./run-key`.
4. The first start takes a minute or two. It downloads a few Python libraries
   into a private folder (`.venv`) inside the project, and nothing else on
   your computer is changed. When it shows **"Open this in your browser:
   http://localhost:8765/"**, open that address. Later starts are quick and
   work offline.
5. Leave the black window open while you use the key. Close it, or press
   Ctrl+C in it, to stop.

The key runs only on your computer: nothing is sent anywhere. If you are
helping with **specimen testing**, the page has a printable tester sheet, and
`docs/SPECIMEN_TESTING.md` explains how to save tests and send your results
file. To remove everything, delete the unzipped folder.

## Licensing

- Code: GPL-3.0-or-later
- Our content and media: CC BY-SA 4.0
- Third-party material: its own licence, recorded per file

See `LICENSING.md`. The name "Geology Rocks" is covered by `NAME_POLICY.md`.

## Contributing

Geologists, photographers, translators and developers are all welcome. See
`CONTRIBUTING.md`.
