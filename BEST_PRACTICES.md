# Best Practices

## Code Quality

**Always prefer simple solutions**  
Keep code straightforward and easy to understand.

**Avoid duplication of code**  
Check for other areas of the codebase that might already have similar functionality.

**Write code that takes into account different environments**  
Consider dev, test, and prod environments in your implementation.

**Make changes carefully**  
Only make changes that are requested or that you are confident are well understood.

**When fixing an issue or bug:**
- Do not introduce a new pattern or technology without first exhausting existing implementation options
- If a new pattern is introduced, remove the old implementation to avoid duplicate logic

**Keep the codebase very clean and organized**  
Maintain consistent formatting and structure.

**Avoid writing scripts in files**  
Especially if the script is likely only to be run once.

**Refactor files over 400 lines of code**  
Break down large files into more manageable components.

## Data Handling

**Mocking data is only needed for tests**  
Never mock data for dev or prod environments.

**Never add stubbing or fake data patterns**  
Avoid fake data in code that affects dev or prod environments.

## Configuration

**Never overwrite the `.env` file**  
Always confirm before making changes to environment configurations.

## Git and Command Line

**Always use --no-pager for git commands**  
Prevent 'q' is not recognized errors by using the --no-pager flag:
```bash
# Good
git --no-pager log
git --no-pager diff

# Bad
git log  # May trigger pager
git diff # May trigger pager
```

**Common commands that need --no-pager:**
- `git log`
- `git diff`
- `git show`
- `git blame`

This prevents issues with command line pagers requiring user interaction. 