use std::env;
use std::fs;
use std::path::Path;
use std::process::ExitCode;

const MAX_FILE_BYTES: u64 = 128 * 1024 * 1024;

fn def_json_escape(value: &str) -> String {
    value
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
        .replace('\n', "\\n")
        .replace('\r', "\\r")
        .replace('\t', "\\t")
}

fn def_fence_balance(text: &str) -> (bool, usize) {
    let mut active: Option<char> = None;
    let mut count = 0usize;
    for line in text.lines() {
        let trimmed = line.trim_start();
        let marker = if trimmed.starts_with("```") {
            Some('`')
        } else if trimmed.starts_with("~~~") {
            Some('~')
        } else {
            None
        };
        if let Some(current) = marker {
            match active {
                None => {
                    active = Some(current);
                    count += 1;
                }
                Some(open) if open == current => {
                    active = None;
                    count += 1;
                }
                _ => {}
            }
        }
    }
    (active.is_none(), count)
}

fn def_main() -> Result<bool, String> {
    let input = env::args().nth(1).ok_or_else(|| "Usage: mdscan <file.md>".to_string())?;
    let path = Path::new(&input);
    let metadata = fs::metadata(path).map_err(|error| error.to_string())?;
    if metadata.len() > MAX_FILE_BYTES {
        return Err(format!("File exceeds {} bytes", MAX_FILE_BYTES));
    }
    let bytes = fs::read(path).map_err(|error| error.to_string())?;
    if bytes.contains(&0) {
        return Err("NUL byte detected".to_string());
    }
    let text = std::str::from_utf8(&bytes).map_err(|error| error.to_string())?;
    let (balanced, fence_markers) = def_fence_balance(text);
    println!(
        "{{\"file\":\"{}\",\"utf8\":true,\"fencesBalanced\":{},\"fenceMarkers\":{},\"bytes\":{}}}",
        def_json_escape(&input),
        balanced,
        fence_markers,
        bytes.len()
    );
    Ok(balanced)
}

fn main() -> ExitCode {
    match def_main() {
        Ok(true) => ExitCode::SUCCESS,
        Ok(false) => ExitCode::from(1),
        Err(error) => {
            eprintln!("{{\"ok\":false,\"error\":\"{}\"}}", def_json_escape(&error));
            ExitCode::from(2)
        }
    }
}
