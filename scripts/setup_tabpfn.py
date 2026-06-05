import os
import sys

def main():
    print("==========================================================")
    print("          TabPFN v2 Token Configuration Helper            ")
    print("==========================================================")
    print("\nTabPFN v2 (Prior Labs) requires a free API key for local weight download.")
    print("To obtain your token:")
    print("  1. Open https://ux.priorlabs.ai in a web browser.")
    print("  2. Register or log in.")
    print("  3. Navigate to the 'Licenses' tab and accept the license.")
    print("  4. Navigate to the 'Account' tab and copy your API Key.")
    print("\n----------------------------------------------------------")

    env_path = ".env"
    existing_token = None

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("TABPFN_TOKEN="):
                    existing_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break

    if existing_token:
        print(f"Current TABPFN_TOKEN configured: {existing_token[:6]}...{existing_token[-4:] if len(existing_token) > 10 else ''}")
        change = input("Do you want to update this token? (y/N): ").strip().lower()
        if change != 'y':
            print("Configuration left unchanged.")
            return
    
    token = input("Enter your TabPFN API Key/Token: ").strip()
    if not token:
        print("Error: Token cannot be empty.")
        return

    # Update or append in .env
    lines = []
    updated = False
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("TABPFN_TOKEN="):
                    lines.append(f'TABPFN_TOKEN="{token}"\n')
                    updated = True
                else:
                    lines.append(line)
    
    if not updated:
        lines.append(f'\n# TabPFN API key for local deep learning inference\nTABPFN_TOKEN="{token}"\n')

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\n[SUCCESS] TABPFN_TOKEN has been saved to your .env file!")
    print("You can now run model training with local TabPFN enabled.")

if __name__ == "__main__":
    main()
