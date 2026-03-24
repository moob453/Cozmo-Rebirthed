# Open the original file for reading and a new file for writing
with open('input.txt', 'r', encoding='utf-8') as infile, \
     open('output.txt', 'w', encoding='utf-8') as outfile:
    
    for line in infile:
        # Split the line into parts based on whitespace (tabs or spaces)
        parts = line.strip().split()
        
        # Check if the line has at least 2 parts to avoid errors on empty lines
        if len(parts) >= 2:
            # Extract the first two parts
            id_num = parts[0]
            name = parts[1]
            
            # Write them to the new file, separated by a tab
            outfile.write(f"{id_num}\t{name}\n")

print("Done! Check output.txt for the cleaned lines.")