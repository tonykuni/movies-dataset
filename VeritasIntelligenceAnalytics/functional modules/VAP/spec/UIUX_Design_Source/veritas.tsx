import React, { useState, useEffect, useMemo } from 'react';
import { 
  Inbox, Briefcase, Mail, CheckCircle2, Clock, AlertCircle, 
  Search, KanbanSquare, List, ArrowRight, Tag, MessageSquare,
  Play, MoreVertical, Calendar, User, Zap, ShieldCheck, Database,
  Plus, Terminal
} from 'lucide-react';

// ============================================================================
// VERITAS DATA ENGINE (Simulating Python Backend, NLP & DuckDB in Memory)
// ============================================================================

class VeritasDataEngine {
  constructor() {
    this.vault = new Map(); // Simulating DuckDB Asset Vault
    this.ledger = [];       // Simulating Append-Only Ledger
    this.tasks = {          // Simulating Project DB
      todo: [],
      doing: [],
      done: []
    };
    
    // Seed initial data
    this._seedData();
  }

  // Helper: Simple deterministic hash function (Simulating Blake3/SHA256)
  _hash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash) + str.charCodeAt(i);
      hash |= 0; 
    }
    return Math.abs(hash).toString(16).substring(0, 6).toUpperCase();
  }

  // Core NLP Simulation: Extract Intent & Entities
  _nlpExtract(text) {
    const textUpper = text.toUpperCase();
    let intent = "GEN"; // General
    let tag = "INFO_REVIEW";
    let tasks = [];
    let project = "未分類專案";

    // Intent Heuristics
    if (textUpper.includes("缺料") || textUpper.includes("變更") || textUpper.includes("急件")) {
      intent = "ECO";
      tag = "ACTION_REQUIRED";
    } else if (textUpper.includes("核准") || textUpper.includes("APPROVED")) {
      intent = "APR";
      tag = "STATUS_UPDATE";
    }

    // Project Heuristics
    const projMatch = text.match(/(MP-\d{3}|PO-\d{6}-\d{3}|Q\d 稽核)/i);
    if (projMatch) project = projMatch[0] + " 專案";

    // Action Item Extraction (Simulating GLiNER/spaCy)
    if (tag === "ACTION_REQUIRED") {
      const actions = text.split(/[，。！\n]/);
      actions.forEach((sentence, idx) => {
        if (sentence.includes("改用") || sentence.includes("加上") || sentence.includes("發行")) {
          tasks.push({
            id: `xt-${this._hash(sentence)}`,
            desc: sentence.replace(/請|必須/g, '').trim(),
            assignee: textUpper.includes("TONY") ? "Tony" : "RD Team",
            deadline: text.match(/\d{4}\/\d{2}\/\d{2}/) ? text.match(/\d{4}\/\d{2}\/\d{2}/)[0] : "ASAP"
          });
        }
      });
    }

    return { intent, tag, project, tasks };
  }

  // Pipeline: Ingest Raw Mail -> Extract -> Mint ID -> Write Vault -> Log Ledger
  ingestMail(rawMail) {
    const { sender, subject, body, time } = rawMail;
    
    // 1. Extraction
    const nlpData = this._nlpExtract(body + " " + subject);
    
    // 2. Mint Universal ID
    const sysId = `${nlpData.intent}-M-2608-${this._hash(body)}`;
    
    if (this.vault.has(sysId)) {
      this._appendLedger('WARN', 'DUPLICATE_REJECTED', `拒絕重複收容: ${sysId}`);
      return null;
    }

    // 3. Create Asset
    const asset = {
      id: sysId,
      sender,
      subject,
      snippet: body.substring(0, 60) + "...",
      fullBody: body,
      time: time || new Date().toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' }),
      isUnread: true,
      aiTag: nlpData.tag,
      project: nlpData.project,
      extractedTasks: nlpData.tasks
    };

    // 4. Write to Vault & Ledger
    this.vault.set(sysId, asset);
    this._appendLedger('SUCCESS', 'ASSET_MINTED', `成功鑄造資產: ${sysId} (${nlpData.intent})`);
    
    return asset;
  }

  _appendLedger(type, event, desc) {
    this.ledger.unshift({
      id: `SEQ-${this.ledger.length + 1000}`,
      time: new Date().toLocaleTimeString('zh-TW', { hour12: false, hour: '2-digit', minute: '2-digit', second:'2-digit' }),
      type, event, desc
    });
  }

  getInbox() {
    return Array.from(this.vault.values()).reverse();
  }

  getLedger() {
    return this.ledger;
  }

  getTasks() {
    return this.tasks;
  }

  addTaskToBoard(taskDesc, project, deadline, sourceId) {
    const newTask = {
      id: `tk-${this._hash(taskDesc + Date.now())}`,
      title: taskDesc,
      project: project,
      due: deadline,
      source: sourceId
    };
    this.tasks.todo.push(newTask);
    this._appendLedger('INFO', 'TASK_CREATED', `從 ${sourceId} 萃取並建立任務: ${newTask.id}`);
    return { ...this.tasks };
  }

  _seedData() {
    this.ingestMail({
      sender: "System ERP", subject: "PO-202608-088 採購單已核准", time: "Yesterday",
      body: "您的採購單 PO-202608-088 已由總經理核准，請進行後續發包作業。"
    });
    this.ingestMail({
      sender: "Sarah (品保部)", subject: "Q3 供應商稽核報告彙整", time: "09:15 AM",
      body: "附件是本季度的稽核報告，其中兩家廠商的交期達交率低於標準，請審閱。"
    });
    this.ingestMail({
      sender: "Andy Lin (供應商)", subject: "Re: MP-001 主機板 DVT 測試異常", time: "10:29 AM",
      body: "Tony，陳總監指示，MP-001 主機板的 MCU 目前嚴重缺料。請即刻改用備用的 IC-MCU-101，並務必於 2026/08/05 前發行 ECO 變更單。急件！"
    });
    
    // Seed some initial board tasks
    this.tasks.doing.push({ id: 'tk-old1', title: '將 PO 單發送給供應商', project: 'PO-202608-088', due: '08/03', source: 'APR-M-2608-D41A' });
    this.tasks.done.push({ id: 'tk-old2', title: '確認 DVT 測試環境', project: 'MP-001 專案', due: '08/01', source: '系統建立' });
  }
}

