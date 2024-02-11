extern crate rocket;
use diesel::pg::PgConnection;
use diesel::prelude::*;
use dotenvy::dotenv;
use serde::{Deserialize, Serialize};
use std::env;

pub fn establish_connection_pg() -> PgConnection {
    dotenv().ok();
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let database_connection_string = format!("postgresql://{}:5432", database_url)
    PgConnection::establish(&database_url)
        .unwrap_or_else(|_| panic!("Error connecting to {}", database_url))
}

#[derive(Serialize, Deserialize)]
pub struct NewQuote {
    pub text: String,
    pub speaker: String,
}