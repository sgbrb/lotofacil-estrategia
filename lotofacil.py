import itertools
import os
import random
import pandas as pd
import requests
from collections import Counter

# ============================================================
# CRITÉRIOS FIXOS — NÃO MUDE A CADA CONCURSO
# Calibrados em faixas para cobrir ~30-50% dos sorteios históricos
# ============================================================
CRITERIOS = {
    "soma_min": 190,
    "soma_max": 230,
    "repetidos_min": 9,
    "repetidos_max": 11,      # faixa, não exato
    "impares_min": 7,
    "impares_max": 9,         # faixa, não exato
    "moldura_min": 9,
    "moldura_max": 12,        # faixa, não exato
    "seq_max": 4,              # máximo de consecutivos
    "primos_min": 4,
    "primos_max": 8,          # faixa larga
}

# Quantos jogos sortear aleatoriamente do universo filtrado
QTD_JOGOS_FINAIS = 15
# Quantos concursos usar como histórico para o bônus de frequência
QTD_HISTORICO = 50

# --- Definições ---
MOLDURA = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS  = {2, 3, 5, 7, 11, 13, 17, 19, 23}


def buscar_resultados_recentes(qtd=QTD_HISTORICO):
    print(f"Buscando os últimos {qtd} concursos para análise de frequência...")
    dezenas_historico = []
    ultimo_resultado = None

    try:
        url_latest = "https://loteriascaixa-api.herokuapp.com/api/lotofacil/latest"
        resp = requests.get(url_latest, timeout=10)
        if resp.status_code != 200:
            raise Exception("Falha ao buscar último concurso.")

        dados_latest = resp.json()
        ultimo_concurso_num = dados_latest["concurso"]
        ultimo_resultado = set(int(d) for d in dados_latest["dezenas"])
        dezenas_historico.append(ultimo_resultado)
        print(f"[SUCESSO] Concurso {ultimo_concurso_num} carregado. "
              f"Dezenas: {sorted(list(ultimo_resultado))}")

        for i in range(1, qtd):
            num_concurso = ultimo_concurso_num - i
            url_concurso = f"https://loteriascaixa-api.herokuapp.com/api/lotofacil/{num_concurso}"
            resp_ant = requests.get(url_concurso, timeout=10)
            if resp_ant.status_code == 200:
                dados_ant = resp_ant.json()
                dezenas_historico.append(set(int(d) for d in dados_ant["dezenas"]))

        print(f"[SUCESSO] {len(dezenas_historico)} concursos carregados para análise.")
        return dezenas_historico, ultimo_resultado

    except Exception as e:
        print(f"[ERRO] Falha na busca online: {e}")
        print("[AVISO] Usando backup manual (Concurso 3807).")
        ultimo_manual = {1, 3, 4, 7, 10, 11, 13, 16, 17, 19, 20, 22, 23, 24, 25}
        return [ultimo_manual], ultimo_manual


def calcular_pesos_frequencia(historico):
    """Calcula pesos com base na frequência histórica (bônus de elite)."""
    if len(historico) <= 1:
        return {d: 0 for d in range(1, 26)}

    contador = Counter()
    for jogo in historico:
        contador.update(jogo)

    max_freq = max(contador.values())
    min_freq = min(contador.values())

    pesos = {}
    for dezena in range(1, 26):
        freq = contador.get(dezena, 0)
        if max_freq == min_freq:
            pesos[dezena] = 2.5
        else:
            pesos[dezena] = ((freq - min_freq) / (max_freq - min_freq)) * 5
    return pesos


def calcular_max_sequencia(jogo):
    max_seq = 1
    seq_atual = 1
    for i in range(len(jogo) - 1):
        if jogo[i + 1] == jogo[i] + 1:
            seq_atual += 1
            max_seq = max(max_seq, seq_atual)
        else:
            seq_atual = 1
    return max_seq


# ============================================================
# EXECUÇÃO
# ============================================================
historico, ultimo_concurso_real = buscar_resultados_recentes(QTD_HISTORICO)
pesos_frequencia = calcular_pesos_frequencia(historico)

