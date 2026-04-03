//! SQLite connection pool with r2d2 and optimal PRAGMAs.

use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use std::path::Path;

/// Type alias for the connection pool.
pub type ConnPool = Pool<SqliteConnectionManager>;

/// Type alias for a pooled connection.
pub type PooledConn = r2d2::PooledConnection<SqliteConnectionManager>;

/// Standard PRAGMAs applied to every connection.
const PRAGMAS: &str = "\
    PRAGMA journal_mode=WAL;\
    PRAGMA synchronous=FULL;\
    PRAGMA busy_timeout=5000;\
    PRAGMA cache_size=-8000;\
    PRAGMA mmap_size=67108864;\
    PRAGMA temp_store=MEMORY;\
";

/// Create a connection pool for the given database path.
pub fn create_pool(db_path: &Path) -> Result<ConnPool, r2d2::Error> {
    let manager = SqliteConnectionManager::file(db_path).with_init(|conn| {
        conn.execute_batch(PRAGMAS)
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))
    });
    Pool::builder().max_size(8).min_idle(Some(2)).build(manager)
}

/// Create an in-memory pool (for testing).
pub fn create_memory_pool() -> Result<ConnPool, r2d2::Error> {
    let manager = SqliteConnectionManager::memory().with_init(|conn| {
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;")
            .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))
    });
    Pool::builder().max_size(1).build(manager)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn memory_pool_works() {
        let pool = create_memory_pool().expect("pool creation");
        let conn = pool.get().expect("get connection");
        conn.execute_batch("CREATE TABLE test_pool (id INTEGER PRIMARY KEY)")
            .expect("create table");
    }
}
