# Fase 30: Background mesh sync

Repo: /Users/Roberdan/GitHub/convergio
Branch: il tuo worktree ha già branch agent/w-mesh-sync.

## Cosa fare
1. Crea daemon/crates/convergio-mesh/src/sync_loop.rs (max 250 righe):
   - pub fn spawn_sync_loop(pool: ConnPool, interval: Duration)
   - tokio::spawn background task: ogni 30s, per ogni peer in peers_registry, chiama sync_table_with_peer()
   - Log: tabelle sincronizzate, righe, errori
2. Aggiungi sync_loop a lib.rs (pub mod sync_loop)
3. In ext.rs on_start(): chiama spawn_sync_loop(self.pool.clone(), Duration::from_secs(30))
4. cargo check --workspace && cargo test --workspace
5. git add, commit (conventional), push, gh pr create --base main

NON toccare file fuori dal tuo scope.