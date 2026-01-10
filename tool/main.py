import requests
import time
import traceback
import threading
from src.java_processing.java_processor import JavaProcessor
from src.template_processing.processor import Processor
from src.config import PROJECT_PATH, OUTPUT_JSON_DIR, TOKEN, CHAT_ID
from src.template_processing.saves.save_csv import JSONHandler
import sys
import os
import re
from src.template_processing.individual_process.individual_practices import IndividualPractices
from src.template_processing.saves.save_individual import SaveIndividual


# Initialization of processing
java_processor = JavaProcessor(PROJECT_PATH, OUTPUT_JSON_DIR)

# processor = Processor("./src/llms_and_prompts/templates/Chatgpt")

# Initialization of variables
llm = None
llm4 = None
save_csv = None
llm_name = None
telegram = None
save_individual = None

# Event to signal threads to exit
exit_event = threading.Event()


# Function to list available template versions
def list_template_versions(model_type, template_id):
    template_dir = f"./src/llms_and_prompts/templates/Chatgpt/t{template_id}"
    
    if not os.path.exists(template_dir):
        return []

    # Listar arquivos que seguem o formato t{template_id}_V{version}.txt
    versions = [f for f in os.listdir(template_dir) 
                if os.path.isfile(os.path.join(template_dir, f)) and 
                f.startswith(f"t{template_id}_V") and f.endswith(".txt")]

    # Ordenar numericamente pela versão V#
    def extract_version(filename):
        match = re.search(r'_V(\d+)\.txt$', filename)
        return int(match.group(1)) if match else -1

    versions.sort(key=extract_version)

    return versions


# Function to choose the LLM model
def choose_llm():
    global llm, llm_name

    options = {
        "1": ("gpt-3.5-turbo", 1),
        "2": ("gpt-4o-mini", 2),
        "3": ("gpt-4.1", 3),
        "4": ("gpt-4.1-mini", 4)
    }

    print("\n[+] Available LLM Models:")
    print("    1 - ChatGPT-3.5-turbo")
    print("    2 - ChatGPT-4o-mini")
    print("    3 - ChatGPT-4.1")
    print("    4 - ChatGPT-4.1-mini")

    while True:
        llm_type = input("Choose the model you want to use (1/2/3/4): ").strip()

        if llm_type in options:
            llm_name, llm = options[llm_type]
            print(f"\n[+] Selected LLM Model: {llm_name}")
            break
        else:
            print("[!] Invalid option! Choose 1, 2, 3 or 4.")


# Function to send messages via the bot
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)


# Function to fetch new messages from Telegram
def get_updates(last_update_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 10}
    response = requests.get(url, params=params).json()
    return response.get("result", [])

# Function to notify user via Telegram if enabled
def notify(message, telegram=telegram):
    if telegram:
        send_telegram_message(message)


# Function to process normal prompts
def process_command(command):
    global llm, llm_name, save_csv, java_processor, joern_processor, processor, telegram
    
    if command in ["1", "2", "3"]:
        notify(f"✅ Processing Template {command}...")

        versions = list_template_versions(llm_name.lower(), command)
        if versions:
            versions_message = f"📜 Available versions for Template {command}:\n"
            versions_message += "\n".join([f"{i+1}. {v}" for i, v in enumerate(versions)])

            notify(versions_message)

            version_choice = input(
                f"\nChoose the version for Template {command} \nAvailable: \n" +
                "\n".join([f"{i+1}. {v}" for i, v in enumerate(versions)]) +
                "\nYour choice: "
            ).strip()
            
            try:
                version_choice = int(version_choice)
                if 1 <= version_choice <= len(versions):
                    selected_version = versions[version_choice - 1]
                    notify(f"✅ Version {selected_version} selected for Template {command}.")
                    
                    print(f"\n[+] Processing Template {command} with version {selected_version}...")

                    save_csv.run(version_choice, command)
                    
                    # processor.processing_template(
                    #     selected_version, llm, java_processor, PROJECT_PATH,
                    #     METHODS_JSON_PATH, "./src/joern_processing/output_joern_process/summary.json",
                    #     joern_processor, save_csv, id=int(command)
                    # )

                    notify(f"✅ Template {command} with version {selected_version} completed!")
                else:
                    print("[!] Invalid version selected.")
                    notify("❌ Invalid version selected.")
            except ValueError:
                print("[!] Invalid input. Please enter a valid number.")
                notify("❌ Invalid input. Please enter a valid number.")
        else:
            print("[!] No versions available for this template.")
            notify("❌ No versions available for this template.")


