use axum::Json;
use diesel::RunQueryDsl;
use diesel::sql_query;
use log::info;

use crate::models::Quote;
use crate::services::establish_connection_pg;

pub async fn random() -> Json<Quote> {
    info!("Creating db connection for /random");
    let connection = &mut establish_connection_pg();
    info!("Created db connection for /random");
    let result = sql_query(include_str!("../sql/get_random.sql"))
        .load::<Quote>(connection)
        .expect("Error loading quote");
    info!("Ran query for /random");
    Json(result)
}