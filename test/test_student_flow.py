from selenium.webdriver.common.by import By
import time

def test_submit_skill(driver):
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(2)

    driver.find_element(By.NAME, "email").send_keys("manojkonda2005@gmail.com")
    driver.find_element(By.NAME, "password").send_keys("manoj kumar.33")
    driver.find_element(By.NAME, "password").submit()

    time.sleep(3)

    # navigate to the correct student route (route is /student/submit-skill)
    driver.get("http://127.0.0.1:5000/student/submit-skill")
    time.sleep(1)  # give it a moment to render

    driver.find_element(By.NAME, "skill_name").send_keys("Python")
    # choose category by clicking the matching option rather than send_keys
    cat_select = driver.find_element(By.NAME, "category")
    for opt in cat_select.find_elements(By.TAG_NAME, "option"):
        if opt.get_attribute("value") == "Programming":
            opt.click()
            break
    # proof_type is required; choose value via clicking option
    proof_select = driver.find_element(By.NAME, "proof_type")
    for option in proof_select.find_elements(By.TAG_NAME, "option"):
        if option.get_attribute("value") == "github":
            option.click()
            break
    driver.find_element(By.NAME, "description").send_keys("Completed Python course")

    # submit the form directly (avoids click interception problems)
    form = driver.find_element(By.TAG_NAME, "form")
    driver.execute_script("arguments[0].scrollIntoView(true);", form)
    form.submit()

    time.sleep(3)

    # should be redirected away from submit-skill (dashboard or similar)
    assert "/student/dashboard" in driver.current_url or "dashboard" in driver.current_url

    # navigate to public profile via share profile button and verify QR image exists with download link
    share_btn = driver.find_element(By.LINK_TEXT, "Share Profile")
    share_btn.click()
    time.sleep(2)
    # look for image within an anchor that has download attribute
    qr_anchor = driver.find_element(By.CSS_SELECTOR, "a[href^='data:image/png'][download]")
    assert qr_anchor is not None
    qr_img = qr_anchor.find_element(By.TAG_NAME, "img")
    assert qr_img.get_attribute("src").startswith("data:image/png;base64,")
