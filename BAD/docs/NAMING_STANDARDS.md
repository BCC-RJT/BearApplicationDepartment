# Bear Application Department - Naming Standards

## Overview
To ensure consistency, discoverability, and maintainability across the Bear Application Department (BAD), all resources must adhere to the following naming convention. This applies to cloud resources, configuration entries, and internal identifiers.

## Global Standard
**Format:** `[PROJECT]-[ENV]-[TYPE]-[NAME]`

### 1. Project (`PROJECT`)
The high-level namespace for the resource.
- **BAD**: Default for Bear Application Department resources.
- **EXT**: For External or Third-Party resources we track but do not own.

### 2. Environment (`ENV`)
The lifecycle stage of the resource.
- **PROD**: Production (Live, critical, stable).
- **DEV**: Development (Testing, volatile).
- **STAGE**: Staging (Pre-production replica).
- **TEST**: Ephemeral testing resources.

### 3. Type (`TYPE`)
A 2-4 letter code indicating the resource type.
- **VM**: Virtual Machine / Compute Instance.
- **DB**: Database.
- **BOT**: Discord Bot or Automation Agent.
- **S3**: Storage Bucket.
- **NET**: Network / VPC.
- **KEY**: API Key or Secret.

### 4. Name (`NAME`)
A descriptive identifier for the specific resource.
- Use `UPPERCASE` with `_` (underscores) or `-` (hyphens) allowed.
- Keep it concise but descriptive.

## Examples

| Old/Bad Name | **New Standard Name** | Description |
| :--- | :--- | :--- |
| `foundation-vm` | **BAD-PROD-VM-FOUNDATION** | The main production VM for BAD. |
| `test-db` | **BAD-DEV-DB-TEST_01** | A development database. |
| `bad_bot` | **BAD-PROD-BOT-OPERATOR** | The main Discord operator bot. |
| `my_bucket` | **BAD-PROD-S3-ARCHIVES** | Production storage for archives. |

## Enforcement
- **Registry**: All valid resources must be logged in `BAD/config/resource_ledger.json`.
- **Janitor**: The "Janitor" agent will periodically scan for non-compliant names and report them.
