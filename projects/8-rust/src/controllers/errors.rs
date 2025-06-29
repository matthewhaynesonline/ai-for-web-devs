use askama::Template;
use axum::{
    extract::Request,
    http::StatusCode,
    middleware::Next,
    response::{Html, IntoResponse, Response},
};

use crate::templates::PageTemplate;

pub(crate) async fn handle_errors(request: Request, next: Next) -> Response {
    let response = next.run(request).await;

    match response.status() {
        StatusCode::INTERNAL_SERVER_ERROR => handle_500().await.into_response(),
        _ => response,
    }
}

pub(crate) async fn handle_500() -> impl IntoResponse {
    let template = PageTemplate {
        title: String::from("Error"),
        content: Some(String::from(
            "We're sorry, there was an error. Please try again later.",
        )),
    };

    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Html(template.render().unwrap()),
    )
}

pub(crate) async fn handle_404() -> impl IntoResponse {
    let template = PageTemplate {
        title: String::from("Not Found"),
        content: Some(String::from("The requested URL was not found.")),
    };

    (StatusCode::NOT_FOUND, Html(template.render().unwrap()))
}
