# BaskStats — Clipes

Clipes gerados pelo **corte automático** (ferramenta do Raya em
`BaskStatsDados/Codigo playBYplay`) e servidos como **Static Site no Render**.
A tela **Vídeos** do site (`BaskStats`) lê esses clipes pela tabela `clipe` do banco.

## Conteúdo

```
1620/                     # id da partida na LBF (= partida.id_partida no banco)
  Ataque/                 # posses ofensivas do SESI
  Defesa/                 # posses ofensivas do adversário (o que a defesa do SESI enfrenta)
  Finalizacoes/           # arremessos e lances livres do SESI
  Rebote_Ofensivo/        # rebotes ofensivos do SESI
clipes.json               # manifesto: categoria, quarto, tempo no jogo, lances e jogadoras de cada clipe
sql/1620_clipes.sql       # INSERT na tabela clipe (rodar com um usuário com permissão de escrita)
ferramentas/              # scripts usados para gerar tudo (ver abaixo)
```

Jogo atual: **1620 — SESI Araraquara 48 × 61 Sampaio Basquete (07/06/2026)**,
vídeo `https://www.youtube.com/watch?v=Gkpg-MNNJn8` (Live Basketball BR).
É o jogo mais recente do SESI com transmissão completa pública e lance a lance da LBF
(os jogos de 11/06 em diante passaram na ESPN/Disney+).

## Deploy no Render (Static Site)

1. Render → **New → Static Site** → conectar este repositório.
2. Build command: *(vazio)* · Publish directory: `.`
3. Depois do deploy, a URL fica `https://<nome>.onrender.com`. Se for diferente de
   `https://baskstatsclipes.onrender.com`, gere o SQL de novo com a URL certa
   (passo 6 abaixo).

## Como gerar clipes de outro jogo

Requisitos: Python 3, `ffmpeg` no PATH, e
`pip install pandas openpyxl yt-dlp deno rapidocr_onnxruntime opencv-python-headless`.

1. **Lance a lance** (JSON público da LBF) → arquivos `1Qjogo.txt … 4Qjogo.txt`, no formato da ferramenta do Raya:
   ```bash
   curl -sL "https://lbf.com.br/ws/tempo_real_bybr/json/<ID>_tempo_real.json" -o t<ID>.json
   python ferramentas/json_to_txt.py t<ID>.json trabalho/<ID>
   ```
2. **Vídeo em baixa resolução**, só para ler o cronômetro:
   `yt-dlp -f "bestvideo[height<=360][ext=mp4]" -o trabalho/<ID>/low.mp4 <link>`
3. **Âncoras dos quartos** (início/fim de cada quarto no vídeo): use `ferramentas/tiles.sh`
   para gerar mosaicos do placar e ajuste `ANCORAS_VIDEO` e as siglas em `run_pipeline.py`.
   Depois rode `python ferramentas/run_pipeline.py trabalho/<ID>`.
4. **Sincronização fina pelo cronômetro da tela.** A interpolação linear da ferramenta original
   erra em média ~1 min, porque o relógio para em faltas, tempos e lances livres. Este passo lê o
   cronômetro do placar da transmissão (OCR, 1 quadro/s) e reposiciona cada lance:
   ```bash
   python ferramentas/ocr_clock.py trabalho/<ID>/low.mp4 trabalho/<ID>/clock_ocr.csv
   python ferramentas/dense_mapping.py trabalho/<ID>     # ajuste JANELAS e siglas no topo
   ```
   O recorte do placar (`crop`) foi calibrado para a transmissão da LBF em 640×360.
5. **Corte** (ferramenta do Raya, sem alterações):
   ```bash
   python "BaskStatsDados/Codigo playBYplay/cut_video.py" "<link>" trabalho/<ID>/clipes/Ataque/lista_clipes.csv --saida trabalho/<ID>/clipes/Ataque --paralelo 4
   ```
   (repita para Defesa, Finalizacoes e Rebote_Ofensivo)
6. **Publicar** (recomprime para 540p, gera o `clipes.json` e o SQL):
   ```bash
   python ferramentas/publish_clips.py trabalho/<ID>/clipes . <ID> https://baskstatsclipes.onrender.com
   ```
