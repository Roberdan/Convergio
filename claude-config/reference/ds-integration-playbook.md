# Convergio Design System — Release & Integration Playbook

> Generato da sessione 2026-03-29. Replica questo processo per qualsiasi
> repo che consuma `@convergio/design-elements` o `@convergio/design-tokens`.

---

## 1. Fix nel Design System upstream

### 1.1 Trovare il bug

Il barrel TypeScript (`packages/elements/src/ts/index.ts`) potrebbe non
esportare tutte le funzioni presenti nel runtime ESM. Per verificare:

```bash
# Nel bundle ESM, trova tutti gli export assegnati al namespace M
grep "M\.\w\+ = " packages/elements/dist/esm/index.js | sort

# Confronta con le righe export nel barrel dei tipi
grep "^export" packages/elements/dist/types/index.d.ts | sort
```

Ogni `M.xxx = xxx` senza corrispondente `export { xxx }` è un bug.
In questa sessione il bug era `aiChat`: presente in ESM, assente dai tipi.

### 1.2 Creare il fix

```bash
cd /path/to/convergio-design
git checkout main && git pull
git checkout -b fix/nome-descrittivo

# Editare packages/elements/src/ts/index.ts (o index-extras.ts se > 244 righe)
# Aggiungere: export { aiChat } from './ai-chat-iife';

# Verificare localmente
pnpm run build   # deve passare senza errori
pnpm run test     # tutti i test devono passare (82 al momento)
```

### 1.3 PR → CI → Merge

```bash
git add -A && git commit -m "fix: export aiChat from barrel index"
git push -u origin fix/nome-descrittivo

gh pr create \
  --title "fix: export aiChat from barrel index" \
  --body "Descrizione dettagliata del problema e del fix" \
  --base main

# Aspettare CI (2 workflow: push + pull_request, ~3-4 minuti)
gh pr checks <PR_NUMBER> --watch

# Merge (SQUASH DISABILITATO nel repo — usare merge commit)
gh pr merge <PR_NUMBER> --merge
```

### 1.4 Release e publish npm

```bash
git checkout main && git pull origin main

# 1) Bump versione in TUTTI e 3 i package.json
#    - package.json (root)
#    - packages/elements/package.json
#    - packages/tokens/package.json

# 2) Aggiornare CHANGELOG.md (formato Keep a Changelog)

# 3) Rebuild con nuova versione
pnpm run build

# 4) Commit + tag + push
git add -A
git commit -m "chore: release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

Il push del tag `v*` triggera automaticamente:
- **`publish.yml`** → `pnpm -r publish --access public --no-git-checks`
  (pubblica su npmjs.org via `NPM_TOKEN` secret)
- **`release.yml`** → crea GitHub Release con asset (CSS, IIFE, sourcemap)

### 1.5 Verificare

```bash
# Aspettare ~1 minuto, poi:
npm view @convergio/design-elements version   # deve mostrare X.Y.Z
npm view @convergio/design-tokens version     # deve mostrare X.Y.Z

# Verificare GitHub Release
gh release view vX.Y.Z
```

---

## 2. Consumare la nuova versione nel progetto web

```bash
cd /path/to/convergio-web-rebuild
npm install @convergio/design-elements@X.Y.Z @convergio/design-tokens@X.Y.Z --save
npx next build   # deve passare
npm test          # deve passare
```

---

## 3. Pattern di integrazione DS (imperative API in React)

### Pattern corretto

```tsx
'use client';
import { useRef, useEffect } from 'react';

