# Setup Guide — Studio Vault + Claude Code

Step-by-step setup. ~30-60 minutes for first time.

---

## Prerequisites

- [ ] **macOS, Windows, or Linux** computer
- [ ] **Claude Pro or Max subscription** (Pro is fine for starting — ~$20/month)
- [ ] **Node.js installed** (Claude Code needs this) — check with `node --version` in terminal
- [ ] **VS Code** installed
- [ ] **Obsidian** installed (free)

If you're missing Node.js: download from https://nodejs.org (LTS version)

---

## Step 1 — Place the vault

Pick a permanent location. Recommended:

- macOS / Linux: `~/Documents/Studio-Vault/`
- Windows: `C:\Users\YourName\Documents\Studio-Vault\`

Move the entire `studio-vault` folder there.

---

## Step 2 — Open in Obsidian (browsing/editing)

1. Open Obsidian
2. Click **"Open folder as vault"**
3. Select your `Studio-Vault` folder
4. Trust the vault when prompted
5. (Recommended) Install Obsidian community plugins:
   - **Templater** — auto-fill date/time in templates
   - **Dataview** — query notes like a database
   - **Excalidraw** — sketch zoning ideas inline

---

## Step 3 — Install Claude Code

Open Terminal (macOS/Linux) or PowerShell (Windows):

```bash
npm install -g @anthropic-ai/claude-code
```

Verify install:

```bash
claude --version
```

If you get a permission error, try with `sudo` (macOS/Linux) or run PowerShell as administrator (Windows).

For up-to-date install instructions, see https://docs.claude.com

---

## Step 4 — Authenticate Claude Code

```bash
claude
```

It'll prompt you to log in via browser. Use your Claude Pro/Max account. Done once — token is saved.

---

## Step 5 — Open vault in VS Code

1. Open VS Code
2. File → Open Folder → select `Studio-Vault`
3. Open the integrated terminal: **View → Terminal** (or `` Ctrl+` ``)
4. In the terminal, run:

```bash
claude
```

Claude Code starts in the vault folder. It auto-reads `CLAUDE.md` for context.

---

## Step 6 — Fill in studio knowledge (~15 min)

Open these files and fill in your real data (each has guiding placeholders):

- `00-Studio-Knowledge/design-principles.md` — your design philosophy + signature moves
- `00-Studio-Knowledge/rate-card.md` — labor rates, finishing costs you charge
- `00-Studio-Knowledge/pricing-formula.md` — how you calculate quotations
- `00-Studio-Knowledge/checklist-by-stage.md` — your gate criteria for each stage

The more accurate this is, the better Claude Code's suggestions will be.

---

## Step 7 — Test the system

In Claude Code terminal, type:

```
สวัสดี ขอ status ของ vault ตอนนี้หน่อย
```

It should respond with:
- No active projects yet
- Today's daily note status
- Suggestion to create first project

Then try:

```
/new-project
```

It should walk you through creating a new client folder.

---

## Step 8 — (Optional) Set up git for version control

In terminal, inside vault:

```bash
git init
git add .
git commit -m "Initial vault setup"
```

Then create a private repo on GitHub and push. This gives you:
- Full history of changes
- Backup
- Sync across machines

---

## Daily startup ritual

1. Open VS Code → vault folder
2. Open terminal → `claude`
3. Open Obsidian (parallel, for visual editing)
4. Type `/daily` in Claude Code → generates today's note

---

## Troubleshooting

**Claude Code doesn't see CLAUDE.md**
→ Make sure you ran `claude` from the vault root, not a parent folder.

**Slash commands don't work**
→ Check `.claude/commands/` folder is in vault root and contains `.md` files.

**Obsidian shows files differently than expected**
→ Toggle "Show all attachments and unlinked references" in Obsidian settings.

**Performance slow with many files**
→ Add `.obsidian/`, `.git/`, `90-Archive/` to Claude Code's ignore patterns.

---

## Next steps

- Read `CLAUDE.md` to understand how the AI behaves
- Try processing a real client transcript with `/brief`
- Customize templates in `10-Clients/_TEMPLATE/` to match your actual workflow
- Add custom slash commands in `.claude/commands/` for your repeated tasks
