use askama::Template;
use axum::{
    http::StatusCode,
    response::{Html, IntoResponse, Response},
};

#[derive(Template)]
#[template(path = "page.html.jinja")]
pub(crate) struct PageTemplate {
    pub(crate) title: String,
    pub(crate) content: Option<String>,
    pub(crate) username: Option<String>,
}

// https://github.com/tokio-rs/axum/blob/main/examples/templates/src/main.rs
pub(crate) struct HtmlTemplateRenderer<T>(pub(crate) T);

impl<T> IntoResponse for HtmlTemplateRenderer<T>
where
    T: Template,
{
    fn into_response(self) -> Response {
        match self.0.render() {
            Ok(html) => Html(html).into_response(),
            Err(err) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("Failed to render template. Error: {err}"),
            )
                .into_response(),
        }
    }
}
