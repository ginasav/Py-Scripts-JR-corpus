import re
results = re.findall(r'\b\w+\b', "l'isola è bella")
print(results)  # Output: ['l', 'isola', 'è', 'bella']