# Function to process individual practices
def individual_practices():
    global llm, llm_name, save_individual, java_processor, telegram
    
    notify("🔄 Processing individual practices...")
    
    try:
        choice = input("Choose an version (1/2/4/5): ").strip().lower()

        version = "a" if choice not in ["2"] else input("Enter the sub-version (A/B): ").strip().lower()

        llm_paths = {
            1: "gpt-3.5-turbo",
            2: "gpt-4o-mini",
            3: "gpt-4.1",
            4: "gpt-4.1-mini"
        }
        base_name = llm_paths.get(llm, "unknown")

        followed_path = f"./src/llms_and_prompts/prompts/{base_name}/individual_practices_prompts/prompt_{choice}/followed/{version}"
        applicable_path = f"./src/llms_and_prompts/prompts/{base_name}/individual_practices_prompts/prompt_{choice}/applicability/a"
        results_path = f"./src/test_results/individual_practices/{base_name}/prompt_{choice}_{version}"

        
        runner = IndividualPractices(followed_path, applicable_path)

        save_individual = SaveIndividual(PROJECT_PATH, results_path)
        save_individual.run()

        if choice == "4":
            runner.run_prompt4(java_processor, PROJECT_PATH, save_individual, llm)
        if choice == "5":
            runner.run_prompt5(java_processor, PROJECT_PATH, save_individual, llm)
        else:
            runner.run(choice, java_processor, PROJECT_PATH, save_individual, llm)

        notify(f"✅ Individual practices {choice.upper()}{version.upper()} completed!")


    except Exception as e:
        error_msg = f"❌ Error in individual practices processing!\n{traceback.format_exc()}"
        print(error_msg)
        notify(error_msg)


# Function to capture commands from the terminal
def terminal_input():
    while True:
        
        print("\n[+] Available options:")
        print("    1, 2, 3 - Process templates")
        print("    4 - Process individual practices")
        print("    model   - Change the LLM model")
        print("    exit    - Exit the program")
        
        choice = input("Choose an option: ").strip().lower()

        if choice in ["1", "2", "3", "model", "exit"]:
            process_command(choice)
        elif choice == "4":
            individual_practices()
        else:
            print("[!] Invalid choice. Try again.")


# Function to capture commands from Telegram
def telegram_input():
    global llm_name
    
    send_telegram_message("🔄 Tool is running...")
    send_telegram_message(f"✅ Bot is active! 🌀 Running LLM {llm_name}...")
    
    last_update_id = 0
    
    while True:
        try:
            updates = get_updates(last_update_id)
            
            for update in updates:
                message = update.get("message", {}).get("text", "").strip().lower()
                update_id = update["update_id"]
                
                if update_id > last_update_id:
                    last_update_id = update_id
                    process_command(message)
        
        except Exception as e:
            error_msg = f"❌ Error!\n{traceback.format_exc()}"
            
            send_telegram_message(error_msg)
        time.sleep(5)


# Main function
def main():
    global telegram
    telegram = input("Telegram Message (1. Yes, 2. No): ").strip().lower()
    try:
        choose_llm()

        global save_csv
        save_csv = JSONHandler(PROJECT_PATH)

        match telegram:
            case "1":
                telegram = 1
                # Create two threads to run inputs simultaneously
                thread_terminal = threading.Thread(target=terminal_input, daemon=True)
                thread_telegram = threading.Thread(target=telegram_input, daemon=True)

                thread_terminal.start()
                thread_telegram.start()

            case "2":
                telegram = None
                thread_terminal = threading.Thread(target=terminal_input, daemon=True)
                thread_terminal.start()

        # Wait for threads to finish or handle Ctrl+C
        while not exit_event.is_set():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[!] KeyboardInterrupt detected. Exiting...")
        
        exit_event.set()  # Signal threads to stop
        if telegram == "1":
            send_telegram_message("⛔ The script was terminated via KeyboardInterrupt!")

    except Exception as e:
        error_msg = f"❌ Error!\n{traceback.format_exc()}"
        print(error_msg)
        if telegram == "1":
            send_telegram_message(error_msg)
        print("[!] Exiting the tool due to an error.")
        
        exit_event.set()
        
        if telegram == "1":
            send_telegram_message("⛔ The script was terminated due to an error!")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()