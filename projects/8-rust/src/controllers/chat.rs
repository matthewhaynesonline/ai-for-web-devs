use axum::{extract::Path, response::Redirect};
use uuid::Uuid;

use entities::errors::AppError;

use crate::{
    ExtractedAppState,
    templates::{HtmlTemplateRenderer, PageTemplate},
};

pub(crate) async fn index(state: ExtractedAppState) -> Result<Redirect, AppError> {
    let chat = state.current_user.get_default_chat(&state.db).await?;

    Ok(Redirect::temporary(&format!("/chats/{}", chat.uuid)))
}

#[utoipa::path(
    get,
    path = "/chat/{chat_uuid}",
    params(
        ("chat_uuid" = String, Path, description = "UUID of the chat.")
    ),
    tag = "Chat",
    responses(
        (status = 200, description = "Chat index", body = String, content_type = "text/html; charset=utf-8")
    )
)]
pub(crate) async fn chat_show(
    state: ExtractedAppState,
    Path(_chat_uuid): Path<Uuid>,
) -> Result<HtmlTemplateRenderer<PageTemplate>, AppError> {
    let template = PageTemplate {
        title: String::from("Chat"),
        content: Some(String::from("Hello chat")),
        username: Some(state.current_user.username.clone()),
    };

    Ok(HtmlTemplateRenderer(template))
}
