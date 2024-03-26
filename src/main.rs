#![feature(decl_macro)]
#[macro_use] extern crate rocket;

use log::LevelFilter;

mod models;
mod services;
mod schema;
mod routes;

use crate::routes::index::static_rocket_route_info_for_index;
use crate::routes::quote::static_rocket_route_info_for_create_quote;
use crate::routes::all::static_rocket_route_info_for_list;
use crate::routes::not_found::static_rocket_catch_info_for_not_found;

pub fn rocket_builder() -> rocket::Rocket {
    rocket::ignite()
        .register(catchers![not_found])
        .mount("/api", routes![index, create_quote, list])
}

fn main() {
    let _ = simple_logging::log_to_file("app.log", LevelFilter::Info);

    rocket_builder().launch();
}