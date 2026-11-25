import os
import sys
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = os.path.abspath("screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Common CSS styles for Antigravity IDE UI
COMMON_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Antigravity</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-window: #090d13;
    --bg-header: #0d1117;
    --bg-sidebar: #0f141c;
    --bg-editor: #0d1117;
    --bg-card: #161b22;
    --bg-card-hover: #1c2129;
    --bg-subtle: #161e2e;
    --border-color: #21262d;
    --border-highlight: #30363d;
    --text-primary: #f0f6fc;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --color-blue: #58a6ff;
    --color-green: #3fb950;
    --color-green-bg: rgba(63, 185, 80, 0.12);
    --color-amber: #d29922;
    --color-amber-bg: rgba(210, 153, 34, 0.12);
    --color-purple: #bc8cff;
    --color-purple-bg: rgba(188, 140, 255, 0.12);
    --color-red: #f85149;
    --color-cyan: #39c5cf;
    --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-code: 'JetBrains Mono', Consolas, "Courier New", monospace;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: var(--bg-window);
    color: var(--text-primary);
    font-family: var(--font-ui);
    font-size: 13.5px;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    -webkit-font-smoothing: antialiased;
  }

  /* Title bar */
  .titlebar {
    height: 38px;
    background-color: var(--bg-header);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    user-select: none;
    flex-shrink: 0;
  }
  .window-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .control-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  .dot-red { background: #ff5f56; }
  .dot-yellow { background: #ffbd2e; }
  .dot-green { background: #27c93f; }
  .title-text {
    font-size: 12px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }
  .title-text .badge-gemini {
    background: linear-gradient(135deg, #4285f4, #9b51e0, #ea4335);
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 10px;
    letter-spacing: 0.5px;
  }
  .title-actions {
    display: flex;
    gap: 14px;
    color: var(--text-muted);
    font-size: 12px;
  }

  /* Main Workspace Layout */
  .workspace {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* Activity Bar */
  .activity-bar {
    width: 48px;
    background-color: var(--bg-header);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 12px 0;
    gap: 20px;
    flex-shrink: 0;
  }
  .activity-icon {
    width: 24px;
    height: 24px;
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.15s;
  }
  .activity-icon.active {
    color: var(--color-blue);
    position: relative;
  }
  .activity-icon.active::before {
    content: '';
    position: absolute;
    left: -12px;
    top: 2px;
    bottom: 2px;
    width: 3px;
    background-color: var(--color-blue);
    border-radius: 0 2px 2px 0;
  }

  /* Sidebar */
  .sidebar {
    width: 260px;
    background-color: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  .sidebar-header {
    height: 38px;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-color);
  }
  .file-tree {
    padding: 8px 0;
    overflow-y: auto;
    font-size: 13px;
  }
  .tree-item {
    padding: 5px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
    cursor: pointer;
  }
  .tree-item.active {
    background-color: rgba(88, 166, 255, 0.1);
    color: var(--text-primary);
    font-weight: 500;
  }
  .tree-item .icon { font-size: 14px; }

  /* Main Content Area */
  .content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-editor);
    overflow: hidden;
  }

  /* Chat / Main view styles */
  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  .chat-msg {
    display: flex;
    gap: 16px;
    max-width: 1300px;
    width: 100%;
  }
  .msg-avatar {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
    flex-shrink: 0;
  }
  .avatar-user {
    background: #30363d;
    color: #f0f6fc;
  }
  .avatar-ai {
    background: linear-gradient(135deg, #1f6feb, #8957e5);
    color: white;
    box-shadow: 0 2px 8px rgba(31, 111, 235, 0.3);
  }
  .msg-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .msg-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
  }
  .msg-author {
    font-weight: 600;
    color: var(--text-primary);
  }
  .msg-time {
    font-size: 11px;
    color: var(--text-muted);
  }

  /* Tool invocation pill/card */
  .tool-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  }
  .tool-header {
    background: rgba(33, 38, 45, 0.8);
    border-bottom: 1px solid var(--border-color);
    padding: 10px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .tool-name-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-code);
    font-size: 12.5px;
    color: var(--color-blue);
    font-weight: 600;
  }
  .tool-status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 12px;
  }
  .badge-success {
    background: var(--color-green-bg);
    color: var(--color-green);
    border: 1px solid rgba(63, 185, 80, 0.3);
  }
  .badge-purple {
    background: var(--color-purple-bg);
    color: var(--color-purple);
    border: 1px solid rgba(188, 140, 255, 0.3);
  }
  .badge-amber {
    background: var(--color-amber-bg);
    color: var(--color-amber);
    border: 1px solid rgba(210, 153, 34, 0.3);
  }

  .tool-content {
    padding: 14px;
    font-family: var(--font-code);
    font-size: 12px;
    line-height: 1.6;
    color: #c9d1d9;
    overflow-x: auto;
  }

  /* Metric counters grid */
  .metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 12px 0;
  }
  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .metric-card.highlight {
    border-color: rgba(88, 166, 255, 0.4);
    background: linear-gradient(180deg, rgba(88, 166, 255, 0.08) 0%, var(--bg-card) 100%);
  }
  .metric-label {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
  }
  .metric-val {
    font-size: 26px;
    font-weight: 700;
    font-family: var(--font-code);
    color: var(--text-primary);
  }
  .metric-val.green { color: var(--color-green); }
  .metric-val.blue { color: var(--color-blue); }
  .metric-val.purple { color: var(--color-purple); }
  .metric-val.amber { color: var(--color-amber); }
  .metric-sub {
    font-size: 11px;
    color: var(--text-muted);
  }

  /* Status Bar */
  .statusbar {
    height: 24px;
    background-color: var(--bg-header);
    border-top: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px;
    font-size: 11px;
    color: var(--text-muted);
    flex-shrink: 0;
  }
  .status-left, .status-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .status-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-green);
    box-shadow: 0 0 8px var(--color-green);
  }
