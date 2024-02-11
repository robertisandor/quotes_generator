#![feature(decl_macro)]
#[macro_use] extern crate rocket;

use rocket::Request;
mod models;
use self::models::Quote;
mod services;
use crate::services::establish_connection_pg;
use crate::services::NewQuote;
mod schema;
use rocket_contrib::json::Json;
use diesel::RunQueryDsl;
use diesel::sql_query;
use serde_json::json;

#[get("/")]
fn index() -> Json<&'static str> {
    Json(r#"{"status": "good"}"#)
}

#[post("/quote", format = "json", data = "<quote>")]
pub fn create_quote(quote: Json<NewQuote>) -> Json<String> {
    let connection = &mut establish_connection_pg();
    let query_string = format! (r#"
        INSERT INTO quotes
            (text, speaker)
        VALUES
            ('{}', '{}');
    "#, quote.text.to_string(), quote.speaker.to_string());
    sql_query(query_string)
        .execute(connection)
        .expect("Error saving new post");
    let status_string = json! ({"text": quote.text.to_string(),"speaker": quote.speaker.to_string(),"status":"Insertion successful"}).to_string();
    Json(status_string)
}

#[get("/all")]
pub fn list() -> Json<Vec<Quote>> {
    let connection = &mut establish_connection_pg();
    let query_string = "
        SELECT
            quote_id
            , text
            , speaker
        FROM
            quotes
        ORDER BY quote_id DESC;
        ";
    let results = sql_query(query_string)
        .load::<Quote>(connection)
        .expect("Error loading quotes");
    Json(results)
}

#[catch(404)]
fn not_found(req: &Request) -> String {
    format!("Oh no! We couldn't find the requested path '{}'", req.uri())
}

fn main() {
    rocket::ignite()
        .register(catchers![not_found])
        .mount("/api", routes![index, create_quote, list])
        .launch();
}
