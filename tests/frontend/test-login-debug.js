import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Listen to console messages
  page.on('console', msg => {
    console.log(`[BROWSER CONSOLE ${msg.type()}]:`, msg.text());
  });

  // Listen to page errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR]:`, error.message);
  });

  try {
    console.log('🚀 Navigating to home page...');
    await page.goto('http://localhost:4001');
    await page.waitForLoadState('networkidle');
    
    console.log('📸 Taking screenshot of home page...');
    await page.screenshot({ path: 'home-page.png' });
    
    console.log('🔗 Clicking Sign In button...');
    await page.click('text=Sign In');
    await page.waitForLoadState('networkidle');
    
    console.log('📸 Taking screenshot of login page...');
    await page.screenshot({ path: 'login-page.png' });
    
    console.log('📝 Filling username field...');
    await page.fill('#username', 'roberdan');
    
    console.log('📝 Filling password field...');
    await page.fill('#password', 'admin123');
    
    console.log('📸 Taking screenshot after filling fields...');
    await page.screenshot({ path: 'login-filled.png' });
    
    // Check button state
    const buttonDisabled = await page.getAttribute('button[type="submit"]', 'disabled');
    console.log('🔘 Button disabled status:', buttonDisabled !== null);
    
    // Get debug info if available
    const debugInfo = await page.textContent('.text-xs:has-text("Debug:")').catch(() => 'Debug info not found');
    console.log('🐛 Debug info:', debugInfo);
    
    // Check form values
    const usernameValue = await page.inputValue('#username');
    const passwordValue = await page.inputValue('#password');
    console.log('📋 Username value:', usernameValue);
    console.log('📋 Password value:', passwordValue);
    
    if (buttonDisabled === null) {
      console.log('✅ Button is enabled, attempting login...');
      await page.click('button[type="submit"]');
      
      // Wait for potential redirect or error
      await page.waitForTimeout(3000);
      
      console.log('📍 Current URL:', page.url());
      console.log('📸 Taking screenshot after login attempt...');
      await page.screenshot({ path: 'after-login.png' });
    } else {
      console.log('❌ Button is disabled, cannot proceed with login');
    }
    
  } catch (error) {
    console.error('❌ Error during test:', error.message);
    await page.screenshot({ path: 'error-screenshot.png' });
  } finally {
    await browser.close();
  }
})();