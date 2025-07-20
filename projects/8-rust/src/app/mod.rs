use anyhow::{Context, Result};
use sea_orm::{Database, DatabaseConnection};
use tokio::{net::TcpListener, signal};

use migration::{Migrator, MigratorTrait};

pub(crate) fn init_logging() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

pub(crate) async fn open_db_connection(db_url: &String) -> DatabaseConnection {
    let db = Database::connect(db_url)
        .await
        .expect("Database connection failed");

    Migrator::up(&db, None).await.unwrap();

    db
}

pub(crate) async fn init_listener(address: &str) -> Result<TcpListener> {
    tokio::net::TcpListener::bind(address)
        .await
        .context(format!("Could not bind TCP Listener on {address}"))
}

/// <https://github.com/tokio-rs/axum/blob/main/examples/tls-graceful-shutdown/src/main.rs>
pub(crate) async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    tracing::info!("signal received, starting graceful shutdown");
}
