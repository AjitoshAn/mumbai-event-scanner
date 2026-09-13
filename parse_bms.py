from bs4 import BeautifulSoup

with open("bms_content.html", "r") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find all elements containing "₹"
price_elements = soup.find_all(string=lambda text: "₹" in text if text else False)

print(f"Found {len(price_elements)} price elements.")

if price_elements:
    first_price = price_elements[0]
    print(f"First Price: {first_price}")
    
    # Traverse up to find the card container
    # Based on previous output: Parent 4 is 'a' tag
    card = first_price.find_parent('a')
    if card:
        print(f"Card found: {card.name} class={card.get('class')}")
        print(f"Card URL: {card.get('href')}")
        
        # Dump text content of the card to see what we have
        print(f"Card Text: {card.get_text(separator=' | ', strip=True)}")
        
        # Try to identify specific fields
        # Usually Title is in a div with specific font weight or color
        # We can try to guess based on position

