//! Lightweight error wrapper for user-facing messages.

#[derive(Debug, Clone, thiserror::Error)]
#[error("{0}")]
pub struct MessageError(pub String);

pub type MessageResult<T> = Result<T, MessageError>;

impl From<String> for MessageError {
    fn from(value: String) -> Self {
        Self(value)
    }
}

impl From<&str> for MessageError {
    fn from(value: &str) -> Self {
        Self(value.to_string())
    }
}

macro_rules! impl_message_error_from {
    ($($ty:ty),* $(,)?) => {
        $(
            impl From<$ty> for MessageError {
                fn from(value: $ty) -> Self {
                    Self(value.to_string())
                }
            }
        )*
    };
}

impl_message_error_from!(std::io::Error, std::net::AddrParseError, serde_json::Error,);
