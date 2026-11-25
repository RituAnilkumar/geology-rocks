# Specimen testing — guide for session leads and testers

Specimen testing checks the key against real rocks whose names we already
know. It finds two kinds of problem: **content** (a probability or question
that is wrong for real rocks) and **wording** (a question people can't answer
confidently). Nothing here needs coding.

There are three parts:

1. **Session lead** (usually Ritu): prepares the specimens, runs the session
   and fills in the true rock types afterwards.
2. **Testers**: key out the rocks without looking at the labels. The printable
   one-page sheet tells them what to do (link at the top of the key page:
   *Tester instructions (print)*).
3. **Report**: one command summarises all the tests.

## 1. Before the session

- **Choose 10–20 specimens the key knows.** The key page's *Test results*
  page lists every rock type in its drop-down. A few rocks that are *not* in
  the key are useful too: the key should say "not sure", not guess
  confidently.
- **Include look-alikes**, such as slate/phyllite, basalt/hornfels,
  conglomerate/breccia and chert/flint. These are the pairs the simulation
  confuses most.
- **Cover the labels and number the specimens** (1, 2, 3…). Keep a private
  list of number → rock name for later.
- **Decide what testers may do to the specimens.** Scratching, acid and
  hammers can damage collection specimens. Tell testers clearly, and only put
  out the kit that is allowed. Testers should tick only that kit in *My kit*.
- **Print the tester sheet**, one per table.
- Start the key (`./run-key`, see section 4) and check that the page opens.

## 2. During the session

- Testers fill in the specimen number, their first name or initials and their
  experience. Then they answer questions until the key runs out of useful
  questions or they are happy with the result.
- **"Not sure" is welcome.** It shows which questions are hard. Encourage
  testers not to guess.
- They press **Save this test**, say how sure they are of the key's answer,
  and add a note if anything was odd.
- One laptop can be passed round, or several people can take turns.
- Leave *Where did you find it?* on "Not saying" unless you are deliberately
  testing find contexts. A museum specimen has no real find context.

## 3. After the session

1. On the key page, click **Test results**.
2. For each test, choose the **true rock type** from the list (or *Not in the
   key*). Each choice is saved straight away.
3. **Tests from other laptops:** put each person's file in the `testing`
   folder. Give it any name ending in `.csv`, for example
   `testing/from-alex.csv`, then reload the Test results page. A test that
   arrives twice is only counted once.
4. In the terminal, run `./run-test-report`.
5. Open `reports/specimen-test-report.md`. In VS Code, right-click the file
   and choose *Open Preview*. The report covers:
   - how often the key named the right rock type, stopped at the right group,
     was not sure yet, or was wrong
   - results by experience level and by rock type
   - the most common mix-ups
   - which questions people skipped or weren't sure about
   - answers that disagree with the content (either a misread specimen or a
     probability worth checking)
   - testers' confidence compared with how the key actually did
6. Share the findings with Claude Code to review together. Any content
   changes stay `draft` until you approve them. After content changes, run
   `./run-test-report` again: its "With today's content" column replays the
   same answers through the new content, so you can see if the fix helped
   without testing again.

The test files are in `testing/`, which is never uploaded to GitHub because
it holds testers' names. You can also open the files in a spreadsheet
program. Close them there before saving more tests.

## 4. Running the key on your own laptop (for testers)

You need **Python 3.11 or newer** (free, from python.org) and the project
files. You do **not** need git or a GitHub account.

1. **Get the files.** On the project's GitHub page, click the green **Code**
   button, then **Download ZIP**. Unzip it somewhere easy to find, such as
   your Documents folder.
2. **Install Python** if you don't have it: download it from
   <https://www.python.org/downloads/>. On Windows, tick **"Add python.exe to
   PATH"** during installation.
3. **Start the key:**
   - **Windows:** open the unzipped folder and double-click **`run-key.bat`**.
   - **Mac:** open *Terminal*, type `cd ` (with a space), drag the unzipped
     folder onto the Terminal window, press Enter, then type `bash run-key`
     and press Enter.
   - **Linux:** in a terminal in the folder, type `./run-key`.

   The first start takes a minute or two while it sets itself up. Then it
   shows **"Open this in your browser: http://localhost:8765/"**. If the
   browser doesn't open by itself, type that address into it.
4. Follow the printed tester sheet. Leave the black window open while you
   test. Close it (or press Ctrl+C) when you're finished.
5. **Send your results:** your tests are saved in the `testing` folder inside
   the unzipped folder, as `test-runs.csv`. Email that file to the session
   lead.

The key runs only on your computer: nothing is sent anywhere, and nobody else
can open your page.

If something goes wrong, copy the message from the black window and send it
to the session lead.
