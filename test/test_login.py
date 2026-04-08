from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def test_student_login(driver):
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(2)

    driver.find_element(By.NAME, "email").send_keys("manojkonda2005@gmail.com")
    driver.find_element(By.NAME, "password").send_keys("manoj kumar.33")
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

    time.sleep(3)

    assert "student" in driver.current_url
