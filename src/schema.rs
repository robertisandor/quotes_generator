// @generated automatically by Diesel CLI.

diesel::table! {
    quotes (quote_id) {
        quote_id -> Int4,
        #[max_length = 512]
        text -> Varchar,
        #[max_length = 64]
        speaker -> Varchar,
    }
}
