# AI Web Tool - LM Studio MCP Browser Integration

Fast, DOM-indexed web automation MCP server for LM Studio. Allows any local LLM in LM Studio to navigate websites, fill out scholarship & internship application forms, upload resumes/transcripts, handle date pickers, manage pop-up dialogs, and search local files directly within the LM Studio chat interface.

---

## 🛠️ How to Enable in LM Studio

### Step 1: Open LM Studio MCP Settings
1. Open **LM Studio**.
2. Click on **Settings** (Gear Icon) or navigate to **Integrations / MCP**.
3. Click **Edit MCP Configuration** (or edit your `mcp.json` file).

### Step 2: Add the Configuration
Add the following block to your `mcpServers` object in LM Studio:

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

---

## 🛡️ Smart Element Disambiguation (Form & Typing Reliability)

To prevent local models (e.g. 4B/8B models) from getting confused by similarly-labeled elements (like clicking an `<a>` link named *"Search for Images"* instead of typing into a `<textarea>` search box), the tool includes **Smart Semantic Actions**:

1. **`browser_type_smart(field_label_or_placeholder, text)`:**
   Automatically searches the DOM for input fields matching a label or placeholder string (e.g. `"Search"`, `"Email"`, `"First Name"`), prioritizing `<input>` and `<textarea>` elements over links.

2. **`browser_click_button(button_label_or_text)`:**
   Finds and clicks buttons matching a text label (e.g. `"Submit"`, `"Apply"`), prioritizing `<button>` and `<input type="submit">` elements over generic navigation links.

3. **System Prompt Rules:**
   Instructs models to filter element types when filling out forms.

---

## 🧰 Available Tools in LM Studio (14 Tools)

### 🧠 Smart & Form Application Tools
* `browser_type_smart(label, text)`: Smart field match & type (bypasses link ambiguity).
* `browser_click_button(label)`: Smart button match & click.
* `browser_upload_file(index, file_path)`: Upload resumes/transcripts into file input elements.
* `browser_select_dropdown(index, option_text)`: Select an option from dropdown menus by visible text.
* `browser_fill_date(index, date_value)`: Fill date input fields (e.g. `2026-09-01`).
* `browser_handle_popup(action)`: Dismiss or close pop-ups, modals, cookie notices, or alerts.
* `browser_send_keys(keys)`: Send special keyboard events (`Enter`, `Tab`, `Escape`, `ArrowDown`).
* `list_user_documents(search_query)`: Scan `~/Documents` and `~/Downloads` for PDFs/DOCX files.

### 🌐 Core Navigation & Inspection Tools
* `execute_browser_task(task)`: Multi-step autonomous browser agent runner.
* `browser_navigate(url)`: Navigate to a web address.
* `browser_get_content()`: Extract current page DOM content (under 2k tokens).
* `browser_click(index)`: Click an element by index number.
* `browser_type(index, text)`: Type text into an input box by index.
* `browser_scroll(down, pages)`: Scroll page up or down.
