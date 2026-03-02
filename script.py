import pandas
from parsel import Selector
from pathlib import Path

url = Path("./webpages/2025_worldchamps.html")

html = url.read_text(encoding="utf-8")
sel = Selector(text=html)

# print("Page loaded successfully.")
# print("Length of HTML:", len(html))

# # Test: print page title
# title = sel.css("title::text").get()
# print("Page title:", title)