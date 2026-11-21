"""Recalcula timestamp_video_segundos de cada lance usando o cronômetro lido da tela (clock_ocr.csv)
em vez da interpolação linear por quarto, e gera de novo as listas de clipes (clip_selector do Raya)."""
import os, sys, csv
import numpy as np, pandas as pd
TOOL = "/home/gui200428/Downloads/buruno/BaskStatsDados/Codigo playBYplay"
sys.path.insert(0, TOOL)
import clip_selector as cs

WORK = sys.argv[1]
JANELAS = {1: (12*60+40, 32*60+50), 2: (35*60+15, 72*60+10), 3: (89*60+10, 106*60+40), 4: (109*60, 131*60+45)}
PRINCIPAL, ADVERSARIO = "SES", "SMB"

ocr = pd.read_csv(os.path.join(WORK, "clock_ocr.csv"))
mapas = {}
for q, (a, b) in JANELAS.items():
    d = ocr[(ocr.video_s >= a) & (ocr.video_s <= b)].sort_values("video_s")
    # remove leituras incoerentes: o relógio só pode descer; mantém a maior sequência não crescente
    v, c = d.video_s.to_numpy(), d.clock_s.to_numpy()
    # o relógio só desce dentro do quarto: mantém a maior subsequência não crescente
    # (descarta leituras erradas do OCR e o "10:00" do quarto seguinte)
    import bisect
    neg = -c  # não crescente em c == não decrescente em -c
    tails, tails_idx, prev = [], [], [-1] * len(c)
    for i, x in enumerate(neg):
        j = bisect.bisect_right(tails, x)
        if j == len(tails): tails.append(x); tails_idx.append(i)
        else: tails[j] = x; tails_idx[j] = i
        prev[i] = tails_idx[j - 1] if j > 0 else -1
    idx, k = [], tails_idx[-1]
    while k != -1: idx.append(k); k = prev[k]
    idx = idx[::-1]
    v, c = v[idx], c[idx]
    mapas[q] = (v, c)
    print(f"Q{q}: {len(v)} leituras, relógio {c.max()}→{c.min()}s")

def janela_relogio(q, clock):
    """Primeiro e último instante do vídeo em que o relógio mostra `clock` (ou interpolado)."""
    v, c = mapas[q]
    hit = v[c == clock]
    if len(hit):
        return float(hit.min()), float(hit.max())
    # interpolação entre a última leitura > clock e a primeira < clock
    maior, menor = v[c > clock], v[c < clock]
    if len(maior) and len(menor):
        t1, t2 = maior.max(), menor[menor > maior.max()].min() if (menor > maior.max()).any() else menor.min()
        c1 = c[v == t1][0]; c2 = c[v == t2][0]
        t = t1 + (t2 - t1) * (c1 - clock) / max(c1 - c2, 1)
        return float(t), float(t)
    return (float(v.min()), float(v.min())) if len(maior) == 0 else (float(v.max()), float(v.max()))

df = pd.read_excel(os.path.join(WORK, "partida_tratada.xlsx"))
df["timestamp_linear_segundos"] = df["timestamp_video_segundos"]
novos = []
for (q, clk), g in df.groupby(["quarto", "clock_segundos_restantes" if "clock_segundos_restantes" in df else "clock"], sort=False):
    pass
clock_s = df["clock"].map(lambda s: int(s.split(":")[0]) * 60 + int(s.split(":")[1]))
for i, r in df.iterrows():
    q, clk = int(r.quarto), int(clock_s[i])
    ini, fim = janela_relogio(q, clk)
    if str(r.tipo_evento).startswith("lance_livre"):
        # lances livres acontecem com o relógio parado, logo antes do jogo voltar
        mesmos = df[(df.quarto == q) & (clock_s == clk) & df.tipo_evento.astype(str).str.startswith("lance_livre")]
        k_restantes = int((mesmos.ordem_global > r.ordem_global).sum())
        t = max(ini, fim - 4 - 14 * k_restantes)
    else:
        t = ini + 0.5
    novos.append(round(t, 1))
df["timestamp_video_segundos"] = novos
df["timestamp_video"] = [f"{int(t//3600)}:{int(t%3600//60):02d}:{int(t%60):02d}" for t in novos]
df.to_excel(os.path.join(WORK, "partida_tratada.xlsx"), index=False, sheet_name="Play-by-play")
dif = (df.timestamp_video_segundos - df.timestamp_linear_segundos).abs()
print(f"diferença vs. interpolação linear: mediana {dif.median():.0f}s, máx {dif.max():.0f}s")

cs.PASTA_CLIPES = os.path.join(WORK, "clipes")
regs = df.to_dict("records")
for nome, (sig, ev) in {
    "Defesa": (ADVERSARIO, cs.EVENTOS_FIM_DE_POSSE),
    "Ataque": (PRINCIPAL, cs.EVENTOS_FIM_DE_POSSE),
    "Finalizacoes": (PRINCIPAL, cs.EVENTOS_FINALIZACAO),
    "Rebote_Ofensivo": (PRINCIPAL, cs.EVENTOS_REBOTE_OFENSIVO),
}.items():
    cs.processar_categoria(regs, nome, sig, ev)