export function MyComponent({ data }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;
    let ctrl: { destroy?: () => void } | null = null;

    import('@convergio/design-elements').then(({ dataTable }) => {
      if (!containerRef.current) return;
      containerRef.current.innerHTML = '';      // pulisci prima di montare
      ctrl = dataTable(containerRef.current, {
        columns: [...],
        data: data as unknown as Record<string, unknown>[],
      });
    });

    return () => { ctrl?.destroy?.(); };        // SEMPRE cleanup
  }, [data]);                                    // deps corrette

  // Loading: early return, NON AnimatePresence
  if (!data) return <Skeleton />;

  return <div ref={containerRef} className="min-h-[200px]" />;
}
```

### Trappole da evitare

| Trappola | Perché è un problema | Soluzione |
|----------|---------------------|-----------|
| `<AnimatePresence>` attorno al container ref | L'exit animation ritarda l'attacco del ref. Il `useEffect` trova `ref.current === null` e non monta nulla. | Usa `if (!loaded) return <Skeleton />;` (early return condizionale). |
| `edges: [{source, target}]` per neuralNodes | L'API usa `connections: [{from, to, strength}]`. Build error silenzioso o crash. | Controlla SEMPRE `dist/types/*.d.ts` per i nomi corretti. |
| `items: [...]` per dashboardStrip | L'API usa `zones: [StripBoardZone]`. | Idem: leggi i tipi, non il CKB/mapping doc. |
| `addMessage({role, content})` per aiChat | L'API è `addMessage(role: 'user'|'ai', content: string, opts?)`. Restituisce `StreamingHandle` con `{append, finish}`. | Usa la signature esatta dai `.d.ts`. |
| `selectEngagement(phaseId)` senza engagements | customerJourney seleziona engagement cards per ID. Se `engagements: []` non c'è nulla da selezionare. | Popola le fasi con engagement reali dai dati. |
| Nessun cleanup SSE/EventSource | EventSource resta aperto dopo unmount, causando leak. | Traccia in un `useRef<EventSource>` e chiudi nel cleanup. |
| Nodi neuralNodes oversize con molti dati | 136 nodi con `size: 18` = muro di cerchi sovrapposti. | Scala: `size = Math.round(base * (total > 80 ? 0.3 : total > 40 ? 0.5 : 1))`. Limita agenti a 20. |
| `sessionId` in deps del useEffect di aiChat | Ogni cambio sessione distrugge e ricrea il widget. Il callback `onSend` chiude su un `ctrl` che viene distrutto mid-send. | Usa `useRef` per sessionId e controller. Monta aiChat una volta sola. |

---

## 4. Checklist pre-commit

- [ ] `npx next build` passa senza errori
- [ ] `npm test` (vitest) — tutti i test passano
- [ ] Screenshot Playwright di OGNI pagina — verificare visivamente:
  - Tabelle renderizzate con dati reali (non vuote)
  - Grafici con nodi leggibili (non sovrapposti)
  - Nessun testo fallback visibile (es. "Gauge: 1,")
  - Header shell presente con navigazione
- [ ] Nessun `console.error` nel browser
- [ ] Max 250 righe per file
- [ ] `'use client'` su ogni file con hooks
- [ ] Ogni `useEffect` con dynamic import ha cleanup `ctrl?.destroy?.()`

---

## 5. Audit cross-modello

Usare un modello AI diverso da quello di sviluppo per l'audit finale.
In questa sessione: sviluppo con Claude Opus 4.6, audit con GPT-5.4.

L'audit ha trovato 4 bug critici che lo sviluppatore non aveva visto:
1. Chat widget distrutto mid-send (sessionId in deps)
2. SSE stream mai chiuso su unmount
3. Guard `ctrlRef.current?.update` su metodo inesistente (brain)
4. `selectEngagement` con engagements vuoti (evolution)

### Come lanciare l'audit

Passare al modello auditor:
- Il contesto completo dei file modificati
- Le API signatures esatte dal DS (tipi `.d.ts`)
- Il pattern di integrazione atteso
- Istruzioni di concentrarsi SOLO su bug, API misuse, logica — MAI stile

---

## 6. DS Components utilizzati (9 su 17+ target)

| Componente | File che lo usano |
|-----------|-------------------|
| `headerShell` | app-shell.tsx |
| `createGauge` | kpi-strip.tsx |
| `dataTable` | agents, mesh, evolution, mission-control, agent-sidebar, chat |
| `kanbanBoard` | workspaces |
| `neuralNodes` | brain, mesh-topology |
| `aiChat` | chat |
| `customerJourney` | evolution |
| `dashboardStrip` | evolution |
| `systemStatus` | mesh-section |

Mancano ancora per raggiungere 17+: `mn-gantt`, `FacetWorkbench`,
`tokenMeter`, `approvalChain`, `mn-chart` (sparkline), `socialGraph`,
`mn-header-shell` (WC), `mn-theme-toggle` (WC).