print("\nIniciando varredura com critérios FIXOS e sustentáveis...")
print(f"Critérios: {CRITERIOS}\n")

dados_filtrados = []

for jogo_tuple in itertools.combinations(range(1, 26), 15):
    jogo_set = set(jogo_tuple)

    # 1. SOMA (faixa)
    somatoria = sum(jogo_tuple)
    if not (CRITERIOS["soma_min"] <= somatoria <= CRITERIOS["soma_max"]):
        continue

    # 2. REPETIDOS (faixa, não exato)
    repetidos = len(jogo_set.intersection(ultimo_concurso_real))
    if not (CRITERIOS["repetidos_min"] <= repetidos <= CRITERIOS["repetidos_max"]):
        continue

    # 3. ÍMPARES (faixa)
    impares = len([n for n in jogo_tuple if n % 2 != 0])
    if not (CRITERIOS["impares_min"] <= impares <= CRITERIOS["impares_max"]):
        continue
    pares = 15 - impares

    # 4. MOLDURA (faixa)
    qtd_moldura = len(jogo_set.intersection(MOLDURA))
    if not (CRITERIOS["moldura_min"] <= qtd_moldura <= CRITERIOS["moldura_max"]):
        continue
    qtd_retrato = 15 - qtd_moldura

    # 5. SEQUÊNCIAS (máximo)
    if calcular_max_sequencia(jogo_tuple) > CRITERIOS["seq_max"]:
        continue

    # 6. PRIMOS (faixa)
    qtd_primos = len(jogo_set.intersection(PRIMOS))
    if not (CRITERIOS["primos_min"] <= qtd_primos <= CRITERIOS["primos_max"]):
        continue

    # --- PONTUAÇÃO DE ELITE (Frequência) ---
    bonus_frequencia = sum(pesos_frequencia[n] for n in jogo_tuple)

    dados_filtrados.append({
        "Jogo": list(jogo_tuple),
        "Score_Total": round(bonus_frequencia, 2),
        "Soma": somatoria,
        "Repetidos": repetidos,
        "Imp/Par": f"{impares}/{pares}",
        "Mold/Retr": f"{qtd_moldura}/{qtd_retrato}",
        "Primos": qtd_primos,
        "Bonus_Freq": round(bonus_frequencia, 2),
    })

# ============================================================
# SELEÇÃO FINAL: sorteio aleatório dentro do universo filtrado
# (mantém a lógica fixa, mas diversifica os jogos a cada concurso)
# ============================================================
if dados_filtrados:
    df_completo = pd.DataFrame(dados_filtrados)

    print("\n" + "=" * 85)
    print(f"✅ Universo filtrado: {len(df_completo)} jogos passaram pelos critérios fixos.")
    print("=" * 85)

    # Sorteia QTD_JOGOS_FINAIS aleatoriamente do universo filtrado
    qtd_sorteio = min(QTD_JOGOS_FINAIS, len(df_completo))
    df_sorteado = df_completo.sample(n=qtd_sorteio, random_state=None)
    df_sorteado = df_sorteado.sort_values(by="Score_Total", ascending=False)

    print("\n" + "=" * 85)
    print(f"🎲 {qtd_sorteio} jogos sorteados aleatoriamente do universo filtrado")
    print("=" * 85)
    print(df_sorteado.to_string(index=False))
    print("=" * 85)

    nome_arquivo = "jogos_lotofacil_estrategia_fixa.csv"
    try:
        df_sorteado.to_csv(nome_arquivo, index=False, sep=";", encoding="utf-8-sig")
        print(f"\n[SALVO] Arquivo gerado em: {os.path.abspath(nome_arquivo)}")
    except Exception as e:
        print(f"\n[ERRO AO SALVAR] {e}")
else:
    print("\n⚠️ ATENÇÃO: Nenhuma combinação atendeu aos critérios fixos.")
    print("Isso é raro com essas faixas, mas se ocorrer, verifique os critérios.")