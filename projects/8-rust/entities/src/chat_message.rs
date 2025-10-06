use std::fmt;

use chrono::{DateTime, Utc};
use sea_orm::{entity::prelude::*, Set};
use sea_orm_utils::{apply_uuid_and_timestamps, impl_has_uuid_and_timestamps, impl_related_to};
use serde::Serialize;
use serde_json::{json, Value as JsonValue};
use utoipa::{schema, ToSchema};

use crate::errors::DatabaseError;

#[derive(Debug, Clone, PartialEq, Eq, EnumIter, DeriveActiveEnum, Serialize, ToSchema)]
#[sea_orm(rs_type = "String", db_type = "String(StringLen::N(10))")]
pub enum ChatMessageRole {
    #[sea_orm(string_value = "Assistant")]
    Assistant,
    #[sea_orm(string_value = "System")]
    System,
    #[sea_orm(string_value = "User")]
    User,
}

impl fmt::Display for ChatMessageRole {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ChatMessageRole::Assistant => write!(f, "Assistant"),
            ChatMessageRole::System => write!(f, "System"),
            ChatMessageRole::User => write!(f, "User"),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, EnumIter, DeriveActiveEnum, Serialize, ToSchema)]
#[sea_orm(rs_type = "String", db_type = "String(StringLen::N(10))")]
pub enum ChatMessageState {
    #[sea_orm(string_value = "Pending")]
    Pending,
    #[sea_orm(string_value = "Loading")]
    Loading,
    #[sea_orm(string_value = "Ready")]
    Ready,
    #[sea_orm(string_value = "Error")]
    Error,
}

impl fmt::Display for ChatMessageState {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ChatMessageState::Pending => write!(f, "Pending"),
            ChatMessageState::Loading => write!(f, "Loading"),
            ChatMessageState::Ready => write!(f, "Ready"),
            ChatMessageState::Error => write!(f, "Error"),
        }
    }
}

// TODO: DRY with proc macro?
// Since SeaOrm requires that structs be named "Model" duplicate it
// for use with Utoipa api docs (multiple stucts named "Model" doesn't)
// work. This and the "Model" struct are duplicates, just one is for
// Utoipa and one is for SeaOrm.
#[derive(Serialize, ToSchema)]
#[schema(title = "ChatMessage")]
pub struct ChatMessageSchema {
    pub id: i32,
    #[schema(value_type = String, format = "uuid")]
    pub uuid: String,
    pub title: Option<String>,
    pub content: Option<String>,
    pub role: ChatMessageRole,
    pub state: ChatMessageState,
    pub chat_id: i32,
    pub user_id: Option<i32>,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub created_at: DateTime<Utc>,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub updated_at: DateTime<Utc>,
}

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, ToSchema)]
#[sea_orm(table_name = "chat_message")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    #[schema(value_type = String, format = "uuid")]
    pub uuid: String,
    pub title: Option<String>,
    pub content: Option<String>,
    pub role: ChatMessageRole,
    pub state: ChatMessageState,
    pub chat_id: i32,
    pub user_id: Option<i32>,

    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    #[sea_orm(column_type = "DateTime")]
    pub created_at: DateTime<Utc>,

    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    #[sea_orm(column_type = "DateTime")]
    pub updated_at: DateTime<Utc>,
}

impl_has_uuid_and_timestamps!(ActiveModel);

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(
        belongs_to = "super::chat::Entity",
        from = "Column::ChatId",
        to = "super::chat::Column::Id"
        on_update = "Cascade",
        on_delete = "Cascade"
    )]
    Chat,
    #[sea_orm(
        belongs_to = "super::user::Entity",
        from = "Column::UserId",
        to = "super::user::Column::Id",
        on_update = "Cascade",
        on_delete = "Cascade"
    )]
    User,
}
impl_related_to!(chat, Chat);
impl_related_to!(user, User);

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(self, db: &C, insert: bool) -> Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        apply_uuid_and_timestamps(self, db, insert).await
    }
}

impl Model {
    pub fn to_json(&self) -> Result<JsonValue, DatabaseError> {
        let message_json = json!({
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "content": self.content,
            "role": self.role,
            "state": self.state,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,

        });

        Ok(message_json)
    }
}
