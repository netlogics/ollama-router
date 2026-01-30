# Quick Start Guide

Welcome to **beads**! This guide will get you up and running in minutes.

## Installation

```bash
pip install beads-cli
```

Or install from source:

```bash
git clone https://github.com/anomalyco/beads.git
cd beads
pip install -e .
```

## Initialize a Project

Navigate to your project and initialize beads:

```bash
cd /path/to/your-project
bd init
```

This creates a `.beads/` directory to store all issue data.

## Your First Issue

Create your first issue:

```bash
bd create --title="Add login page" --type=feature --priority=2
```

View all open issues:

```bash
bd list
```

## Common Workflow Patterns

### 1. Find Available Work

See what issues are ready to work (no blockers):

```bash
bd ready
```

### 2. Start Working

Claim an issue:

```bash
bd show beads-1          # View issue details
bd update beads-1 --status=in_progress
```

### 3. Complete Work

Mark as done:

```bash
bd close beads-1
```

### 4. Multi-Issue Workflow

```bash
# See all open issues
bd list --status=open

# See what you're working on
bd list --status=in_progress

# See blocked issues
bd blocked
```

## Basic Commands

| Command | Description |
|---------|-------------|
| `bd init` | Initialize beads in a project |
| `bd ready` | Show issues ready to work |
| `bd list` | List all issues |
| `bd show <id>` | View issue details |
| `bd create --title="..."` | Create new issue |
| `bd update <id>` | Update issue fields |
| `bd close <id>` | Mark issue complete |
| `bd blocked` | Show blocked issues |
| `bd stats` | Project statistics |
| `bd doctor` | Check for issues |
| `bd sync` | Sync with git remote |

## Dependency Management

Create dependent issues:

```bash
# Create issues
bd create --title="Build API endpoint" --type=feature --priority=1
bd create --title="Write API tests" --type=task --priority=2

# Set dependency (tests depend on API)
bd dep add beads-2 beads-1

# Now beads-2 is blocked until beads-1 is closed
bd blocked  # Shows beads-2

# View dependency chain
bd show beads-2  # Shows what's blocking it
```

Remove a dependency:

```bash
bd dep remove beads-2 beads-1
```

## Git Integration

Beads automatically syncs with git. Your workflow:

```bash
# Start work
bd update beads-1 --status=in_progress

# ... make code changes ...

# Stage and commit code
git add .
git commit -m "Add login page"

# Sync beads state
bd sync

# Push everything
git push
```

### Automatic Sync

Enable git hooks to auto-sync:

```bash
bd hooks install
```

This adds pre-commit and post-merge hooks to keep beads in sync.

## Priority Levels

- **0 (P0)**: Critical - system down, urgent fix needed
- **1 (P1)**: High - important feature/bug, do soon
- **2 (P2)**: Medium - normal work, standard priority
- **3 (P3)**: Low - nice to have, do when time permits
- **4 (P4)**: Backlog - maybe someday

## Issue Types

- **bug**: Something is broken
- **feature**: New capability
- **task**: General work item
- **epic**: Large body of work (groups other issues)
- **milestone**: Target/goal date

## Tips

1. **Use `--json` for scripting**: Most commands support `--json` output
2. **Check status anytime**: `bd sync --status` shows sync state
3. **Bulk close**: `bd close beads-1 beads-2 beads-3`
4. **Avoid `bd edit`**: It opens an editor; use inline updates instead

## Getting Help

- `bd --help` - Show all commands
- `bd <command> --help` - Help for specific command
- `bd doctor` - Check for setup issues

## Next Steps

- Read the full documentation: [../README.md](../README.md)
- Check AGENTS.md for agent-specific workflows
- Explore `bd stats` and `bd doctor` for project health
