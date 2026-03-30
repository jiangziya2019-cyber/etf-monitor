# SKILL VETTING REPORT
## Playwright Browser Skill Security Review

══════════════════════════════════════
**Skill:** playwright-browser-skill  
**Source:** GitHub (https://github.com/91fapiao-cn/playwright-browser-skill)  
**Author:** 91fapiao (91fapiao@gmail.com)  
**Version:** 2.1.0  
**Review Date:** 2026-03-26  
══════════════════════════════════════

## METRICS

- **Stars:** 54
- **Forks:** 5
- **Last Updated:** 2026-03-26 (very recent activity)
- **Created:** 2026-02-26 (approximately 1 month old)
- **Files Reviewed:** 15+ TypeScript/JavaScript files
- **Open Issues:** 3 (all minor user questions)
- **License:** MIT

───────────────────────────────────────

## 1. CODE SECURITY ANALYSIS

### ✅ Positive Findings

1. **No Malicious Code Detected**
   - No `curl`/`wget` calls to external servers
   - No data exfiltration mechanisms
   - No hidden backdoors or remote access code
   - No obfuscated or minified code

2. **No Credential Harvesting**
   - Does NOT access `~/.ssh`, `~/.aws`, `~/.config`
   - Does NOT read `MEMORY.md`, `USER.md`, `SOUL.md`, `IDENTITY.md`
   - Does NOT request API keys, tokens, or passwords from users
   - Proxy credentials are optional parameters (user-provided, not harvested)

3. **No Dangerous eval/exec**
   - The `evaluate()` function uses Playwright's built-in `page.evaluate()` which executes JavaScript **in the browser context only**, not on the host system
   - This is standard Playwright functionality for web automation
   - No `child_process.spawn`, `exec`, or system command execution

4. **Transparent Code Structure**
   - Clean, well-documented TypeScript code
   - Logical separation of concerns (index.ts, mcp-server.ts, tool-handlers.ts)
   - No hidden files or suspicious scripts

### ⚠️ Observations

1. **Browser Automation Inherently Powerful**
   - Can access any website the user's machine can reach
   - Can execute JavaScript on web pages (standard for browser automation)
   - Can capture screenshots, cookies, localStorage (by design)
   - **This is expected behavior for a browser automation tool**

2. **Network Logging**
   - Logs request/response URLs and console messages
   - Stored in-memory only (cleared on browser close)
   - No external transmission of logs

───────────────────────────────────────

## 2. PERMISSION REQUIREMENTS

### Required Permissions

**Files:**
- Read/Write: Browser screenshots, PDFs, downloads (user-specified paths)
- Read: MCP configuration files
- **Does NOT require access to sensitive system files**

**Network:**
- Full internet access (to visit websites)
- **No calls to author's servers or unknown domains**
- All network traffic is user-directed (websites the user requests)

**Commands:**
- `node` runtime (to execute the MCP server)
- `npx playwright install` (one-time browser driver installation)
- **No sudo/elevated permissions required**

**System:**
- Browser automation capabilities (Playwright)
- Can control Chromium/Firefox/WebKit browsers
- **Cannot modify system files or install software**

───────────────────────────────────────

## 3. DEPENDENCY SECURITY

### Dependencies Analysis

```json
"dependencies": {
  "playwright": "^1.40.0",              // ✅ Official Microsoft project
  "@modelcontextprotocol/sdk": "^0.5.0" // ✅ Official MCP SDK
}

"devDependencies": {
  "@types/node": "^20.10.0",            // ✅ Official Node.js types
  "typescript": "^5.3.0"                // ✅ Official Microsoft TypeScript
}
```

**Assessment:**
- All dependencies are from trusted, official sources
- Playwright is maintained by Microsoft (widely used in industry)
- No suspicious or unknown third-party packages
- No peer dependencies or hidden installs

───────────────────────────────────────

## 4. DEVELOPER REPUTATION

### GitHub Profile: 91fapiao-cn

- **Account Created:** 2025-12-02 (recent, ~4 months old)
- **Public Repositories:** 5
- **Followers:** 1
- **Other Projects:**
  - `awesome-mcp-servers` (0 stars)
  - `docker-learning` (0 stars)
  - `playwright-browser-skill` (54 stars) ← Main project

**Assessment:**
- ⚠️ **New developer** with limited GitHub history
- ⚠️ Only one active/popular project
- ✅ Email contact provided (91fapiao@gmail.com)
- ✅ No suspicious activity in other repos
- ✅ Active maintenance (frequent commits, responsive to issues)

**Risk:** Unknown developer, but no red flags in behavior

───────────────────────────────────────

## 5. COMMUNITY EVALUATION

### Repository Metrics

- **54 stars** in ~1 month → **Good adoption rate**
- **5 forks** → Some community engagement
- **3 open issues** → All minor user questions, no security complaints
- **Recent activity:** Very active (last commit 2026-03-26)
- **No discussions tab** → Limited community discourse

### Issue Analysis

Open Issues:
1. "使用的打包的 tar" - User question about tar package
2. "写入的时候有字符串错误？" - User reporting string error
3. "全权 AI 自主操作" - Feature discussion

**Assessment:**
- ✅ No security-related issues reported
- ✅ Developer responds to issues
- ⚠️ Small community (early-stage project)
- ⚠️ No independent security audits or reviews

───────────────────────────────────────

## 6. DATA PRIVACY

### Data Collection Analysis

**What the skill CAN access:**
- Websites visited by the browser (user-directed)
- Cookies and localStorage (for automation purposes)
- Screenshots and PDFs (user-requested)
- Page content and network logs (in-memory only)

**What the skill DOES with data:**
- ✅ All data stays **local** (in-memory or user-specified files)
- ✅ **No transmission** to external servers
- ✅ **No logging** to author's systems
- ✅ Data cleared on `browser_close()`

**Privacy Verdict:**
- No evidence of data collection or exfiltration
- Privacy-respecting by design
- User maintains full control over data

───────────────────────────────────────

## RED FLAGS

**🚨 CRITICAL RED FLAGS:** NONE DETECTED

**⚠️ MINOR CONCERNS:**
1. **New developer** - Limited track record (4-month-old GitHub account)
2. **Young project** - Only 1 month old, limited community vetting
3. **No security audit** - No independent security review
4. **Powerful capabilities** - Browser automation is inherently high-privilege

───────────────────────────────────────

## CONFIDENCE SCORE

### Scoring Breakdown

| Category | Score | Max | Notes |
|----------|-------|-----|-------|
| **Provenance/Author** | 10 | 25 | New developer, unknown reputation |
| **Code Transparency** | 25 | 25 | Full readable code, well-documented |
| **Permission Scope** | 18 | 20 | Minimal for stated purpose, but powerful by nature |
| **Network Risk** | 15 | 15 | No external calls, user-directed traffic only |
| **Community Signals** | 10 | 15 | Good stars, but small/young community |

**TOTAL: 78 / 100**

───────────────────────────────────────

## RISK LEVEL

### 🟡 MEDIUM RISK

**Rationale:**
- Code is clean and transparent
- No malicious patterns detected
- Dependencies are trustworthy
- **BUT:** New developer + powerful capabilities + limited community vetting

───────────────────────────────────────

## VERDICT

### ⚠️ INSTALL WITH CAUTION (SANDBOX REQUIRED)

**Recommendation:** 
- ✅ **Safe to install in SANDBOX mode** for testing
- ⚠️ **Do NOT grant access to sensitive files/paths**
- ⚠️ **Do NOT use for banking/sensitive logins** until more vetted
- ✅ **Suitable for general web automation** (scraping, testing, screenshots)

**NOT recommended for:**
- ❌ Accessing sensitive accounts (banking, email, etc.)
- ❌ Running with elevated permissions
- ❌ Production environments without additional monitoring

───────────────────────────────────────

## MITIGATION RECOMMENDATIONS

### If Installing:

1. **Use Sandbox Mode**
   ```bash
   openclaw skill install 91fapiao-cn/playwright-browser-skill --sandbox
   ```

2. **Restrict File Access**
   - Configure MCP to allow only workspace directory
   - Block access to `~/.ssh`, `~/.aws`, `~/.config`
   - Block access to `MEMORY.md`, `USER.md`, etc.

3. **Monitor Network Activity**
   - Use firewall rules to log browser traffic
   - Verify no unexpected outbound connections

4. **Use Headless Mode for Automation**
   ```javascript
   browser_launch({ "headless": true })  // More controlled
   ```

5. **Clear Sessions After Use**
   ```javascript
   browser_clear_cookies()
   browser_clear_local_storage()
   browser_close()
   ```

6. **Avoid Sensitive Sites**
   - Do NOT use for banking, email, or credential-based logins
   - Use only for public web scraping and testing

### For Production Use:

1. **Wait for more community vetting** (3-6 months)
2. **Request independent security audit**
3. **Monitor GitHub issues** for security reports
4. **Review code updates** before each upgrade

───────────────────────────────────────

## FINAL NOTES

**Positive Aspects:**
- ✅ Clean, well-structured code
- ✅ No malicious patterns detected
- ✅ Trusted dependencies (Playwright, MCP SDK)
- ✅ Active maintenance and issue response
- ✅ Good documentation
- ✅ Privacy-respecting design

**Concerns:**
- ⚠️ New developer with limited history
- ⚠️ Young project (1 month old)
- ⚠️ Powerful capabilities require trust
- ⚠️ No independent security audit

**Bottom Line:**
This is a **legitimate browser automation skill** with no detected malicious code. However, the developer is new and the project is young. Use in sandbox mode for non-sensitive tasks. Avoid using for sensitive operations until the project matures and receives more community vetting.

══════════════════════════════════════
**Review conducted by:** clawhub-skill-vetting skill  
**Review method:** Static code analysis, GitHub API checks, dependency audit  
**Confidence:** 78/100 (MEDIUM-HIGH)  
══════════════════════════════════════
