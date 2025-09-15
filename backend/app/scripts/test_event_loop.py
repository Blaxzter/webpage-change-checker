# app/scripts/test_event_loop.py
"""
Test script to verify that the event loop policy works correctly
for both database operations and Playwright on Windows.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))


async def test_database_connection():
    """Test that database operations work with the current event loop."""
    try:
        from app.core.db import async_session
        
        print("🔍 Testing database connection...")
        
        async with async_session() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            
            if row and row.test == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database query failed")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_playwright_setup():
    """Test that Playwright works with the current event loop."""
    try:
        from playwright.async_api import async_playwright
        
        print("🔍 Testing Playwright setup...")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        
        page = await browser.new_page()
        await page.goto("https://httpbin.org/json")
        
        content = await page.content()
        if "httpbin" in content.lower():
            print("✅ Playwright works correctly")
            success = True
        else:
            print("❌ Playwright page load failed")
            success = False
            
        await browser.close()
        await playwright.stop()
        
        return success
        
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Testing Event Loop Compatibility")
    print("=" * 50)
    
    # Show current event loop info
    loop = asyncio.get_running_loop()
    print(f"📊 Current event loop: {type(loop).__name__}")
    
    if sys.platform == "win32":
        policy = asyncio.get_event_loop_policy()
        print(f"📊 Event loop policy: {type(policy).__name__}")
    
    print()
    
    # Test database
    db_success = await test_database_connection()
    print()
    
    # Test Playwright
    playwright_success = await test_playwright_setup()
    print()
    
    # Summary
    print("=" * 50)
    if db_success and playwright_success:
        print("🎉 All tests passed! Event loop is compatible with both systems.")
        return True
    else:
        print("💥 Some tests failed. Check your setup.")
        return False


if __name__ == "__main__":
    # Set the correct event loop policy for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("🪟 Set WindowsSelectorEventLoopPolicy for Windows compatibility")
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🔄 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        sys.exit(1)

