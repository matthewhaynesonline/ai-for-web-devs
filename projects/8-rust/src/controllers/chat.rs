use axum::response::IntoResponse;

use crate::templates::{HtmlTemplateRenderer, PageTemplate};

#[utoipa::path(
    get,
    path = "/",
    tag = "hello",
    responses(
        (status = 200, description = "Successful response with greeting message", body = String, content_type = "text/html; charset=utf-8")
    )
)]
pub(crate) async fn index() -> impl IntoResponse {
    let template = PageTemplate {
        title: String::from("Index"),
        content: Some(String::from("Hello world")),
    };

    HtmlTemplateRenderer(template)
}
