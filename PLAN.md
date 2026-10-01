# AI Web Tool - Architecture & Project Memory

## Project Overview
`AI Web Tool` is a specialized, fast MCP (Model Context Protocol) browser integration designed for LM Studio local AI models (e.g. Gemma, Qwen, Llama). It enables local models to perform autonomous web browsing, search the web via Brave Search, fill out complex scholarship and internship application forms, upload local documents (resumes, transcripts), handle multi-tab workflows, and manage pop-ups.

---

## Key Architecture & Design Decisions

### 1. Native `browser-use` Event Pipeline (Restored & Cleaned)
* **Root Cause Fix:** Avoid custom action overrides (`@self.registry.action`) for built-in action names like `input` or `click`. Custom overrides broke `browser-use`'s internal `TypeTextEvent` / `ClickElementEvent` event-bus routing, causing input text to fail visually.
* **Solution:** `BrowserEngineManager` in `browser_engine.py` uses clean, standard `Controller()`. Native Playwright/CDP event handlers now perform visible typing, element highlighting, and form filling reliably.

### 2. Smart Element Disambiguation (Local Model Helper)
Small 4B/8B local models can occasionally get confused by similarly-labeled elements (e.g. clicking an `<a>` link titled `"Search for Images"` instead of typing into a `<textarea>` search box).
To solve this:
* **`browser_type_smart(label, text)`:** Prioritizes `<input>`, `<textarea>`, and `[contenteditable]` elements matching a label/placeholder string, ignoring `<a>` links.
* **`browser_click_button(label)`:** Prioritizes `<button>`, `<input type="submit">`, and `[role=button]` elements matching a label over generic links.
* **System Prompt Guidance:** `COMPRESSED_SYSTEM_PROMPT` explicitly instructs models to filter by tag type when filling forms.

### 3. Brave Search & Direct Queries
* **Default Search Engine:** All web searches use **Brave Search** (`https://search.brave.com/search?q=...`), matching the user's default Brave Browser environment and avoiding Google CAPTCHA timeouts.
* **`browser_search_query(query)`:** Allows the model to execute web searches without needing an explicit URL.

### 4. Multi-Tab Workflow Tools
* **`browser_list_tabs()`:** Lists all open tabs with index, title, URL, and target ID.
* **`browser_switch_tab(tab_id_or_index)`:** Switches active browser focus between open tabs by index (e.g. `'0'`, `'1'`) or tab ID.
* **`browser_new_tab(url)`:** Opens a new tab with an optional URL (default: `https://search.brave.com`).

### 5. Persistent Session & Single-Window Constraint
* **Persistent Window (`keep_alive=True`):** The browser window and user tabs stay open when agent tasks complete or stop, allowing the user to navigate to pages manually for the model to work on.
* **Single Window Policy:** `_cleanup_old_browser_instances()` terminates lingering debug browser processes (`remote-debugging-port=9222`) upon session startup/restart, ensuring only **ONE** visible browser window exists on the desktop at any time.

---

## 🧰 Available MCP Tools (18 Tools Total)

1. `execute_browser_task(task, max_steps)`
2. `browser_navigate(url)`
3. `browser_search_query(query)`
4. `browser_list_tabs()`
5. `browser_switch_tab(tab_id_or_index)`
6. `browser_new_tab(url)`
7. `browser_get_content()`
8. `browser_click(index)`
9. `browser_click_button(button_label_or_text)`
10. `browser_type(index, text, clear)`
11. `browser_type_smart(field_label_or_placeholder, text, clear)`
12. `browser_upload_file(index, file_path)`
13. `browser_select_dropdown(index, option_text)`
14. `browser_fill_date(index, date_value)`
15. `browser_handle_popup(action)`
16. `browser_send_keys(keys)`
17. `list_user_documents(search_query)`
18. `browser_scroll(down, pages)`

---

## LM Studio Configuration

File path: `/home/pengufen/Code Projects/AI Web Tool/server.py`

```json
{
  "mcpServers": {
    "ai-web-tool": {
      "command": "/home/pengufen/agent-env/bin/python",
      "args": [
        "/home/pengufen/Code Projects/AI Web Tool/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```
