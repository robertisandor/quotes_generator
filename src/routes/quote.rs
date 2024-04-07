use axum::Json;
use diesel::{RunQueryDsl, sql_query, sql_types::Text};
use log::info;
use serde_json::json;

use crate::services::NewQuote;
use crate::services::establish_connection_pg;

pub async fn create_quote(quote: Json<NewQuote>) -> Json<String> {
    info!("Creating db connection for /api/quote");
    let connection = &mut establish_connection_pg();
    info!("Created db connection for /api/quote");
    
    sql_query(include_str!("../sql/create_quote.sql"))
        .bind::<Text, _>(quote.text.to_string())
        .bind::<Text, _>(quote.speaker.to_string())
        .execute(connection)
        .expect("Error saving new post");
    info!("Ran query for /api/quote");
    let status_string = json! ({"text": quote.text.to_string(),"speaker": quote.speaker.to_string(),"status":"Insertion successful"}).to_string();
    Json(status_string)
}