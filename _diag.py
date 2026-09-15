import requests
from bs4 import BeautifulSoup

r = requests.get('https://safepay.pk/pricing', headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')
main = soup.find('main')

# Find all pricing cards (sections with bg-primary-grey)
cards = main.find_all('section', class_=lambda c: c and 'bg-primary-grey' in c)
print(f'Found {len(cards)} pricing cards\n')
for card in cards:
    # Get all h4 headings in order
    h4s = [h.get_text(strip=True) for h in card.find_all('h4')]
    # Get description paragraphs
    ps = [p.get_text(' ', strip=True) for p in card.find_all('p') if p.get_text(strip=True)]
    print('CARD:')
    print('  h4s:', h4s)
    print('  ps:', ps[:3])
    print()