# aismell — vhs script
Set Theme "Catppuccin Mocha"
Set FontSize 16
Set Width 1200
Set Height 700
Set Padding 28
Set TypingSpeed 30ms

Type "# Texto AI: olor evidente"
Enter
Sleep 600ms
Type "aismell examples/sample-es.md"
Sleep 400ms
Enter
Sleep 4500ms

Type "clear"
Enter

Type "# Texto humano: limpio"
Enter
Sleep 500ms
Type "aismell examples/clean-es.md"
Sleep 400ms
Enter
Sleep 2500ms

Type "clear"
Enter

Type "# Inglés: misma vibra"
Enter
Sleep 400ms
Type "aismell examples/sample-en.md"
Sleep 400ms
Enter
Sleep 4000ms

Type "clear"
Enter

Type "# Pipe + score-only para CI"
Enter
Sleep 500ms
Type `echo "Vale la pena destacar que delve into the tapestry." | aismell --score-only`
Sleep 400ms
Enter
Sleep 1800ms

Output demo.gif
