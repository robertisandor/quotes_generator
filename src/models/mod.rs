use super::schema::quotes;
use diesel::{prelude::*};
use serde::{Serialize, Deserialize};
use diesel::sql_types::{Integer, Text};

#[derive(Queryable, QueryableByName, Insertable, Serialize, Deserialize)]
#[diesel(primary_key(quote_id))]
#[diesel(table_name = quotes)]
pub struct Quote {
    #[diesel(sql_type = Integer)]
    pub quote_id: i32,
    #[diesel(sql_type = Text)]
    pub text: String,
    #[diesel(sql_type = Text)]
    pub speaker: String, 
}