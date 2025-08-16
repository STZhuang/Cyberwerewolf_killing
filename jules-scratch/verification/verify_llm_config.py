from playwright.sync_api import sync_playwright, expect

def verify_llm_config_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the settings page
            page.goto("http://localhost:5173/settings", timeout=60000)

            # The page should have the title "设置" (Settings) or something similar.
            # Let's wait for the LLM config panel to be visible.
            llm_panel = page.locator(".llm-config-panel")
            expect(llm_panel).to_be_visible()

            # The tabs should be visible. Let's find the tabs for the roles.
            gm_tab = page.get_by_role("tab", name="GM")
            expect(gm_tab).to_be_visible()

            werewolf_tab = page.get_by_role("tab", name="狼人")
            expect(werewolf_tab).to_be_visible()

            # Click on the "狼人" (Werewolf) tab to show that the tabs are functional
            werewolf_tab.click()

            # Wait for the form for the werewolf to be visible
            # It's better to locate something specific inside the form
            model_id_input = page.locator('.role-config-form').locator('input[placeholder="例如: gpt-4o-mini"]')
            expect(model_id_input).to_be_visible()

            # Take a screenshot of the settings page with the new UI
            page.screenshot(path="jules-scratch/verification/llm-config-ui.png")

            print("Screenshot taken successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")
            # Take a screenshot even if it fails, for debugging
            page.screenshot(path="jules-scratch/verification/error.png")

        finally:
            browser.close()

if __name__ == "__main__":
    verify_llm_config_ui()
