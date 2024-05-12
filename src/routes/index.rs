use tracing::{event, Level};
use axum::{
    Json,
    http::header::HeaderMap,
};

pub async fn index(headers: HeaderMap) -> Json<&'static str> {
    event!(Level::INFO, host = headers.get("host").unwrap().to_str().unwrap() 
                      , user_agent = headers.get("user-agent").unwrap().to_str().unwrap()
                      , accept = headers.get("accept").unwrap().to_str().unwrap()
                      , accept_language = headers.get("accept-language").unwrap().to_str().unwrap()
                      , accept_encoding = headers.get("accept-encoding").unwrap().to_str().unwrap()
                      , upgrade_insecure_requests = headers.get("upgrade-insecure-requests").unwrap().to_str().unwrap());
    Json(r#"{"status": "good"}"#)
}

#[cfg(test)]
mod tests {
    use crate::app;
    use axum::{
        body::Body,
        http::{Request, StatusCode},
    };
    use http_body_util::BodyExt; 
    use tower::ServiceExt; 

    #[tokio::test]
    async fn test_get_index() {
        let app = app();

        let response = app
            .oneshot(Request::builder().uri("/").body(Body::empty()).unwrap())
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        let body = response.into_body().collect().await.unwrap().to_bytes();
        assert_eq!(&body[..], b"\"{\\\"status\\\": \\\"good\\\"}\"");
    }
}