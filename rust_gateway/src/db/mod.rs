pub mod crypto;
pub mod repo;
pub mod schema;

use sqlx::{
    postgres::{PgConnectOptions, PgPoolOptions},
    sqlite::{SqliteConnectOptions, SqliteJournalMode, SqlitePoolOptions, SqliteSynchronous},
    Pool, Postgres, Sqlite,
};
use std::str::FromStr;
use std::time::Duration;

#[derive(Clone, Debug)]
pub enum DbPool {
    Sqlite(Pool<Sqlite>),
    Postgres(Pool<Postgres>),
}

impl DbPool {
    /// Create and connect to a database pool dynamically inferred from `DATABASE_URL`.
    /// Supports SQLite (file-based or `:memory:`) and PostgreSQL.
    pub async fn new(database_url: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        if is_sqlite_url(database_url) {
            let options = parse_sqlite_options(database_url)?;
            
            let pool = SqlitePoolOptions::new()
                .max_connections(32)
                .min_connections(1)
                .idle_timeout(Duration::from_secs(300))
                .max_lifetime(Duration::from_secs(1800))
                .connect_with(options)
                .await?;

            // Execute high-performance SQLite PRAGMAs
            sqlx::query("PRAGMA journal_mode = WAL;").execute(&pool).await?;
            sqlx::query("PRAGMA synchronous = NORMAL;").execute(&pool).await?;
            sqlx::query("PRAGMA cache_size = -64000;").execute(&pool).await?; // 64MB memory page cache
            sqlx::query("PRAGMA temp_store = MEMORY;").execute(&pool).await?;
            sqlx::query("PRAGMA mmap_size = 536870912;").execute(&pool).await?; // 512MB MMAP
            sqlx::query("PRAGMA busy_timeout = 5000;").execute(&pool).await?;
            sqlx::query("PRAGMA foreign_keys = ON;").execute(&pool).await?;

            let db_pool = DbPool::Sqlite(pool);
            schema::init_schema(&db_pool).await?;
            Ok(db_pool)
        } else {
            let mut pg_url = database_url.to_string();
            if pg_url.starts_with("postgres://") {
                pg_url = pg_url.replacen("postgres://", "postgresql://", 1);
            }
            pg_url = pg_url
                .replace("&channel_binding=require", "")
                .replace("?channel_binding=require", "");

            let pool = PgPoolOptions::new()
                .max_connections(32)
                .min_connections(2)
                .acquire_timeout(Duration::from_secs(10))
                .idle_timeout(Duration::from_secs(300))
                .max_lifetime(Duration::from_secs(1800))
                .connect(&pg_url)
                .await?;

            let db_pool = DbPool::Postgres(pool);
            schema::init_schema(&db_pool).await?;
            Ok(db_pool)
        }
    }

    /// Create a lazy database pool without blocking on connection check.
    pub fn connect_lazy(database_url: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        if is_sqlite_url(database_url) {
            let options = parse_sqlite_options(database_url)?;
            let pool = SqlitePoolOptions::new()
                .max_connections(32)
                .min_connections(1)
                .idle_timeout(Duration::from_secs(300))
                .connect_lazy_with(options);
            Ok(DbPool::Sqlite(pool))
        } else {
            let mut pg_url = database_url.to_string();
            if pg_url.starts_with("postgres://") {
                pg_url = pg_url.replacen("postgres://", "postgresql://", 1);
            }
            let options = PgConnectOptions::from_str(&pg_url)?;
            let pool = PgPoolOptions::new()
                .max_connections(32)
                .min_connections(2)
                .idle_timeout(Duration::from_secs(300))
                .connect_lazy_with(options);
            Ok(DbPool::Postgres(pool))
        }
    }

    /// Return total active + idle connections in pool
    pub fn size(&self) -> u32 {
        match self {
            DbPool::Sqlite(p) => p.size(),
            DbPool::Postgres(p) => p.size(),
        }
    }

    pub fn is_sqlite(&self) -> bool {
        matches!(self, DbPool::Sqlite(_))
    }

    pub fn is_postgres(&self) -> bool {
        matches!(self, DbPool::Postgres(_))
    }

    pub fn as_sqlite(&self) -> Option<&Pool<Sqlite>> {
        match self {
            DbPool::Sqlite(p) => Some(p),
            _ => None,
        }
    }

    pub fn as_postgres(&self) -> Option<&Pool<Postgres>> {
        match self {
            DbPool::Postgres(p) => Some(p),
            _ => None,
        }
    }

    /// Close the pool connections
    pub async fn close(&self) {
        match self {
            DbPool::Sqlite(p) => p.close().await,
            DbPool::Postgres(p) => p.close().await,
        }
    }
}

fn is_sqlite_url(url: &str) -> bool {
    let lower = url.to_lowercase();
    lower.starts_with("sqlite:") || lower.contains(".db") || lower == ":memory:" || lower.is_empty()
}

fn parse_sqlite_options(url: &str) -> Result<SqliteConnectOptions, Box<dyn std::error::Error + Send + Sync>> {
    let clean = url
        .trim_start_matches("sqlite:///")
        .trim_start_matches("sqlite://")
        .trim_start_matches("sqlite:");

    let options = if clean == ":memory:" || clean.is_empty() {
        SqliteConnectOptions::from_str("sqlite::memory:")?
            .journal_mode(SqliteJournalMode::Wal)
            .synchronous(SqliteSynchronous::Normal)
            .busy_timeout(Duration::from_secs(5))
            .foreign_keys(true)
    } else {
        SqliteConnectOptions::new()
            .filename(clean)
            .create_if_missing(true)
            .journal_mode(SqliteJournalMode::Wal)
            .synchronous(SqliteSynchronous::Normal)
            .busy_timeout(Duration::from_secs(5))
            .foreign_keys(true)
    };

    Ok(options)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_sqlite_in_memory_pool_and_schema_init() {
        let pool = DbPool::new("sqlite::memory:").await.expect("Failed to create SQLite in-memory pool");
        assert!(pool.is_sqlite());

        // Verify that tables were created
        let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
            .fetch_one(pool.as_sqlite().unwrap())
            .await
            .expect("Failed to query users table");
        assert_eq!(count.0, 0);

        let fac_count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM hospital_facilities")
            .fetch_one(pool.as_sqlite().unwrap())
            .await
            .expect("Failed to query hospital_facilities table");
        assert_eq!(fac_count.0, 0);
    }
}
