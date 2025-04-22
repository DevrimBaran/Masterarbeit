import csv
import pathlib

def remove_duplicates(csv_path):
   """
   Remove duplicate rows in the CSV based on the 'url' field.
   """
   temp_path = csv_path.with_suffix('.tmp')
   seen = set()
   with csv_path.open('r', newline='', encoding='utf-8') as infile, \
      temp_path.open('w', newline='', encoding='utf-8') as outfile:
      reader = csv.DictReader(infile, delimiter=';')
      writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames, delimiter=';')
      writer.writeheader()
      for row in reader:
         url = row.get('url', '').strip()
         if url and url not in seen:
               seen.add(url)
               writer.writerow(row)
   temp_path.replace(csv_path)
   
def main():
   remove_duplicates(pathlib.Path('google_scholar.csv'))
   print("Done removing duplicates.")


if __name__ == '__main__':
   main()