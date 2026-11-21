"""Converte o JSON de tempo real da LBF no formato QxFinais.txt (4 linhas por lance) da ferramenta do Raya."""
import json, re, sys
from pathlib import Path
src, outdir = sys.argv[1], Path(sys.argv[2])
d = json.load(open(src, encoding="utf-8"))
siglas = {d["equipe1"]["id"]: d["equipe1"]["sigla"], d["equipe2"]["id"]: d["equipe2"]["sigla"]}
por_quarto = {}
for j in d["jogadas"]:  # já vem do mais recente para o mais antigo, como o .txt original
    q = j["quarto"]
    sig = siglas.get(j["equipe"], "")
    msg = re.sub(r"\s+", " ", j["msg"]).strip()
    msg = re.sub(r"\s+\.", ".", msg)
    por_quarto.setdefault(q, []).append([f"{q}º Q{sig}", j["tempo"], j["placar"], msg])
for q, regs in sorted(por_quarto.items()):
    p = outdir / f"{q}Qjogo.txt"
    p.write_text("\n".join("\n".join(r) for r in regs) + "\n", encoding="utf-8")
    print(p, len(regs))
print("equipe1 (placar à esquerda):", d["equipe1"]["sigla"], d["equipe1"]["nome"])
print("equipe2:", d["equipe2"]["sigla"], d["equipe2"]["nome"])
