use log::info;
use axum::Json;

// pub async fn index(user_agent: UserAgent) -> Json<&'static str> {
pub async fn index() -> Json<&'static str> {
    // info!("{}", format!("user agent is: {0}", user_agent.value));
    info!("Got pinged at /api/");
    Json(r#"{"status": "good"}"#)
}

// struct UserAgent {
//     value: String
// }

// impl std::fmt::Display for UserAgent {
//     fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
//         write!(f, "(value: {})", self.value)
//     }
// }

// #[derive(Debug)]
// enum UserAgentError {
//     Missing
// }

// impl<'a, 'r> FromRequest<'a, 'r> for UserAgent {
//     type Error = UserAgentError;

//     fn from_request(request: &'a Request<'r>) -> request::Outcome<Self, Self::Error> {
//         let user_agent = request.headers().get_one("User-Agent");
//         match user_agent {
//             Some(user_agent) => {
//                 // check validity
//                 Outcome::Success(UserAgent {value: user_agent.to_string()})
//             }
//             None => Outcome::Failure((Status::NoContent, UserAgentError::Missing)),
//         }
//     }
// }

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