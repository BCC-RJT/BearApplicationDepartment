# Decision Log

| Date       | Type     | Decision / Rule / Fact                                                                 | Rationale                                                                 |
|------------|----------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| 2026-02-08 | Rule     | Use **Browser Intervention Protocol** for blocked tasks (2FA/CAPTCHA).                 | Agents cannot bypass security challenges via terminal.                    |
| 2026-02-08 | Decision | Rename **BAD-Bridge-Bot** to **BADbot** via browser and enforce nickname in code.      | Provide consistent branding across Discord and code without API renaming. |
| 2026-02-09 | Decision | Use **gemini-2.0-flash** for Agent Brain and Ticket Builder.                         | **gemini-1.5-flash** unavailable; **gemini-2.5-flash** unstable (empty responses).     |
