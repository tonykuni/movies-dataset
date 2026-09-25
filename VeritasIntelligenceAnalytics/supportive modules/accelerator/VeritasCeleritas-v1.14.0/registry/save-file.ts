export async function saveUrlAsFile(url: string, filename: string): Promise<void> {
  const abs = new URL(url, window.location.origin).toString();
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch ${res.status}`);
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    trigger(href, filename);
    window.setTimeout(() => URL.revokeObjectURL(href), 8000);
    return;
  } catch {
    // fall through
  }
  trigger(abs, filename);
  const opened = window.open(abs, "_blank", "noopener,noreferrer");
  if (!opened) {
    const top = window.top;
    if (top && top !== window) {
      try {
        top.location.assign(abs);
        return;
      } catch {
        /* framed */
      }
    }
    window.location.assign(abs);
  }
}

function trigger(href: string, filename: string) {
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
