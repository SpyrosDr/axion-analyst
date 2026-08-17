# Axion Analyst — How-To Guide

Short, task-focused instructions for using Axion Analyst. Each section stands alone — jump straight to the one you need.

For **Run Analysis**, a short video may be added later since watching the AI pass complete communicates it faster than steps do. Everything else is covered here.

---

## How to sign in
1. Go to the login page.
2. Enter your username and password.
3. Click **Sign in**.

Access is admin-provisioned — there's no public signup. If you don't have an account, ask an admin to create one for you (see [How to add a user and set roles](#how-to-add-a-user-and-set-roles)).

## How to read the dashboard
The **Dashboard** tab (shown after login) gives a portfolio view across every case you own or collaborate on:
- **Stat tiles** — Total cases, Open, In review, Closed.
- **Risk donut** — Awaiting analysis, High / Medium / Low risk, at a glance.
- **Recent Cases** — a shortcut list; click any case to open it.

## How to search and filter cases
1. Click **Cases** in the top nav.
2. Use the status chips (**All / Open / In Review / Closed**) to narrow the list by state.
3. Use the search box to find a case by text in its context or description.

## How to create a case
1. From the **Cases** tab, click **+ New Case**.
2. Fill in:
   - **Case context** — pick the option that best matches who's asking (e.g. "Auditor reviewing possible vendor misuse"). This is a fixed dropdown, not free text.
   - **Case description** — a paragraph on what's suspected.
   - **Evidence Items (optional)** — add one or more items now (Title, Type, Details) if you already have some, or leave this blank and add evidence later.
3. Click **Create Case**.

You don't need evidence up front — add it as the investigation develops.

## How to add evidence
1. Open a case.
2. Scroll to the evidence editor below the evidence list.
3. Fill in **Title**, **Type** (optional), and **Evidence details**.
4. Click **Add Evidence**.

Each entry — a note, an email summary, a transaction record — is tied back to the case.

## How to attach a file to evidence
1. Open a case and add the evidence entry first (see [How to add evidence](#how-to-add-evidence)) — the entry must already exist in the list.
2. On that evidence item in the list, use the file picker next to it to choose a file (screenshot, PDF, statement, etc.).
3. The file uploads automatically as soon as you pick it — there's no separate submit step.

## How to search for an entity
1. On a case, scroll to the **Web Research** panel.
2. Type the name of a person or company mentioned in the case.
3. Pick a type (e.g. Company, Person).
4. Click **Search**.

Results are cached — searching the same entity again is instant, and past searches appear in **History**.

## How to run analysis
1. On a case with evidence already added, scroll to the **Run Analysis** button.
2. Click it.
3. Wait for the loading state to clear — the page populates below with entities, timeline, risk signals, and a draft report, all from the same pass so they stay consistent with each other.

## How to review extracted entities
1. On an analyzed case, scroll to the **Entities** section.
2. Each entity shows its type (Person, Account Number, etc.) as a chip.
3. Hover over a chip to see which evidence item it was sourced from (shown in the tooltip); chips with a source are marked "· source".

Nothing is asserted without a source you can check.

## How to review the timeline
1. On an analyzed case, scroll to the **Timeline** section.
2. Scroll through the chronology — each entry shows the date, what happened, and which document it came from.

## How to review risk signals
1. On an analyzed case, scroll to **Risk signals for investigator review**.
2. Check the risk level badge (e.g. "High Risk") and the bulleted indicators.

These are flagged for review, not a verdict — confirm, amend, or reject each one against the source evidence.

## How to export the draft report
1. On an analyzed case, scroll to **Draft investigation report**.
2. Review the sections: Overview, Evidence, Entities, Timeline, Risk assessment, Recommendations.
3. Click **Print / Save as PDF** to export.

The report is a starting point, not a finished conclusion.

## How to add a collaborator
1. On a case, scroll to **Collaborators**.
2. Use the **Add collaborator...** dropdown to pick a user.
3. Set their role — **Viewer**, **Editor**, or **Manager**.
4. Click **Add**.

Cases are private by default; this is how you share one with a colleague.

## How to add a user and set roles
*(Admin only)*
1. Click **Manage Users** in the top nav.
2. Under **Create User**, fill in a username and password. Check **Admin** if the new account should be an admin.
3. Click **Create User**.
4. To adjust an existing user's access, use the role dropdown next to their name: **None**, **View**, **Edit**, or **Manage**. This sets *global* access across every case in the system — leave it as **None** to rely on per-case sharing instead (see [How to add a collaborator](#how-to-add-a-collaborator)).
