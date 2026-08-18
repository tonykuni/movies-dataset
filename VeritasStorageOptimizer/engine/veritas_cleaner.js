#!/usr/bin/env node
/**
 * Veritas Engine - Node.js High-Performance File Purger (2026 Edition)
 * Zero-Dependency / Asynchronous Stream Hashing / Non-Blocking
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const TEMP_EXTENSIONS = new Set(['.tmp', '.log', '.cache', '.bak', '.old', '.temp', '.swp', '.dmp']);
const PROTECTED_DIRS = new Set(['.git', '.svn', '.venv', 'node_modules', 'site-packages', '$RECYCLE.BIN', 'System Volume Information']);
// Files below this size never enter duplicate detection: freeing ~0 bytes,
// while near-empty twins (__init__.py, .gitkeep, stdout stubs) are structural.
const DUP_MIN_BYTES = 1024;

// Coding byproducts: caches and compiled leftovers that tooling regenerates.
const CODING_JUNK_DIRS = new Set(['__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.ipynb_checkpoints']);
const CODING_JUNK_EXTENSIONS = new Set(['.pyc', '.pyo']);

// User-placed marker: any directory containing this file is off-limits to
// every strategy, letting users pin "do not touch" zones inside a scan.
const PROTECT_MARKER = '.veritas_protect';

// Protected names, Python virtual environments (pyvenv.cfg marker), and
// user-protected zones: venvs share thousands of identical package files,
// so cross-venv dedup would gut every env after the first-scanned one.
function isSkippedDir(fullPath, name) {
    if (PROTECTED_DIRS.has(name)) return true;
    try {
        return fs.existsSync(path.join(fullPath, 'pyvenv.cfg'))
            || fs.existsSync(path.join(fullPath, PROTECT_MARKER));
    } catch (err) { return true; }
}

function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let i = 0;
    while (size >= 1024 && i < units.length - 1) {
        size /= 1024;
        i++;
    }
    return `${size.toFixed(2)} ${units[i]}`;
}

// 串流雜湊計算,防止大型檔案直接卡爆 V8 Buffer
function getFileHashAsync(filePath) {
    return new Promise((resolve) => {
        const hash = crypto.createHash('md5');
        const stream = fs.createReadStream(filePath);
        stream.on('data', chunk => hash.update(chunk));
        stream.on('end', () => resolve(hash.digest('hex')));
        stream.on('error', () => resolve(null));
    });
}

async function scanDirectory(dirPath, sizeThresholdMB, executeLive = false, logFile = 'js_cleanup_audit.log') {
    const absoluteTarget = path.resolve(dirPath);

    let targetStats;
    try {
        targetStats = fs.statSync(absoluteTarget);
    } catch (err) {
        console.error(`[Error] Target directory '${dirPath}' does not exist.`);
        process.exit(1);
    }
    if (!targetStats.isDirectory()) {
        console.error(`[Error] Target '${dirPath}' is not a directory.`);
        process.exit(1);
    }
    if (fs.existsSync(path.join(absoluteTarget, PROTECT_MARKER))) {
        console.error(`[Error] Target is locked by a ${PROTECT_MARKER} marker.`);
        process.exit(1);
    }

    const sizeLimitBytes = sizeThresholdMB * 1024 * 1024;

    let totalFreedBytes = 0;
    const itemsToRemove = [];
    const sizeGroups = new Map();

    console.log(`=== Node.js Storage Purger Scan: ${absoluteTarget} ===`);
    console.log(`Mode: ${executeLive ? 'LIVE_EXECUTION' : 'DRY_RUN (Safe Preview)'}`);

    function walkSync(currentDir, inJunk) {
        let entries = [];
        try {
            entries = fs.readdirSync(currentDir, { withFileTypes: true });
        } catch (err) {
            return;
        }
        for (const entry of entries) {
            const fullPath = path.join(currentDir, entry.name);
            if (entry.isDirectory()) {
                if (!isSkippedDir(fullPath, entry.name)) {
                    walkSync(fullPath, inJunk || CODING_JUNK_DIRS.has(entry.name));
                }
            } else if (entry.isFile()) {
                try {
                    const stats = fs.statSync(fullPath);
                    const ext = path.extname(entry.name).toLowerCase();
                    // 0. 編程垃圾——快取目錄內容與 .pyc/.pyo 編譯殘留
                    if (inJunk || CODING_JUNK_EXTENSIONS.has(ext)) {
                        itemsToRemove.push({ path: fullPath, size: stats.size, reason: 'Coding Junk' });
                        totalFreedBytes += stats.size;
                        continue;
                    }
                    // 1. 暫存檔
                    if (TEMP_EXTENSIONS.has(ext)) {
                        itemsToRemove.push({ path: fullPath, size: stats.size, reason: 'Temp File' });
                        totalFreedBytes += stats.size;
                        continue;
                    }
                    // 2. 超過限制的大檔案
                    if (stats.size > sizeLimitBytes) {
                        itemsToRemove.push({ path: fullPath, size: stats.size, reason: `Over Size Limit (${sizeThresholdMB}MB)` });
                        totalFreedBytes += stats.size;
                        continue;
                    }
                    // 3. 收集「同副檔名 + 同容量」候選待驗證 Hash——複合鍵讓群組
                    //    更小,需要 Hash 的檔案更少(省記憶體與 I/O)
                    if (stats.size >= DUP_MIN_BYTES) {
                        const key = ext + '|' + stats.size;
                        if (!sizeGroups.has(key)) {
                            sizeGroups.set(key, { size: stats.size, paths: [] });
                        }
                        sizeGroups.get(key).paths.push(fullPath);
                    }
                } catch (err) {
                    // 權限缺失或檔名例外跳過
                }
            }
        }
    }

    walkSync(absoluteTarget, false);

    // 比對重複檔案 (2-Pass: 僅對「同副檔名 + 同容量」群組計算 Hash)
    for (const group of sizeGroups.values()) {
        const { size, paths: filePaths } = group;
        if (filePaths.length < 2) continue;
        const hashMap = new Map();
        for (const filePath of filePaths) {
            const hash = await getFileHashAsync(filePath);
            if (!hash) continue;
            if (hashMap.has(hash)) {
                itemsToRemove.push({ path: filePath, size, reason: `Duplicate of ${path.basename(hashMap.get(hash))}` });
                totalFreedBytes += size;
            } else {
                hashMap.set(hash, filePath);
            }
        }
    }

    // 輸出 Log 報告
    const logLines = [
        '=== VERITAS JS PURGER AUDIT LOG ===',
        `Timestamp: ${new Date().toISOString()}`,
        `Target: ${absoluteTarget}`,
        `Execution Mode: ${executeLive ? 'LIVE_DELETE' : 'DRY-RUN'}`,
        'Action Items:'
    ];

    for (const item of itemsToRemove) {
        const line = `[${item.reason}] ${formatSize(item.size)} -> ${item.path}`;
        logLines.push(line);
        console.log(line);
        if (executeLive) {
            try {
                fs.unlinkSync(item.path);
            } catch (err) {
                logLines.push(`   └─ Purge Failed: ${err.message}`);
            }
        }
    }

    logLines.push(`\nSummary: Total ${itemsToRemove.length} files. Space freed: ${formatSize(totalFreedBytes)}`);

    fs.writeFileSync(logFile, logLines.join('\n'), 'utf-8');
    console.log('Scan Complete.');
    console.log(`Target Purge Count: ${itemsToRemove.length} files`);
    console.log(`Potential Space Released: ${formatSize(totalFreedBytes)}`);
    console.log(`Audit saved to ${path.resolve(logFile)}`);
}

// 讀取命令列參數執行
function parseArgs(argv) {
    const opts = { dir: null, maxMB: 200, execute: false, log: 'js_cleanup_audit.log' };
    for (let i = 0; i < argv.length; i++) {
        const arg = argv[i];
        if (arg === '--execute') {
            opts.execute = true;
        } else if (arg === '--max-mb') {
            opts.maxMB = parseFloat(argv[++i]);
        } else if (arg.startsWith('--max-mb=')) {
            opts.maxMB = parseFloat(arg.split('=')[1]);
        } else if (arg === '--log') {
            opts.log = argv[++i];
        } else if (arg.startsWith('--log=')) {
            opts.log = arg.split('=')[1];
        } else if (arg === '--dir') {
            opts.dir = argv[++i];
        } else if (!arg.startsWith('--') && opts.dir === null) {
            opts.dir = arg;
        }
    }
    if (opts.dir === null) opts.dir = '.';
    if (!Number.isFinite(opts.maxMB) || opts.maxMB <= 0) {
        console.error('[Error] Invalid --max-mb value.');
        process.exit(1);
    }
    return opts;
}

const opts = parseArgs(process.argv.slice(2));
scanDirectory(opts.dir, opts.maxMB, opts.execute, opts.log);
