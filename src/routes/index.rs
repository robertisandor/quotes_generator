use log::info;
use rocket_contrib::json::Json;

#[get("/")]
pub fn index() -> Json<&'static str> {
    info!("Got pinged at /api/");
    Json(r#"{"status": "good"}"#)
}

#[cfg(test)]
mod tests {
    use rocket::local::Client;
    use rocket::http::Status;
    use crate::rocket_builder;

    #[test]
    fn test_get_index() {
        let client = Client::new(rocket_builder()).expect("Valid Rocket instance");
        let mut response = client.get("/api/").dispatch();
        assert_eq!(response.status(), Status::Ok);
        assert_eq!(response.body_string(), Some(r#""{\"status\": \"good\"}""#.into()));
    }
}
