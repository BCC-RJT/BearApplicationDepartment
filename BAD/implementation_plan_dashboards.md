
### **Plan: Unified Role-Based Dashboard for Ticket Assistant**

We will implement a unified **Dashboard System** within `tickets_assistant.py`. This approach consolidates the distinct "User", "Helper", and "Manager" views into a single, interactive interface that allows users to switch contexts seamlessly.

#### **1. Architecture & Core Values Alignment**
- **User-Centric**: A single `!dashboard` command opens the interface. Users don't need to remember multiple commands (`!ticket`, `!manager`, etc.).
- **Scalable**: The View logic allows adding more roles or widgets later without rewriting the core bot.
- **Secure (RBAC)**: Role checks (Manager/Staff) are enforced *before* rendering the view.
- **Efficient**: Uses Discord's `Interaction` system to update the message in-place, reducing channel clutter.

#### **2. Dashboard Views**
We will create a `UnifiedDashboardView` that manages the state.

**A. User Dashboard (Default)**
*   **Target**: All Users.
*   **Content**:
    *   "My Active Tickets": List of open tickets created by the user.
    *   "Create Ticket": Button to start a new ticket.
    *   "Ticket History": (Optional) Access to closed tickets.

**B. Helper Dashboard (Staff)**
*   **Target**: Users with `Staff` or `Support` roles.
*   **Content**:
    *   "Queue": High-level view of Unassigned Limit 5 (Urgency > Time).
    *   "My Claimed Tickets": Tickets assigned to this helper.
    *   "Quick Actions": `Claim Next`, `Clock In/Out`.

**C. Manager Dashboard (Leadership)**
*   **Target**: Users with `Manager` or `Admin` roles.
*   **Content**:
    *   "Command Center": The stats view we currently have (Total Open, Urgent, Unassigned).
    *   "Team Status": Who is effective/online (if we track it).
    *   "Global Actions": Force assign, Bulk close, etc.

#### **3. Implementation Details**

1.  **Refactor `tickets_assistant.py`**:
    *   Add `generate_user_dashboard(user_id)`: returns Embed + View.
    *   Add `generate_helper_dashboard(user_id)`: returns Embed + View.
    *   Modify `generate_dashboard_embed` to be `generate_manager_dashboard`.

2.  **New `UnifiedDashboardView` Class**:
    *   Contains a `Select Menu` primarily for **"Switch View"** (User | Helper | Manager).
    *   Dynamic Buttons based on current view (state stored in the View object).

3.  **Command**:
    *   `!dashboard`: Entry point. Checks permissions and defaults to the highest role available (Manager > Helper > User), or defaults to User and lets them switch.

#### **4. Execution Plan**
1.  **Modify `src/db.py`** (if needed) for efficient queries (e.g., `get_unassigned_tickets`).
2.  **Update `tickets_assistant.py`** with the new classes.
3.  **Test** the switching mechanism with your user account (as you likely have all roles).

### **Do you want to proceed with this Discord-native approach, or were you envisioning a separate Web Application?**
(I will assume Discord-native for now as it fits your active file list, but please correct me if I'm wrong.)
