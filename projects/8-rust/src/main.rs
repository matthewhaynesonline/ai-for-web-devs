use anyhow::{Context, Result};
use axum::{Router, routing::get};
use tracing::info;

#[tokio::main]
async fn main() -> Result<()> {
    init_logging();

    let app = Router::new().route("/", get(root));

    let addr = "0.0.0.0:3000";
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .context(format!("Could not bind TCP Listener on {addr}"))?;

    info!("Starting HTTP server: {}", &addr);
    info!("Ready");

    axum::serve(listener, app).await?;

    Ok(())
}

fn init_logging() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

async fn root() -> &'static str {
    "Hello, World!"
}
