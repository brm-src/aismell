# aismell — vhs demo
Set Theme "Catppuccin Mocha"
Set FontSize 16
Set Width 1200
Set Height 720
Set Padding 28
Set TypingSpeed 28ms

# Use the mock CLI for deterministic, fast, small output during recording.
# It falls through to the real ./bin/aismell when no --out flag is given.
Env PATH "/home/brm/Developer/aismell/demo:/home/brm/Developer/aismell/bin:/usr/local/bin:/usr/bin:/bin"

# 1. Detect AI smell in plain text
Type "# 1. detect AI smell in your text"
Enter
Sleep 500ms
Type `aismell examples/sample-es.md`
Sleep 300ms
Enter
Sleep 4500ms

Type "clear"
Enter
Sleep 200ms

# 2. Score only (CI-friendly)
Type "# 2. just a number — for CI / pre-commit"
Enter
Sleep 400ms
Type `aismell --score-only examples/sample-es.md`
Sleep 300ms
Enter
Sleep 1500ms

Type `aismell --score-only examples/clean-es.md`
Sleep 300ms
Enter
Sleep 1500ms

Type "clear"
Enter
Sleep 200ms

# 3. Annotate a Word docx
Type "# 3. annotate a Word .docx — yellow highlights + comments"
Enter
Sleep 400ms
Type `aismell tesis.docx --out tesis-marcada.docx`
Sleep 300ms
Enter
Sleep 2200ms

Type "clear"
Enter
Sleep 200ms

# 4. Annotate a PDF
Type "# 4. annotate a PDF — same idea, sticky notes"
Enter
Sleep 400ms
Type `aismell paper.pdf --out paper-marcado.pdf`
Sleep 300ms
Enter
Sleep 2200ms

Type "clear"
Enter
Sleep 200ms

# 5. No args = file picker
Type "# 5. no arguments? opens a native file picker"
Enter
Sleep 400ms
Type `aismell`
Sleep 300ms
Enter
Sleep 2000ms

Output demo.gif