// Instantiate Global Engine
const engine = new VeritasDataEngine();

// ============================================================================
// REACT UI (Frontend connecting to the JS Engine)
// ============================================================================

export default function VeritasUnifiedApp() {
  const [activeNav, setActiveNav] = useState('inbox');
  const [inbox, setInbox] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [boardTasks, setBoardTasks] = useState(engine.getTasks());
  const [ledgerLogs, setLedgerLogs] = useState([]);

  // Sync state with Engine
  const syncWithEngine = () => {
    const mails = engine.getInbox();
    setInbox(mails);
    setBoardTasks(engine.getTasks());
    setLedgerLogs(engine.getLedger());
    if (!selectedEmail && mails.length > 0) setSelectedEmail(mails[0]);
  };

  useEffect(() => {
    syncWithEngine();
  }, []);

  const handleSimulateNewEmail = () => {
    const newMail = {
      sender: "機構部 - Leo",
      subject: "急: MP-001 機殼開模尺寸修改",
      body: "Tony，我們剛收到工廠回報，MP-001 的機殼干涉到新的 TVS 二極體。請在 2026/08/06 前修改機構 3D 圖面，並發布新版 CAD 檔！",
      time: "Just Now"
    };
    const asset = engine.ingestMail(newMail);
    syncWithEngine();
    if (asset) setSelectedEmail(asset);
  };

  const handleAddTask = (taskDesc, project, deadline, sourceId) => {
    engine.addTaskToBoard(taskDesc, project, deadline, sourceId);
    syncWithEngine();
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-300 font-sans flex flex-col overflow-hidden selection:bg-emerald-500/30">
      
      {/* Top Header */}
      <header className="h-14 border-b border-slate-800 bg-[#040C1A]/90 flex items-center justify-between px-6 z-20">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-900 flex items-center justify-center shadow-lg shadow-emerald-900/20">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold text-white tracking-widest uppercase">Veritas <span className="text-emerald-500 font-mono text-[10px] ml-2 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">Unified Engine</span></span>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={handleSimulateNewEmail}
            className="flex items-center text-[10px] font-mono bg-slate-800 hover:bg-slate-700 text-emerald-400 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
          >
            <Plus className="w-3 h-3 mr-1" /> 模擬接收新信件 (Inject)
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-16 bg-[#040C1A] border-r border-slate-800/80 flex flex-col items-center py-6 space-y-4 z-20">
          <NavIcon icon={<Inbox />} id="inbox" active={activeNav} onClick={setActiveNav} tooltip="智能收件匣" badge={inbox.filter(m=>m.isUnread).length} />
          <NavIcon icon={<KanbanSquare />} id="board" active={activeNav} onClick={setActiveNav} tooltip="專案看板" />
          <NavIcon icon={<Terminal />} id="ledger" active={activeNav} onClick={setActiveNav} tooltip="引擎總帳" />
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex overflow-hidden relative">
          {/* Background Grid */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none"></div>
          
          <div className="w-full h-full relative z-10 flex">
            {activeNav === 'inbox' && (
              <InboxView 
                mails={inbox} 
                selected={selectedEmail} 
                onSelect={(m) => { setSelectedEmail(m); m.isUnread = false; setInbox([...inbox]); }} 
                onAddTask={handleAddTask}
              />
            )}
            {activeNav === 'board' && <ProjectBoardView tasks={boardTasks} />}
            {activeNav === 'ledger' && <LedgerView logs={ledgerLogs} />}
          </div>
        </main>
      </div>
    </div>
  );
}

function NavIcon({ icon, id, active, onClick, tooltip, badge }) {
  const isActive = active === id;
  return (
    <button 
      onClick={() => onClick(id)}
      title={tooltip}
      className={`relative w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
        isActive ? 'bg-emerald-900/30 text-emerald-400 border border-emerald-800/50' : 'text-slate-500 hover:bg-slate-800/50 hover:text-slate-300'
      }`}
    >
      {React.cloneElement(icon, { className: 'w-5 h-5' })}
      {badge > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
          {badge}
        </span>
      )}
    </button>
  );
}

function TagBadge({ tag }) {
  let colorClass = 'bg-slate-800 text-slate-400 border-slate-700';
  let label = tag;

  if (tag === 'ACTION_REQUIRED') {
    colorClass = 'bg-red-950/50 text-red-400 border-red-900/50';
    label = 'Action Req';
  } else if (tag === 'STATUS_UPDATE') {
    colorClass = 'bg-blue-950/50 text-blue-400 border-blue-900/50';
    label = 'Status Upd';
  } else if (tag === 'INFO_REVIEW') {
    colorClass = 'bg-emerald-950/50 text-emerald-400 border-emerald-900/50';
    label = 'Info/Review';
  }

  return (
    <span className={`text-[9px] font-bold font-mono px-2 py-0.5 rounded border ${colorClass} uppercase tracking-wider`}>
      {label}
    </span>
  );
}

function InboxView({ mails, selected, onSelect, onAddTask }) {
  return (
    <div className="flex flex-1 overflow-hidden animate-in fade-in duration-300">
      {/* Email List Column */}
      <div className="w-96 border-r border-slate-800/80 bg-[#050B14] flex flex-col z-10">
        <div className="p-4 border-b border-slate-800/80">
          <h2 className="text-sm font-semibold text-white flex items-center mb-3">
            AI Triage Inbox <span className="ml-2 text-[10px] font-mono bg-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-800/30">L0 Filter</span>
          </h2>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="搜尋意圖、任務或 ID..." 
              className="w-full bg-[#020617] border border-slate-700/50 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {mails.map(email => (
            <div 
              key={email.id}
              onClick={() => onSelect(email)}
              className={`p-4 border-b border-slate-800/40 cursor-pointer transition-colors ${
                selected?.id === email.id ? 'bg-slate-800/60 border-l-2 border-l-emerald-500' : 'hover:bg-slate-800/30 border-l-2 border-l-transparent'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span className={`text-xs font-medium ${email.isUnread ? 'text-white' : 'text-slate-400'}`}>{email.sender}</span>
                <span className="text-[10px] text-slate-500 font-mono">{email.time}</span>
              </div>
              <h3 className={`text-sm mb-1 truncate ${email.isUnread ? 'text-emerald-100 font-semibold' : 'text-slate-300'}`}>{email.subject}</h3>
              <p className="text-[11px] text-slate-500 truncate mb-2">{email.snippet}</p>
              
              <div className="flex items-center space-x-2">
                <TagBadge tag={email.aiTag} />
                <span className="text-[9px] font-mono text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded flex items-center border border-slate-800">
                  <Database className="w-2.5 h-2.5 mr-1" /> {email.id.split('-')[2]}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Email Reader & Task Extraction Column */}
      <div className="flex-1 bg-transparent flex flex-col overflow-y-auto">
        {selected ? (
          <div className="p-8 max-w-4xl mx-auto w-full space-y-6">
            
            {/* Header */}
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-2xl font-semibold text-white mb-2">{selected.subject}</h1>
                <div className="flex items-center space-x-3 text-sm text-slate-400">
                  <span className="font-medium text-slate-300">{selected.sender}</span>
                  <span>•</span>
                  <span>{selected.time}</span>
                  <span>•</span>
                  <span className="font-mono text-xs text-slate-500">SYS_ID: {selected.id}</span>
                </div>
              </div>
              <div className="flex space-x-2">
                <button className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium transition-colors">封存</button>
              </div>
            </div>

            {/* Email Body */}
            <div className="bg-[#050B14] border border-slate-800 p-6 rounded-2xl shadow-lg relative">
              <pre className="text-sm text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
                {selected.fullBody}
              </pre>
            </div>

            {/* AI Task Extraction Panel */}
            <div className="border border-emerald-900/30 bg-gradient-to-br from-emerald-950/20 to-slate-900/20 rounded-2xl p-6 shadow-xl relative overflow-hidden">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500"></div>
              
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xs font-bold text-emerald-400 flex items-center uppercase tracking-widest font-mono">
                  <Zap className="w-4 h-4 mr-2" /> NLP Mail-to-Task Resolution
                </h3>
                <span className="text-[10px] bg-slate-900 border border-slate-700 text-slate-400 px-2 py-1 rounded font-mono">
                  Context: {selected.project}
                </span>
              </div>

              {selected.extractedTasks.length > 0 ? (
                <div className="space-y-3">
                  {selected.extractedTasks.map(task => (
                    <div key={task.id} className="bg-[#020617]/80 border border-slate-800 p-3 rounded-xl flex items-center justify-between group hover:border-emerald-800/50 transition-colors">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 rounded border border-slate-600 flex-shrink-0"></div>
                        <span className="text-sm text-slate-200">{task.desc}</span>
                      </div>
                      <div className="flex items-center space-x-4 flex-shrink-0">
                        <div className="flex items-center text-xs text-slate-400 font-mono">
                          <User className="w-3.5 h-3.5 mr-1" /> {task.assignee}
                        </div>
                        <div className="flex items-center text-[10px] text-red-400 font-mono bg-red-950/30 px-2 py-1 rounded border border-red-900/30">
                          <Clock className="w-3 h-3 mr-1" /> {task.deadline}
                        </div>
                        <button 
                          onClick={() => onAddTask(task.desc, selected.project, task.deadline, selected.id)}
                          className="text-xs bg-emerald-600/90 hover:bg-emerald-500 text-white px-3 py-1.5 rounded-lg font-medium transition-all shadow-[0_0_10px_rgba(16,185,129,0.2)]"
                        >
                          加入看板
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-slate-500 font-mono italic p-4 text-center border border-dashed border-slate-700/50 rounded-lg">
                  無偵測到具體行動事項 (No Action Items detected).
                </div>
              )}
            </div>

          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-600 font-mono text-sm">Select an email to analyze</div>
        )}
      </div>
    </div>
  );
}

function ProjectBoardView({ tasks }) {
  return (
    <div className="flex-1 flex flex-col animate-in fade-in duration-300">
      {/* Board Header */}
      <div className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-[#040C1A]/50">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <KanbanSquare className="w-5 h-5 mr-2 text-emerald-500" />
            SSOT 專案看板
          </h2>
          <span className="px-2 py-0.5 bg-slate-800 text-slate-400 border border-slate-700 rounded text-[10px] font-mono">Data Driven</span>
        </div>
      </div>

      {/* Board Columns */}
      <div className="flex-1 overflow-x-auto p-8 flex space-x-6">
        <KanbanColumn title="TO DO (待處理)" tasks={tasks.todo} borderColor="border-slate-700" />
        <KanbanColumn title="IN PROGRESS (進行中)" tasks={tasks.doing} borderColor="border-blue-600" />
        <KanbanColumn title="DONE (已完成)" tasks={tasks.done} borderColor="border-emerald-600" />
      </div>
    </div>
  );
}

function KanbanColumn({ title, tasks, borderColor }) {
  return (
    <div className="w-80 flex flex-col flex-shrink-0">
      <h3 className={`text-xs font-bold text-slate-400 mb-4 uppercase tracking-widest flex items-center justify-between border-t-2 ${borderColor} pt-3`}>
        <span>{title}</span>
        <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full text-[10px]">{tasks.length}</span>
      </h3>
      <div className="space-y-3">
        {tasks.map(task => (
          <div key={task.id} className="bg-[#050B14] border border-slate-800 hover:border-slate-600 p-4 rounded-xl shadow-lg cursor-pointer transition-colors group relative overflow-hidden">
            <div className={`absolute top-0 left-0 bottom-0 w-1 ${borderColor.replace('border-', 'bg-')}`}></div>
            <div className="text-[9px] text-slate-500 font-mono mb-2">{task.project}</div>
            <h4 className="text-sm text-slate-200 font-medium mb-4 leading-snug">{task.title}</h4>
            <div className="flex items-center justify-between mt-auto">
              <span className="text-[9px] text-slate-400 font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 flex items-center truncate max-w-[120px]">
                <Database className="w-2.5 h-2.5 mr-1" /> {task.source.split('-').pop()}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${task.due === 'ASAP' || task.due.includes('08/05') || task.due.includes('08/06') ? 'text-red-400 bg-red-950/30 border border-red-900/30' : 'text-slate-400 bg-slate-800'}`}>
                {task.due}
              </span>
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="border-2 border-dashed border-slate-800 rounded-xl h-24 flex items-center justify-center text-xs text-slate-600 font-mono">Empty Dropzone</div>
        )}
      </div>
    </div>
  );
}

