import { useState } from "react";
import { Download } from "lucide-react";
import { PACK_FILE, PACK_NAME, VERSION } from "@/lib/registry";
import { saveUrlAsFile } from "@/lib/save-file";
import { cn } from "@/lib/utils";

type Status = "idle" | "saving" | "done" | "fail";

export function PackSave({ compact = false }: { compact?: boolean }) {
  const [status, setStatus] = useState<Status>("idle");

  async function save() {
    if (status === "saving") return;
    setStatus("saving");
    try {
      await saveUrlAsFile(PACK_FILE, PACK_NAME);
      setStatus("done");
    } catch {
      setStatus("fail");
    }
  }

  if (compact) {
    return (
      <a
        href="/download.html"
        target="_blank"
        rel="noreferrer"
        className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg"
      >
        <Download className="size-4" strokeWidth={1.75} />
        輸出 ZIP
      </a>
    );
  }

  return (
    <section className="rounded-[var(--radius-xl)] border border-border bg-bg-elevated p-4 sm:p-5">
      <p className="font-mono text-[10px] tracking-[0.18em] text-muted">OUTPUT · v{VERSION}</p>
      <h2 className="mt-1 text-lg font-medium tracking-display">輸出全包到下載資料夾</h2>
      <p className="mt-1 max-w-2xl text-sm text-muted">
        預覽框會擋住下載。請用「另開頁面」或聊天裡的檔案卡。
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <a
          href="/download.html"
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] bg-accent px-4 text-sm font-medium text-accent-fg"
        >
          <Download className="size-4" strokeWidth={1.75} />
          另開頁面存 ZIP
        </a>
        <a
          href={PACK_FILE}
          download={PACK_NAME}
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle"
        >
          直連 ZIP
        </a>
        <a
          href="/VeritasCeleritas.PS7.ps1"
          download="VeritasCeleritas.PS7.ps1"
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle"
        >
          只存 .ps1
        </a>
        <button
          type="button"
          onClick={() => void save()}
          disabled={status === "saving"}
          className="inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-border px-4 text-sm text-fg hover:bg-bg-subtle disabled:opacity-60"
        >
          {status === "saving" ? "嘗試中…" : "本頁強制存"}
        </button>
      </div>
      <p
        className={cn(
          "mt-3 font-mono text-xs",
          status === "fail" ? "text-danger" : status === "done" ? "text-ok" : "text-muted",
        )}
      >
        {status === "idle" && `檔名 ${PACK_NAME} · 若沒跳出檔案，點「另開頁面存 ZIP」`}
        {status === "saving" && "正在交給瀏覽器…"}
        {status === "done" && "已嘗試送出。沒看到檔案就改點「另開頁面存 ZIP」。"}
        {status === "fail" && "預覽擋住了。請點「另開頁面存 ZIP」或聊天檔案卡。"}
      </p>
    </section>
  );
}
