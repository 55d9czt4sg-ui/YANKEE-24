# Security

- Never commit secrets, credentials, API keys, or `.env` files. If one is
  found in the working tree, flag it instead of committing it.
- Validate and sanitize all external input (user input, API responses, file
  contents) at trust boundaries; trust internal code otherwise.
- Avoid introducing common vulnerability classes: injection (SQL/command/
  shell), XSS, path traversal, insecure deserialization, and SSRF.
- Use parameterized queries / prepared statements for any database access —
  never build queries via string concatenation.
- Don't disable TLS verification, weaken authentication checks, or bypass
  permission/sandbox controls to "make something work".
- If you notice you've written insecure code, fix it immediately rather than
  leaving it for later.
