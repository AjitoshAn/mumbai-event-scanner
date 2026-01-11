from bs4 import BeautifulSoup

with open("paytm_content.html", "r") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# List all links to see if we have event links
links = soup.find_all("a")
print(f"Found {len(links)} links.")

event_links = []
for link in links:
    href = link.get("href", "")
    if "/event/" in href:
        event_links.append(href)

print(f"Found {len(event_links)} event links.")
if event_links:
    print("Sample event links:")
    for l in event_links[:5]:
        print(l)

# Check for price text
prices = soup.find_all(string=lambda text: "₹" in text or "Rs." in text if text else False)
print(f"Found {len(prices)} price elements.")
if prices:
    first_price = prices[0]
    print(f"First price: {first_price}")
    
    # Traverse up to find the card container
    # Looking for the 'a' tag or the main card div
    parent = first_price.parent
    for i in range(6):
        print(f"Parent {i}: {parent.name} class={parent.get('class')}")
        if parent.name == 'a':
            print(f"Found Anchor: {parent.get('href')}")
            print(f"Card Text: {parent.get_text(separator=' | ', strip=True)}")
            break
        parent = parent.parent
        if parent is None:
            break
