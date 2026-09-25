import re
import os

path = r'c:\Proyectos\Aura_Writer\src\ui\character_dock.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Regular expression to match .setStyleSheet(...)
# It handles strings with balanced parentheses (mostly)
# For multiline """ """ we can use a more robust approach:
# We just want to replace .setStyleSheet( <anything up to the balanced closing paren> )

def remove_stylesheets(text):
    # This regex is a bit complex for python's standard library if there are nested parentheses.
    # An easier way: replace specific hardcoded style strings that force dark mode
    # like background: #1c1c1e or #2c2c2e
    
    # Or just replace all occurrences of `self.setStyleSheet(` with `pass # self.setStyleSheet(`
    # wait, that won't handle multi-line easily if it's chained.
    
    # Let's replace colors that force dark mode with transparent or nothing.
    # Actually, the user wants the widget to follow the theme manager.
    # So removing all setStyleSheet is best.
    pass

# Let's manually parse and strip setStyleSheet blocks
lines = content.split('\n')
new_lines = []
skip = False
for line in lines:
    if '.setStyleSheet(' in line:
        # Check if it ends on the same line
        if line.count('(') == line.count(')'):
            new_lines.append(line.replace('.setStyleSheet(', ' # .setStyleSheet('))
            continue
        else:
            skip = True
            new_lines.append('# ' + line)
            continue
    
    if skip:
        new_lines.append('# ' + line)
        if line.count(')') > line.count('('):
            skip = False
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print("Done")
