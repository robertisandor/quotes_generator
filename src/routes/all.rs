use diesel::RunQueryDsl;
use diesel::sql_query;
use log::info;
use rocket_contrib::json::Json;

use crate::models::Quote;
use crate::services::establish_connection_pg;

#[get("/all")]
pub fn list() -> Json<Vec<Quote>> {
    info!("Creating db connection for /api/all");
    let connection = &mut establish_connection_pg();
    info!("Created db connection for /api/all");
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
    info!("Ran query for /api/all");
    Json(results)
}