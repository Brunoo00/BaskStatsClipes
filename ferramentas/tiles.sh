#!/bin/bash
# uso: tiles.sh video saida_dir passo_seg "ini fim" ...
v=$1; out=$2; step=$3; shift 3; i=0
for w in "$@"; do set -- $w; i=$((i+1))
ffmpeg -loglevel error -y -copyts -ss $1 -to $2 -i "$v" -vf "fps=1/$step,crop=400:46:120:287,drawtext=text='%{pts\:hms}':x=2:y=2:fontsize=14:fontcolor=yellow:box=1:boxcolor=black,tile=3x15" -frames:v 1 "$out/w$i.png"
done
