use diesel::RunQueryDsl;
use diesel::sql_query;
use log::info;
use rocket_contrib::json::Json;
use serde_json::json;

use crate::services::NewQuote;
use crate::services::establish_connection_pg;

#[post("/quote", format = "json", data = "<quote>")]
pub fn create_quote(quote: Json<NewQuote>) -> Json<String> {
    info!("Creating db connection for /api/quote");
    let connection = &mut establish_connection_pg();
    info!("Created db connection for /api/quote");
    let query_string = format! (r#"
        INSERT INTO quotes
            (text, speaker)
        VALUES
            ('{}', '{}');
    "#, quote.text.to_string(), quote.speaker.to_string());
    sql_query(query_string)
        .execute(connection)
        .expect("Error saving new post");
    info!("Ran query for /api/quote");
    let status_string = json! ({"text": quote.text.to_string(),"speaker": quote.speaker.to_string(),"status":"Insertion successful"}).to_string();
    Json(status_string)
}