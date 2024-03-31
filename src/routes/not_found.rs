use axum::{
    http::{StatusCode, Uri},
};

pub async fn not_found(uri: Uri) -> (StatusCode, String) {
    (StatusCode::NOT_FOUND, format!("No route for {uri}"))
}