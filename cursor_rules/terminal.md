# Terminal Command Rules

## Operating System
- All terminal commands must be Windows-compatible (Windows 10/11)
- Use Windows Command Prompt (cmd.exe) or PowerShell syntax
- Do not use Unix/Linux specific commands (e.g., `cat`, `grep`, etc.)

## Command Prompt (cmd.exe) Guidelines
- Use Windows equivalents for Unix commands:
  - `type` instead of `cat`
  - `findstr` instead of `grep`
  - `dir` instead of `ls`
  - `del` instead of `rm`
  - `copy` instead of `cp`
  - `move` instead of `mv`
  - `md` or `mkdir` for creating directories
  - `rd` or `rmdir` for removing directories

## PowerShell Guidelines
- Use PowerShell cmdlets when more functionality is needed:
  - `Get-Content` instead of `type`
  - `Select-String` instead of `findstr`
  - `Get-ChildItem` or `dir` instead of `ls`
  - `Remove-Item` instead of `del`
  - `Copy-Item` instead of `copy`
  - `Move-Item` instead of `move`
  - `New-Item -ItemType Directory` for creating directories
  - `Remove-Item -Recurse` for removing directories

## Path Conventions
- Use Windows path format with backslashes (`\`) or escaped forward slashes (`/`)
- For variables, use Windows environment variable syntax: `%VARIABLE%`
- For PowerShell variables, use: `$env:VARIABLE`

## Output Handling
- Instead of piping to `less` or `more`, use:
  - CMD: `command | more`
  - PowerShell: `command | Out-Host -Paging`
- For Git commands that might trigger a pager:
  - Use `--no-pager` flag: `git --no-pager log`
  - Or set Git config: `git config --global core.pager ""`

## Process Management
- Use Windows Task Manager commands:
  - `tasklist` to list processes
  - `taskkill` to terminate processes
- For background processes:
  - Use `start` command in CMD
  - Use `Start-Process` in PowerShell

## File System Operations
- Respect Windows file system limitations:
  - Maximum path length of 260 characters (unless long paths are enabled)
  - Reserved characters: `< > : " / \ | ? *`
  - Reserved names: CON, PRN, AUX, NUL, COM1-9, LPT1-9

## Security Considerations
- Use proper escaping for special characters in paths and commands
- Consider UAC (User Account Control) when requiring elevated privileges
- Use `runas` or PowerShell's `Start-Process -Verb RunAs` for admin privileges 