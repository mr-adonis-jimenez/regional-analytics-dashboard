## Development Setup

### Enable repository git hooks (recommended)

This repo includes a `pre-push` hook to prevent direct pushes to the protected `master` branch.

1. Configure git to use the repo’s hook directory:

   `git config core.hooksPath scripts/git-hooks`

2. Ensure the hook is executable:

   `chmod +x scripts/git-hooks/pre-push`

After that, any attempt to `git push` updates directly to `master` will be blocked locally.

## Code Style
## Testing
## Commit Conventions
## Pull Request Process
