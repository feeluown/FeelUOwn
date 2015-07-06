#!/bin/sh
for dd in /usr/share/applications ~/.local/share/applications; do
 for d in $(ls $dd 2>/dev/null | grep "\\.desktop$" 2>/dev/null); do
  for m in $(grep MimeType $dd/$d | cut -d= -f2 | tr ";" " "); do
   echo xdg-mime default $d $m;
  done;
 done;
done;
