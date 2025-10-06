use chrono::{DateTime, Utc};
use sea_orm::{entity::prelude::*, DeleteResult, Set};
use sea_orm_utils::{
    apply_uuid_and_timestamps, impl_has_uuid_and_timestamps, impl_related_to, impl_related_to_via,
};
use serde::Serialize;
use serde_json::{json, Value as JsonValue};
use utoipa::{schema, ToSchema};

use crate::errors::DatabaseError;

// TODO: DRY with proc macro?
// Since SeaOrm requires that structs be named "Model" duplicate it
// for use with Utoipa api docs (multiple stucts named "Model" doesn't)
// work. This and the "Model" struct are duplicates, just one is for
// Utoipa and one is for SeaOrm.
#[derive(Serialize, ToSchema)]
#[schema(title = "Chat")]
pub struct ChatSchema {
    pub id: i32,
    #[schema(value_type = String, format = "uuid")]
    pub uuid: String,
    pub title: String,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub created_at: DateTime<Utc>,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub updated_at: DateTime<Utc>,
}

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, ToSchema)]
#[sea_orm(table_name = "chat")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub uuid: String,
    pub title: String,

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
    #[sea_orm(has_many = "crate::chat_message::Entity")]
    ChatMessage,
}
impl_related_to!(chat_message, ChatMessage);
impl_related_to_via!(Chat, chats_users, user, User);

#[async_trait::async_trait]
impl ActiveModelBehavior for ActiveModel {
    async fn before_save<C>(self, db: &C, insert: bool) -> Result<Self, DbErr>
    where
        C: ConnectionTrait,
    {
        apply_uuid_and_timestamps(self, db, insert).await
    }
}

// Extension methods for Chat Model
impl Model {
    /// Find chat by ID
    pub async fn find<C>(db: &C, chat_id: i32) -> Result<Option<Self>, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let chat = Entity::find()
            .filter(Column::Id.eq(chat_id))
            .one(db)
            .await?;

        Ok(chat)
    }

    /// Find chat by ID, return error if not found
    pub async fn get<C>(db: &C, chat_id: i32) -> Result<Self, DatabaseError>
    where
        C: ConnectionTrait,
    {
        Self::find(db, chat_id)
            .await?
            .ok_or(DatabaseError::ChatNotFound)
    }

    /// Find chat by UUID
    pub async fn find_by_uuid<C>(db: &C, chat_uuid: &Uuid) -> Result<Option<Self>, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let chat = Entity::find()
            .filter(Column::Uuid.eq(chat_uuid.to_string()))
            .one(db)
            .await?;

        Ok(chat)
    }

    /// Find chat by UUID, return error if not found
    pub async fn get_by_uuid<C>(db: &C, chat_uuid: &Uuid) -> Result<Self, DatabaseError>
    where
        C: ConnectionTrait,
    {
        Self::find_by_uuid(db, chat_uuid)
            .await?
            .ok_or(DatabaseError::ChatNotFound)
    }

    /// Get all messages for this chat
    pub async fn get_messages<C>(
        &self,
        db: &C,
    ) -> Result<Vec<crate::chat_message::Model>, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let messages = self
            .find_related(crate::chat_message::Entity)
            .all(db)
            .await?;

        Ok(messages)
    }

    /// Convert chat to JSON including messages
    pub async fn to_json<C>(&self, db: &C) -> Result<JsonValue, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let chat_messages = self.get_messages(db).await?;

        let chat_messages_json: Result<Vec<JsonValue>, DatabaseError> = chat_messages
            .into_iter()
            .map(|chat_message| chat_message.to_json())
            .collect();

        let chat_messages_json = chat_messages_json?;

        let chat_json = json!({
            "title": self.title,
            "id": self.id,
            "uuid": self.uuid,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chat_messages": chat_messages_json,
        });

        Ok(chat_json)
    }

    /// Create a new chat message for this chat
    pub async fn create_chat_message<C>(
        &self,
        db: &C,
        content: &str,
        user_id: Option<i32>,
        state: Option<crate::chat_message::ChatMessageState>,
    ) -> Result<crate::chat_message::Model, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let mut chat_message = match user_id {
            Some(user_id) => crate::chat_message::ActiveModel {
                content: Set(Some(content.to_string())),
                chat_id: Set(self.id),
                state: Set(crate::chat_message::ChatMessageState::Ready),
                role: Set(crate::chat_message::ChatMessageRole::User),
                user_id: Set(Some(user_id)),
                ..Default::default()
            },
            None => crate::chat_message::ActiveModel {
                content: Set(Some(content.to_string())),
                chat_id: Set(self.id),
                state: Set(crate::chat_message::ChatMessageState::Ready),
                role: Set(crate::chat_message::ChatMessageRole::Assistant),
                ..Default::default()
            },
        };

        if let Some(actual_state) = state {
            chat_message.state = Set(actual_state);
        }

        let result = chat_message.insert(db).await?;
        Ok(result)
    }

    /// Delete all messages for this chat
    pub async fn delete_all_messages<C>(&self, db: &C) -> Result<DeleteResult, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let result = crate::chat_message::Entity::delete_many()
            .filter(crate::chat_message::Column::ChatId.eq(self.id))
            .exec(db)
            .await?;

        Ok(result)
    }
}
