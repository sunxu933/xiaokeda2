"""Playwright UI tests for xiaokeda application."""
from playwright.sync_api import sync_playwright
import sys

def run_tests():
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        try:
            # Test 1: Homepage loads
            print("Test 1: Homepage loads...")
            page.goto('http://localhost:5000/')
            page.wait_for_load_state('networkidle')
            title = page.title()
            assert '小课大' in title, f"Expected '小课大' in title, got: {title}"
            print(f"  ✓ Title: {title}")

            # Test 2: No student redirect
            print("Test 2: No student page shown...")
            content = page.content()
            assert '创建学生档案' in content or '设置学生' in content
            print("  ✓ No student page displayed correctly")

            # Test 3: Settings page loads
            print("Test 3: Settings page...")
            page.goto('http://localhost:5000/settings/')
            page.wait_for_load_state('networkidle')
            assert page.title()
            print(f"  ✓ Settings page: {page.title()}")

            # Test 4: AI config page loads
            print("Test 4: AI config page...")
            page.goto('http://localhost:5000/settings/ai-config')
            page.wait_for_load_state('networkidle')
            content = page.content()
            assert 'API' in content
            print("  ✓ AI config page loads correctly")

            # Test 5: Navigation works
            print("Test 5: Navigation elements...")
            page.goto('http://localhost:5000/')
            page.wait_for_load_state('networkidle')
            # Check navbar exists
            navbar = page.locator('nav.navbar')
            assert navbar.count() > 0
            print("  ✓ Navigation bar present")

            # Test 6: Sidebar (if student exists)
            print("Test 6: Checking page structure...")
            page.goto('http://localhost:5000/')
            page.wait_for_load_state('networkidle')
            main_content = page.locator('main.main-content')
            assert main_content.count() > 0
            print("  ✓ Main content area present")

            # Report console errors
            if console_errors:
                print(f"\n⚠ Console errors detected: {len(console_errors)}")
                for err in console_errors[:5]:
                    print(f"  - {err[:100]}")
                errors.append(f"Console errors: {len(console_errors)}")
            else:
                print("\n✓ No console errors detected")

        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            errors.append(str(e))
        finally:
            browser.close()

    # Summary
    print("\n" + "="*50)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    else:
        print("ALL UI TESTS PASSED ✓")
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())
