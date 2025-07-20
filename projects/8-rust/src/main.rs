use std::sync::Arc;

use anyhow::Result;
use axum::{Router, extract::State, routing::get};
use clap::Parser;
use sea_orm::DatabaseConnection;
use tower_http::{
    services::ServeDir,
    trace::{self, TraceLayer},
};
use tracing::{Level, info};
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

use entities::{
    chat::ChatSchema,
    chat_message::ChatMessageSchema,
    user::{self, Model as UserModel, UserSchema},
};

mod app;
use app::{init_listener, init_logging, open_db_connection, shutdown_signal};

mod controllers;
use controllers::{
    chat::{chat_show, index},
    errors::{handle_errors, handle_fallback},
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

    // Need mode=rwc
    // https://github.com/launchbadge/sqlx/issues/3099#issuecomment-2556452267
    /// Database URL connection string
    #[arg(long, default_value_t = String::from("sqlite://app.db?mode=rwc"))]
    datebase_url: String,
}

#[derive(OpenApi)]
#[openapi(
    paths(controllers::chat::chat_show),
    components(schemas(ChatSchema, UserSchema, ChatMessageSchema)),
    info(title = "Hello Rust", version = "1.0.0", description = "A simple app")
)]
struct ApiDoc;

#[derive(Clone)]
pub(crate) struct AppState {
    pub(crate) db: DatabaseConnection,
    pub(crate) current_user: user::Model,
}

pub(crate) type SharedAppState = Arc<AppState>;
pub(crate) type ExtractedAppState = State<SharedAppState>;

#[tokio::main]
async fn main() -> Result<()> {
    init_logging();

    let args = Args::parse();
    let db = open_db_connection(&args.datebase_url).await;
    let router = init_router(db).await;
    let address = format!("{}:{}", &args.ip, args.port);
    let listener = init_listener(&address).await?;

    info!("Starting HTTP server: {address}");
    axum::serve(listener, router)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    Ok(())
}

async fn init_router(db: DatabaseConnection) -> Router {
    let current_user = UserModel::find_first(&db)
        .await
        .expect("Couldn't load user!");

    let state = Arc::new(AppState { db, current_user });

    let api_docs = ApiDoc::openapi();

    Router::new()
        .route("/", get(index))
        .nest(
            "/chats",
            Router::new()
                .route("/", get(index))
                .route("/{uuid}", get(chat_show)),
        )
        .merge(SwaggerUi::new("/api-docs").url("/api-docs/openapi.json", api_docs))
        .nest_service("/static", ServeDir::new("static"))
        .layer(axum::middleware::from_fn_with_state(
            state.clone(),
            handle_errors,
        ))
        .fallback(handle_fallback)
        .with_state(state)
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(trace::DefaultMakeSpan::new().level(Level::INFO))
                .on_response(trace::DefaultOnResponse::new().level(Level::INFO)),
        )
}
