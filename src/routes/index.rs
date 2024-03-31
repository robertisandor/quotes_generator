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

// #[cfg(test)]
// mod tests {
//     use rocket::local::Client;
//     use rocket::http::Status;
//     use crate::rocket_builder;

//     #[test]
//     fn test_get_index() {
//         let client = Client::new(rocket_builder()).expect("Valid Rocket instance");
//         let mut response = client.get("/api/").dispatch();
//         assert_eq!(response.status(), Status::Ok);
//         assert_eq!(response.body_string(), Some(r#""{\"status\": \"good\"}""#.into()));
//     }
// }
