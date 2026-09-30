"""
Gera a VOZ HUMANA (neural) da apresentação.

Lê todas as frases do apresentacao-tds.html e grava um arquivo .mp3 para cada uma
na pasta "audio". A apresentação toca esses arquivos em qualquer computador
(não precisa de internet na hora de apresentar).

Como usar:  dê dois cliques em  gerar_audios.bat   (ou:  python gerar_audios.py)
Refaça sempre que mudar nomes/textos no bloco CONFIG do HTML.
Requer: Python, Node.js e internet (só para gerar).
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts

# ====== AJUSTES DE VOZ ======================================================
# Vozes neurais em português do Brasil:
#   pt-BR-AntonioNeural              -> masculina (a única masculina neural pt-BR)
#   pt-BR-FranciscaNeural            -> feminina, calorosa e clara
#   pt-BR-ThalitaMultilingualNeural  -> feminina, multilíngue (evite: pode falar com sotaque inglês)
# Marquês = "m"  |  Aura = "f"
VOZES = {
    "m": "pt-BR-AntonioNeural",
    "f": "pt-BR-FranciscaNeural",   # só português do Brasil (a Thalita "Multilingual" pode pegar sotaque inglês)
}
VELOCIDADE = "-4%"    # negativo = mais devagar (ex.: "-8%"); positivo = mais rápido
TOM = "+0Hz"          # ex.: "+8Hz" deixa a voz um pouco mais aguda
VOLUME = "+0%"
# ============================================================================

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "audio"
ASSINATURA = SAIDA / "_voz.txt"


def carregar_frases():
    r = subprocess.run(
        ["node", str(AQUI / "extrair_textos.js")],
        capture_output=True, encoding="utf-8",
    )
    if r.returncode != 0:
        sys.exit("Erro ao ler as frases (o Node.js está instalado?):\n" + r.stderr)
    return json.loads(r.stdout)  # lista de [id, texto, quem]


async def gerar(id_, texto, quem, sem, tentativas=4):
    destino = SAIDA / f"{id_}.mp3"
    async with sem:
        for t in range(1, tentativas + 1):
            try:
                com = edge_tts.Communicate(texto, VOZES[quem], rate=VELOCIDADE, pitch=TOM, volume=VOLUME)
                await com.save(str(destino))
                if destino.stat().st_size > 500:
                    return True
            except Exception as e:  # rede instável: tenta de novo
                if t == tentativas:
                    print(f"  ! falhou: {texto[:50]}… ({e})")
                await asyncio.sleep(1.5 * t)
    return False


async def principal():
    SAIDA.mkdir(exist_ok=True)
    frases = carregar_frases()
    assinatura = f"{VOZES['m']}|{VOZES['f']}|{VELOCIDADE}|{TOM}|{VOLUME}"

    # Se a voz mudou, refaz tudo; senão só cria o que falta.
    refazer = "--refazer" in sys.argv or not ASSINATURA.exists() or ASSINATURA.read_text(encoding="utf-8") != assinatura
    ids_atuais = {i for i, _, _ in frases}
    for velho in SAIDA.glob("*.mp3"):
        if refazer or velho.stem not in ids_atuais:
            velho.unlink()

    pendentes = [(i, t, q) for i, t, q in frases if not (SAIDA / f"{i}.mp3").exists()]
    print(f"Vozes: {VOZES['m']} (masc.) e {VOZES['f']} (fem.)  |  frases: {len(frases)}  |  a gerar: {len(pendentes)}")
    sem = asyncio.Semaphore(4)
    ok = await asyncio.gather(*(gerar(i, t, q, sem) for i, t, q in pendentes))
    if pendentes:
        print(f"Gerados {sum(ok)} de {len(pendentes)} áudios.")
    if all(ok):
        ASSINATURA.write_text(assinatura, encoding="utf-8")
        print("Pronto! Abra o apresentacao-tds.html (a pasta 'audio' deve ficar junto do arquivo).")
    else:
        print("Alguns áudios falharam. Rode de novo para completar.")


def gerar_envelopes():
    """Mede o volume REAL de cada áudio (40 medidas por segundo) e grava em audio/env.js.
    O robô usa isso para abrir e fechar a boca exatamente conforme a voz."""
    try:
        import array
        import miniaudio
    except ImportError:
        print("Aviso: instale o pacote 'miniaudio' (pip install miniaudio) para a boca acompanhar a voz.")
        return
    FPS = 40
    bruto = {}
    for arq in sorted(SAIDA.glob("*.mp3")):
        d = miniaudio.decode_file(str(arq), output_format=miniaudio.SampleFormat.SIGNED16,
                                  nchannels=1, sample_rate=16000)
        amostras = array.array("h", d.samples)
        passo = 16000 // FPS
        janela = passo * 2  # janela um pouco maior deixa o movimento mais suave
        rms = []
        for ini in range(0, len(amostras), passo):
            trecho = amostras[max(0, ini - passo // 2): ini - passo // 2 + janela]
            if not trecho:
                rms.append(0.0)
                continue
            rms.append((sum(x * x for x in trecho) / len(trecho)) ** 0.5)
        bruto[arq.stem] = rms
    if not bruto:
        return
    todos = sorted(v for r in bruto.values() for v in r if v > 0)
    ref = todos[int(len(todos) * 0.95)] or 1.0  # 95% do volume = boca bem aberta
    piso = ref * 0.06                            # abaixo disso é silêncio: boca fechada
    saida = {}
    for nome, rms in bruto.items():
        niveis = []
        for v in rms:
            n = 0 if v < piso else min(1.0, (v - piso) / (ref - piso)) ** 0.8
            niveis.append("%x" % round(n * 15))
        saida[nome] = "".join(niveis)
    js = "window.TDS_ENV=" + json.dumps({"fps": FPS, "d": saida}, separators=(",", ":")) + ";\n"
    (SAIDA / "env.js").write_text(js, encoding="utf-8")
    print(f"Movimento da boca gravado para {len(saida)} áudios (audio/env.js).")


if __name__ == "__main__":
    asyncio.run(principal())
    gerar_envelopes()
