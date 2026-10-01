import asyncio
import os
import sys
import random
import subprocess
import logging
from typing import Optional, Dict, Any, List

from browser_use import Agent, Browser, BrowserProfile, Controller, ActionResult
from browser_use.llm import ChatOpenAI

logger = logging.getLogger("browser_engine")

LM_STUDIO_URL = "http://localhost:1234/v1"
DEFAULT_CDP_URL = "http://localhost:9222"
DEFAULT_BRAVE_PATH = "/usr/bin/brave-browser"

COMPRESSED_SYSTEM_PROMPT = """You are a browser agent specialized in form filling (scholarships, internships, applications), web search, and multi-tab navigation.
PHASE 1: DRAFT A PLAN. Break the task into Steps, each with Subtasks.
PHASE 2: EXECUTE. Perform one subtask at a time.

DISAMBIGUATION & SELECTION RULES:
1. TYPING INPUT FIELDS: When executing 'input' or 'browser_type', ALWAYS choose an element index for an <input>, <textarea>, or [contenteditable] field. NEVER select <a> links or <div> containers.
2. BUTTON CLICKS: For form submissions, prioritize <button>, <input type="submit">, or [role=button] element indices.
3. SEARCHING & TABS: Use 'browser_search_query(query)' to search without needing a URL (uses Brave Search). Use 'browser_list_tabs' and 'browser_switch_tab' to manage multiple open tabs.

Output JSON only:
{
  "thinking": "Plan: Step 1 (a,b), Step 2... Current: Step X, Subtask Y",
  "evaluation_previous_goal": "success/fail",
  "memory": "key facts",
  "next_goal": "next subtask",
  "current_plan_item": 1,
  "plan_update": ["Step 1: Done", "Step 2: In Progress"],
  "action": [{"click": {"index": 1}}]
}
Actions: click(idx), input(idx, text, clear), browser_search_query(query), browser_list_tabs(), browser_switch_tab(tab_id_or_index), browser_type_smart(label, text), browser_click_button(label), upload_file(idx, path), select_dropdown(idx, text), navigate(url), wait(sec), switch_tab(tab_id), scroll(down, pages), done(text, success).
Indices are in [brackets]. Use vision=False."""

class BrowserEngineManager:
    """Singleton manager for persistent browser sessions across tool calls."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserEngineManager, cls).__new__(cls)
            cls._instance.browser = None
            cls._instance.controller = Controller()
            cls._instance.lock = asyncio.Lock()
        return cls._instance

    async def _cleanup_old_browser_instances(self):
        """Clean up any orphan/previous automated browser processes so only ONE browser window exists."""
        try:
            if self.browser is not None:
                try:
                    await self.browser.stop()
                except Exception:
                    pass
                self.browser = None

            # Kill lingering debug browser processes on port 9222 to prevent multiple windows
            subprocess.run(["pkill", "-f", "remote-debugging-port=9222"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")

    async def get_browser(self, cdp_url: Optional[str] = DEFAULT_CDP_URL) -> Browser:
        async with self.lock:
            # Re-use current active browser instance if connected
            if self.browser is not None and getattr(self.browser, 'is_cdp_connected', False):
                return self.browser

            # If opening a fresh session or restarting, clean up any previous browser instances first
            await self._cleanup_old_browser_instances()

            # Attach to existing open CDP browser on port 9222 if available
            try:
                import urllib.request
                urllib.request.urlopen(f"{cdp_url}/json/version", timeout=1)
                profile = BrowserProfile(cdp_url=cdp_url, keep_alive=True)
                logger.info(f"Attached to open browser session at {cdp_url}")
            except Exception:
                logger.info("CDP port 9222 not active. Launching single persistent visible Brave browser window...")
                profile = BrowserProfile(headless=False, executable_path=DEFAULT_BRAVE_PATH, args=["--profile-directory=Default", "--remote-debugging-port=9222"], keep_alive=True)

            self.browser = Browser(browser_profile=profile, keep_alive=True)
            await self.browser.start()
            if self.controller is None:
                self.controller = Controller()
            return self.browser

    async def get_page_summary(self) -> str:
        browser = await self.get_browser()
        return await browser.get_state_as_text()

    async def execute_task(self, task: str, max_steps: int = 20, model_name: str = "local-model") -> str:
        browser = await self.get_browser()
        llm = ChatOpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio", model=model_name, temperature=0.0)
        
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            controller=self.controller or Controller(),
            use_vision=False,
            max_actions_per_step=1,
            max_clickable_elements_length=8000,
            include_attributes=['href', 'title', 'aria-label', 'role', 'placeholder', 'type', 'value', 'name', 'accept'],
            override_system_message=COMPRESSED_SYSTEM_PROMPT,
            enable_planning=True,
            llm_timeout=120
        )

        steps = 0
        while not agent.history.is_done() and steps < max_steps:
            if len(agent.history.history) > 10:
                agent.history.history = agent.history.history[:2] + agent.history.history[-5:]
            await agent.step()
            steps += 1

        return agent.history.final_result() or "Task execution finished."

    async def close(self):
        async with self.lock:
            await self._cleanup_old_browser_instances()
