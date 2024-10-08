use axum::{
    routing::{get, post},
    Router,
};
use std::{fs::File, sync::Arc};
use tokio::net::TcpListener;
use tracing_subscriber::{Registry, prelude::*};

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
    let std_log = tracing_subscriber::fmt::layer().json();
    Registry::default()
        .with(std_log)
        .init();

    // run our app with hyper, listening globally on port 80
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