function LedgerView({ logs }) {
  return (
    <div className="flex-1 p-8 overflow-y-auto animate-in fade-in duration-300">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-end justify-between mb-8">
          <div>
            <h2 className="text-2xl font-light text-white tracking-tight flex items-center">
              <Terminal className="w-6 h-6 mr-3 text-emerald-500" />
              JS 引擎時序總帳 <span className="text-sm text-emerald-500 ml-3 font-mono">/ Console Ledger</span>
            </h2>
            <p className="text-xs text-slate-500 mt-2 font-mono">VeritasDataEngine._appendLedger() Memory Logs</p>
          </div>
          <div className="bg-slate-900/80 border border-slate-700 px-3 py-1.5 rounded-lg flex items-center text-xs font-mono text-slate-400">
            <Lock className="w-3.5 h-3.5 mr-2" /> Immutable Stream
          </div>
        </div>

        <div className="relative bg-[#050B14] p-6 rounded-2xl border border-slate-800 shadow-xl">
          <div className="absolute left-[71px] top-6 bottom-6 w-px bg-slate-800"></div>

          <div className="space-y-4 relative">
            {logs.map((log, idx) => (
              <div key={idx} className="flex items-start">
                <div className="w-20 pt-2.5 pr-4 text-right relative z-10">
                  <span className="text-[10px] font-mono text-slate-500 block">{log.time}</span>
                  <div className={`absolute right-[-4.5px] top-3 w-2 h-2 rounded-full border border-[#050B14] ${log.type === 'WARN' ? 'bg-amber-500' : log.type === 'SUCCESS' ? 'bg-emerald-500' : 'bg-blue-500'}`}></div>
                </div>
                <div className="flex-1 bg-slate-900/50 border border-slate-800/80 rounded-lg p-3">
                  <div className="flex items-center space-x-3 mb-1">
                    <span className={`font-mono text-[10px] px-2 py-0.5 rounded border ${log.type === 'SUCCESS' ? 'text-emerald-400 bg-emerald-950/30 border-emerald-900/30' : log.type === 'WARN' ? 'text-amber-400 bg-amber-950/30 border-amber-900/30' : 'text-blue-400 bg-blue-950/30 border-blue-900/30'}`}>
                      {log.event}
                    </span>
                    <span className="text-[9px] text-slate-500 font-mono">[{log.id}]</span>
                  </div>
                  <p className="text-xs text-slate-300 font-mono mt-2">{log.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}