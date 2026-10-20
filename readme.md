# Lotofácil — Estratégia Fixa Calibrada

Script para gerar 15 jogos de Lotofácil usando **critérios fixos calibrados** com base em 100 concursos reais. A lógica não muda a cada concurso — apenas o sorteio dos jogos e o histórico de frequência se atualizam automaticamente.

---

## 📋 O que o script faz

1. Baixa o **último concurso** e os **50 anteriores** da API pública.
2. Aplica 6 filtros fixos (soma, repetidos, ímpares, moldura, sequência, primos).
3. Varre as **3.268.760 combinações** possíveis de 15 dezenas.
4. **Sorteia aleatoriamente 15 jogos** do universo filtrado.
5. Salva o resultado em `jogos_lotofacil_estrategia_fixa.csv`.

---

## 🎯 Critérios fixos (calibrados)

| Critério | Faixa | Cobertura histórica |
| :--- | :--- | :--- |
| Soma | 180–220 | ~72% |
| Repetidos (vs. último) | 8–10 | ~87% |
| Ímpares | 7–9 | ~89% |
| Moldura | 9–11 | ~82% |
| Sequência máxima | ≤5 | ~72% |
| Primos | 5–7 | ~79% |
| **Cobertura combinada** | — | **~21% do universo** |

> ⚠️ **Não altere esses critérios a cada concurso.** A força da estratégia está na consistência.

---

## 🚀 Como rodar (passo a passo)

### Pré-requisitos (instalar uma vez só)

1. **Python 3.10+** instalado com "Add to PATH" marcado.
2. Bibliotecas necessárias. No PowerShell:

```powershell
pip install requests pandas

powershell
cd C:\Users\BGS13627\Desktop\loto

powershell
python jogos_lotofacil_estrategia_fixa.py