from config import KEEP_TEMP_FILES, IGNORE_VERSION_CHECK, MOCK_OLD_DATE, KEEP_OUTDATED_DATA, USE_LIVE_MONGODB

def main():
    errors = []

    test_flags = {
        "KEEP_TEMP_FILES": KEEP_TEMP_FILES,
        "IGNORE_VERSION_CHECK": IGNORE_VERSION_CHECK,
        "MOCK_OLD_DATE": MOCK_OLD_DATE,
        "KEEP_OUTDATED_DATA": KEEP_OUTDATED_DATA,
        "USE_LIVE_MONGODB": USE_LIVE_MONGODB,
    }

    for name, value in test_flags.items():
        if value:
            errors.append(f"{name} is True, must be False before committing to main")

    if errors:
        print("\n".join(errors))
        exit(1)  # Fail the CI build
    else:
        print("Success: all test flags are False")

if __name__ == "__main__":
    main()