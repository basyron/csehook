from time import sleep

from csehook import CseHook, WiredDriver


if __name__ == "__main__":
    wired_driver = WiredDriver()
    try:
        cse_hook = CseHook(
            "https://cse.google.com/cse?cx=8d57d6f6129439b92",
            wired_driver)

        pages_results = cse_hook.search("cards")
        for results in pages_results:
            sleep(3)
            for r in results:
                print(r.get("url"))
    except Exception as error:
        print(error)
    finally:
        wired_driver.instance.close()
