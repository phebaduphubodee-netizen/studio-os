# Studio Vault — Interior Design Knowledge Base

Personal assistant system for interior design workflow, powered by Claude Code + Obsidian.
**Version 2.0** — with source hierarchy, change order tracking, and explicit tool limits.

## What this is

A pre-structured Obsidian vault that doubles as a Claude Code workspace. Open it in **Obsidian** to browse/edit notes manually, or open in **VS Code** with Claude Code to delegate work to AI.

## Quick start

1. **Move this folder** to where you want your knowledge base (e.g. `~/Documents/Studio-Vault/`)
2. **Open in Obsidian**: Open Obsidian → "Open folder as vault" → select this folder
3. **Open in VS Code**: File → Open Folder → select this folder
4. **Install Claude Code**: see [SETUP-GUIDE.md](SETUP-GUIDE.md)
5. **Fill in your studio info** in `00-Studio-Knowledge/` (placeholders guide you)
6. **Create your first project**: in Claude Code, type `/new-project`

## What's in v2

Project files now include **control layer** beyond stage files:
- `04-decisions.md` — **confirmed** decisions only
- `99-followup.md` — pending / drafts / open questions
- `risks.md` — risk register
- `change-orders.md` — scope changes after approval

The assistant follows strict rules around:
- **Source hierarchy** — what beats what when data conflicts
- **Change order rule** — never silently update BOQ on scope creep
- **Cost estimate standard** — every cost has source + confidence
- **Tool limitations** — assistant declares missing capabilities, doesn't pretend

See `CLAUDE.md` for the full configuration.

## Folder structure

| Folder | Purpose |
|--------|---------|
| `00-Studio-Knowledge/` | Your studio's principles, rates, formulas, checklists |
| `10-Clients/` | One subfolder per client project |
| `10-Clients/_TEMPLATE/` | Master template — copy for new projects |
| `20-Templates/` | Reusable templates (material/supplier/contractor cards) |
| `30-Materials-DB/` | Material library — one card per material |
| `40-Suppliers/` | Supplier contacts + capability cards |
| `50-Contractors/` | Contractor / sub-contractor cards |
| `60-References/` | Inspiration, case studies, building codes |
| `70-Daily-Notes/` | Daily journal (YYYY-MM-DD.md) |
| `90-Archive/` | Completed / cancelled projects |
| `.claude/commands/` | Custom Claude Code slash commands |
| `CLAUDE.md` | System prompt — auto-loaded by Claude Code |

## Daily workflow

```
Morning:
  /daily               → today's note with active project summary

During work:
  /brief               → process new client transcript
  /material            → recommend materials for current project
  /boq                 → generate BOQ from spec (with status flags)
  /change-order        → log scope change with impact estimate
  /qc                  → compare site photo to render

End of day:
  Update daily note → commit changes (if using git)
```

## Backup

This vault is just markdown files in folders. Recommended backup options:
- **Git**: initialize a repo and push to GitHub/GitLab (private)
- **Obsidian Sync** (~$8/month): native, encrypted, multi-device
- **iCloud / Dropbox / Google Drive**: works but watch for sync conflicts

## Editing this system

The structure is yours — edit freely. If you change folder names or add stages, update `CLAUDE.md` so Claude Code stays aligned with reality.

---

See **[SETUP-GUIDE.md](SETUP-GUIDE.md)** for installation steps.
See **[CLAUDE.md](CLAUDE.md)** to understand how the AI assistant behaves.
