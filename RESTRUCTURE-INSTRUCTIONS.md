# Istruzioni per ristrutturare WORKSPACE-SPLIT.md

## Problema
Il file è cresciuto a 2600+ righe organicamente. Ha:
- Fasi numerate fuori ordine (1-22, 23a-e, 24a-f, 27a-f, 29a, 30-35, 32b-f, 36b-c, 37b, 38b-c, 39b, 40b, 41-46)
- Learnings in 4 sezioni diverse (sessione 1-3, sessione 3 agenti, sessione 4, sparse)
- Buchi documentati in 3 posti (tabella workflow, sezione audit, architecture review)
- Ordine esecuzione in MISSION.md ma non qui
- Fasi completate mischiate con fasi future

## Struttura target

```
# Convergio — Master Tracker

## 1. VISION (cosa è convergio — 20 righe)

## 2. ARCHITECTURE (3 layer, extension contract — 50 righe)

## 3. STATO ATTUALE (tabella onesta: cosa funziona / cosa è stub / cosa manca)
   Include la sezione Architecture Review con i 7 gap e il confronto competitivo.

## 4. FASI COMPLETATE (storia — collassata, solo titolo+PR+data per ogni fase)
   Fase 1-22: infrastruttura core — DONE
   Fase 23a-d: integration hardening — DONE (PR #25-32)
   Fase 24a-f: plan protocol — DONE (PR #30, #35)
   ... etc (una riga per fase, non il dettaglio)

## 5. FASI IN CORSO
   Dettaglio completo solo per le fasi attive.

## 6. FASI FUTURE (ordinate per priorità, con deps)
   Step 0: Loop chiuso (32b ✅, 32c, 32d, 32e, 32f)
   Step 1: Fondamenta (23e)
   Step 2: Delegation (31, 37b, 34, 35)
   Step 3: Completamento (36b, 39b, 40b, Frontend)
   Step 4: Production hardening (41-46)
   Step 5: Self-hosting (26)

## 7. CONSTITUTION (regole 1-12, compatte)

## 8. WORKFLOW CONTRATTO (il flusso E2E con tabella buchi ✅/❌)

## 9. LEARNINGS (TUTTI in ordine cronologico, 1-22+)
   Ogni learning: numero, titolo, root cause, fix, regola derivata.

## 10. ARCHITECTURE REVIEW (feedback esterno, confronto, gap)

## 11. APPENDICI
   - Piano 10056 task assorbiti
   - Repo coinvolti
   - Come delegare a Copilot
   - Fase 27a guardrails migration dettaglio
```

## Regole per la ristrutturazione
1. NON eliminare nessun contenuto — sposta, non cancella
2. Le fasi completate vanno COLLASSATE (titolo+PR+data, non il dettaglio dei task)
3. Le fasi future restano con il dettaglio completo
4. I learnings vanno UNIFICATI in una sola sezione, in ordine cronologico
5. L'ordine di esecuzione deve essere in WORKSPACE-SPLIT.md (non solo in MISSION.md)
6. La sezione STATO ATTUALE deve essere la prima cosa utile che un agente legge
7. Il file deve restare <2000 righe dopo la ristrutturazione
