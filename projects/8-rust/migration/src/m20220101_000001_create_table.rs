use sea_orm_migration::{prelude::*, schema::*, sea_orm::entity::*};
use sea_query::{ForeignKey, ForeignKeyAction, Index, Table};

#[derive(DeriveIden)]
enum User {
    Table,
    Id,
    Uuid,
    Username,
    CreatedAt,
    UpdatedAt,
}

#[derive(DeriveIden)]
enum Chat {
    Table,
    Id,
    Uuid,
    Title,
    CreatedAt,
    UpdatedAt,
}

#[derive(DeriveIden)]
enum ChatsUsers {
    Table,
    ChatId,
    UserId,
}

#[derive(DeriveIden)]
enum ChatMessage {
    Table,
    Id,
    Uuid,
    Title,
    Content,
    Role,
    State,
    ChatId,
    UserId,
    CreatedAt,
    UpdatedAt,
}

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        let _user_table = manager
            .create_table(
                Table::create()
                    .table(User::Table)
                    .if_not_exists()
                    .col(pk_auto(User::Id))
                    .col(string(User::Uuid).unique_key())
                    .col(string(User::Username).unique_key())
                    .col(timestamp(User::CreatedAt))
                    .col(timestamp(User::UpdatedAt))
                    .to_owned(),
            )
            .await;

        let _chat_table = manager
            .create_table(
                Table::create()
                    .table(Chat::Table)
                    .if_not_exists()
                    .col(pk_auto(Chat::Id))
                    .col(string(Chat::Uuid).unique_key())
                    .col(string(Chat::Title))
                    .col(timestamp(Chat::CreatedAt))
                    .col(timestamp(Chat::UpdatedAt))
                    .to_owned(),
            )
            .await;

        let _chats_users_table = manager
            .create_table(
                Table::create()
                    .table(ChatsUsers::Table)
                    .if_not_exists()
                    .col(integer(ChatsUsers::ChatId))
                    .col(integer(ChatsUsers::UserId))
                    .primary_key(
                        Index::create()
                            .name("pk-chats_users")
                            .col(entities::chats_users::Column::ChatId)
                            .col(entities::chats_users::Column::UserId),
                    )
                    .foreign_key(
                        ForeignKey::create()
                            .name("fk-chats_users-chat_id")
                            .from(
                                entities::chats_users::Entity,
                                entities::chats_users::Column::ChatId,
                            )
                            .to(entities::chat::Entity, entities::chat::Column::Id)
                            .on_delete(ForeignKeyAction::Cascade)
                            .on_update(ForeignKeyAction::Cascade),
                    )
                    .foreign_key(
                        ForeignKey::create()
                            .name("fk-chats_users-user_id")
                            .from(
                                entities::chats_users::Entity,
                                entities::chats_users::Column::UserId,
                            )
                            .to(entities::user::Entity, entities::user::Column::Id),
                    )
                    .to_owned(),
            )
            .await;

        let _chat_message_table = manager
            .create_table(
                Table::create()
                    .table(ChatMessage::Table)
                    .if_not_exists()
                    .col(pk_auto(ChatMessage::Id))
                    .col(string(ChatMessage::Uuid).unique_key())
                    .col(
                        sea_query::ColumnDef::new(ChatMessage::Title)
                            .string()
                            .null(),
                    )
                    .col(
                        sea_query::ColumnDef::new(ChatMessage::Content)
                            .string()
                            .null(),
                    )
                    .col(string(ChatMessage::Role))
                    .col(string(ChatMessage::State))
                    .col(integer(ChatMessage::ChatId))
                    .col(
                        sea_query::ColumnDef::new(ChatMessage::UserId)
                            .integer()
                            .null(),
                    )
                    .col(timestamp(ChatMessage::CreatedAt))
                    .col(timestamp(ChatMessage::UpdatedAt))
                    .foreign_key(
                        ForeignKey::create()
                            .name("fk-chat_message-chat_id")
                            .from(
                                entities::chat_message::Entity,
                                entities::chat_message::Column::ChatId,
                            )
                            .to(entities::chat::Entity, entities::chat::Column::Id)
                            .on_delete(ForeignKeyAction::Cascade)
                            .on_update(ForeignKeyAction::Cascade),
                    )
                    .foreign_key(
                        ForeignKey::create()
                            .name("fk-chat_message-user_id")
                            .from(
                                entities::chat_message::Entity,
                                entities::chat_message::Column::UserId,
                            )
                            .to(entities::user::Entity, entities::user::Column::Id)
                            .on_delete(ForeignKeyAction::Cascade)
                            .on_update(ForeignKeyAction::Cascade),
                    )
                    .to_owned(),
            )
            .await;

        let _ = manager
            .create_index(
                Index::create()
                    .name("idx_chat_message_chat_id")
                    .table(ChatMessage::Table)
                    .col(ChatMessage::ChatId)
                    .to_owned(),
            )
            .await;

        let _ = manager
            .create_index(
                Index::create()
                    .name("idx_chat_message_user_id")
                    .table(ChatMessage::Table)
                    .col(ChatMessage::UserId)
                    .to_owned(),
            )
            .await;

        let _ = manager
            .create_index(
                Index::create()
                    .name("idx_chat_message_role")
                    .table(ChatMessage::Table)
                    .col(ChatMessage::Role)
                    .to_owned(),
            )
            .await;

        let _ = manager
            .create_index(
                Index::create()
                    .name("idx_chat_message_state")
                    .table(ChatMessage::Table)
                    .col(ChatMessage::State)
                    .to_owned(),
            )
            .await;

        let db = manager.get_connection();

        seed(db).await?;

        Ok(())
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        let _ = manager
            .drop_table(Table::drop().table(ChatMessage::Table).to_owned())
            .await;

        let _ = manager
            .drop_table(Table::drop().table(ChatsUsers::Table).to_owned())
            .await;

        let _ = manager
            .drop_table(Table::drop().table(User::Table).to_owned())
            .await;

        let _ = manager
            .drop_table(Table::drop().table(Chat::Table).to_owned())
            .await;

        Ok(())
    }
}

async fn seed(db: &SchemaManagerConnection<'_>) -> Result<(), DbErr> {
    let user = entities::user::ActiveModel {
        username: Set("test_user".to_owned()),
        ..Default::default()
    }
    .insert(db)
    .await?;

    let chat = entities::chat::ActiveModel {
        title: Set("test_chat".to_owned()),
        ..Default::default()
    }
    .insert(db)
    .await?;

    entities::chats_users::ActiveModel {
        user_id: Set(user.id),
        chat_id: Set(chat.id),
        // ..Default::default()
    }
    .insert(db)
    .await?;

    Ok(())
}
