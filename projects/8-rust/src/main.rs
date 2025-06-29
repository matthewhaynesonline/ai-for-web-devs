use anyhow::{Context, Result};
use axum::{Router, routing::get};
use clap::Parser;
use tokio::signal;
use tower_http::services::ServeDir;
use tracing::info;
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

mod controllers;
use controllers::{
    chat::index,
    errors::{handle_404, handle_errors},
};

mod templates;

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Args {
    /// IP to serve on.
    #[arg(long, default_value_t = String::from("0.0.0.0"))]
    ip: String,

    /// Port to serve on.
    #[arg(short, long, default_value_t = 3000)]
    port: u16,
}

#[derive(OpenApi)]
#[openapi(
    paths(controllers::chat::index),
    tags(
        (name = "hello", description = "Hello world endpoints")
    ),
    info(
        title = "Hello World API",
        version = "1.0.0",
        description = "A simple API that responds with a greeting"
    )
)]
struct ApiDoc;

#[tokio::main]
async fn main() -> Result<()> {
    init_logging();

    let args = Args::parse();
    let api_docs = ApiDoc::openapi();

    let app = Router::new()
        .route("/", get(index))
        .merge(SwaggerUi::new("/api-docs").url("/api-docs/openapi.json", api_docs))
        .nest_service("/static", ServeDir::new("static"))
        .layer(axum::middleware::from_fn(handle_errors))
        .fallback(handle_404);

    let address = format!("{}:{}", args.ip, args.port);
    let listener = tokio::net::TcpListener::bind(&address)
        .await
        .context(format!("Could not bind TCP Listener on {address}"))?;

    info!("Starting HTTP server: {address}");
    info!("Ready");

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

/// Init logging
fn init_logging() {
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();
}

/// Shutdown signal handler
async fn shutdown_signal() {
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
