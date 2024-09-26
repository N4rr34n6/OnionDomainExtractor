import os
import subprocess
import re
import concurrent.futures
import random

# Start the Tor service
subprocess.run(["sudo", "service", "tor", "start"])

def search_onionsearch():
    # Load keywords from a file
    keywords_file = "Keywords.txt"
    keywords = []
    with open(keywords_file, "r") as f:
        for line in f:
            keywords.append(line.strip())
    
    # Create a thread pool to run onionsearch for each keyword
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_onionsearch, keyword) for keyword in keywords]
        concurrent.futures.wait(futures)
    
    # Extract onion domains after search completion
    extract_onion_domains()

def run_onionsearch(keyword):
    # Run the onionsearch command with the specified keyword
    subprocess.run(["onionsearch", "--proxy=127.0.0.1:9050", "--continuous_write", "True", keyword])

def extract_onion_domains():
    # Extract and store the found .onion domains in a file
    with open("onion_domains_list.txt", "a") as f_out:
        for filename in os.listdir():
            if filename.startswith("output_") and filename.endswith(".txt"):
                with open(f"{filename}", "r") as f_in:
                    for line in f_in:
                        # Match .onion domain pattern
                        match = re.search(r"http://[a-zA-Z0-9]{56}\.onion", line)
                        if match:
                            # Write the domain without the protocol
                            f_out.write(match.group().replace("http://", "") + "\n")
    print("Los dominios '.onion' se han extraido y se han guardado en el archivo 'onion_domains_list.txt'")

def check_keywords():
    while True:
        # Check if the onion_domains_list.txt exists and is not empty
        if not os.path.exists("onion_domains_list.txt") or os.stat("onion_domains_list.txt").st_size == 0:
            print("El archivo 'onion_domains_list.txt' no existe o está vacío.")
            return
        
        processed_domains = set()
        keywords_file = "Keywords.txt"
        with open(keywords_file, "r", encoding="latin-1") as f:
            keywords = [line.strip() for line in f]
        
        # Load domains from the onion_domains_list.txt file
        with open("onion_domains_list.txt", "r") as f:
            domains = [line.strip() for line in f]
        
        random.shuffle(domains)  # Shuffle the domains to randomize processing
        with open("domains_to_scan.txt", "a+") as f_out, open("domains_no_match.txt", "a+") as f_no_match:
            existing_domains = f_out.read() + f_no_match.read()
            for domain in domains:
                if domain in processed_domains:
                    continue  # Skip already processed domains
                else:
                    processed_domains.add(domain)
                
                if domain in existing_domains:
                    continue  # Skip domains already classified
                
                # Fetch the domain content using torsocks and curl
                result = subprocess.run(["torsocks", "curl", "-s", domain], capture_output=True, text=True, encoding="ISO-8859-1")
                match = False
                for keyword in keywords:
                    # Check if any keyword matches the domain content
                    if re.search(keyword, result.stdout):
                        match = True
                        break
                
                # Write domain to respective file based on keyword match
                if match:
                    f_out.write(domain + "\n")
                else:
                    f_no_match.write(domain + "\n")
        print("Los dominios han sido clasificados y guardados en los archivos domains_to_scan.txt y domains_no_match.txt")

# Prompt user to start onionsearch
response = input("¿Deseas llevar a cabo la búsqueda con onionsearch? (s/n): ")
if response.lower() == "s":
    search_onionsearch()
else:
    print("La búsqueda no se llevará a cabo.")

# Start the keyword checking process in a separate thread
if __name__ == "__main__":
    process2 = multiprocessing.Process(target=check_keywords)
    process2.start()
    process2.join()