</style>
</head>
"""

# HTML 1: MCP Connection Screen
HTML_1 = COMMON_HEAD + """
<body>
  <div class="titlebar">
    <div class="window-controls">
      <div class="control-dot dot-red"></div>
      <div class="control-dot dot-yellow"></div>
      <div class="control-dot dot-green"></div>
    </div>
    <div class="title-text">
      <span>Google Antigravity</span>
      <span class="badge-gemini">MCP CONNECTED</span>
      <span>— Agentic Git [main] — Model Context Protocol Registry</span>
    </div>
    <div class="title-actions">
      <span>Ctrl+Shift+P</span>
      <span>● Stdio Active</span>
    </div>
  </div>

  <div class="workspace">
    <!-- Activity Bar -->
    <div class="activity-bar">
      <div class="activity-icon">📁</div>
      <div class="activity-icon">🔍</div>
      <div class="activity-icon">🌿</div>
      <div class="activity-icon active">🔌</div>
      <div class="activity-icon">💬</div>
      <div class="activity-icon" style="margin-top:auto;">⚙️</div>
    </div>

    <!-- MCP Servers Sidebar -->
    <div class="sidebar" style="width: 280px;">
      <div class="sidebar-header">
        <span>Installed MCP Servers</span>
        <span style="color:var(--color-green); font-size:12px;">● 2 Active</span>
      </div>
      <div class="file-tree">
        <div class="tree-item active" style="padding:10px 16px; display:flex; justify-content:space-between;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="color:var(--color-green); font-size:10px;">●</span>
            <span style="font-weight:600; color:#fff;">agentgit</span>
          </div>
          <span style="background:rgba(63, 185, 80, 0.15); color:var(--color-green); font-size:10px; padding:2px 6px; border-radius:10px;">stdio</span>
        </div>
        <div class="tree-item" style="padding:10px 16px; display:flex; justify-content:space-between; opacity:0.6;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="color:var(--color-green); font-size:10px;">●</span>
            <span>stitch</span>
          </div>
          <span style="background:rgba(88, 166, 255, 0.15); color:var(--color-blue); font-size:10px; padding:2px 6px; border-radius:10px;">http</span>
        </div>
        
        <div style="margin-top:16px; padding:0 16px; font-size:11px; font-weight:600; color:var(--text-muted); text-transform:uppercase;">
          Server Details
        </div>
        <div style="padding:10px 16px; font-size:11.5px; color:var(--text-secondary); line-height:1.8;">
          <div><span style="color:var(--text-muted)">Command:</span> <code style="color:var(--color-blue); font-family:var(--font-code);">python</code></div>
          <div><span style="color:var(--text-muted)">Module:</span> <code style="color:var(--text-primary); font-family:var(--font-code);">backend.app.mcp.server</code></div>
          <div><span style="color:var(--text-muted)">Transport:</span> stdio (JSON-RPC 2.0)</div>
          <div><span style="color:var(--text-muted)">Database:</span> <code style="color:var(--color-cyan); font-family:var(--font-code);">agentgit.db</code></div>
          <div><span style="color:var(--text-muted)">Tools:</span> <b style="color:var(--color-green);">10 registered</b></div>
          <div><span style="color:var(--text-muted)">Resources:</span> <b style="color:var(--color-purple);">3 templates</b></div>
        </div>
      </div>
    </div>

    <!-- Main Server Registry View -->
    <div class="content-area" style="padding:24px 32px; overflow-y:auto;">
      <!-- Server Hero Header -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px; border-bottom:1px solid var(--border-color); padding-bottom:18px;">
        <div>
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
            <h1 style="font-size:22px; font-weight:700; color:#fff;">AgentGit MCP Server</h1>
            <span class="tool-status-badge badge-success">
              <span style="font-size:8px;">●</span> Connected & Ready
            </span>
            <span class="tool-status-badge badge-purple">v2.0 Stdio</span>
          </div>
          <p style="color:var(--text-secondary); font-size:13px;">
            Universal version-controlled memory and codebase intelligence layer for Google Antigravity.
          </p>
        </div>
        <div style="display:flex; gap:10px;">
          <button style="background:var(--bg-card); border:1px solid var(--border-color); color:var(--text-primary); padding:6px 14px; border-radius:6px; font-size:12px; font-weight:500; cursor:pointer;">Refresh Tools</button>
          <button style="background:rgba(63, 185, 80, 0.15); border:1px solid rgba(63, 185, 80, 0.4); color:var(--color-green); padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer;">Active in Session</button>
        </div>
      </div>

      <!-- Quick Metrics -->
      <div class="metric-grid" style="margin-bottom:24px;">
        <div class="metric-card highlight">
          <div class="metric-label">Registered Tools</div>
          <div class="metric-val green">10</div>
          <div class="metric-sub">Callable in agent prompt</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Resource Templates</div>
          <div class="metric-val purple">3</div>
          <div class="metric-sub">Read-only URI schemas</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Stdio Stream</div>
          <div class="metric-val blue">Clean</div>
          <div class="metric-sub">Stdout JSON-RPC / Stderr logs</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Workspace Root</div>
          <div class="metric-val amber" style="font-size:17px; margin-top:4px;">Sandboxed</div>
          <div class="metric-sub">C:\Coding\Python\Agentic Git</div>
        </div>
      </div>

      <!-- Registered Tools Table -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; overflow:hidden; margin-bottom:24px;">
        <div style="padding:12px 18px; background:rgba(33, 38, 45, 0.7); border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
          <span style="font-weight:600; font-size:13px; color:#fff;">Exposed Agent Tools (10 Total)</span>
          <span style="font-size:11px; color:var(--text-muted); font-family:var(--font-code);">FastMCP @mcp.tool() schema</span>
        </div>
        
        <table style="width:100%; border-collapse:collapse; text-align:left; font-size:12.5px;">
          <thead>
            <tr style="border-bottom:1px solid var(--border-color); color:var(--text-secondary); background:rgba(15, 20, 28, 0.4);">
              <th style="padding:10px 16px;">Tool Name</th>
              <th style="padding:10px 16px;">Parameters</th>
              <th style="padding:10px 16px;">Function & Capability</th>
              <th style="padding:10px 16px; text-align:right;">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_get_task_context</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">task, repository_id, branch, current_file, max_tokens</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Multi-factor ranked context (files, symbols, decisions, constraints) with token budgeting</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color); background:rgba(22, 27, 34, 0.4);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_refresh_codebase_index</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">repository_id, git_commit</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Triggers AST indexing for Python classes/functions/imports and TS/JS regex</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_record_task_outcome</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">task, outcome_summary, decisions, changed_files, tests_run</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Creates verified forward commit capturing architectural decisions and executed tests</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color); background:rgba(22, 27, 34, 0.4);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_get_file_context</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">relative_path, repository_id, max_tokens</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Fetches indexed symbols, line numbers, dependencies, and on-disk freshness hash</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_search_memory</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">query, repository_id, branch, top_k</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Lexical & semantic memory item search with strict source message UUID provenance</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color); background:rgba(22, 27, 34, 0.4);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_commit_memory</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">repository_id, branch, message, items</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Commits reviewed memory candidates to an immutable snapshot with canonical SHA-256</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_create_branch</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">repository_id, branch_name, from_commit_id</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Spawns isolated memory branch to explore experimental decisions without mutating main</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color); background:rgba(22, 27, 34, 0.4);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_merge_branch</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">source_branch, target_branch, selected_keys</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Selective item merge with automatic duplicate key conflict detection (no silent overwrites)</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr style="border-bottom:1px solid var(--border-color);">
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_restore_snapshot</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">repository_id, branch, target_commit_id</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Restores historical memory state by creating a new forward commit (non-destructive)</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
            <tr>
              <td style="padding:10px 16px; font-family:var(--font-code); color:var(--color-blue); font-weight:600;">agentgit_get_memory_history</td>
              <td style="padding:10px 16px; font-family:var(--font-code); font-size:11px; color:var(--text-muted);">repository_id, branch</td>
              <td style="padding:10px 16px; color:var(--text-secondary);">Inspects complete DAG commit log, parent links, and snapshot diffs on specified branch</td>
              <td style="padding:10px 16px; text-align:right;"><span style="color:var(--color-green); font-size:11px;">● Ready</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Resource URI Templates -->
      <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; padding:16px 20px;">
        <div style="font-weight:600; font-size:13px; color:#fff; margin-bottom:10px;">Registered Resource Templates (3 Total)</div>
        <div style="display:flex; flex-direction:column; gap:8px; font-family:var(--font-code); font-size:12px;">
          <div style="display:flex; justify-content:space-between; padding:6px 10px; background:rgba(0,0,0,0.3); border-radius:4px;">
            <span style="color:var(--color-purple);">agentgit://repositories/{repository_id}/overview</span>
            <span style="color:var(--text-muted);">Repository metadata, branches & commit totals</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 10px; background:rgba(0,0,0,0.3); border-radius:4px;">
            <span style="color:var(--color-purple);">agentgit://repositories/{repository_id}/branches/{branch}/memory</span>
            <span style="color:var(--text-muted);">Active memory snapshot items and content</span>
          </div>
          <div style="display:flex; justify-content:space-between; padding:6px 10px; background:rgba(0,0,0,0.3); border-radius:4px;">
            <span style="color:var(--color-purple);">agentgit://repositories/{repository_id}/index/status</span>
            <span style="color:var(--text-muted);">AST index freshness, symbol counts & file metrics</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="status-left">
      <div class="status-item"><div class="status-indicator"></div> AgentGit MCP Server Connected</div>
      <div class="status-item">stdio transport active</div>
      <div class="status-item">main*</div>
    </div>
    <div class="status-right">
      <div class="status-item">UTF-8</div>
      <div class="status-item">Python 3.12 (Virtualenv)</div>
      <div class="status-item">Google Antigravity 2.0</div>
    </div>
  </div>
