use std::{collections::HashMap, sync::LazyLock};

use askama::Template;
use axum::{
    extract::{Request, State},
    http::StatusCode,
    middleware::Next,
    response::{Html, IntoResponse, Response},
};

use crate::{AppState, ExtractedAppState, templates::PageTemplate};

static ERROR_MAP: LazyLock<HashMap<StatusCode, (&'static str, &'static str)>> =
    LazyLock::new(|| {
        HashMap::from([
            (
                StatusCode::BAD_REQUEST,
                ("Bad Request", "The request was invalid or malformed."),
            ),
            (
                StatusCode::UNAUTHORIZED,
                (
                    "Unauthorized",
                    "You must be logged in to access this resource.",
                ),
            ),
            (
                StatusCode::FORBIDDEN,
                (
                    "Forbidden",
                    "You don't have permission to access this resource.",
                ),
            ),
            (
                StatusCode::NOT_FOUND,
                ("Not Found", "The requested URL was not found."),
            ),
            (
                StatusCode::METHOD_NOT_ALLOWED,
                (
                    "Method Not Allowed",
                    "The requested method is not allowed for this resource.",
                ),
            ),
            (
                StatusCode::UNPROCESSABLE_ENTITY,
                (
                    "Validation Error",
                    "The submitted data could not be processed due to validation errors.",
                ),
            ),
            (
                StatusCode::TOO_MANY_REQUESTS,
                (
                    "Too Many Requests",
                    "You've made too many requests. Please try again later.",
                ),
            ),
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                (
                    "Error",
                    "We're sorry, there was an error. Please try again later.",
                ),
            ),
            (
                StatusCode::SERVICE_UNAVAILABLE,
                (
                    "Service Unavailable",
                    "The service is temporarily unavailable. Please try again later.",
                ),
            ),
        ])
    });

pub(crate) async fn handle_errors(
    State(state): ExtractedAppState,
    request: Request,
    next: Next,
) -> Response {
    let response = next.run(request).await;

    if let Some((title, message)) = ERROR_MAP.get(&response.status()) {
        handle_error_with_template(&state, response.status(), title, message).into_response()
    } else {
        response
    }
}

pub(crate) async fn handle_fallback(State(state): ExtractedAppState) -> impl IntoResponse {
    let status = StatusCode::NOT_FOUND;
    let (title, message) = ERROR_MAP
        .get(&status)
        .unwrap_or(&("Not Found", "The requested URL was not found."));

    handle_error_with_template(&state, status, title, message)
}

fn handle_error_with_template(
    state: &AppState,
    status: StatusCode,
    title: &str,
    message: &str,
) -> impl IntoResponse + use<> {
    let template = PageTemplate {
        title: title.to_string(),
        content: Some(message.to_string()),
        username: Some(state.current_user.username.clone()),
    };

    (status, Html(template.render().unwrap()))
}
