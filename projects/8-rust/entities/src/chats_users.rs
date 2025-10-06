use sea_orm::entity::prelude::*;

use sea_orm_utils::impl_related_to;

#[derive(Clone, Debug, PartialEq, Eq, DeriveEntityModel)]
#[sea_orm(table_name = "chats_users")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub chat_id: i32,
    #[sea_orm(primary_key)]
    pub user_id: i32,
}

#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {
    #[sea_orm(
        belongs_to = "super::chat::Entity",
        from = "Column::ChatId",
        to = "super::chat::Column::Id",
        on_update = "Cascade",
        on_delete = "Cascade"
    )]
    Chat,
    #[sea_orm(
        belongs_to = "super::user::Entity",
        from = "Column::UserId",
        to = "super::user::Column::Id"
        on_update = "Cascade",
        on_delete = "Cascade"
    )]
    User,
}
impl_related_to!(chat, Chat);
impl_related_to!(user, User);

impl ActiveModelBehavior for ActiveModel {}
