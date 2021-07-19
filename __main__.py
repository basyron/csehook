from random import randint, shuffle
from time import sleep

from english_words import english_words_lower_set

from config import CSE_URI, RENEW_CSE_DEFAULT
from csehook import CseHook, WiredDriver


if __name__ == "__main__":
    wired_driver = WiredDriver()
    amount_of_requests = 0
    try:
        cse_hook = CseHook(CSE_URI, wired_driver)

        english_words_list = list(english_words_lower_set)
        shuffle(english_words_list)

        # When reaches 0, its time to renew client-side URIs.
        requests_to_reload_cse_uris = RENEW_CSE_DEFAULT

        for word in english_words_list:
            if requests_to_reload_cse_uris <= 0:
                pages_results = cse_hook.search(word, renew_cse_uris=True)
                requests_to_reload_cse_uris = RENEW_CSE_DEFAULT
            else:
                pages_results = cse_hook.search(word)

            # It returns bool (False) if temporary ban was imposed.
            if isinstance(pages_results, bool) and not pages_results:
                break

            for results in pages_results:
                print(results)
                amount_of_requests += 1
                print(amount_of_requests)

                requests_to_reload_cse_uris -= 1

    finally:
        print(f"Number of requests: {amount_of_requests}")
        wired_driver.instance.close()