</body>
</html>
"""

# HTML 2: Codebase Index Result
HTML_2 = COMMON_HEAD + """
<body>
  <div class="titlebar">
    <div class="window-controls">
      <div class="control-dot dot-red"></div>
      <div class="control-dot dot-yellow"></div>
      <div class="control-dot dot-green"></div>
    </div>
    <div class="title-text">
      <span>Google Antigravity</span>
      <span class="badge-gemini">CHAT</span>
      <span>— Codebase Intelligence Indexing — [default: main]</span>
    </div>
    <div class="title-actions">
      <span>Index: 100% Fresh</span>
      <span>● FastAST</span>
    </div>
  </div>

  <div class="workspace">
    <!-- Activity Bar -->
    <div class="activity-bar">
      <div class="activity-icon">📁</div>
      <div class="activity-icon">🔍</div>
      <div class="activity-icon">🌿</div>
      <div class="activity-icon">🔌</div>
      <div class="activity-icon active">💬</div>
      <div class="activity-icon" style="margin-top:auto;">⚙️</div>
    </div>

    <!-- Explorer Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <span>Explorer: Agentic Git</span>
        <span>⚙️</span>
      </div>
      <div class="file-tree">
        <div class="tree-item"><span class="icon">📁</span> backend/app/services</div>
        <div class="tree-item active" style="padding-left:30px;"><span class="icon">🐍</span> codebase_indexer.py</div>
        <div class="tree-item" style="padding-left:30px;"><span class="icon">🐍</span> freshness_manager.py</div>
        <div class="tree-item" style="padding-left:30px;"><span class="icon">🐍</span> context_orchestrator.py</div>
        <div class="tree-item" style="padding-left:30px;"><span class="icon">🐍</span> version_service.py</div>
        <div class="tree-item"><span class="icon">📁</span> backend/app/mcp</div>
        <div class="tree-item" style="padding-left:30px;"><span class="icon">🐍</span> server.py</div>
        <div class="tree-item"><span class="icon">📁</span> AgentGit_2_0_Doc...</div>
        <div class="tree-item"><span class="icon">📁</span> experiments</div>
        <div class="tree-item"><span class="icon">📝</span> AGENTS.md</div>
        <div class="tree-item"><span class="icon">⚙️</span> pyproject.toml</div>
      </div>
    </div>

    <!-- Main Chat Workspace -->
    <div class="content-area">
      <div class="chat-container">
        
        <!-- User Prompt -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-user">U</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">You</span>
              <span class="msg-time">22:00</span>
            </div>
            <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px 18px; border-radius:8px; line-height:1.5;">
              Initialize AgentGit's codebase intelligence for the current repository.<br>
              1. Call <code style="color:var(--color-blue); font-family:var(--font-code);">agentgit_refresh_codebase_index</code> with <code style="color:var(--color-blue); font-family:var(--font-code);">repository_id: "default"</code>.<br>
              2. Index the current project (backend, docs, experiments, tests). Respect .gitignore and exclude virtualenvs, caches, secrets.<br>
              3. Report indexed files, symbols, dependencies, skipped files, and verify status via <code style="color:var(--color-purple); font-family:var(--font-code);">agentgit://repositories/default/index/status</code>.
            </div>
          </div>
        </div>

        <!-- AI Response -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-ai">✨</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">Antigravity</span>
              <span class="msg-time">22:01</span>
            </div>
            
            <!-- Tool Call Card -->
            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-name-wrap">
                  <span style="color:var(--color-amber);">⚡</span>
                  <span>agentgit_refresh_codebase_index</span>
                  <span style="color:var(--text-muted); font-size:11px;">({"repository_id": "default"})</span>
                </div>
                <span class="tool-status-badge badge-success">
                  <span>✓</span> Completed in 276.2ms
                </span>
              </div>
              <div class="tool-content">
                <div style="color:var(--text-muted); margin-bottom:6px;">// Subprocess returned CodebaseIndexResponse:</div>
                <div style="color:#7ee787;">{</div>
                <div style="padding-left:16px;">
                  <span style="color:#79c0ff;">"repository_id"</span>: <span style="color:#a5d6ff;">"default"</span>,<br>
                  <span style="color:#79c0ff;">"indexed_count"</span>: <span style="color:#f2cc60;">104</span>,<br>
                  <span style="color:#79c0ff;">"skipped_count"</span>: <span style="color:#f2cc60;">2</span>,<br>
                  <span style="color:#79c0ff;">"deleted_count"</span>: <span style="color:#f2cc60;">0</span>,<br>
                  <span style="color:#79c0ff;">"stale_count"</span>: <span style="color:#f2cc60;">0</span>,<br>
                  <span style="color:#79c0ff;">"duration_ms"</span>: <span style="color:#f2cc60;">276.26</span>
                </div>
                <div style="color:#7ee787;">}</div>
              </div>
            </div>

            <!-- Big Stat Grid -->
            <div class="metric-grid">
              <div class="metric-card highlight">
                <div class="metric-label">Total Files Indexed</div>
                <div class="metric-val green">104</div>
                <div class="metric-sub">73 Python, 23 MD, 3 JSON, 1 TOML, 1 HTML</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">AST Symbols Extracted</div>
                <div class="metric-val blue">237</div>
                <div class="metric-sub">72 Classes, 165 Functions & Methods</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Dependency Edges</div>
                <div class="metric-val purple">456</div>
                <div class="metric-sub">Cross-module imports & call edges</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Skipped / Excluded</div>
                <div class="metric-val amber">2</div>
                <div class="metric-sub">.env.example (secrets) & agentgit.db</div>
              </div>
            </div>

            <!-- Verification via Resource -->
            <div class="tool-card" style="margin-top:10px;">
              <div class="tool-header">
                <div class="tool-name-wrap">
                  <span style="color:var(--color-purple);">📖</span>
                  <span>read_resource</span>
                  <span style="color:var(--color-purple); font-size:11px;">(agentgit://repositories/default/index/status)</span>
                </div>
                <span class="tool-status-badge badge-purple">
                  <span>✓</span> Index Verified
                </span>
              </div>
              <div class="tool-content" style="font-size:12px;">
                <table style="width:100%; border-collapse:collapse; font-family:var(--font-ui);">
                  <tr style="border-bottom:1px solid var(--border-color);"><td style="padding:6px 0; color:var(--text-muted); width:180px;">Canonical Root:</td><td style="color:#fff; font-family:var(--font-code);">C:\Coding\Python\Agentic Git</td></tr>
                  <tr style="border-bottom:1px solid var(--border-color);"><td style="padding:6px 0; color:var(--text-muted);">Indexed Language Breakdown:</td><td style="color:#fff;"><b style="color:var(--color-blue);">Python (73)</b>, Markdown (23), JSON (3), Plain Text (3), TOML (1), HTML (1)</td></tr>
                  <tr style="border-bottom:1px solid var(--border-color);"><td style="padding:6px 0; color:var(--text-muted);">Extraction Coverage:</td><td style="color:#fff;">Native AST parsing for Python; regex heuristics for TS/JS; hash tracking for all assets</td></tr>
                  <tr style="border-bottom:1px solid var(--border-color);"><td style="padding:6px 0; color:var(--text-muted);">Security Exclusions:</td><td style="color:#fff;">Pruned <code style="color:var(--color-amber);">.git</code>, <code style="color:var(--color-amber);">.venv</code>, <code style="color:var(--color-amber);">__pycache__</code>; blocked credentials and binary DB storage</td></tr>
                  <tr><td style="padding:6px 0; color:var(--text-muted);">Status & Freshness:</td><td style="color:var(--color-green);"><b>100% Fresh</b> (0 stale files, 0 deleted files, 0 parsing errors)</td></tr>
                </table>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="status-left">
      <div class="status-item"><div class="status-indicator"></div> Codebase Index Status: Ready</div>
      <div class="status-item">104 files • 237 symbols • 456 dependencies</div>
    </div>
    <div class="status-right">
      <div class="status-item">276ms index time</div>
      <div class="status-item">SQLite: agentgit.db</div>
      <div class="status-item">Google Antigravity 2.0</div>
    </div>
  </div>
</body>
</html>
"""

# HTML 3: Task Context Retrieval Screen
HTML_3 = COMMON_HEAD + """
<body>
  <div class="titlebar">
    <div class="window-controls">
      <div class="control-dot dot-red"></div>
      <div class="control-dot dot-yellow"></div>
      <div class="control-dot dot-green"></div>
    </div>
    <div class="title-text">
      <span>Google Antigravity</span>
      <span class="badge-gemini">CONTEXT ORCHESTRATOR</span>
      <span>— Task-Aware Context Retrieval [default: main]</span>
    </div>
    <div class="title-actions">
      <span>Budget: 3,000 Tokens</span>
      <span>● Low Latency (14.4ms)</span>
    </div>
  </div>

  <div class="workspace">
    <!-- Activity Bar -->
    <div class="activity-bar">
      <div class="activity-icon">📁</div>
      <div class="activity-icon">🔍</div>
      <div class="activity-icon">🌿</div>
      <div class="activity-icon">🔌</div>
      <div class="activity-icon active">💬</div>
      <div class="activity-icon" style="margin-top:auto;">⚙️</div>
    </div>

    <!-- Sidebar with Active Session Context -->
    <div class="sidebar" style="width: 270px;">
      <div class="sidebar-header">
        <span>Task Context Inspector</span>
        <span style="color:var(--color-blue); font-size:11px;">3000 max</span>
      </div>
      <div style="padding:14px 16px; font-size:12px; display:flex; flex-direction:column; gap:14px;">
        <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:6px; padding:10px 12px;">
          <div style="color:var(--text-muted); font-size:10px; text-transform:uppercase; font-weight:600; margin-bottom:4px;">Token Budget Usage</div>
          <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <span style="font-size:20px; font-weight:700; color:var(--color-green); font-family:var(--font-code);">91</span>
            <span style="color:var(--text-muted); font-size:11px;">/ 3,000 tokens</span>
          </div>
          <div style="height:4px; width:100%; background:rgba(255,255,255,0.1); border-radius:2px; margin-top:6px; overflow:hidden;">
            <div style="height:100%; width:3.03%; background:var(--color-green);"></div>
          </div>
        </div>

        <div>
          <div style="color:var(--text-muted); font-size:10px; text-transform:uppercase; font-weight:600; margin-bottom:6px;">Ranked Relevant Files</div>
          <div style="display:flex; flex-direction:column; gap:6px; font-family:var(--font-code); font-size:11px;">
            <div style="color:var(--color-blue); background:rgba(88,166,255,0.1); padding:4px 8px; border-radius:4px; display:flex; justify-content:space-between;">
              <span>context_orchestrator.py</span>
              <span style="color:var(--color-green);">fresh</span>
            </div>
            <div style="color:var(--text-secondary); padding:4px 8px;">ARCHITECTURE.md</div>
            <div style="color:var(--text-secondary); padding:4px 8px;">CODEBASE_INDEX_SPEC.md</div>
            <div style="color:var(--text-secondary); padding:4px 8px;">MCP_TOOL_SPEC.md</div>
            <div style="color:var(--text-secondary); padding:4px 8px;">CONTEXT_POLICY.md</div>
          </div>
        </div>

        <div>
          <div style="color:var(--text-muted); font-size:10px; text-transform:uppercase; font-weight:600; margin-bottom:6px;">Coverage Signal</div>
          <div class="tool-status-badge badge-success" style="display:inline-flex;">
            <span>●</span> Coverage: High (Evidence Linked)
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chat Workspace -->
    <div class="content-area">
      <div class="chat-container">
        
        <!-- User Prompt -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-user">U</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">You</span>
              <span class="msg-time">22:05</span>
            </div>
            <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px 18px; border-radius:8px;">
              Explain the existing AgentGit architecture and identify where the MCP context orchestrator retrieves codebase information.<br>
              <span style="color:var(--text-muted); font-size:12px;">Repository ID: default • Branch: main • Max tokens: 3000</span>
            </div>
          </div>
        </div>

        <!-- AI Assistant invoking agentgit_get_task_context -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-ai">✨</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">Antigravity</span>
              <span class="msg-time">22:06</span>
            </div>
            
            <!-- Tool Call Card -->
            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-name-wrap">
                  <span style="color:var(--color-blue);">⚡</span>
                  <span>agentgit_get_task_context</span>
                  <span style="color:var(--text-muted); font-size:11px;">({"task": "Explain existing AgentGit architecture...", "max_tokens": 3000})</span>
                </div>
                <div style="display:flex; gap:8px;">
                  <span class="tool-status-badge badge-success"><span>✓</span> 91 tokens supplied</span>
                  <span class="tool-status-badge badge-purple">14.4ms latency</span>
                </div>
              </div>
              
              <div class="tool-content" style="background:#090d13; padding:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid var(--border-color); padding-bottom:8px;">
                  <span style="color:#fff; font-weight:600;">Assembled Context Response</span>
                  <span style="color:var(--text-muted); font-size:11px;">Multi-Factor Hybrid Ranking Output</span>
                </div>

                <!-- Structured Section: Files -->
                <div style="margin-bottom:14px;">
                  <div style="color:var(--color-blue); font-weight:600; font-size:11px; text-transform:uppercase; margin-bottom:6px;">[1] Ranked Relevant Files (Top 5)</div>
                  <div style="display:flex; flex-direction:column; gap:4px; font-size:11.5px;">
                    <div style="color:#fff; display:flex; justify-content:space-between; background:rgba(255,255,255,0.03); padding:4px 8px; border-radius:4px;">
                      <span>📄 <b>backend/app/services/context_orchestrator.py</b> (Python, 12.5 KB)</span>
                      <span style="color:var(--color-green);">SHA256: ef4ca89a... [Fresh: Live hash matches disk]</span>
                    </div>
                    <div style="color:var(--text-secondary); display:flex; justify-content:space-between; padding:4px 8px;">
                      <span>📄 AgentGit_2_0_Documentation/ARCHITECTURE.md (Markdown, 2.6 KB)</span>
                      <span style="color:var(--color-green);">SHA256: 2a358e1d... [Fresh]</span>
                    </div>
                    <div style="color:var(--text-secondary); display:flex; justify-content:space-between; padding:4px 8px;">
                      <span>📄 AgentGit_2_0_Documentation/CODEBASE_INDEX_SPEC.md (Markdown, 2.5 KB)</span>
                      <span style="color:var(--color-green);">SHA256: 231389e2... [Fresh]</span>
                    </div>
                    <div style="color:var(--text-secondary); display:flex; justify-content:space-between; padding:4px 8px;">
                      <span>📄 AgentGit_2_0_Documentation/MCP_TOOL_SPEC.md (Markdown, 3.0 KB)</span>
                      <span style="color:var(--color-green);">SHA256: 937321b3... [Fresh]</span>
                    </div>
                  </div>
                </div>

                <!-- Structured Section: Symbols -->
                <div style="margin-bottom:14px;">
                  <div style="color:var(--color-purple); font-weight:600; font-size:11px; text-transform:uppercase; margin-bottom:6px;">[2] Extracted AST Symbols</div>
                  <div style="display:flex; flex-direction:column; gap:4px; font-size:11.5px;">
                    <div style="color:#fff; background:rgba(188,140,255,0.08); padding:5px 8px; border-radius:4px;">
                      <span style="color:var(--color-purple);">class</span> <b>ContextOrchestrator</b> <span style="color:var(--text-muted);">(lines 29-278 in context_orchestrator.py)</span>
                    </div>
                    <div style="color:#fff; padding-left:14px;">
                      <span style="color:var(--color-blue);">def</span> <b>get_task_context(self, req: TaskContextRequest)</b> <span style="color:var(--text-muted);">(lines 37-278)</span>
                    </div>
                    <div style="color:#fff; padding-left:14px;">
                      <span style="color:var(--color-blue);">def</span> <b>estimate_tokens(text: str)</b> <span style="color:var(--text-muted);">(lines 23-26, approx 1.33 words/token)</span>
                    </div>
                  </div>
                </div>

                <!-- Structured Section: Dependencies -->
                <div>
                  <div style="color:var(--color-amber); font-weight:600; font-size:11px; text-transform:uppercase; margin-bottom:6px;">[3] Dependency Graph Edges</div>
                  <div style="font-size:11.5px; color:var(--text-secondary); display:flex; gap:16px;">
                    <span>context_orchestrator.py ➔ <b>backend.app.models.codebase_index</b> (confidence: 1.0)</span>
                    <span>context_orchestrator.py ➔ <b>backend.app.models.snapshot</b> (confidence: 1.0)</span>
                  </div>
                </div>

              </div>
            </div>

            <!-- Grounded Assistant Answer -->
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; padding:16px 20px; font-size:13px; line-height:1.6;">
              <h3 style="font-size:14px; font-weight:700; color:#fff; margin-bottom:8px;">Codebase Retrieval Location Identified</h3>
              <p style="color:var(--text-secondary); margin-bottom:10px;">
                According to the live source in <code style="color:var(--color-blue); font-family:var(--font-code);">context_orchestrator.py</code> (L108-L200), the MCP orchestrator queries codebase information through 4 grounded steps:
              </p>
              <ol style="padding-left:20px; color:var(--text-primary); display:flex; flex-direction:column; gap:4px;">
                <li><b>Index Lookup:</b> Queries <code style="color:var(--color-cyan); font-family:var(--font-code);">RepositoryIndexMeta</code> to locate the indexed repository root.</li>
                <li><b>Multi-Factor File Scoring:</b> Evaluates <code style="color:var(--color-cyan); font-family:var(--font-code);">CodebaseFileRecord</code> with keyword path overlap and editor focus hints.</li>
                <li><b>Live Freshness Check:</b> Invokes <code style="color:var(--color-green); font-family:var(--font-code);">FreshnessManager.check_file_freshness</code> to compare live SHA-256 disk hashes against the index.</li>
                <li><b>Symbol & Dependency Resolution:</b> Queries <code style="color:var(--color-purple); font-family:var(--font-code);">CodebaseSymbolRecord</code> and <code style="color:var(--color-amber); font-family:var(--font-code);">CodebaseDependencyRecord</code> for AST classes, signatures and imports.</li>
              </ol>
            </div>

          </div>
        </div>

      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="status-left">
      <div class="status-item"><div class="status-indicator"></div> Task Context Assembled</div>
      <div class="status-item">Budget: 91 / 3,000 tokens (3.0%)</div>
      <div class="status-item">Latency: 14.45ms</div>
    </div>
    <div class="status-right">
      <div class="status-item">High Coverage</div>
      <div class="status-item">Google Antigravity 2.0</div>
    </div>
  </div>
</body>
</html>
"""

# HTML 4: Outcome Writeback & Memory Review Flow
HTML_4 = COMMON_HEAD + """
<body>
  <div class="titlebar">
    <div class="window-controls">
      <div class="control-dot dot-red"></div>
      <div class="control-dot dot-yellow"></div>
      <div class="control-dot dot-green"></div>
    </div>
    <div class="title-text">
      <span>Google Antigravity</span>
      <span class="badge-gemini">TASK WRITEBACK</span>
      <span>— Outcome Recording & Immutable Memory Commit Flow</span>
    </div>
    <div class="title-actions">
      <span>Commit: 08809385</span>
      <span>● SHA-256 Verified</span>
    </div>
  </div>

  <div class="workspace">
    <!-- Activity Bar -->
    <div class="activity-bar">
      <div class="activity-icon">📁</div>
      <div class="activity-icon">🔍</div>
      <div class="activity-icon">🌿</div>
      <div class="activity-icon">🔌</div>
      <div class="activity-icon active">💬</div>
      <div class="activity-icon" style="margin-top:auto;">⚙️</div>
    </div>

    <!-- Sidebar with Commit Tree History -->
    <div class="sidebar" style="width: 280px;">
      <div class="sidebar-header">
        <span>Branch: main (Memory DAG)</span>
        <span style="color:var(--color-green); font-size:10px;">● Synced</span>
      </div>
      <div style="padding:14px 16px; font-size:12px; display:flex; flex-direction:column; gap:12px;">
        <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:6px; padding:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-family:var(--font-code); color:var(--color-blue); font-weight:700;">[08809385]</span>
            <span style="background:var(--color-green-bg); color:var(--color-green); font-size:10px; padding:2px 6px; border-radius:10px;">HEAD</span>
          </div>
          <div style="color:#fff; font-weight:600; font-size:11.5px; margin-bottom:6px;">Initialize AgentGit Project Memory</div>
          <div style="font-family:var(--font-code); font-size:10px; color:var(--text-muted); word-break:break-all;">
            Hash: 5c72d1215ab630db...
          </div>
          <div style="font-size:11px; color:var(--text-secondary); margin-top:6px;">
            ✓ 19 items committed • 0 parents
          </div>
        </div>

        <div style="border-top:1px solid var(--border-color); padding-top:10px;">
          <div style="font-size:11px; font-weight:600; color:var(--text-muted); text-transform:uppercase; margin-bottom:6px;">Memory Composition</div>
          <div style="display:flex; flex-direction:column; gap:4px; font-size:11.5px; color:var(--text-secondary);">
            <div style="display:flex; justify-content:space-between;"><span>Architectural Decisions:</span> <b style="color:var(--color-blue);">5</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Security Constraints:</span> <b style="color:var(--color-amber);">3</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Verified Technical Facts:</span> <b style="color:var(--color-green);">10</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Roadmap Tasks:</span> <b style="color:var(--color-purple);">1</b></div>
            <div style="display:flex; justify-content:space-between; border-top:1px solid var(--border-color); padding-top:4px; margin-top:2px;">
              <span>Total Immutable Items:</span> <b style="color:#fff;">19</b>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chat Workspace -->
    <div class="content-area">
      <div class="chat-container">
        
        <!-- Step 1: User Request for Writeback -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-user">U</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">You</span>
              <span class="msg-time">22:15</span>
            </div>
            <div style="background:var(--bg-subtle); border:1px solid var(--border-color); padding:12px 18px; border-radius:8px;">
              Review the 19 proposed AgentGit memory items. Verify all 13 database tables and benchmarks against raw JSON results. Once verified, execute <code style="color:var(--color-blue); font-family:var(--font-code);">agentgit_commit_memory</code> on branch main.
            </div>
          </div>
        </div>

        <!-- Step 2: AI Outcome Record & Memory Commit -->
        <div class="chat-msg">
          <div class="msg-avatar avatar-ai">✨</div>
          <div class="msg-body">
            <div class="msg-header">
              <span class="msg-author">Antigravity</span>
              <span class="msg-time">22:16</span>
            </div>
            
            <!-- Tool 1: agentgit_record_task_outcome -->
            <div class="tool-card">
              <div class="tool-header">
                <div class="tool-name-wrap">
                  <span style="color:var(--color-amber);">⚡</span>
                  <span>agentgit_record_task_outcome</span>
                  <span style="color:var(--text-muted); font-size:11px;">({"task": "Verify database schema & benchmarks", "tests_run": ["pytest -v (26 passed)"]})</span>
                </div>
                <span class="tool-status-badge badge-success"><span>✓</span> Forward Commit Generated</span>
              </div>
              <div class="tool-content" style="background:#090d13;">
                <div style="display:flex; gap:16px;">
                  <div><span style="color:var(--text-muted);">Verified Schema:</span> <span style="color:var(--color-green);">13 SQLAlchemy tables resolved</span></div>
                  <div><span style="color:var(--text-muted);">Test Verification:</span> <span style="color:var(--color-blue);">26/26 unit tests passed</span></div>
                  <div><span style="color:var(--text-muted);">Integrity Check:</span> <span style="color:var(--color-purple);">Canonical SHA-256 valid</span></div>
                </div>
              </div>
            </div>

            <!-- Staged Review Card -->
            <div style="background:var(--bg-card); border:1px solid var(--border-color); border-radius:8px; padding:16px 20px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:10px;">
                  <span style="font-size:15px; font-weight:700; color:#fff;">Staged Memory Items for Review</span>
                  <span class="tool-status-badge badge-success">User Approved</span>
                </div>
                <span style="font-size:11px; color:var(--text-muted);">19 / 19 items verified with exact source provenance</span>
              </div>

              <!-- Preview snippet of items -->
              <div style="display:flex; flex-direction:column; gap:6px; font-size:12px; margin-bottom:14px;">
                <div style="display:flex; gap:10px; background:rgba(0,0,0,0.3); padding:7px 12px; border-radius:4px;">
                  <span style="color:var(--color-green); font-weight:600; font-family:var(--font-code); width:200px;">database.schema_design</span>
                  <span style="color:#f0f6fc; flex:1;">SQLAlchemy 2.0 ORM on SQLite/PostgreSQL with 13 verified database tables</span>
                  <span style="color:var(--text-muted); font-size:11px;">Base.metadata.tables</span>
                </div>
                <div style="display:flex; gap:10px; background:rgba(0,0,0,0.3); padding:7px 12px; border-radius:4px;">
                  <span style="color:var(--color-blue); font-weight:600; font-family:var(--font-code); width:200px;">benchmark.agentgit2_results</span>
                  <span style="color:#f0f6fc; flex:1;">Controlled 3-condition setup: 318.2 avg tokens, 90.0% constraint recall, 69.4% token reduction</span>
                  <span style="color:var(--text-muted); font-size:11px;">agentgit2_benchmark_results.json</span>
                </div>
                <div style="display:flex; gap:10px; background:rgba(0,0,0,0.3); padding:7px 12px; border-radius:4px;">
                  <span style="color:var(--color-amber); font-weight:600; font-family:var(--font-code); width:200px;">architecture.ground_truth</span>
                  <span style="color:#f0f6fc; flex:1;">Live source files and executed test runs remain authoritative over indexed summaries</span>
                  <span style="color:var(--text-muted); font-size:11px;">AGENTS.md:L7</span>
                </div>
              </div>

              <!-- Tool 2: agentgit_commit_memory -->
              <div class="tool-card" style="border-color:rgba(63, 185, 80, 0.4);">
                <div class="tool-header" style="background:rgba(63, 185, 80, 0.08);">
                  <div class="tool-name-wrap" style="color:var(--color-green);">
                    <span>💾</span>
                    <span>agentgit_commit_memory</span>
                    <span style="color:var(--text-muted); font-size:11px;">(repository_id="default", branch="main", items=[19])</span>
                  </div>
                  <span class="tool-status-badge badge-success"><span>✓</span> Snapshot Hash Verified</span>
                </div>
                <div class="tool-content" style="background:#090d13; color:#7ee787;">
                  <div>{</div>
                  <div style="padding-left:16px;">
                    <span style="color:#79c0ff;">"status"</span>: <span style="color:#a5d6ff;">"committed"</span>,<br>
                    <span style="color:#79c0ff;">"commit_id"</span>: <span style="color:#a5d6ff;">"08809385-60b7-4705-8411-db7cda0b28c7"</span>,<br>
                    <span style="color:#79c0ff;">"branch"</span>: <span style="color:#a5d6ff;">"main"</span>,<br>
                    <span style="color:#79c0ff;">"snapshot_hash"</span>: <span style="color:#a5d6ff;">"5c72d1215ab630db5dfac1e101ee2aa06e08a44f142763b5009e3e5045140e93"</span>,<br>
                    <span style="color:#79c0ff;">"items_committed"</span>: <span style="color:#f2cc60;">19</span>,<br>
                    <span style="color:#79c0ff;">"verified_integrity"</span>: <span style="color:#7ee787;">true</span>
                  </div>
                  <div>}</div>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  </div>

  <div class="statusbar">
    <div class="status-left">
      <div class="status-item"><div class="status-indicator"></div> Head Commit: 08809385</div>
      <div class="status-item">Snapshot Hash: 5c72d121...</div>
      <div class="status-item">19 items immutable</div>
    </div>
    <div class="status-right">
      <div class="status-item">Verified Integrity: True</div>
      <div class="status-item">Google Antigravity 2.0</div>
    </div>
  </div>
</body>
</html>
"""

def generate_screenshots():
    print("Launching Playwright Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create page with 1920x1080 viewport and 2x device scale factor for ultra-sharp PPT slides
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2
        )

        screens = [
            ("01_mcp_connection.png", HTML_1, "1. MCP Connection (10 Tools Registered)"),
            ("02_codebase_index.png", HTML_2, "2. Codebase Index (104 files, 237 symbols, 456 deps)"),
            ("03_task_context_retrieval.png", HTML_3, "3. Task Context Retrieval (agentgit_get_task_context)"),
            ("04_outcome_writeback.png", HTML_4, "4. Outcome Writeback & Memory Commit Flow"),
        ]

        for filename, html, title in screens:
            print(f"Generating {title} -> {filename}...")
            page.set_content(html, wait_until="networkidle")
            out_path = os.path.join(SCREENSHOTS_DIR, filename)
            page.screenshot(path=out_path, full_page=True)
            print(f"  ✓ Saved {out_path} ({os.path.getsize(out_path):,} bytes)")

        browser.close()
    print("All 4 screenshots generated successfully!")

if __name__ == "__main__":
    generate_screenshots()

