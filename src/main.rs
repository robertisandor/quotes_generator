#![feature(decl_macro)]

use log::LevelFilter;

use axum::{
    routing::{get, post},
    Router,
};
use tokio::net::TcpListener;

mod models;
mod services;
mod schema;
mod routes;

use crate::routes::index::index;
use crate::routes::all::list;
use crate::routes::quote::create_quote;
use crate::routes::not_found::not_found;

#[tokio::main]
async fn main() {
    let _ = simple_logging::log_to_file("app.log", LevelFilter::Info);

    // run our app with hyper, listening globally on port 3000
    let listener = TcpListener::bind("0.0.0.0:8000").await.unwrap();
    axum::serve(listener, app()).await.unwrap();
}

fn app() -> Router {
    Router::new()
        .route("/", get(index))
        .route("/all", get(list))
        .route("/quote", post(create_quote))
        .fallback(not_found)
}