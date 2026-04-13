from phase1_agent.tools import TavilySearch, JinaScrape

s = TavilySearch()
scraper = JinaScrape()

# What does his personal site actually contain?
print('=== ishankumax.me ===')
r = scraper.scrape('https://ishankumax.me')
if r:
    print(len(r.content), 'chars')
    print(r.content[:1000])

print()

# What does InTheBox website have?
print('=== inthebox.co.in ===')
r2 = scraper.scrape('https://inthebox.co.in')
if r2:
    print(len(r2.content), 'chars')
    print(r2.content[:800])