from selenium.webdriver.common.by import By
import time

def test_faculty_login(driver):
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(2)

    driver.find_element(By.NAME, "email").send_keys("manojkumar87122@gmail.com")
    driver.find_element(By.NAME, "password").send_keys("manoj kumar.33")
    driver.find_element(By.NAME, "password").submit()

    time.sleep(3)

    assert "faculty" in driver.current_url
