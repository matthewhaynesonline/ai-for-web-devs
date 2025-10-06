use chrono::{DateTime, Utc};
use sea_orm::{entity::prelude::*, QueryOrder, Set};
use sea_orm_utils::{
    apply_uuid_and_timestamps, impl_has_uuid_and_timestamps, impl_related_to, impl_related_to_via,
};
use serde::Serialize;
use utoipa::{schema, ToSchema};

use crate::errors::DatabaseError;

// TODO: DRY with proc macro?
// Since SeaOrm requires that structs be named "Model" duplicate it
// for use with Utoipa api docs (multiple stucts named "Model" doesn't)
// work. This and the "Model" struct are duplicates, just one is for
// Utoipa and one is for SeaOrm.
#[derive(Serialize, ToSchema)]
#[schema(title = "User")]
pub struct UserSchema {
    pub id: i32,
    #[schema(value_type = String, format = "uuid")]
    pub uuid: String,
    pub username: String,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub created_at: DateTime<Utc>,
    #[schema(value_type = String, format = "date-time", example = "2025-03-29T12:34:56Z")]
    pub updated_at: DateTime<Utc>,
}

#[derive(Clone, Debug, PartialEq, DeriveEntityModel, Serialize, ToSchema)]
#[sea_orm(table_name = "user")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    #[schema(value_type = String, format = "uuid")]
    pub uuid: String,
    pub username: String,

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
impl_related_to_via!(User, chats_users, chat, Chat);

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
    /// Find first user (useful for single-user scenarios)
    pub async fn find_first<C>(db: &C) -> Result<Self, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let user = Entity::find().order_by_asc(Column::Id).one(db).await?;

        user.ok_or(DatabaseError::UserNotFound)
    }

    /// Get default/first chat for this user
    pub async fn get_default_chat<C>(&self, db: &C) -> Result<crate::chat::Model, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let chat = self
            .find_related(crate::chat::Entity)
            .order_by_asc(crate::chat::Column::CreatedAt)
            .one(db)
            .await?;

        chat.ok_or(DatabaseError::ChatNotFound)
    }

    /// Get specific chat by UUID for this user
    pub async fn get_chat_by_uuid<C>(
        &self,
        db: &C,
        chat_uuid: &Uuid,
    ) -> Result<crate::chat::Model, DatabaseError>
    where
        C: ConnectionTrait,
    {
        let chat = self
            .find_related(crate::chat::Entity)
            .filter(crate::chat::Column::Uuid.eq(chat_uuid.to_string()))
            .one(db)
            .await?;

        chat.ok_or(DatabaseError::ChatNotFound)
    }
}
