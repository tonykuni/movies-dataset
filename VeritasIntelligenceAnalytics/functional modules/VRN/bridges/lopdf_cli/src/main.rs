//! VIA lib.lopdf 接頭:`lopdf_cli <pdf>` → stdout 一行 JSON(物件摘要;唯讀)。
//! 契約:成功 rc 0;任何錯誤印 stderr、rc 1(宿主 runner 有界執行,不在此設限)。
use std::env;
use std::process::exit;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("usage: lopdf_cli <pdf>");
        exit(1);
    }
    let doc = match lopdf::Document::load(&args[1]) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("lopdf load error: {e}");
            exit(1);
        }
    };
    let pages = doc.get_pages();
    let page_ids: Vec<String> = pages
        .iter()
        .map(|(no, (id, gen))| format!("p{no}:{id} {gen} R"))
        .collect();
    let encrypted = doc.trailer.get(b"Encrypt").is_ok();
    let out = serde_json::json!({
        "tool": "lopdf_cli",
        "bridge": "lib.lopdf",
        "pdf_version": doc.version,
        "page_count": pages.len(),
        "object_count": doc.objects.len(),
        "encrypted": encrypted,
        "max_object_id": doc.max_id,
        "pages": page_ids,
    });
    println!("{out}");
}
