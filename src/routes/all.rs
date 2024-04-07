use axum::Json;
use diesel::RunQueryDsl;
use diesel::sql_query;
use log::info;

use crate::models::Quote;
use crate::services::establish_connection_pg;

pub async fn list() -> Json<Vec<Quote>> {
    info!("Creating db connection for /api/all");
    let connection = &mut establish_connection_pg();
    info!("Created db connection for /api/all");
    let results = sql_query(include_str!("../sql/list_quotes.sql"))
        .load::<Quote>(connection)
        .expect("Error loading quotes");
    info!("Ran query for /api/all");
    Json(results)
}