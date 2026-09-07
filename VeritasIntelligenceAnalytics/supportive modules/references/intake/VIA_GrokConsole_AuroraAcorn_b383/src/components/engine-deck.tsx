import { useRef, useState, type ReactNode } from "react";
import { Cpu, Globe, Languages, Plug } from "lucide-react";
import { RightRail } from "@/components/right-rail";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { LiveLog } from "@/components/live-log";
import { Matrix } from "@/components/matrix";
import { StatusLight } from "@/components/status-light";
import { useVia } from "@/lib/via/store";
import { aliasOf } from "@/lib/via/inventory";
import { accelToolOf, autoRegOf, engineMountNote, nlpToolOf, netToolOf } from "@/lib/via/engine-mount";

const KINDS = ["VRN", "VDF", "NLP", "ACCEL", "NET", "GOV", "ENG"];

export function EngineDeck() {
  const {
    engines,
    engineLogs,
    confirmNet,
    confirmNlp,
    setConfirmNet,
    setConfirmNlp,
    pendingMounts,
    setPendingMounts,
    mountEngines,
    engineBusy,
    tools,
    handoverDay,
  } = useVia();
  const fileRef = useRef<HTMLInputElement>(null);
  const dirRef = useRef<HTMLInputElement>(null);
  const [kind, setKind] = useState("VRN");
  const [filter, setFilter] = useState("LIVE");
  const [manualName, setManualName] = useState("");
  const [manualPath, setManualPath] = useState("functional modules/VRN/");
  const [over, setOver] = useState(false);

  const openMount = (drafts: { name: string; path: string }[]) => {
    setPendingMounts(drafts.map((d) => ({ ...d, kind })));
  };

  const fromList = (list: FileList | null, folder: boolean) => {
    if (!list?.length) return;
    const files = Array.from(list);
    openMount(
      files.map((f) => ({
        name: f.name,
        path: folder ? `I/O/${(f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name}` : `I/O/${f.name}`,
      })),
    );
  };

  const nlpTools = tools.filter((t) => t.kind === "nlp");
  const shown = engines.filter((e) => {
    const aliased = Boolean(aliasOf(e.id));
    if (filter === "LIVE") return !aliased;
    if (filter === "ALIAS") return aliased;
    if (filter === "ALL") return true;
    return e.kind === filter && !aliased;
  });

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_240px]">
      <div className="min-w-0 space-y-4">
        <header>
          <p className="text-xs font-medium uppercase tracking-widest text-subtle">引擎 · Action 03 · Central Govern</p>
          <h2 className="text-lg font-medium tracking-tight">引擎主管 · SSOT 登錄</h2>
          <p className="mt-1 max-w-2xl text-xs leading-relaxed text-muted">
            右側只列活路＋治理工具。同職舊模組 ALIAS 退下，工具仍在冊。網路與 NLP 須確認。加速一律 ACC-CEL、網路一律 NET-AEG。{engineMountNote()}
          </p>
        </header>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            fromList(e.dataTransfer.files, true);
          }}
          className={`space-y-3 rounded-lg bg-surface p-4 shadow-[var(--shadow-border)] ${over ? "ring-2 ring-ring" : ""}`}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>名稱 / 檔案</Label>
              <Input value={manualName} placeholder="VRN_ENG080_…" onChange={(e) => setManualName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label>路徑</Label>
              <Input value={manualPath} onChange={(e) => setManualPath(e.target.value)} />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {KINDS.map((k) => (
              <Button key={k} size="sm" variant={kind === k ? "default" : "outline"} onClick={() => setKind(k)}>
                {k}
              </Button>
            ))}
            <input ref={fileRef} type="file" multiple className="hidden" onChange={(e) => fromList(e.target.files, false)} />
            <input
              ref={dirRef}
              type="file"
              multiple
              className="hidden"
              {...{ webkitdirectory: "", directory: "" }}
              onChange={(e) => fromList(e.target.files, true)}
            />
            <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()}>
              選取檔案
            </Button>
            <Button variant="outline" size="sm" onClick={() => dirRef.current?.click()}>
              選取資料夾
            </Button>
            <Button
              className="ml-auto"
              data-action="engine-mount"
              disabled={!manualName.trim()}
              onClick={() => openMount([{ name: manualName.trim(), path: manualPath }])}
            >
              <Plug className="size-3.5" />
              掛載
            </Button>
          </div>
        </div>

        <section>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">NLP 總線確認</h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {nlpTools.map((t) => (
              <div key={t.id} className="flex items-center justify-between rounded-md bg-inset px-3 py-2">
                <div>
                  <p className="text-xs">{t.name}</p>
                  <p className="font-mono text-xs text-subtle">{t.id}</p>
                </div>
                <StatusLight status={t.status} />
              </div>
            ))}
          </div>
        </section>

        <div className="flex flex-wrap gap-1">
          {["LIVE", "ALIAS", "ALL", ...KINDS].map((k) => (
            <Button key={k} size="sm" variant={filter === k ? "default" : "ghost"} onClick={() => setFilter(k)}>
              {k}
              <span className="font-mono text-xs opacity-70">
                {k === "ALL"
                  ? engines.length
                  : k === "LIVE"
                    ? engines.filter((e) => !aliasOf(e.id)).length
                    : k === "ALIAS"
                      ? engines.filter((e) => aliasOf(e.id)).length
                      : engines.filter((e) => e.kind === k && !aliasOf(e.id)).length}
              </span>
            </Button>
          ))}
        </div>

        <Matrix
          columns={["燈", "ID", "編號", "加速器", "網路", "NLP", "類", "SSOT", "註"]}
          rows={shown.map((e) => {
            const { reg, auto } = autoRegOf(e);
            return [
              <StatusLight key="l" status={aliasOf(e.id) ? "idle" : e.status} />,
              <span key="id" className="font-mono">
                {e.id}
              </span>,
              <span key="r" className="font-mono text-xs">
                {auto ? reg : `無 · ${e.hash}`}
              </span>,
              accelToolOf(e),
              netToolOf(e),
              nlpToolOf(e),
              e.kind,
              yn(e.ssot),
              <span key="n" className="max-w-60 truncate text-muted">
                {e.note}
              </span>,
            ];
          })}
        />

        <section className="space-y-2">
          <h3 className="text-xs font-medium uppercase tracking-wide text-subtle">SSOT JSON</h3>
          <pre className="max-h-48 overflow-auto rounded-md bg-inset p-3 font-mono text-xs leading-relaxed text-muted shadow-[var(--shadow-border)]">
            {JSON.stringify(
              engines.map((e) => ({
                vis_id: e.id,
                name: e.name,
                kind: e.kind,
                path: e.path,
                hash: e.hash,
                auto_reg: autoRegOf(e).reg,
                accel: accelToolOf(e),
                net: netToolOf(e),
                nlp: nlpToolOf(e),
                ssot: e.ssot,
              })),
              null,
              2,
            )}
          </pre>
        </section>

        <LiveLog lines={engineLogs} />
      </div>

      <div className="space-y-3 lg:sticky lg:top-2 lg:self-start">
        <div className="space-y-3 rounded-lg bg-surface p-4 shadow-[var(--shadow-border)]">
          <p className="text-xs font-medium uppercase tracking-wide text-subtle">確認閘</p>
          <Gate
            icon={<Globe className="size-4" />}
            title="網路工具"
            desc="VIA_NET_CONSENT"
            checked={confirmNet}
            onChange={setConfirmNet}
          />
          <Gate
            icon={<Languages className="size-4" />}
            title="NLP 工具"
            desc="ENG066 樞紐"
            checked={confirmNlp}
            onChange={setConfirmNlp}
          />
          <div className="flex items-center gap-2 pt-1 text-xs text-muted">
            <Cpu className="size-4" />
            加速器：預設自動掛載
          </div>
        </div>
        <RightRail engines={engines} day={handoverDay} />
      </div>

      <Dialog open={pendingMounts.length > 0} onOpenChange={(o) => !o && setPendingMounts([])}>
        <DialogContent>
          <DialogTitle>確認掛載</DialogTitle>
          <DialogDescription>
            {pendingMounts.length} 件將登錄 SSOT。加速器自動掛上總線。網路與 NLP 依目前閘狀態。
          </DialogDescription>
          <ul className="mt-3 max-h-32 space-y-1 overflow-auto text-sm text-muted">
            {pendingMounts.slice(0, 8).map((p) => (
              <li key={p.path} className="truncate font-mono text-xs">
                {p.kind} · {p.name}
              </li>
            ))}
            {pendingMounts.length > 8 ? <li>… +{pendingMounts.length - 8}</li> : null}
          </ul>
          <ul className="mt-3 space-y-1 text-sm text-muted">
            <li>ACCEL · 自動</li>
            <li>NET · {confirmNet ? "已確認" : "未確認，保持零外呼"}</li>
            <li>NLP · {confirmNlp ? "已確認" : "不掛樞紐"}</li>
          </ul>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setPendingMounts([])}>
              取消
            </Button>
            <Button data-action="engine-ssot" disabled={engineBusy} onClick={() => void mountEngines()}>
              寫入 SSOT
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function yn(v: boolean) {
  return <Badge tone={v ? "ok" : "idle"}>{v ? "ON" : "OFF"}</Badge>;
}

function Gate({
  icon,
  title,
  desc,
  checked,
  onChange,
}: {
  icon: ReactNode;
  title: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-center gap-2">
        <span className="text-muted">{icon}</span>
        <div>
          <p className="text-xs">{title}</p>
          <p className="font-mono text-xs text-subtle">{desc}</p>
        </div>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}
