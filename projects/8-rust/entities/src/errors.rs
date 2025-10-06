use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};

#[derive(Debug, thiserror::Error)]
pub enum DatabaseError {
    #[error("User not found")]
    UserNotFound,
    #[error("Chat not found")]
    ChatNotFound,
    #[error("Database error: {0}")]
    Database(#[from] sea_orm::DbErr),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
}

#[derive(Debug)]
pub struct AppError {
    pub status: StatusCode,
    pub message: String,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        (self.status, self.message).into_response()
    }
}

impl From<DatabaseError> for AppError {
    fn from(err: DatabaseError) -> Self {
        match err {
            DatabaseError::UserNotFound => AppError {
                status: StatusCode::NOT_FOUND,
                message: "User not found".to_string(),
            },
            DatabaseError::ChatNotFound => AppError {
                status: StatusCode::NOT_FOUND,
                message: "Chat not found".to_string(),
            },
            DatabaseError::Database(_) => AppError {
                status: StatusCode::INTERNAL_SERVER_ERROR,
                message: "Database error".to_string(),
            },
            DatabaseError::Serialization(_) => AppError {
                status: StatusCode::INTERNAL_SERVER_ERROR,
                message: "Serialization error".to_string(),
            },
        }
    }
}
