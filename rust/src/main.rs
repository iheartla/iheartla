use iheartla::grammar;
use iheartla::peg::ParserConfig;
use iheartla::pnode;
use serde_json::Value;
use std::io::Read;

fn usage() -> ! {
    eprintln!(
        "usage:\n  iheartla parse [--init|--full] < file  print the parse tree as JSON\n  \
         iheartla check-parses <golden-dir>  compare parse trees with TatSu's\n  \
         iheartla compile [--backend numpy|eigen|matlab|latex|mathjax|macromathjax] [--name heartlib] [--main] < file\n  \
             (--main: also generateRandomData() and main(), for the code backends)"
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

/// Compare the declarations pass with the second-parse configurations
/// recorded from the Python compiler (main programs only).
fn check_config(dir: &str) {
    let mut paths: Vec<_> = std::fs::read_dir(dir).unwrap().filter_map(|e| e.ok()).map(|e| e.path()).collect();
    paths.sort();
    let (mut total, mut ok) = (0, 0);
    let sorted = |v: &Value| -> Vec<String> {
        let mut x: Vec<String> = v.as_array().unwrap().iter().map(|s| s.as_str().unwrap().to_string()).collect();
        x.sort();
        x
    };
    for path in paths {
        let golden: Value = serde_json::from_str(&std::fs::read_to_string(&path).unwrap()).unwrap();
        let src = golden["src"].as_str().unwrap();
        let Some(expected) = golden["parses"]
            .as_array()
            .unwrap()
            .iter()
            .find(|p| p["kind"] == "default" && p["text"].as_str() == Some(src))
        else {
            continue;
        };
        let Ok(tree) = grammar::parse_init(src) else { continue };
        // modules are found in the case's directory (relative to the repository root)
        let dirs = golden["path"].as_str().map(|p| vec![std::path::Path::new(dir).join("../../..").join(p)]).unwrap_or_default();
        let loader = iheartla::modules::Loader::new(dirs);
        total += 1;
        let cfg = iheartla::decls::second_parse_config_with(&tree, &|n| iheartla::node_text(src, n).to_string(), &|m| loader.function_names(m));
        let e = &expected["config"];
        let mut mine_ids = cfg.ids.clone();
        mine_ids.sort();
        let mut mine_funcs = cfg.funcs.clone();
        mine_funcs.sort();
        let mut problems = Vec::new();
        if mine_ids != sorted(&e["ids"]) {
            problems.push(format!("ids: expected {:?} got {:?}", sorted(&e["ids"]), mine_ids));
        }
        if mine_funcs != sorted(&e["funcs"]) {
            problems.push(format!("funcs: expected {:?} got {:?}", sorted(&e["funcs"]), mine_funcs));
        }
        let builtins: Vec<String> = e["builtins"].as_array().unwrap().iter().map(|s| s.as_str().unwrap().into()).collect();
        if builtins != cfg.builtins {
            problems.push(format!("builtins: expected {builtins:?} got {:?}", cfg.builtins));
        }
        if e["const_e"].as_bool() != Some(cfg.const_e) {
            problems.push("const_e".into());
        }
        let rename: std::collections::HashMap<String, String> =
            e["rename"].as_object().unwrap().iter().map(|(k, v)| (k.clone(), v.as_str().unwrap().into())).collect();
        if rename != cfg.rename {
            problems.push(format!("rename: expected {rename:?} got {:?}", cfg.rename));
        }
        if problems.is_empty() {
            ok += 1;
        } else {
            println!("{}: {}", golden["id"].as_str().unwrap(), problems.join("; "));
        }
    }
    println!("{ok}/{total} configurations identical");
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("parse") => {
            let mut text = String::new();
            std::io::stdin().read_to_string(&mut text).unwrap();
            let r = if args.iter().any(|a| a == "--init") {
                grammar::parse_init(&text)
            } else if args.iter().any(|a| a == "--full") {
                // both passes, as a compile does: declared names configure the second
                grammar::parse_init(&text).and_then(|first| {
                    let config = iheartla::decls::second_parse_config(&first, &|n| iheartla::node_text(&text, n).to_string());
                    grammar::parse_default(&text, &config)
                })
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
        Some("check-config") => check_config(args.get(2).map(String::as_str).unwrap_or("corpus/golden")),
        Some("compile") => {
            // iheartla compile [--backend numpy] [--name heartlib] [--main] < source
            let mut text = String::new();
            std::io::stdin().read_to_string(&mut text).unwrap();
            let opt = |flag: &str, default: &str| -> String {
                args.iter().position(|a| a == flag).and_then(|i| args.get(i + 1)).cloned().unwrap_or(default.into())
            };
            let backend = opt("--backend", "numpy");
            let name = opt("--name", "heartlib");
            let with_main = args.iter().any(|a| a == "--main");
            let result = iheartla::compile(&text, &backend, &name, with_main);
            match result {
                Ok(code) => print!("{code}"),
                Err(e) => {
                    eprint!("{e}");
                    std::process::exit(1)
                }
            }
        }
        _ => usage(),
    }
}
