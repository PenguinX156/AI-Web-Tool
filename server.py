import asyncio
import sys
import os
import glob
import re
import urllib.parse
import logging
from typing import Optional, List

from mcp.server.fastmcp import FastMCP
from browser_engine import BrowserEngineManager

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp_server")

mcp = FastMCP(name="LM-Studio-Web-Tool")
manager = BrowserEngineManager()

@mcp.tool()
async def execute_browser_task(task: str, max_steps: int = 20) -> str:
    """Execute an autonomous multi-step web browsing or form-filling task (e.g. 'Fill out the internship form on this page with my resume and contact details', 'Search for scholarships and apply').
    
    Args:
        task: Instruction of what the browser agent should do.
        max_steps: Maximum browsing steps allowed (default: 20).
    """
    try:
        logger.info(f"Executing browser task: {task}")
        result = await manager.execute_task(task=task, max_steps=max_steps)
        return f"Task Completed:\n{result}"
    except Exception as e:
        logger.error(f"Error executing task: {e}", exc_info=True)
        return f"Error executing browser task: {str(e)}"

@mcp.tool()
async def browser_navigate(url: str) -> str:
    """Navigate the active visible browser to a specific URL.
    
    Args:
        url: The web address (e.g. 'https://scholarships.org/apply').
    """
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("navigate", params={"url": url}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Navigated to {url}.\n\nCurrent Page Content (Indexed DOM):\n{summary[:3000]}"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"

@mcp.tool()
async def browser_search_query(query: str) -> str:
    """Search the web directly using Brave Search with a query string without needing an explicit URL (e.g. 'Fedora 43 release date', 'best computer science scholarships').
    
    Args:
        query: Search keywords or query string.
    """
    try:
        search_url = f"https://search.brave.com/search?q={urllib.parse.quote(query)}"
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("navigate", params={"url": search_url}, browser_session=browser)
        await asyncio.sleep(1.5)
        summary = await manager.get_page_summary()
        return f"Searched Brave for '{query}'.\n\nSearch Results Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error searching Brave for '{query}': {str(e)}"

@mcp.tool()
async def browser_list_tabs() -> str:
    """List all currently open browser tabs with their index, title, URL, and target ID."""
    try:
        browser = await manager.get_browser()
        tabs = await browser.get_tabs()
        if not tabs:
            return "No open browser tabs found."
        
        tab_list = []
        for idx, t in enumerate(tabs):
            tab_list.append(f"- Tab [{idx}]: Title='{t.title}', URL='{t.url}', ID='{t.target_id}'")
            
        output = "Currently Open Browser Tabs:\n" + "\n".join(tab_list)
        return output
    except Exception as e:
        return f"Error listing tabs: {str(e)}"

@mcp.tool()
async def browser_switch_tab(tab_id_or_index: str) -> str:
    """Switch active browser focus to a specific tab by tab index (e.g. '0', '1') or tab target ID.
    
    Args:
        tab_id_or_index: The tab index number ('0', '1', '2') or tab target ID.
    """
    try:
        browser = await manager.get_browser()
        tabs = await browser.get_tabs()
        target_id = None
        
        if str(tab_id_or_index).isdigit():
            idx = int(tab_id_or_index)
            if 0 <= idx < len(tabs):
                target_id = tabs[idx].target_id
                
        if not target_id:
            for t in tabs:
                if tab_id_or_index in t.target_id or tab_id_or_index in t.url or tab_id_or_index in t.title:
                    target_id = t.target_id
                    break
                    
        if not target_id:
            return f"Tab '{tab_id_or_index}' not found in open tabs."

        res = await manager.controller.registry.execute_action("switch", params={"tab_id": target_id}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Switched to tab '{tab_id_or_index}' (ID: {target_id}).\n\nActive Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error switching to tab '{tab_id_or_index}': {str(e)}"

@mcp.tool()
async def browser_new_tab(url: Optional[str] = "https://search.brave.com") -> str:
    """Open a new browser tab with an optional URL.
    
    Args:
        url: The web address for the new tab (default: 'https://search.brave.com').
    """
    try:
        if url and not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("navigate", params={"url": url or "https://search.brave.com", "new_tab": True}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Opened new tab at {url}.\n\nNew Tab State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error opening new tab: {str(e)}"

@mcp.tool()
async def browser_get_content() -> str:
    """Get current page content in clean, indexed DOM format (under 2k tokens)."""
    try:
        summary = await manager.get_page_summary()
        return f"Current Page Content:\n{summary}"
    except Exception as e:
        return f"Error fetching page content: {str(e)}"

@mcp.tool()
async def browser_click(index: int) -> str:
    """Click an element by its bracketed index number.
    
    Args:
        index: The bracketed index number of the element.
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("click", params={"index": index}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Clicked element {index}.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error clicking element {index}: {str(e)}"

@mcp.tool()
async def browser_click_button(button_label_or_text: str) -> str:
    """Smart click tool: Finds and clicks a button or clickable element matching a label or text (e.g. 'Submit', 'Search', 'Apply', 'Upload', 'Next'), prioritizing <button> and <input type='submit'> elements over links.
    
    Args:
        button_label_or_text: Button label, text, or title to click (e.g. 'Submit', 'Search', 'Apply').
    """
    try:
        summary = await manager.get_page_summary()
        lines = summary.split('\n')
        target_idx = None
        
        for line in lines:
            line_lower = line.lower()
            if button_label_or_text.lower() in line_lower:
                if any(tag in line_lower for tag in ['<button', 'role=button', 'type=submit', 'type=button']):
                    m = re.search(r'\[(\d+)\]', line)
                    if m:
                        target_idx = int(m.group(1))
                        break

        if not target_idx:
            for line in lines:
                if button_label_or_text.lower() in line.lower() and '[' in line and ']' in line:
                    m = re.search(r'\[(\d+)\]', line)
                    if m:
                        target_idx = int(m.group(1))
                        break

        if not target_idx:
            return f"Could not find a button matching '{button_label_or_text}' on current page."

        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("click", params={"index": target_idx}, browser_session=browser)
        await asyncio.sleep(1.0)
        updated_summary = await manager.get_page_summary()
        return f"Smart-clicked button element {target_idx} (matched '{button_label_or_text}').\n\nUpdated Page State:\n{updated_summary[:3000]}"
    except Exception as e:
        return f"Error smart clicking button: {str(e)}"

@mcp.tool()
async def browser_type(index: int, text: str, clear: bool = False) -> str:
    """Type text into an input element by index.
    
    Args:
        index: The bracketed index number of the input box.
        text: The text string to type.
        clear: Whether to clear existing text first (default: False).
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("input", params={"index": index, "text": text, "clear": clear}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Typed '{text}' into element {index}.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error typing into element {index}: {str(e)}"

@mcp.tool()
async def browser_type_smart(field_label_or_placeholder: str, text: str, clear: bool = True) -> str:
    """Smart typing tool: Automatically finds the correct input field, textarea, or search box matching a label, name, or placeholder string (e.g. 'Search', 'First Name', 'Resume', 'Email'), prioritizing <input> and <textarea> elements over <a> links.
    
    Args:
        field_label_or_placeholder: Label, placeholder, name, or aria-label of the input box (e.g. 'Search', 'Email', 'First Name').
        text: The text string to type.
        clear: Whether to clear existing text first (default: True).
    """
    try:
        summary = await manager.get_page_summary()
        lines = summary.split('\n')
        target_idx = None
        
        for line in lines:
            line_lower = line.lower()
            if field_label_or_placeholder.lower() in line_lower:
                if any(tag in line_lower for tag in ['<input', '<textarea', 'contenteditable', 'role=textbox', 'type=text', 'type=search', 'type=email']):
                    m = re.search(r'\[(\d+)\]', line)
                    if m:
                        target_idx = int(m.group(1))
                        break

        if not target_idx:
            for line in lines:
                if field_label_or_placeholder.lower() in line.lower() and '[' in line and ']' in line:
                    m = re.search(r'\[(\d+)\]', line)
                    if m:
                        target_idx = int(m.group(1))
                        break

        if not target_idx:
            return f"Could not find an input field matching '{field_label_or_placeholder}' on current page."

        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("input", params={"index": target_idx, "text": text, "clear": clear}, browser_session=browser)
        await asyncio.sleep(1.0)
        updated_summary = await manager.get_page_summary()
        return f"Smart-typed '{text}' into field element {target_idx} (matched '{field_label_or_placeholder}').\n\nUpdated Page State:\n{updated_summary[:3000]}"
    except Exception as e:
        return f"Error in smart typing: {str(e)}"

@mcp.tool()
async def browser_upload_file(index: int, file_path: str) -> str:
    """Upload a file (resume, cover letter, transcript, photo, PDF) into a file upload element on a form.
    
    Args:
        index: The bracketed index number of the file input box/button.
        file_path: Absolute or relative path to the file on disk (e.g. '/home/pengufen/Documents/resume.pdf').
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("upload_file", params={"index": index, "path": file_path}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Uploaded file '{file_path}' into element {index}.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error uploading file into element {index}: {str(e)}"

@mcp.tool()
async def browser_select_dropdown(index: int, option_text: str) -> str:
    """Select an option from a dropdown element by text.
    
    Args:
        index: The bracketed index number of the select/dropdown element.
        option_text: The visible text of the option to select (e.g. 'Full-time', 'Senior', 'Computer Science').
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("select_dropdown", params={"index": index, "text": option_text}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Selected '{option_text}' in dropdown {index}.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error selecting dropdown option: {str(e)}"

@mcp.tool()
async def browser_fill_date(index: int, date_value: str) -> str:
    """Fill a date field on a form (e.g. start date, graduation date, birthday).
    
    Args:
        index: The bracketed index number of the date input element.
        date_value: Date string in 'YYYY-MM-DD' or 'MM/DD/YYYY' format.
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("input", params={"index": index, "text": date_value, "clear": True}, browser_session=browser)
        await asyncio.sleep(0.5)
        summary = await manager.get_page_summary()
        return f"Set date field {index} to '{date_value}'.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error setting date field {index}: {str(e)}"

@mcp.tool()
async def browser_handle_popup(action: str = "close") -> str:
    """Dismiss, close, or accept pop-ups, modals, cookie notices, or JS alerts on form pages.
    
    Args:
        action: 'close' (press Escape / click close), 'accept' (accept JS alert/confirm), or 'dismiss'.
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("send_keys", params={"keys": "Escape"}, browser_session=browser)
        await asyncio.sleep(0.5)
        summary = await manager.get_page_summary()
        return f"Handled pop-up with action '{action}'.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error handling pop-up: {str(e)}"

@mcp.tool()
async def browser_send_keys(keys: str) -> str:
    """Send special keyboard keys (e.g. 'Enter', 'Tab', 'Escape', 'ArrowDown').
    
    Args:
        keys: Key string (e.g. 'Enter', 'Tab', 'Escape').
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("send_keys", params={"keys": keys}, browser_session=browser)
        await asyncio.sleep(0.5)
        summary = await manager.get_page_summary()
        return f"Sent key '{keys}'.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error sending key '{keys}': {str(e)}"

@mcp.tool()
async def list_user_documents(search_query: Optional[str] = None) -> str:
    """List available documents (resumes, transcripts, cover letters, PDFs, DOCX) in ~/Documents and ~/Downloads so you can locate exact file paths for uploads.
    
    Args:
        search_query: Optional keyword to filter file names (e.g. 'resume', 'transcript', 'pdf').
    """
    try:
        search_dirs = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~")
        ]
        found_files = []
        extensions = [".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"]
        
        for sdir in search_dirs:
            if not os.path.exists(sdir): continue
            for root, dirs, files in os.walk(sdir):
                rel_depth = root.count(os.sep) - sdir.count(os.sep)
                if rel_depth > 2: continue
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in extensions:
                        full_path = os.path.join(root, f)
                        if search_query:
                            if search_query.lower() in f.lower():
                                found_files.append(full_path)
                        else:
                            found_files.append(full_path)
                            
        found_files = sorted(found_files)[:30]
        if not found_files:
            return "No matching document files found in ~/Documents or ~/Downloads."
        
        output = "Available User Documents:\n" + "\n".join([f"- {path}" for path in found_files])
        return output
    except Exception as e:
        return f"Error listing user documents: {str(e)}"

@mcp.tool()
async def browser_scroll(down: bool = True, pages: float = 1.0) -> str:
    """Scroll the active web page up or down.
    
    Args:
        down: True to scroll down, False to scroll up (default: True).
        pages: Number of page heights to scroll (default: 1.0).
    """
    try:
        browser = await manager.get_browser()
        res = await manager.controller.registry.execute_action("scroll", params={"down": down, "pages": pages}, browser_session=browser)
        await asyncio.sleep(1.0)
        summary = await manager.get_page_summary()
        return f"Scrolled {'down' if down else 'up'} {pages} pages.\n\nUpdated Page State:\n{summary[:3000]}"
    except Exception as e:
        return f"Error scrolling page: {str(e)}"

if __name__ == "__main__":
    mcp.run()
