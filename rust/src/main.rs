use iheartla::grammar;
use iheartla::peg::ParserConfig;
use iheartla::pnode;
use serde_json::Value;
use std::io::Read;

fn usage() -> ! {
    eprintln!(
        "usage:\n  iheartla parse [--init] < file      print the parse tree as JSON\n  \
         iheartla check-parses <golden-dir>  compare parse trees with TatSu's"
    );
    std::process::exit(2)
}

fn config_from_json(v: &Value) -> ParserConfig {
    let strs = |k: &str| -> Vec<String> {
        v[k].as_array().map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect()).unwrap_or_default()
    };
    ParserConfig {
        ids: strs("ids"),
        funcs: strs("funcs"),
        builtins: strs("builtins"),
        rename: v["rename"]
            .as_object()
            .map(|o| o.iter().map(|(k, x)| (k.clone(), x.as_str().unwrap_or("").to_string())).collect())
            .unwrap_or_default(),
        const_e: v["const_e"].as_bool().unwrap_or(false),
    }
}

fn check_parses(dir: &str) {
    let mut paths: Vec<_> = std::fs::read_dir(dir).unwrap().filter_map(|e| e.ok()).map(|e| e.path()).collect();
    paths.sort();
    let (mut total, mut ok) = (0, 0);
    for path in paths {
        if path.extension().and_then(|e| e.to_str()) != Some("json") {
            continue;
        }
        let golden: Value = serde_json::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
        let id = golden["id"].as_str().unwrap_or("?");
        for (i, p) in golden["parses"].as_array().unwrap().iter().enumerate() {
            total += 1;
            let text = p["text"].as_str().unwrap();
            let result = if p["kind"] == "init" {
                grammar::parse_init(text)
            } else {
                grammar::parse_default(text, &config_from_json(&p["config"]))
            };
            let offsets = iheartla::char_offsets(text);
            let mine: Value = match &result {
                Ok(v) => serde_json::from_str(&pnode::to_json(v, &|b| offsets[b])).unwrap(),
                Err(e) => Value::String(format!("error at {}: {}", offsets[e.pos], e.message)),
            };
            let expected = match (&p.get("ast"), &p.get("error")) {
                (Some(a), _) => (*a).clone(),
                (_, Some(e)) => Value::String(format!("TatSu error: {}", e.as_str().unwrap_or(""))),
                _ => Value::Null,
            };
            let same = match (&result, p.get("error")) {
                (Err(_), Some(_)) => true,
                _ => mine == expected,
            };
            if same {
                ok += 1;
            } else {
                println!("MISMATCH {id} parse {i} ({})", p["kind"]);
                let a = serde_json::to_string(&expected).unwrap();
                let b = serde_json::to_string(&mine).unwrap();
                let common = a.chars().zip(b.chars()).take_while(|(x, y)| x == y).count();
                let from = common.saturating_sub(150);
                println!("  expected: …{}", a.chars().skip(from).take(400).collect::<String>());
                println!("  got:      …{}", b.chars().skip(from).take(400).collect::<String>());
            }
        }
    }
    println!("{ok}/{total} parses identical");
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("parse") => {
            let mut text = String::new();
            std::io::stdin().read_to_string(&mut text).unwrap();
            let r = if args.iter().any(|a| a == "--init") {
                grammar::parse_init(&text)
            } else {
                grammar::parse_default(&text, &ParserConfig::default())
            };
            let offsets = iheartla::char_offsets(&text);
            match r {
                Ok(v) => println!("{}", pnode::to_json(&v, &|b| offsets[b])),
                Err(e) => {
                    eprintln!("parse error at {}: {} ({})", offsets[e.pos], e.message, e.stack.join(" < "));
                    std::process::exit(1)
                }
            }
        }
        Some("check-parses") => check_parses(args.get(2).map(String::as_str).unwrap_or("corpus/golden")),
        _ => usage(),
    }
}
