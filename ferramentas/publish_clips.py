"""Copia (recomprimindo) os clipes cortados para o repositório BaskStatsClipes e gera:
  - <repo>/<partida>/<Categoria>/clipe_XXX....mp4   (540p, H.264 + AAC, faststart p/ streaming)
  - <repo>/clipes.json                              (manifesto: categoria, tempo no jogo, lances)
  - <repo>/sql/<partida>_clipes.sql                 (INSERT na tabela clipe do banco)

Uso: python publish_clips.py <pasta_clipes> <repo> <id_partida> <base_url>
"""
import csv, json, subprocess, sys
from pathlib import Path

src, repo, partida, base = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4].rstrip("/")
CATEGORIAS = ["Ataque", "Defesa", "Finalizacoes", "Rebote_Ofensivo"]


def nome_base(c):
    return f"clipe_{int(float(c['clipe_id'])):03d}_Q{c['quarto']}_{int(float(c['inicio_seg']))}s-{int(float(c['fim_seg']))}s"


manifesto, sql = [], [
    f"-- Clipes da partida {partida} (gerado automaticamente a partir do corte automático)",
    "BEGIN;",
    f"DELETE FROM clipe WHERE partida_id = {partida} AND caminho_arquivo LIKE '{base}/%';",
]
for cat in CATEGORIAS:
    lista = src / cat / "lista_clipes.csv"
    if not lista.exists():
        continue
    destino = repo / str(partida) / cat
    destino.mkdir(parents=True, exist_ok=True)
    for c in csv.DictReader(open(lista, encoding="utf-8-sig")):
        nb = nome_base(c)
        origem = src / cat / f"{nb}.mp4"
        if not origem.exists():
            print("FALTANDO", origem)
            continue
        alvo = destino / f"{nb}.mp4"
        if not alvo.exists():
            subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-y", "-i", str(origem), "-vf", "scale=-2:540",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac", "-b:a", "96k",
                 "-movflags", "+faststart", str(alvo)], check=True)
        rel = alvo.relative_to(repo).as_posix()
        url = f"{base}/{rel}"
        ini, fim, dur = float(c["inicio_seg"]), float(c["fim_seg"]), float(c["duracao_seg"])
        manifesto.append({
            "partida": partida, "categoria": cat, "arquivo": rel, "url": url,
            "quarto": c["quarto"], "inicio_jogo_seg": ini, "fim_jogo_seg": fim, "duracao_seg": dur,
            "tipos_evento": c.get("tipos_evento", ""), "jogadoras": c.get("jogadoras", ""),
            "descricao": c.get("descricao", ""),
        })
        sql.append(
            "INSERT INTO clipe (categoria_clipe_id, partida_id, inicio_segundos, fim_segundos, duracao_segundos, caminho_arquivo) "
            f"SELECT id_categoria_clipe, {partida}, {ini}, {fim}, {dur}, '{url}' FROM categoriaclipe WHERE nome = '{cat}';"
        )
sql.append("COMMIT;")
(repo / "clipes.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
(repo / "sql").mkdir(exist_ok=True)
(repo / "sql" / f"{partida}_clipes.sql").write_text("\n".join(sql) + "\n", encoding="utf-8")
print(f"{len(manifesto)} clipes publicados em {repo}")
