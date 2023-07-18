extern crate serde_json;
use std::fs::File;
use std::io::prelude::*;
use std::path::Path;
use serde_json::Value;

pub fn read_items() -> Value {
    let path = Path::new("storage/items.json");
    let mut file = File::open(&path).expect("Unable to open the file");
    let mut contents = String::new();
    file.read_to_string(&mut contents).expect("Unable to read the file");
    let grocery_items: Value = serde_json::from_str(&contents).expect("Unable to parse the JSON");
    grocery_items
}

pub fn write_items(grocery_items: Value) {
    let path = Path::new("storage/items.json");
    let mut file = File::create(&path).expect("Unable to create the file");
    let contents = serde_json::to_string(&grocery_items).expect("Unable to convert to JSON");
    file.write_all(contents.as_bytes()).expect("Unable to write data");
}