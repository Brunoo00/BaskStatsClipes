"""Roda a ferramenta do Raya (BaskStatsDados/Codigo playBYplay) sem alterar o código dela:
só troca as constantes (times, pastas, âncoras) para o jogo escolhido."""
import os, sys
TOOL = "/home/gui200428/Downloads/buruno/BaskStatsDados/Codigo playBYplay"
sys.path.insert(0, TOOL)
import transform, main as etl, clip_selector as cs
import pandas as pd

WORK = sys.argv[1]
PRINCIPAL, ADVERSARIO = "SES", "SMB"
transform.SIGLAS_TIME = {"SES": "SESI ARARAQUARA BASQUETE", "SMB": "SAMPAIO BASQUETE"}
etl.PASTA_SAIDA = WORK
etl.ANCORAS_VIDEO = {
    1: ("12:55", "32:41"),
    2: ("35:27", "1:11:58"),
    3: ("1:29:24", "1:46:26"),
    4: ("1:49:11", "2:11:33"),
}
etl.main([os.path.join(WORK, f"{q}Qjogo.txt") for q in (1, 2, 3, 4)])

cs.PASTA_CLIPES = os.path.join(WORK, "clipes")
cats = {
    "Defesa": (ADVERSARIO, cs.EVENTOS_FIM_DE_POSSE),
    "Ataque": (PRINCIPAL, cs.EVENTOS_FIM_DE_POSSE),
    "Finalizacoes": (PRINCIPAL, cs.EVENTOS_FINALIZACAO),
    "Rebote_Ofensivo": (PRINCIPAL, cs.EVENTOS_REBOTE_OFENSIVO),
}
regs = pd.read_excel(os.path.join(WORK, "partida_tratada.xlsx")).to_dict("records")
for nome, (sig, ev) in cats.items():
    cs.processar_categoria(regs, nome, sig, ev)
nc = [r for r in regs if r["tipo_evento"] == "nao_classificado"]
print("nao_classificados:", len(nc), sorted({r["descricao_original"][:40] for r in nc})[:15])
