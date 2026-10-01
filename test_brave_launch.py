import asyncio
from browser_use import Browser, BrowserProfile

async def test():
    print("🚀 Attempting to launch Brave with a fresh profile...")
    # Not specifying user_data_dir creates a fresh temporary profile
    profile = BrowserProfile(
        headless=False,
        executable_path='/usr/bin/brave-browser'
    )
    browser = Browser(browser_profile=profile)
    try:
        await browser.start()
        print("✅ Browser started successfully!")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"❌ Failed to start browser: {e}")
    finally:
        await browser.stop()
        print("🛑 Browser stopped.")

if __name__ == "__main__":
    asyncio.run(test())
