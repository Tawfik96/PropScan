
## (7/4/2026)Run — (13:44)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (520 words, 3184 chars, 1874 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*EL Rehab*
Apartment Available For Rent:
Bua: 255sqm.
___
3 Bedrooms.
3 Bathrooms.
Living room.
3 Balconies.
___
NG.
___
Price : 38k ...

--- AD 2 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate*
Apartment Available For Rent:
Prime Location ✨ 
2th Floor.
Bua: 150sqm.
____
2 Bedrooms.
2 Bathrooms.
____
AC'S and Kitchen Cabinets.
Garage.
____
Price: 35k ...

--- AD 3 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Madinaty*
Apartment Available For Rent:
Prime Location ✨ 
____
2 Bedrooms.
2 Bathrooms.
Fully furnished.
____
Facing North (bahary).
Garden View.

Price 25k per month ...

--- AD 4 (from: +20
[truncated — 3,183 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (534 words, 5184 chars, 2002 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 38000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "EL Rehab",
    "ad_snippet": "Apartment Available For Rent:\nBua: 255sqm.\n___ \n3 Bedrooms.\n3 Bathrooms.\nLiving room.\n3 Balconies.\n___ \nNG.\n___ \nPrice : 38k ...",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Village Gate",
    "ad_snippet": "Apartment Available For Rent:\nPrime Location ✨ \n2th Floor.\nBua: 150sqm.\n____\n2 Bedrooms.\n2 Bathrooms.\n____\nAC'S and Kitchen Cabinets.\nGarage.\n____\nPric
[truncated — 5,184 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (441) words, (5184) chars, 3950 tokens)</summary>

```
**JSON Data Extraction and Formatting**

Okay, so I'm tasked with taking these real estate ads and transforming them into a structured JSON array. I need to be precise and ensure each listing gets its own object with specific key-value pairs: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, `ad_snippet`, and `ad_index`. The `ad_index` is straightforward; I'll just use the provided index number. I have to process each advertisement separately.

I have reviewed each of the ads, one by one, to normalize the data. I have paid careful attention to price parsing, converting "k" or commas or periods to numeric values and the correct price based on the currency.
[truncated — 3,362 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (212 words, 1314 chars, 980 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code Mi648
Apartment for rent in mivida 
Boulevard 
Area 238m
4 bedrooms 
3 bathrooms 
Maids room with bathroom 
Ultra super lux
Furnished 
Price 3000$

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:58:00) ---
Code mvhpr306
Apartment for rent in mountain view hyde park
Area 203m
3 bedrooms 
3 bathrooms 
Dressing 
Super luxury
Furnished 
Price 60k

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:58:00) ---
code ncc1484
Apartment for sale in stone residence 
2nd floor
Area 175m
3 bedrooms
3 bathrooms 
3 terrace 
Reception 3 pieces 
3 balcony with double view
 semi finished 
Price 6,509,000

--- AD 4 (from: +20 11 03387
[truncated — 1,313 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (234 words, 2198 chars, 834 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 3000,
    "currency": "USD",
    "bedrooms": 4,
    "compound_name": "mivida",
    "ad_snippet": "Apartment for rent in mivida \nBoulevard \nArea 238m\n4 bedrooms \n3 bathrooms \nMaids room with bathroom \nUltra super lux\nFurnished \nPrice 3000$",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 60000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "mountain view hyde park",
    "ad_snippet": "Apartment for rent in mountain view hyde park\nArea 203m\n3 bedrooms \n3 bathrooms \nDressing \nSuper luxury\nFurnished \nPrice 60k",
    "ad_in
[truncated — 2,198 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (415) words, (2198) chars, 1281 tokens)</summary>

```
**My Processing Plan for Real Estate Ad Extraction**

Okay, so I need to get this done. My objective is to build a JSON array from real estate advertisements. Each object in the array will represent a single listing and must contain the following fields: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, `ad_snippet`, and `ad_index`.

The core of the task is to process each ad block individually, applying the transformation logic consistently. Let's walk through each example, making sure I cover all the variations.

**AD 1:** This is straightforward. "Apartment", "rent", "3000$", "4 bedrooms", "mivida", and the ad snippet.  I need to convert "Apartment" to
[truncated — 2,714 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 1874 | 2002 | 3950 | 0 | $0.00257 | 23.80 | 21.01 |
| 2 | 6 | 6 | 6 | 980 | 834 | 1281 | 0 | $0.00094 | 11.89 | 11.19 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 35.69 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17.85 | 16.10 | 1427 | 1418 | 366 | 384 | 10.0 | 0.56 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 2854 | $0.00029 | 1427 |
| output | 2836 | $0.00113 | 1418 |
| thinking | 5231 | $0.00209 | 2616 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.003512**


**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (7/4/2026)Run — (14:40)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 4 | 1 | 32_messages_30_03_2025.txt |

### Batch 1/4


**Input**

<details>
<summary>▶ Show input text (327 words, 1972 chars, 1356 tokens)</summary>

```
--- AD 1 (from: +20 11 11885910, date: 2025-03-30T00:06:00) ---
Code ESr242
Apartment for rent in Eastown 
Area 220 SQM
3 bedrooms (1master & dressing) 
3 bathrooms 
Reception 
Kitchen 
ACs
Price 60k

--- AD 2 (from: +20 10 08378787, date: 2025-03-30T00:11:00) ---
Any available units
rent 
3 bed rooms
200m 
Empty 
Mivida

--- AD 3 (from: +20 11 11885910, date: 2025-03-30T00:14:00) ---
Update price
Code ESr196
Apartment for rent in Eastown 
Area 216 SQM
1st floor 
3 bedrooms (1 master)
3 bathrooms 
Reception 
Laundry Room 
Fully furnished 
Kitchen with appliances 
ACs
Price 150k

--- AD 4 (from: +20 10 09337264, date: 2025-03-30T00:50:00) ---
شقه ايجار ف سوديك فيلت ريزيدنس
فيو بحيرات 
3 غرف ن
[truncated — 1,971 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (366 words, 3025 chars, 1138 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 60000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "ad_snippet": "Apartment for rent in Eastown Area 220 SQM 3 bedrooms (1master & dressing) 3 bathrooms Reception Kitchen ACs Price 60k",
    "ad_index": 1
  },
  {
    "property_type": null,
    "transaction_type": "rent",
    "price": null,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Mivida",
    "ad_snippet": "Any available units rent 3 bed rooms 200m Empty Mivida",
    "ad_index": 2
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 150000,
    "currency": "EGP",
   
[truncated — 3,025 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (303) words, (3025) chars, 2088 tokens)</summary>

```
**JSON Data Extraction and Formatting**

Okay, so I'm tackling this real estate data extraction task. The goal is to take a set of ad snippets and transform them into a clean JSON array of structured objects.  I'm focusing on key fields for each ad: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, `ad_snippet`, and `ad_index`.

I'm processing each ad block independently. Here's the breakdown of my thought process for each:

*   **Property Type:** I'm standardizing property types (e.g., "Apartment", "Duplex", "Studio"). If a type isn't explicitly stated or is vague (like "units"), I'll set it to null.  I'm also handling Arabic translations where present (
[truncated — 1,984 chars total]
```

</details>


---

### Batch 2/4


**Input**

<details>
<summary>▶ Show input text (315 words, 1977 chars, 1208 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨sale in Eastown 🚨
Code ESs229
Apartment for sale in Eastown 
Area 156 SQM 
2 bedrooms ( 1 master & dressing ) 
3 bathrooms 
Fully furnished 
Kitchen 
ACs 
View Landscape 
*Price* 
Fully furnished 14,600,000
 Unfurnished 13,650,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
Available 
Code ESs236
Apartment ground floor with garden for sale in Eastown 
Area 156 SQM
Garden 120 SQM
3 bedrooms 
2 bathrooms 
Reception 
Fully finished 
Kitchen 
ACs
Price 15,500,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESs239
Duplex ground floor with garden for sale in Eastown 
Area 263 SQM
Garden 60 SQM
3 bedrooms (1master & dressing)
3 bathrooms 
Nanny room with bathroom 
Semi finished 
Price 19,950,00
[truncated — 1,976 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (397 words, 3591 chars, 1431 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 14600000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "ad_snippet": "Apartment for sale in Eastown \nArea 156 SQM \n2 bedrooms ( 1 master & dressing ) \n3 bathrooms \nFully furnished \nKitchen \nACs \nView Landscape \n*Price* \nFully furnished 14,600,000\nUnfurnished 13,650,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 15500000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "ad_snippet": "Apartment ground floor with garden for sale in Eastown \nArea 156 SQM\nGarden 120 SQM\n3 be
[truncated — 3,591 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (451) words, (3591) chars, 2713 tokens)</summary>

```
**JSON Data Extraction and Structuring**

Okay, I'm going to take this real estate ad data and convert it into a JSON array, as requested. The core of this is extracting structured data from each individual listing and formatting it into a defined JSON object. I've got to make sure each entry accurately represents the information provided and adheres to the specified fields: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, `ad_snippet`, and `ad_index`. The `ad_index` will be 1 for all entries, since this all seems to be from the same ad.

First, I need to go through each listing, treating it as a separate unit. This means taking the information for each 
[truncated — 3,401 chars total]
```

</details>


---

### Batch 3/4


**Input**

<details>
<summary>▶ Show input text (470 words, 2820 chars, 1589 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨rent in Eastown 🚨
Available 
Code ESr230
Apartment for rent in Eastown 
Area 205 SQM 
2nd floor 
3 bedrooms 
3 bathrooms 
Nany room with bathroom 
Kitchen 
ACs 
Price 50k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr88
Duplex with roof for rent in  Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
 price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr89
Duplex for rent in Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESr238
Apartment for rent in Eastown 
Area 195 SQM
2nd floor 
3 bedrooms (1 master)
3
[truncated — 2,819 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (593 words, 5403 chars, 2107 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 50000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "ad_snippet": "Apartment for rent in Eastown \nArea 205 SQM \n2nd floor \n3 bedrooms \n3 bathrooms \nNany room with bathroom \nKitchen \nACs \nPrice 50k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 100000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "ad_snippet": "Duplex with roof for rent in Eastown \nArea 283sqm\nRoof 79 sqm \n3 bedrooms (1master)\n3 bathrooms\nNanny room \nFully finished\nKitchen\nAc's \n price 100k",
    "ad_ind
[truncated — 5,403 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (401) words, (5403) chars, 5922 tokens)</summary>

```
**JSON Extraction & Formatting**

Alright, let's get down to it. My task here is to pull relevant data from these real estate ads, specifically extracting information for each listing and structuring it into a JSON array. Each object in this array will represent a single listing and must include the fields: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, `ad_snippet`, and `ad_index`. I will be processing each AD block as a distinct unit.

Here's my thought process: I'm going to iterate through each AD block and then parse each individual listing within the block. For each listing, I'll extract the data and create a JSON object. The crucial aspect here i
[truncated — 2,491 chars total]
```

</details>


---

### Batch 4/4


**Input**

<details>
<summary>▶ Show input text (225 words, 1349 chars, 1030 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T20:26:00) ---
🚨sale in The Square🚨
 
Code SQs134
Apartment for sale in the square 
Area 162 SQM
5th floor 
3 bedrooms 
2 bathrooms 
Fully finished 
Kitchen only 
Internet 
View landscape and lake 
Price 8,000,000
⚡⚡⚡⚡⚡⚡⚡⚡
Code SQs96
Apartment for sale in the square 
Area 225 SQM 
3 bedrooms ( 1 master & dressing )
3 bathrooms 
Nany room with bathroom 
Reception 3 pieces 
Fully finished 
View landscape 
Price 12,500,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code SQs126
Apartment for sale in the square 
Area 178 SQM 
2nd floor 
3 bedrooms
3 bathrooms 
Semi finished 
View Lake&landscape 
Price 6,400,000
⚡⚡⚡⚡⚡⚡⚡⚡
 Code SQs86
Apartment for sale in The Square 
Area 172 SQM
4t
[truncated — 1,347 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (297 words, 2581 chars, 1048 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 8000000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "The Square",
    "ad_snippet": "Code SQs134\nApartment for sale in the square \nArea 162 SQM\n5th floor \n3 bedrooms \n2 bathrooms \nFully finished \nKitchen only \nInternet \nView landscape and lake \nPrice 8,000,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12500000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "The Square",
    "ad_snippet": "Code SQs96\nApartment for sale in the square \nArea 225 SQM \n3 bedrooms ( 1 master & dressing )\n3 bathrooms 
[truncated — 2,581 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (299) words, (2581) chars, 1624 tokens)</summary>

```
**JSON Extraction from Real Estate Ads**

Okay, here's how I'm going to approach this. My goal is to create a JSON array, with each element representing a single real estate listing. I need to parse the provided text, which consists of several advertisement blocks. Each block has an `ad_index` and a snippet. Some blocks contain multiple distinct listings.

For each block, I'll iterate through it and extract the required information: `property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `compound_name`, and `ad_snippet`. I will ensure that the extracted data conforms to the following rules:

*   **Strict Zero-Assumption Policy:** I will make zero assumptions about the data. Th
[truncated — 1,921 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 9 | 9 | 9 | 1356 | 1138 | 2088 | 0 | $0.00143 | 15.89 | 13.13 |
| 2 | 1 | 9 | 9 | 1208 | 1431 | 2713 | 0 | $0.00178 | 15.45 | 14.50 |
| 3 | 2 | 15 | 15 | 1589 | 2107 | 5922 | 0 | $0.00337 | 26.15 | 22.97 |
| 4 | 4 | 7 | 7 | 1030 | 1048 | 1624 | 0 | $0.00117 | 9.75 | 9.10 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 16 | 40 | 40 | 67.24 | 4 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16.81 | 14.92 | 1296 | 1431 | 334 | 413 | 10.0 | 0.59 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 5183 | $0.00052 | 1296 |
| output | 5724 | $0.00229 | 1431 |
| thinking | 12347 | $0.00494 | 3087 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.007747**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-07 | 0.0077 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 7 | 0 | 8 | 1 | 16 |

**Listings inserted:** 40


============================================================

## (7/4/2026)Run — (18:06)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

## (7/4/2026)Run — (18:09)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (520 words, 3184 chars, 3118 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*EL Rehab*
Apartment Available For Rent:
Bua: 255sqm.
___
3 Bedrooms.
3 Bathrooms.
Living room.
3 Balconies.
___
NG.
___
Price : 38k ...

--- AD 2 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate*
Apartment Available For Rent:
Prime Location ✨ 
2th Floor.
Bua: 150sqm.
____
2 Bedrooms.
2 Bathrooms.
____
AC'S and Kitchen Cabinets.
Garage.
____
Price: 35k ...

--- AD 3 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Madinaty*
Apartment Available For Rent:
Prime Location ✨ 
____
2 Bedrooms.
2 Bathrooms.
Fully furnished.
____
Facing North (bahary).
Garden View.

Price 25k per month ...

--- AD 4 (from: +20
[truncated — 3,183 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (591 words, 4958 chars, 1821 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 38000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "El Rehab",
    "ad_snippet": "Apartment Available For Rent: Bua: 255sqm. 3 Bedrooms. 3 Bathrooms. Living room. 3 Balconies. NG. Price : 38k ...",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Village Gate",
    "ad_snippet": "Apartment Available For Rent: Prime Location ✨ 2th Floor. Bua: 150sqm. 2 Bedrooms. 2 Bathrooms. AC'S and Kitchen Cabinets. Garage. Price: 35k ...",
    "ad_index": 2
  },
  {
    "propert
[truncated — 4,958 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (622) words, (4958) chars, 888 tokens)</summary>

```
**My Approach to Structured Data Extraction from WhatsApp Ads**

Okay, so I've been given a JSON schema and a set of rules, and my task is to meticulously extract structured data from these WhatsApp ad messages. My goal is to create a JSON array of listing objects, one object per AD block.  I need to go through each AD block individually, following a defined set of steps.

Here's the breakdown of my planned process:

1.  **AD Block Identification:** First, I'll scan each text chunk, looking for that specific marker: "--- AD N ---". This tells me where each advertisement starts, and importantly, it provides the `ad_index`, which I need to record.

2.  **Ad Index Extraction:** From the marker 
[truncated — 3,709 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (212 words, 1314 chars, 2224 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code Mi648
Apartment for rent in mivida 
Boulevard 
Area 238m
4 bedrooms 
3 bathrooms 
Maids room with bathroom 
Ultra super lux
Furnished 
Price 3000$

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:58:00) ---
Code mvhpr306
Apartment for rent in mountain view hyde park
Area 203m
3 bedrooms 
3 bathrooms 
Dressing 
Super luxury
Furnished 
Price 60k

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:58:00) ---
code ncc1484
Apartment for sale in stone residence 
2nd floor
Area 175m
3 bedrooms
3 bathrooms 
3 terrace 
Reception 3 pieces 
3 balcony with double view
 semi finished 
Price 6,509,000

--- AD 4 (from: +20 11 03387
[truncated — 1,313 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (228 words, 1826 chars, 616 tokens)</summary>

```
[{"property_type": "apartment", "transaction_type": "rent", "price": 3000, "currency": "USD", "bedrooms": 4, "compound_name": "Mivida", "ad_snippet": "Apartment for rent in mivida Boulevard Area 238m 4 bedrooms 3 bathrooms Maids room with bathroom Ultra super lux Furnished Price 3000$", "ad_index": 1}, {"property_type": "apartment", "transaction_type": "rent", "price": 60000, "currency": "EGP", "bedrooms": 3, "compound_name": "Mountain View Hyde Park", "ad_snippet": "Apartment for rent in mountain view hyde park Area 203m 3 bedrooms 3 bathrooms Dressing Super luxury Furnished Price 60k", "ad_index": 2}, {"property_type": "apartment", "transaction_type": "sale", "price": 6509000, "currency": 
[truncated — 1,826 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (598) words, (1826) chars, 829 tokens)</summary>

```
**My Approach to Structured Data Extraction from WhatsApp Ads**

Okay, so I've been tasked with pulling structured data from these WhatsApp ad messages. It seems pretty straightforward, essentially a classic information extraction problem, but the devil's in the details, as usual. The goal is to take each advertisement block and turn it into a JSON object, then combine all those objects into a single JSON array, conforming to a given schema. I'm going to work through each ad methodically and detail each step I took.

First, I need to break down the task into smaller, manageable steps. Here’s how I'm thinking I'll do it:

1.  **Identify the AD Index:** That's easy enough. The "--- AD N ---" f
[truncated — 3,732 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 3118 | 1821 | 888 | 0 | $0.00140 | 12.30 | 12.30 |
| 2 | 6 | 6 | 6 | 2224 | 616 | 829 | 0 | $0.00080 | 9.11 | 9.11 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 21.42 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10.71 | 10.71 | 2671 | 1218 | 366 | 410 | 10.0 | 0.93 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 5342 | $0.00053 | 2671 |
| output | 2437 | $0.00097 | 1218 |
| thinking | 1717 | $0.00069 | 858 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.002196**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-07 | 0.0022 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (11:34)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 4 | 2 | v3New50DayGTSample.txt |

### Batch 1/4


**Input**

<details>
<summary>▶ Show input text (482 words, 2932 chars, 2979 tokens)</summary>

```
--- AD 1 (from: +20 10 14836790, date: 2025-02-26T21:35:00) ---
For rent semi furnished ( Ac - appliances - Kitchen )    in East Town sodic  💥💥💥
Unique type 175M
3 bed rooms 
4 bath rooms 
Nany room
Double view (Garden - open view )  
4th  floor 
Ba7ry
Families only plz 
Price 70k


--- AD 2 (from: +20 11 11431057, date: 2025-02-26T14:14:00) ---
code hp362
Apartment for rent in hyde park
Ground floor
Area 135m
2 bedrooms
2 bathrooms
Ultra super lux
Kitchen with appliances & Acs
Price 40k


--- AD 3 (from: +20 10 62855071, date: 2025-02-26T08:29:00) ---
للبيع دوبلكس مميز بجنوب الأكاديمية – مدخل خاص

🔹 المساحة: 370 متر²
🔹 الحديقة: 120 متر²
🔹 الحالة: نصف تشطيب
🔹 التقسيم الداخلي:
✅ البيزمنت + ال
[truncated — 2,930 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (521 words, 3923 chars, 1514 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 70000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown Sodic",
    "ad_snippet": "For rent semi furnished ( Ac - appliances - Kitchen ) in East Town sodic Unique type 175M 3 bed rooms 4 bath rooms Nany room Double view (Garden - open view ) 4th floor Ba7ry Families only plz Price 70k",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 40000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Hyde Park",
    "ad_snippet": "Apartment for rent in hyde park Ground floor Area 135m 2 bedrooms 2 bathrooms Ultra super lux Ki
[truncated — 3,923 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (490) words, (3923) chars, 817 tokens)</summary>

```
**My Real Estate Data Extraction Plan**

Okay, so I need to get structured data from these real estate ads. My goal is to break down each ad block and output a clean JSON array. Here's my strategy, step-by-step:

First, I'll process each individual ad. I need to keep the process structured to avoid confusion and loss of data.

1.  **AD Indexing**: I'll start by grabbing the unique number, the `ad_index`, from the "--- AD N ---" marker. That's my key identifier.

2.  **Property Type Classification**: Next, I'll need to figure out what kind of property it is. I'll look for keywords like "apartment", "villa", "duplex", and the rest. If I don't find a clear match, I'll default to `null` – I need
[truncated — 2,998 chars total]
```

</details>


---

### Batch 2/4


**Input**

<details>
<summary>▶ Show input text (556 words, 3614 chars, 3145 tokens)</summary>

```
--- AD 1 (from: +20 11 11883746, date: 2025-02-26T12:24:00) ---
Update price
Code BHr14
A penthouse for rent in midtown
Area 240 sqm
Roof
Living 
3 bedrooms
4 bathrooms
Fully furnished 
Kitchen 
ACs
Price 80k short term
_________________________
*Update price*
Code BHr943
Apartment for rent in Midtown 
Area 180 SQM
3 bedrooms 
2 bathrooms 
Fully furnished 
Kitchen 
AC's
Price 80k short term 
Available 7/3
_____________________
Code BHr1464
Apartment for rent in district 5 
area 126 SQM
First floor 
2 masters room
3 bathrooms 
Kitchen 
Price 30k
_____________________
Available 
Code BHr1178
Apartment ground floor with garden for rent in Azad 
Area 180 SQM 
Garden 120 SQM 
3 bedrooms 
3 bathro
[truncated — 3,612 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (610 words, 4644 chars, 1595 tokens)</summary>

```
[{"property_type": "penthouse", "transaction_type": "rent", "price": 80000, "currency": "EGP", "bedrooms": 3, "compound_name": "Midtown", "ad_snippet": "A penthouse for rent in midtown Area 240 sqm Roof Living 3 bedrooms 4 bathrooms Fully furnished Kitchen ACs Price 80k short term", "ad_index": 1}, {"property_type": "apartment", "transaction_type": "rent", "price": 80000, "currency": "EGP", "bedrooms": 3, "compound_name": "Midtown", "ad_snippet": "Apartment for rent in Midtown Area 180 SQM 3 bedrooms 2 bathrooms Fully furnished Kitchen AC's Price 80k short term Available 7/3", "ad_index": 1}, {"property_type": "apartment", "transaction_type": "rent", "price": 30000, "currency": "EGP", "bedro
[truncated — 4,644 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (365) words, (4644) chars, 874 tokens)</summary>

```
**Data Extraction from WhatsApp Ad Block**

Okay, here's how I'm approaching this. I've been given a WhatsApp ad block and a JSON schema and some rules for data extraction. My goal is to parse this ad block, identify individual listings within it, and then extract the specified fields for each listing based on the schema and rules. It looks like this ad block contains multiple listings. I have to make sure each is processed individually and correctly.

Let's break down AD 1:

*   **Listing 1 (BHr14):**
    *   This is straightforward. "penthouse" is the `property_type`, and "for rent" tells me `transaction_type` is "rent".
    *   The `price` is "80k short term". The rules say "short term" i
[truncated — 2,329 chars total]
```

</details>


---

### Batch 3/4


**Input**

<details>
<summary>▶ Show input text (916 words, 5742 chars, 4246 tokens)</summary>

```
--- AD 1 (from: +20 11 11431057, date: 2025-02-26T14:19:00) ---
code hp391
apartment  for rent in hyde park
 area 180m
2 bedrooms(1 master) 
3 bathrooms
super lux 
furnished
Update price 55k


--- AD 2 (from: +20 10 62855071, date: 2025-02-26T08:37:00) ---
للبيع - شقة مميزة في كمبوند هايد بارك

المواصفات:

المساحة: 228 م²

الموقع: الطابق الثاني


تفاصيل الشقة:

3 غرف نوم + غرفة نوم رئيسية بحمام خاص

غرفة مربية بحمام مستقل

حمام ضيوف

حمام رئيسي

استقبال كبير يوفر مساحة مثالية للضيوف


المزايا:

5 شرفات فرنسية تطل على منظر رائع

إطلالة مزدوجة على المول، منطقة الأعمال، وحديقة صغيرة

نصف تشطيب، مما يتيح لك تصميمها حسب ذوقك الخاص

رسوم الصيانة مدفوعة بالكامل


الموقع: في قلب كمبوند هايد بارك، بم
[truncated — 5,740 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (933 words, 7085 chars, 2664 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 55000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Hyde Park",
    "ad_snippet": "apartment for rent in hyde park area 180m 2 bedrooms(1 master) 3 bathrooms super lux furnished Update price 55k",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12600000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Hyde Park",
    "ad_snippet": "شقة مميزة في كمبوند هايد بارك المساحة: 228 م² الطابق الثاني 3 غرف نوم + غرفة نوم رئيسية بحمام خاص غرفة مربية بحمام مستقل حمام ضيوف حمام رئيسي استقبال كبير 5 شرفات فرنسية تطل على منظر رائع 
[truncated — 7,085 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (595) words, (7085) chars, 840 tokens)</summary>

```
**My Approach to Real Estate Data Extraction**

Okay, here's how I'm thinking about this task. My goal is to reliably extract structured data from these real estate advertisements and output them in a JSON array of listing objects. I'm treating each advertisement block as a distinct unit, ready to be dissected.

Here's my internal process for each AD I encounter:

1.  **AD Block Identification**: First, I'll be looking for the distinct marker "--- AD N ---", which tells me where one ad block ends and the next begins. This is my key to parsing the information.
2.  **`ad_index` Retrieval**: Once I've found an AD block, I'll grab that "N" value, which I'm thinking of as the `ad_index`. This wil
[truncated — 3,675 chars total]
```

</details>


---

### Batch 4/4


**Input**

<details>
<summary>▶ Show input text (397 words, 2405 chars, 2762 tokens)</summary>

```
--- AD 1 (from: +20 11 11431057, date: 2025-02-26T14:16:00) ---
code hp367
Apartment with garden for rent in hyde park
Area 100m
Garden 50m
2 bedrooms
1 bathroom
Ultra super lux
Kitchen with some appliances
Acs
Price 30k


--- AD 2 (from: +20 10 26318054, date: 2025-02-26T15:37:00) ---
Code cs738
Twin house with private Pool for sale in Bellagio Sabbour 
Area 440 m
BUA 350 m
4 bedrooms 
4 bathrooms 
Super lux 
Fully furnished
Kitchen & ACs
Price 32,000,000
فيها مستأجر حتى ٧/٢٠٢٥ 
بيدفع ٧٠ الف فى الشهر


--- AD 3 (from: +20 11 11431057, date: 2025-02-26T14:00:00) ---
Code ncc975
Apartment for rent in Lila compound 
Area 165m
3 bedrooms 
2 bathrooms 
Furnished 
Price 50k


--- AD 4 (from: +20 
[truncated — 2,403 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (404 words, 3226 chars, 1229 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 30000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Hyde Park",
    "ad_snippet": "Apartment with garden for rent in hyde park Area 100m Garden 50m 2 bedrooms 1 bathroom Ultra super lux Kitchen with some appliances Acs Price 30k",
    "ad_index": 1
  },
  {
    "property_type": "twin_house",
    "transaction_type": "sale",
    "price": 32000000,
    "currency": "EGP",
    "bedrooms": 4,
    "compound_name": "Bellagio Sabbour",
    "ad_snippet": "Twin house with private Pool for sale in Bellagio Sabbour Area 440 m BUA 350 m 4 bedrooms 4 bathrooms Super lux Fully furnished Kitchen & ACs Pric
[truncated — 3,226 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (353) words, (3226) chars, 1025 tokens)</summary>

```
**My Approach to Structuring Real Estate Ads**

Okay, so I need to get some structured data out of these real estate ads.  My plan is pretty straightforward: I'll tackle this ad-by-ad and build a JSON object for each listing. First, I have to iterate through each ad block, recognizing that each one seems to contain a single listing.

For each ad, I’ll need to extract specific fields:

*   `ad_index`:  This will be easy; it's right there, marked with "--- AD N ---".
*   `property_type`: I'll use some keyword spotting for this – look for terms like "Apartment," "Twin house," "Townhouse," etc.
*   `transaction_type`:  Again, keyword-based. I'll be looking for "rent" or "sale."
*   `price`:  Thi
[truncated — 2,153 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8 | 8 | 8 | 2979 | 1514 | 817 | 0 | $0.00123 | 10.94 | 10.94 |
| 2 | 8 | 15 | 14 | 3145 | 1595 | 874 | 0 | $0.00130 | 9.86 | 9.86 |
| 3 | 15 | 15 | 15 | 4246 | 2664 | 840 | 0 | $0.00183 | 14.14 | 14.14 |
| 4 | 8 | 8 | 8 | 2762 | 1229 | 1025 | 0 | $0.00118 | 9.87 | 9.87 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 39 | 46 | 45 | 44.82 | 4 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11.20 | 11.20 | 3283 | 1750 | 588 | 617 | 11.2 | 1.00 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 13132 | $0.00131 | 3283 |
| output | 7002 | $0.00280 | 1750 |
| thinking | 3556 | $0.00142 | 889 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.005536**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0055 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 0 | 0 | 10 | 1 | 39 |

**Listings inserted:** 45


============================================================

## (8/4/2026)Run — (14:43)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 4 | 2 | v3New50DayGTSample.txt |

### Batch 1/4


**Input**

<details>
<summary>▶ Show input text (949 words, 5880 chars, 4154 tokens)</summary>

```
--- AD 1 (from: +20 11 11883746, date: 2025-02-26T12:24:00) ---
Update price
Code BHr14
A penthouse for rent in midtown
Area 240 sqm
Roof
Living 
3 bedrooms
4 bathrooms
Fully furnished 
Kitchen 
ACs
Price 80k short term
_________________________
*Update price*
Code BHr943
Apartment for rent in Midtown 
Area 180 SQM
3 bedrooms 
2 bathrooms 
Fully furnished 
Kitchen 
AC's
Price 80k short term 
Available 7/3
_____________________
Code BHr1464
Apartment for rent in district 5 
area 126 SQM
First floor 
2 masters room
3 bathrooms 
Kitchen 
Price 30k
_____________________
Available 
Code BHr1178
Apartment ground floor with garden for rent in Azad 
Area 180 SQM 
Garden 120 SQM 
3 bedrooms 
3 bathro
[truncated — 5,878 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (974 words, 7092 chars, 2687 tokens)</summary>

```
[
  {
    "property_type": "penthouse",
    "transaction_type": "rent",
    "price": 80000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Midtown",
    "ad_snippet": "A penthouse for rent in midtown Area 240 sqm Roof Living 3 bedrooms 4 bathrooms Fully furnished Kitchen ACs Price 80k short term",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 80000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Midtown",
    "ad_snippet": "Apartment for rent in Midtown Area 180 SQM 3 bedrooms 2 bathrooms Fully furnished Kitchen AC's Price 80k short term Available 7/3",
    "ad_index": 1
  },
  {
    "property_type"
[truncated — 7,092 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (376) words, (7092) chars, 747 tokens)</summary>

```
**My Analysis of the WhatsApp Ad Data**

Okay, so I've got this WhatsApp ad data and a JSON schema. My task is to extract structured information from these ad messages, essentially breaking them down into individual listings and pulling out the specific fields the schema defines. Let's see how well I can process this.

The first ad block contains multiple listings; looks like I need to process each one separately.

**AD 1 Analysis:**

*   **Listing 1 (BHr14):** I've identified this as a "penthouse" for "rent". The price is listed as "80k short term", and I'm interpreting that as a lump sum of 80,000 EGP. The term "short term" is ambiguous, and might indicate a daily or weekly rate, but it's 
[truncated — 2,205 chars total]
```

</details>


---

### Batch 2/4


**Input**

<details>
<summary>▶ Show input text (827 words, 5311 chars, 4132 tokens)</summary>

```
--- AD 1 (from: +20 10 62855071, date: 2025-02-26T08:35:00) ---
ڤيلا للبيع أمام نادي النسور – مساكن شيراتون

الموقع: أمام شارع الأوتوستراد، تطل على النادي وليست على الشارع.

الخصوصية: مدخل خاص لأصحاب الفلل.

المساحة:

مساحة الأرض: 520 متر

مساحة المباني: 430 متر

الحديقة: 90 متر

التفاصيل:

3 أدوار (نصف تشطيب).

ريسبشن كبير.

5 غرف نوم.

3 حمامات.

جراج خاص.

مساحة إضافية لعمل حديقة وحمام سباحة (90 متر).
مطلوب 25مليون 
للتواصل:
📞 هاتف أو واتساب: 01062855071

https://wa.me/+201062855071


--- AD 2 (from: +20 15 55526667, date: 2025-02-26T22:39:00) ---
*شقه لقطه للبيع* 🔥
 *البنفسج عمارات*
تشطيب سوبر لوكس على واجهه العمارة جاهزة للسكن بعمارات البنفسج عمارات. مساحه ١٣٥ متر.
موقع ممتاز دقيقه التس
[truncated — 5,309 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (768 words, 6290 chars, 2418 tokens)</summary>

```
[
  {
    "property_type": "villa",
    "transaction_type": "sale",
    "price": 25000000,
    "down_payment": null,
    "currency": "EGP",
    "bedrooms": 5,
    "compound_name": null,
    "ad_snippet": "ڤيلا للبيع أمام نادي النسور – مساكن شيراتون مساحة الأرض: 520 متر مساحة المباني: 430 متر 3 أدوار (نصف تشطيب). 5 غرف نوم. مطلوب 25مليون",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 4250000,
    "down_payment": null,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": null,
    "ad_snippet": "شقه لقطه للبيع البنفسج عمارات تشطيب سوبر لوكس مساحه ١٣٥ متر. حجرتين كبار وريسبشن 42 متر واثنين حمام ومطبخ مطلوب ٤،٢٥٠ مليون",
    
[truncated — 6,290 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (542) words, (6290) chars, 875 tokens)</summary>

```
**My Approach to Real Estate Ad Data Extraction**

Okay, so I need to tackle this real estate data extraction project. The goal is to intelligently parse these ads and output a structured JSON array for each ad block. My expertise is in data processing and information retrieval, so let's break this down into a systematic plan.

First, I'll need to treat each ad block as a separate entity. I'll identify the start of an ad using the "--- AD N ---" marker, where "N" is the ad index. This index is crucial for keeping things organized.

My process will be as follows:

1.  **Block Identification & Indexing:** Isolate each ad and extract its unique `ad_index`.

2.  **Property Type Classification:**
[truncated — 3,493 chars total]
```

</details>


---

### Batch 3/4


**Input**

<details>
<summary>▶ Show input text (551 words, 3364 chars, 3184 tokens)</summary>

```
--- AD 1 (from: +20 11 03023009, date: 2025-02-26T17:05:00) ---
Twin house for sale
bellagio 
G+first+roof 

Bua 350
Land 460 

4 bedrooms (1 master+dressing)
4 bathrooms 
Living room 
Maid’s room 

Very prime location 
Direct on lake & greenery 
Semi finished 

30,000,000


--- AD 2 (from: +20 11 11431057, date: 2025-02-26T13:53:00) ---
Eastown sodic
Apartment for rent
4th Floor
216 meters
3 bedrooms + Living room + laundry or nanny room
3 bathrooms
Kitchen (بوتجاز و فرن) + AC’s
55,000 per month (دفع كل ٣ شهور)
٢ تأمين
Direct المفتاح موجود 🔑


--- AD 3 (from: +20 10 26318054, date: 2025-02-26T15:37:00) ---
Code mvhps90
Twinhouse for sale in Mountain View Hyde Park 
Land area 481m
BUA 376m
4
[truncated — 3,362 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (595 words, 5070 chars, 1864 tokens)</summary>

```
[
  {
    "property_type": "twin_house",
    "transaction_type": "sale",
    "price": 30000000,
    "currency": "EGP",
    "bedrooms": 4,
    "compound_name": "Bellagio",
    "ad_snippet": "Twin house for sale bellagio Bua 350 Land 460 4 bedrooms Very prime location Semi finished 30,000,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 55000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown Sodic",
    "ad_snippet": "Apartment for rent in Eastown sodic 216 meters 3 bedrooms 3 bathrooms Kitchen (بوتجاز و فرن) + AC’s 55,000 per month",
    "ad_index": 2
  },
  {
    "property_type": "twin_house",
    "transact
[truncated — 5,070 chars total]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (513) words, (5070) chars, 992 tokens)</summary>

```
**My Approach to Real Estate Ad Data Extraction**

Okay, so I need to get this real estate data structured. My goal here is to process these ad blocks and get a clean JSON object for each individual property listing. It's a pretty straightforward process, but I need to be meticulous.

Here's the strategy I'm going with:

1.  **Iterate and Isolate:** First, I'm going to iterate through each ad block. The "--- AD N ---" marker is my key to identifying and separating each distinct advertisement. I'll need to extract the `ad_index` from this.
2.  **Listing Dissection:** Within each ad, I have to be ready for the possibility of multiple property listings. I need to figure out how to parse the ad 
[truncated — 3,193 chars total]
```

</details>


---

### Batch 4/4


**Input**

<details>
<summary>▶ Show input text (24 words, 144 chars, 1668 tokens)</summary>

```
--- AD 1 (from: +20 10 14836790, date: 2025-02-26T21:34:00) ---
For rent
171 m 
3 bedrooms
2 bathrooms 
With kitchen 
Address East
Request 30k
```

</details>


**Output**

<details>
<summary>▶ Show output text (14 words, 219 chars, 69 tokens)</summary>

```
[{"property_type":null,"transaction_type":"rent","price":30000,"currency":"EGP","bedrooms":3,"compound_name":null,"ad_snippet":"For rent 171 m 3 bedrooms 2 bathrooms With kitchen Address East Request 30k","ad_index":1}]
```

</details>


**Thinking**

<details>
<summary>▶ Show thinking text (190) words, (219) chars, 206 tokens)</summary>

```
**Analyzing the Real Estate Ad and Preparing the JSON Response**

Okay, so I need to dissect this real estate ad and translate the key information into a JSON object, adhering strictly to the defined schema. First, I see this is ad number 1, so the `ad_index` is definitely 1. The ad clearly states "For rent", which I will correctly map to `"rent"` for the `transaction_type` field. Now, let's look for the `property_type`. Hmmm, there isn't a direct descriptor like "apartment" or "villa" in the text. I'll flag that and assign `null` to `property_type`. Next, the price: "Request 30k". That's straightforward; I need to convert that to 30000, and since no currency is specified, I'll default to "E
[truncated — 1,142 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8 | 15 | 14 | 4154 | 2687 | 747 | 0 | $0.00179 | 14.45 | 14.45 |
| 2 | 15 | 15 | 15 | 4132 | 2418 | 875 | 0 | $0.00173 | 13.71 | 13.71 |
| 3 | 15 | 15 | 15 | 3184 | 1864 | 992 | 0 | $0.00146 | 13.53 | 13.53 |
| 4 | 1 | 1 | 1 | 1668 | 69 | 206 | 0 | $0.00028 | 2.97 | 2.97 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 39 | 46 | 45 | 44.66 | 4 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11.17 | 11.17 | 3284 | 1760 | 588 | 588 | 11.2 | 1.01 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 13138 | $0.00131 | 3284 |
| output | 7038 | $0.00282 | 1760 |
| thinking | 2820 | $0.00113 | 705 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.005257**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0108 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 0 | 0 | 10 | 1 | 39 |

**Listings inserted:** 45


============================================================

## (8/4/2026)Run — (18:17)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (554 words, 3382 chars, 4770 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate Palm Hills*
Duplex Available For Rent:
Bua: 220sqm.
Garden: 120sqm.
_____
3 Bedrooms ( 1 Master ).
3 Bathrooms ( 2 Water heaters ).
_____
AC'S and Kitchen with Appliances.
Private Parking.
_____
Price: 45k per month ✨ ...

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code sh177
pharmacy for sale in hyde park 
 Unit CVA3-4g
 area :50 m
fully  finished
 Price : 1,100,000$ cash
installments : 1,200,000 / 2 years
60% 1st Yr , 40 % 2nd Yr
(USD for installments  will be the reference for amount in EGP)

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code vgk43
Apartment with garden for
[truncated — 3,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (672 words, 5782 chars, 2067 tokens)</summary>

```
[
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 45000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Palm Hills",
    "city": "6th of October City",
    "district": null,
    "ad_snippet": "Duplex Available For Rent: Bua: 220sqm. Garden: 120sqm. 3 Bedrooms ( 1 Master ). 3 Bathrooms ( 2 Water heaters ). AC'S and Kitchen with Appliances. Private Parking. Price: 45k per month",
    "ad_index": 1
  },
  {
    "property_type": "shop",
    "transaction_type": "sale",
    "price": 1100000,
    "down_payment": null,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": "Hyde Park",
    "city": "New Cairo",
    "district": "5th Settlemen
[truncated — 5,782 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (178 words, 1116 chars, 3762 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1954
Apartment For Rent in Compound  Lamirada
ground floor 
Area 100m 
2 bedroom 
2 bathroom 
Fully furnished 
Price 35.000

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code lv279
Apartment for sale in Lake view Residence
Area143m 
2 bedrooms 
2 bathrooms 
super lux
kitchen & Acs 
price 12.000.000

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1484
Apartment for sale in stone residence 
2nd floor 
Area 175m
3 bedrooms 
3 bathrooms 
Semi finished 
Price 6,457,500

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code hp337
studio for sale in hyde park
area 81m
1
[truncated — 1,115 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (252 words, 2268 chars, 837 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "La Mirada",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment For Rent in Compound Lamirada ground floor Area 100m 2 bedroom 2 bathroom Fully furnished Price 35.000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12000000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Lake View Residence",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Lake view Residence Area143m 2 bedroo
[truncated — 2,268 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 4770 | 2067 | 0 | 0 | $0.00130 | 5.22 | 5.22 |
| 2 | 6 | 6 | 6 | 3762 | 837 | 0 | 0 | $0.00071 | 2.87 | 2.87 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 8.09 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.04 | 4.04 | 4266 | 1452 | 366 | 462 | 10.0 | 2.47 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 8532 | $0.00085 | 4266 |
| output | 2904 | $0.00116 | 1452 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.002015**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0020 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (18:18)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 3 | 2 | 50_messages_24_02_2025.txt |

### Batch 1/3


**Input**

<details>
<summary>▶ Show input text (843 words, 5070 chars, 5443 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-02-24T16:31:00) ---
🚨rent in Mivida🚨

Code MIVr232
Twin house for rent in Mivida
Land area 340 
Bua 330 SQM
3 bedrooms (1 master)
3 bathrooms 
Nanny room with bathroom 
Living room 
Kitchen with appliances 
AC's
Price 3000$ 
او ما يعادله
☀️☀️☀️☀️☀️☀️☀️☀️☀️
Code MIVr19
Apartment for rent in mivida Boulevard 
Area 220 SQM
2nd floor 
3 bedrooms
3 bathrooms
Maids room with bathroom
Fully furnished
Kitchen
AC'S 
Price 100k
☀️☀️☀️☀️☀️☀️☀️☀️ 
Code MIVr167
Townhouse for rent in Mivida - parcel 2
Area 216 SQM 
Garden 90 SQM 
3 bedrooms 
4 bathrooms 
Nany room 
Fully furnished 
Kitchen 
ACs 
Price 120k
Day 10k
☀️☀️☀️☀️☀️☀️☀️☀️☀️
Code MIVr4
Apartment ground f
[truncated — 5,068 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (899 words, 7008 chars, 2632 tokens)</summary>

```
[
  {
    "property_type": "twin_house",
    "transaction_type": "rent",
    "price": 3000,
    "currency": "USD",
    "bedrooms": 3,
    "compound_name": "Mivida",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Twin house for rent in Mivida Land area 340 Bua 330 SQM 3 bedrooms (1 master) 3 bathrooms Nanny room with bathroom Living room Kitchen with appliances AC's Price 3000$",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 100000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Mivida",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in 
[truncated — 7,008 chars total]
```

</details>


---

### Batch 2/3


**Input**

<details>
<summary>▶ Show input text (914 words, 5383 chars, 5799 tokens)</summary>

```
--- AD 1 (from: +20 10 04640537, date: 2025-02-24T20:36:00) ---
New listing
Hills of one (people and places)New Zayed 
(Standalone villa)🏡

Total area:342 m
Land:323 m
_____________
Ground floor:98 m
Reception +kitchen 
Maid's room +Guest toilet 
_________

First floor:95 m +terrace:56 
3bedroom (masterroom +dressing)
3bathroom 
Kitchen 
_____________
Penthouse:47 m+46 m
1bedroom+bathroom
__________
Core&shell
Delivery:2027
D.p:4,950,000
Maintenance:2,207,520
Total:27,594,000
Remaining for 8 years


--- AD 2 (from: +20 12 88084056, date: 2025-02-24T19:02:00) ---
◾Unit type : Twin house for Rent in mivida
▫️Area : 310m
▫️3  Bedrooms
▫️4 Bathrooms 
▫️Fully Super lux Furnished
Asking price 150k
[truncated — 5,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (1042 words, 8066 chars, 3080 tokens)</summary>

```
[
  {
    "property_type": "villa",
    "transaction_type": "sale",
    "price": 27594000,
    "down_payment": 4950000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Hills of One",
    "city": "New Zayed",
    "district": null,
    "ad_snippet": "Standalone villa 🏡 Total area:342 m Land:323 m Ground floor:98 m Reception +kitchen Maid's room +Guest toilet First floor:95 m +terrace:56 3bedroom (masterroom +dressing) 3bathroom Kitchen Penthouse:47 m+46 m 1bedroom+bathroom Core&shell Delivery:2027 D.p:4,950,000 Maintenance:2,207,520 Total:27,594,000 Remaining for 8 years",
    "ad_index": 1
  },
  {
    "property_type": "twin_house",
    "transaction_type": "rent",
    "price":
[truncated — 8,066 chars total]
```

</details>


---

### Batch 3/3


**Input**

<details>
<summary>▶ Show input text (404 words, 2439 chars, 4484 tokens)</summary>

```
--- AD 1 (from: +20 11 11885910, date: 2025-02-24T23:50:00) ---
*Update price*
Code ESr212
Apartment for rent in Eastown 
Area 180 SQM
3 bedrooms 
3 bathrooms 
Fully furnished 
Kitchen 
ACs
Price :
For year 85k
For month 80k
For day 8k


--- AD 2 (from: +20 11 11885910, date: 2025-02-24T02:55:00) ---
Code ESr234
Apartment for rent in Eastown 
Area 205 SQM
2nd floor 
3 bedrooms ( 1 master & dressing)
3 bathrooms 
Fully furnished 
Kitchen with appliances 
ACs
Price 95k


--- AD 3 (from: +20 11 11885910, date: 2025-02-24T02:57:00) ---
Update price
Code ESr208
Apartment for rent in Eastown 
Area 205 SQM
3 bedrooms 
3 bathrooms 
Fully furnished 
Kitchen 
ACs
Price 95k ( negotiable)


--- AD 4 (fr
[truncated — 2,438 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (556 words, 4921 chars, 1818 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 80000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 180 SQM 3 bedrooms 3 bathrooms Fully furnished Kitchen ACs Price For month 80k",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 95000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 205 SQM 2nd floor 3 bedrooms ( 1 master 
[truncated — 4,921 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7 | 15 | 15 | 5443 | 2632 | 0 | 0 | $0.00160 | 6.34 | 6.34 |
| 2 | 15 | 15 | 17 | 5799 | 3080 | 0 | 0 | $0.00181 | 7.49 | 7.49 |
| 3 | 13 | 13 | 13 | 4484 | 1818 | 0 | 0 | $0.00118 | 5.10 | 5.09 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 35 | 43 | 45 | 18.93 | 3 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.31 | 6.31 | 5242 | 2510 | 720 | 832 | 15.0 | 2.38 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 15726 | $0.00157 | 5242 |
| output | 7530 | $0.00301 | 2510 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.004585**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0066 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 11 | 0 | 4 | 0 | 35 |

**Listings inserted:** 45


============================================================

## (8/4/2026)Run — (18:22)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 3 | 2 | 32_messages_30_03_2025.txt |

### Batch 1/3


**Input**

<details>
<summary>▶ Show input text (557 words, 3452 chars, 4704 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨sale in Eastown 🚨
Code ESs229
Apartment for sale in Eastown 
Area 156 SQM 
2 bedrooms ( 1 master & dressing ) 
3 bathrooms 
Fully furnished 
Kitchen 
ACs 
View Landscape 
*Price* 
Fully furnished 14,600,000
 Unfurnished 13,650,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
Available 
Code ESs236
Apartment ground floor with garden for sale in Eastown 
Area 156 SQM
Garden 120 SQM
3 bedrooms 
2 bathrooms 
Reception 
Fully finished 
Kitchen 
ACs
Price 15,500,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESs239
Duplex ground floor with garden for sale in Eastown 
Area 263 SQM
Garden 60 SQM
3 bedrooms (1master & dressing)
3 bathrooms 
Nanny room with bathroom 
Semi finished 
Price 19,950,00
[truncated — 3,451 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (755 words, 6871 chars, 2670 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 14600000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Eastown Area 156 SQM 2 bedrooms Fully furnished Price 14,600,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 13650000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Eastown Area 156 SQM 2 bedrooms Unfurnished Price 13,650,000",
    "ad_ind
[truncated — 6,871 chars total]
```

</details>


---

### Batch 2/3


**Input**

<details>
<summary>▶ Show input text (467 words, 2840 chars, 4451 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨rent in Eastown 🚨
Available 
Code ESr230
Apartment for rent in Eastown 
Area 205 SQM 
2nd floor 
3 bedrooms 
3 bathrooms 
Nany room with bathroom 
Kitchen 
ACs 
Price 50k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr88
Duplex with roof for rent in  Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
 price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr89
Duplex for rent in Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESr238
Apartment for rent in Eastown 
Area 195 SQM
2nd floor 
3 bedrooms (1 master)
3
[truncated — 2,839 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (719 words, 6091 chars, 2199 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 50000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 205 SQM 2nd floor 3 bedrooms 3 bathrooms Nany room with bathroom Kitchen ACs Price 50k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 100000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Duplex with roof for rent in Eastown Area 283sqm Roof 79 sqm 3 bedroo
[truncated — 6,091 chars total]
```

</details>


---

### Batch 3/3


**Input**

<details>
<summary>▶ Show input text (313 words, 1828 chars, 4200 tokens)</summary>

```
--- AD 1 (from: +20 11 11885910, date: 2025-03-30T00:14:00) ---
Update price
Code ESr196
Apartment for rent in Eastown 
Area 216 SQM
1st floor 
3 bedrooms (1 master)
3 bathrooms 
Reception 
Laundry Room 
Fully furnished 
Kitchen with appliances 
ACs
Price 150k

--- AD 2 (from: +20 11 11885910, date: 2025-03-30T05:02:00) ---
Code ESr243
Duplex for rent in eastown 
Area 286 SQM 
3 bedrooms ( 1 master ) 3 Bathrooms 
Nany room with bathroom 
Kitchen 
ACs
Price 2500$

--- AD 3 (from: +20 11 11885910, date: 2025-03-30T00:06:00) ---
Code ESr242
Apartment for rent in Eastown 
Area 220 SQM
3 bedrooms (1master & dressing) 
3 bathrooms 
Reception 
Kitchen 
ACs
Price 60k

--- AD 4 (from: +20 10 09337264
[truncated — 1,827 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (444 words, 3760 chars, 1426 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 150000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 216 SQM 1st floor 3 bedrooms (1 master) 3 bathrooms Reception Laundry Room Fully furnished Kitchen with appliances ACs Price 150k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 2500,
    "currency": "USD",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Duplex for rent in eastown 
[truncated — 3,760 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 15 | 19 | 4704 | 2670 | 0 | 0 | $0.00154 | 3.96 | 3.96 |
| 2 | 3 | 15 | 15 | 4451 | 2199 | 0 | 0 | $0.00132 | 6.40 | 6.40 |
| 3 | 10 | 10 | 10 | 4200 | 1426 | 0 | 0 | $0.00099 | 4.56 | 4.56 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 16 | 40 | 44 | 14.93 | 3 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.98 | 4.98 | 4452 | 2098 | 446 | 639 | 14.7 | 2.95 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 13355 | $0.00134 | 4452 |
| output | 6295 | $0.00252 | 2098 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.003854**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0105 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 7 | 0 | 8 | 1 | 16 |

**Listings inserted:** 44


============================================================

## (8/4/2026)Run — (18:27)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (554 words, 3382 chars, 4770 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate Palm Hills*
Duplex Available For Rent:
Bua: 220sqm.
Garden: 120sqm.
_____
3 Bedrooms ( 1 Master ).
3 Bathrooms ( 2 Water heaters ).
_____
AC'S and Kitchen with Appliances.
Private Parking.
_____
Price: 45k per month ✨ ...

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code sh177
pharmacy for sale in hyde park 
 Unit CVA3-4g
 area :50 m
fully  finished
 Price : 1,100,000$ cash
installments : 1,200,000 / 2 years
60% 1st Yr , 40 % 2nd Yr
(USD for installments  will be the reference for amount in EGP)

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code vgk43
Apartment with garden for
[truncated — 3,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (680 words, 5807 chars, 2084 tokens)</summary>

```
[
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 45000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Palm Hills",
    "city": "6th of October City",
    "district": null,
    "ad_snippet": "Duplex Available For Rent: Bua: 220sqm. Garden: 120sqm. 3 Bedrooms ( 1 Master ). 3 Bathrooms ( 2 Water heaters ). AC'S and Kitchen with Appliances. Private Parking. Price: 45k per month",
    "ad_index": 1
  },
  {
    "property_type": "shop",
    "transaction_type": "sale",
    "price": 1100000,
    "down_payment": null,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": "Hyde Park",
    "city": "New Cairo",
    "district": "5th Settlemen
[truncated — 5,807 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (178 words, 1116 chars, 3762 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1954
Apartment For Rent in Compound  Lamirada
ground floor 
Area 100m 
2 bedroom 
2 bathroom 
Fully furnished 
Price 35.000

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code lv279
Apartment for sale in Lake view Residence
Area143m 
2 bedrooms 
2 bathrooms 
super lux
kitchen & Acs 
price 12.000.000

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1484
Apartment for sale in stone residence 
2nd floor 
Area 175m
3 bedrooms 
3 bathrooms 
Semi finished 
Price 6,457,500

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code hp337
studio for sale in hyde park
area 81m
1
[truncated — 1,115 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (252 words, 2268 chars, 837 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "La Mirada",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment For Rent in Compound Lamirada ground floor Area 100m 2 bedroom 2 bathroom Fully furnished Price 35.000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12000000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Lake View Residence",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Lake view Residence Area143m 2 bedroo
[truncated — 2,268 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 4770 | 2084 | 0 | 0 | $0.00131 | 6.25 | 6.25 |
| 2 | 6 | 6 | 6 | 3762 | 837 | 0 | 0 | $0.00071 | 2.78 | 2.78 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 9.03 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.51 | 4.51 | 4266 | 1460 | 366 | 466 | 10.0 | 2.22 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 8532 | $0.00085 | 4266 |
| output | 2921 | $0.00117 | 1460 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.002022**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0125 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (18:35)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (554 words, 3382 chars, 4770 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate Palm Hills*
Duplex Available For Rent:
Bua: 220sqm.
Garden: 120sqm.
_____
3 Bedrooms ( 1 Master ).
3 Bathrooms ( 2 Water heaters ).
_____
AC'S and Kitchen with Appliances.
Private Parking.
_____
Price: 45k per month ✨ ...

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code sh177
pharmacy for sale in hyde park 
 Unit CVA3-4g
 area :50 m
fully  finished
 Price : 1,100,000$ cash
installments : 1,200,000 / 2 years
60% 1st Yr , 40 % 2nd Yr
(USD for installments  will be the reference for amount in EGP)

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code vgk43
Apartment with garden for
[truncated — 3,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (672 words, 5782 chars, 2067 tokens)</summary>

```
[
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 45000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Palm Hills",
    "city": "6th of October City",
    "district": null,
    "ad_snippet": "Duplex Available For Rent: Bua: 220sqm. Garden: 120sqm. 3 Bedrooms ( 1 Master ). 3 Bathrooms ( 2 Water heaters ). AC'S and Kitchen with Appliances. Private Parking. Price: 45k per month",
    "ad_index": 1
  },
  {
    "property_type": "shop",
    "transaction_type": "sale",
    "price": 1100000,
    "down_payment": null,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": "Hyde Park",
    "city": "New Cairo",
    "district": "5th Settlemen
[truncated — 5,782 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (178 words, 1116 chars, 3762 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1954
Apartment For Rent in Compound  Lamirada
ground floor 
Area 100m 
2 bedroom 
2 bathroom 
Fully furnished 
Price 35.000

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code lv279
Apartment for sale in Lake view Residence
Area143m 
2 bedrooms 
2 bathrooms 
super lux
kitchen & Acs 
price 12.000.000

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1484
Apartment for sale in stone residence 
2nd floor 
Area 175m
3 bedrooms 
3 bathrooms 
Semi finished 
Price 6,457,500

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code hp337
studio for sale in hyde park
area 81m
1
[truncated — 1,115 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (252 words, 2268 chars, 837 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "La Mirada",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment For Rent in Compound Lamirada ground floor Area 100m 2 bedroom 2 bathroom Fully furnished Price 35.000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12000000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Lake View Residence",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Lake view Residence Area143m 2 bedroo
[truncated — 2,268 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 4770 | 2067 | 0 | 0 | $0.00130 | 5.29 | 5.29 |
| 2 | 6 | 6 | 6 | 3762 | 837 | 0 | 0 | $0.00071 | 2.64 | 2.64 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 7.92 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.96 | 3.96 | 4266 | 1452 | 366 | 462 | 10.0 | 2.52 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 8532 | $0.00085 | 4266 |
| output | 2904 | $0.00116 | 1452 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.002015**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0145 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (18:41)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (554 words, 3382 chars, 4770 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate Palm Hills*
Duplex Available For Rent:
Bua: 220sqm.
Garden: 120sqm.
_____
3 Bedrooms ( 1 Master ).
3 Bathrooms ( 2 Water heaters ).
_____
AC'S and Kitchen with Appliances.
Private Parking.
_____
Price: 45k per month ✨ ...

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code sh177
pharmacy for sale in hyde park 
 Unit CVA3-4g
 area :50 m
fully  finished
 Price : 1,100,000$ cash
installments : 1,200,000 / 2 years
60% 1st Yr , 40 % 2nd Yr
(USD for installments  will be the reference for amount in EGP)

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code vgk43
Apartment with garden for
[truncated — 3,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (672 words, 5786 chars, 2068 tokens)</summary>

```
[
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 45000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Palm Hills",
    "city": "6th of October City",
    "district": null,
    "ad_snippet": "Duplex Available For Rent: Bua: 220sqm. Garden: 120sqm. 3 Bedrooms ( 1 Master ). 3 Bathrooms ( 2 Water heaters ). AC'S and Kitchen with Appliances. Private Parking. Price: 45k per month",
    "ad_index": 1
  },
  {
    "property_type": "shop",
    "transaction_type": "sale",
    "price": 1100000,
    "down_payment": null,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": "Hyde Park",
    "city": "New Cairo",
    "district": "5th Settlemen
[truncated — 5,786 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (178 words, 1116 chars, 3762 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1954
Apartment For Rent in Compound  Lamirada
ground floor 
Area 100m 
2 bedroom 
2 bathroom 
Fully furnished 
Price 35.000

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code lv279
Apartment for sale in Lake view Residence
Area143m 
2 bedrooms 
2 bathrooms 
super lux
kitchen & Acs 
price 12.000.000

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1484
Apartment for sale in stone residence 
2nd floor 
Area 175m
3 bedrooms 
3 bathrooms 
Semi finished 
Price 6,457,500

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code hp337
studio for sale in hyde park
area 81m
1
[truncated — 1,115 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (252 words, 2268 chars, 837 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "La Mirada",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment For Rent in Compound Lamirada ground floor Area 100m 2 bedroom 2 bathroom Fully furnished Price 35.000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12000000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Lake View Residence",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Lake view Residence Area143m 2 bedroo
[truncated — 2,268 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 4770 | 2068 | 0 | 0 | $0.00130 | 5.01 | 5.01 |
| 2 | 6 | 6 | 6 | 3762 | 837 | 0 | 0 | $0.00071 | 2.61 | 2.61 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 7.61 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.81 | 3.81 | 4266 | 1452 | 366 | 462 | 10.0 | 2.63 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 8532 | $0.00085 | 4266 |
| output | 2905 | $0.00116 | 1452 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.002015**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0165 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (18:41)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 3 | 2 | 32_messages_30_03_2025.txt |

### Batch 1/3


**Input**

<details>
<summary>▶ Show input text (557 words, 3452 chars, 4704 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨sale in Eastown 🚨
Code ESs229
Apartment for sale in Eastown 
Area 156 SQM 
2 bedrooms ( 1 master & dressing ) 
3 bathrooms 
Fully furnished 
Kitchen 
ACs 
View Landscape 
*Price* 
Fully furnished 14,600,000
 Unfurnished 13,650,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
Available 
Code ESs236
Apartment ground floor with garden for sale in Eastown 
Area 156 SQM
Garden 120 SQM
3 bedrooms 
2 bathrooms 
Reception 
Fully finished 
Kitchen 
ACs
Price 15,500,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESs239
Duplex ground floor with garden for sale in Eastown 
Area 263 SQM
Garden 60 SQM
3 bedrooms (1master & dressing)
3 bathrooms 
Nanny room with bathroom 
Semi finished 
Price 19,950,00
[truncated — 3,451 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (746 words, 6820 chars, 2651 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 14600000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Eastown Area 156 SQM 2 bedrooms Fully furnished Price 14,600,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 13650000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Eastown Area 156 SQM 2 bedrooms Unfurnished Price 13,650,000",
    "ad_ind
[truncated — 6,820 chars total]
```

</details>


---

### Batch 2/3


**Input**

<details>
<summary>▶ Show input text (467 words, 2840 chars, 4451 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-03-30T17:52:00) ---
🚨rent in Eastown 🚨
Available 
Code ESr230
Apartment for rent in Eastown 
Area 205 SQM 
2nd floor 
3 bedrooms 
3 bathrooms 
Nany room with bathroom 
Kitchen 
ACs 
Price 50k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr88
Duplex with roof for rent in  Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
 price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr89
Duplex for rent in Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESr238
Apartment for rent in Eastown 
Area 195 SQM
2nd floor 
3 bedrooms (1 master)
3
[truncated — 2,839 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (719 words, 6091 chars, 2199 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 50000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 205 SQM 2nd floor 3 bedrooms 3 bathrooms Nany room with bathroom Kitchen ACs Price 50k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 100000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Duplex with roof for rent in Eastown Area 283sqm Roof 79 sqm 3 bedroo
[truncated — 6,091 chars total]
```

</details>


---

### Batch 3/3


**Input**

<details>
<summary>▶ Show input text (313 words, 1828 chars, 4200 tokens)</summary>

```
--- AD 1 (from: +20 11 11885910, date: 2025-03-30T00:14:00) ---
Update price
Code ESr196
Apartment for rent in Eastown 
Area 216 SQM
1st floor 
3 bedrooms (1 master)
3 bathrooms 
Reception 
Laundry Room 
Fully furnished 
Kitchen with appliances 
ACs
Price 150k

--- AD 2 (from: +20 11 11885910, date: 2025-03-30T05:02:00) ---
Code ESr243
Duplex for rent in eastown 
Area 286 SQM 
3 bedrooms ( 1 master ) 3 Bathrooms 
Nany room with bathroom 
Kitchen 
ACs
Price 2500$

--- AD 3 (from: +20 11 11885910, date: 2025-03-30T00:06:00) ---
Code ESr242
Apartment for rent in Eastown 
Area 220 SQM
3 bedrooms (1master & dressing) 
3 bathrooms 
Reception 
Kitchen 
ACs
Price 60k

--- AD 4 (from: +20 10 09337264
[truncated — 1,827 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (445 words, 3774 chars, 1425 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 150000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 216 SQM 1st floor 3 bedrooms (1 master) 3 bathrooms Reception Laundry Room Fully furnished Kitchen with appliances ACs Price 150k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 2500,
    "currency": "USD",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Duplex for rent in eastown 
[truncated — 3,774 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 15 | 19 | 4704 | 2651 | 0 | 0 | $0.00153 | 4.37 | 4.37 |
| 2 | 3 | 15 | 15 | 4451 | 2199 | 0 | 0 | $0.00132 | 5.88 | 5.88 |
| 3 | 10 | 10 | 10 | 4200 | 1425 | 0 | 3336 | $0.00107 | 3.55 | 3.55 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 16 | 40 | 44 | 13.81 | 3 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.60 | 4.60 | 4452 | 2092 | 446 | 637 | 14.7 | 3.19 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 13355 | $0.00134 | 4452 |
| output | 6275 | $0.00251 | 2092 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 3336 | $0.00008 | 1112 |

**Total run cost: $0.003929**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0204 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 7 | 0 | 8 | 1 | 16 |

**Listings inserted:** 44


============================================================

## (8/4/2026)Run — (18:46)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 2 | 2 | 27_messages_13_10_2024.txt |

### Batch 1/2


**Input**

<details>
<summary>▶ Show input text (554 words, 3382 chars, 4770 tokens)</summary>

```
--- AD 1 (from: +20 10 28830195, date: 2024-10-13T00:43:00) ---
*Village Gate Palm Hills*
Duplex Available For Rent:
Bua: 220sqm.
Garden: 120sqm.
_____
3 Bedrooms ( 1 Master ).
3 Bathrooms ( 2 Water heaters ).
_____
AC'S and Kitchen with Appliances.
Private Parking.
_____
Price: 45k per month ✨ ...

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code sh177
pharmacy for sale in hyde park 
 Unit CVA3-4g
 area :50 m
fully  finished
 Price : 1,100,000$ cash
installments : 1,200,000 / 2 years
60% 1st Yr , 40 % 2nd Yr
(USD for installments  will be the reference for amount in EGP)

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code vgk43
Apartment with garden for
[truncated — 3,381 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (669 words, 5752 chars, 2056 tokens)</summary>

```
[
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 45000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Palm Hills",
    "city": "6th of October City",
    "district": null,
    "ad_snippet": "Duplex Available For Rent: Bua: 220sqm. Garden: 120sqm. 3 Bedrooms ( 1 Master ). 3 Bathrooms ( 2 Water heaters ). AC'S and Kitchen with Appliances. Private Parking. Price: 45k per month",
    "ad_index": 1
  },
  {
    "property_type": "shop",
    "transaction_type": "sale",
    "price": 1100000,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": "Hyde Park",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "pha
[truncated — 5,752 chars total]
```

</details>


---

### Batch 2/2


**Input**

<details>
<summary>▶ Show input text (178 words, 1116 chars, 3762 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1954
Apartment For Rent in Compound  Lamirada
ground floor 
Area 100m 
2 bedroom 
2 bathroom 
Fully furnished 
Price 35.000

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code lv279
Apartment for sale in Lake view Residence
Area143m 
2 bedrooms 
2 bathrooms 
super lux
kitchen & Acs 
price 12.000.000

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code ncc1484
Apartment for sale in stone residence 
2nd floor 
Area 175m
3 bedrooms 
3 bathrooms 
Semi finished 
Price 6,457,500

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
code hp337
studio for sale in hyde park
area 81m
1
[truncated — 1,115 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (252 words, 2268 chars, 837 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 35000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "La Mirada",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment For Rent in Compound Lamirada ground floor Area 100m 2 bedroom 2 bathroom Fully furnished Price 35.000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 12000000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Lake View Residence",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Lake view Residence Area143m 2 bedroo
[truncated — 2,268 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | 15 | 14 | 4770 | 2056 | 0 | 0 | $0.00130 | 5.94 | 5.94 |
| 2 | 6 | 6 | 6 | 3762 | 837 | 0 | 3206 | $0.00079 | 2.67 | 2.67 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 20 | 21 | 20 | 8.61 | 2 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.30 | 4.30 | 4266 | 1446 | 366 | 460 | 10.0 | 2.32 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 8532 | $0.00085 | 4266 |
| output | 2893 | $0.00116 | 1446 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 3206 | $0.00008 | 1603 |

**Total run cost: $0.002091**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0225 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 2 | 0 | 4 | 1 | 20 |

**Listings inserted:** 20


============================================================

## (8/4/2026)Run — (19:04)

| model | total_batches | days | file |
| --- | --- | --- | --- |
| gemini-2.5-flash-lite | 5 | 2 | 2days_53_messages.txt |

### Batch 1/5


**Input**

<details>
<summary>▶ Show input text (543 words, 3404 chars, 4704 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-04-01T11:23:00) ---
🚨sale in Eastown 🚨
Code ESs229
Apartment for sale in Eastown 
Area 156 SQM 
2 bedrooms ( 1 master & dressing ) 
3 bathrooms 
Fully furnished 
Kitchen 
ACs 
View Landscape 
*Price* 
Fully furnished 14,600,000
 Unfurnished 13,650,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
Available 
Code ESs236
Apartment ground floor with garden for sale in Eastown 
Area 156 SQM
Garden 120 SQM
3 bedrooms 
2 bathrooms 
Reception 
Fully finished 
Kitchen 
ACs
Price 15,500,000
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESs239
Duplex ground floor with garden for sale in Eastown 
Area 263 SQM
Garden 60 SQM
3 bedrooms (1master & dressing)
3 bathrooms 
Nanny room with bathroom 
Semi finished 
Price 19,950,00
[truncated — 3,403 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (1009 words, 8552 chars, 3113 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 14600000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sale in Eastown Area 156 SQM 2 bedrooms ( 1 master & dressing ) 3 bathrooms Fully furnished Kitchen ACs View Landscape Price Fully furnished 14,600,000",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 13650000,
    "currency": "EGP",
    "bedrooms": 2,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for sal
[truncated — 8,552 chars total]
```

</details>


---

### Batch 2/5


**Input**

<details>
<summary>▶ Show input text (480 words, 2874 chars, 4475 tokens)</summary>

```
--- AD 1 (from: +20 11 02043283, date: 2025-04-01T11:23:00) ---
🚨rent in Eastown 🚨
Available 
Code ESr230
Apartment for rent in Eastown 
Area 205 SQM 
2nd floor 
3 bedrooms 
3 bathrooms 
Nany room with bathroom 
Kitchen 
ACs 
Price 50k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr88
Duplex with roof for rent in  Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
 price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
*Update price*
Code ESr89
Duplex for rent in Eastown 
Area 283sqm
Roof 79 sqm 
3 bedrooms  (1master)
3 bathrooms
Nanny room  
Fully finished
Kitchen
Ac's 
price 100k
⚡⚡⚡⚡⚡⚡⚡⚡⚡
Code ESr238
Apartment for rent in Eastown 
Area 195 SQM
2nd floor 
3 bedrooms (1 master)
3
[truncated — 2,873 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (729 words, 6129 chars, 2231 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 50000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in Eastown Area 205 SQM 2nd floor 3 bedrooms 3 bathrooms Nany room with bathroom Kitchen ACs Price 50k",
    "ad_index": 1
  },
  {
    "property_type": "duplex",
    "transaction_type": "rent",
    "price": 100000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Eastown",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Duplex with roof for rent in Eastown Area 283sqm Roof 79 sqm 3 bedroo
[truncated — 6,129 chars total]
```

</details>


---

### Batch 3/5


**Input**

<details>
<summary>▶ Show input text (665 words, 4090 chars, 5028 tokens)</summary>

```
--- AD 1 (from: +44 7308 548512, date: 2025-04-01T11:50:00) ---
SWIFT GPIMT103 SENDER!!
As a reliable and trustworthy provider of SWIFT Funding, we offer a range of options including GPI, GPI with UETR Code,
GPI-Semi Auto, MT103, MT103.202, and PIP, with global coverage across all banks.
  We are currently seeking competent and trustworthy Direct Receivers, Receiver Consultants, and Bankers who can handle our SWIFT Transfer with the utmost professionalism and reliability .
 Anyone that has someone in USA, UK, Canada, Dubai, Australia, Malaysia, Oman, kuwait, japan, Ecuador, Italy, spain, france, sweden, Romania, Netherlands, Greece, Austria, Germany, Belgium, Ireland, Russia or any  Europe c
[truncated — 4,089 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (763 words, 6350 chars, 2269 tokens)</summary>

```
[
  {
    "property_type": null,
    "transaction_type": null,
    "price": null,
    "currency": "USD",
    "bedrooms": null,
    "compound_name": null,
    "city": null,
    "district": null,
    "ad_snippet": "SWIFT GPIMT103 SENDER!! As a reliable and trustworthy provider of SWIFT Funding, we offer a range of options including GPI, GPI with UETR Code, GPI-Semi Auto, MT103, MT103.202, and PIP, with global coverage across all banks. We are currently seeking competent and trustworthy Direct Receivers, Receiver Consultants, and Bankers who can handle our SWIFT Transfer with the utmost professionalism and reliability . Anyone that has someone in USA, UK, Canada, Dubai, Australia, Malaysia, Oma
[truncated — 6,350 chars total]
```

</details>


---

### Batch 4/5


**Input**

<details>
<summary>▶ Show input text (465 words, 2894 chars, 4692 tokens)</summary>

```
--- AD 1 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code Mi648
Apartment for rent in mivida 
Boulevard 
Area 238m
4 bedrooms 
3 bathrooms 
Maids room with bathroom 
Ultra super lux
Furnished 
Price 3000$

--- AD 2 (from: +20 11 03387996, date: 2024-10-13T00:57:00) ---
Code sv19
Apartment for rent in villette sodice
Area 188m
3 bedrooms 
3 bathrooms 
Nany room with bathroom 
Super lux
Furnished 
Price 90k long term

--- AD 3 (from: +20 11 03387996, date: 2024-10-13T00:58:00) ---
Code mi650
Twin house for sale in mivida 
Area 300m
4 bedrooms ( 1 master)
4 bathrooms 
Living 
Acs
Heaters 
Ultra super lux 
Price 34.000.000

--- AD 4 (from: +20 11 03387996, date: 2024-10-13T00:58:00) -
[truncated — 2,893 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (638 words, 5711 chars, 2104 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 3000,
    "currency": "USD",
    "bedrooms": 4,
    "compound_name": "Mivida",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in mivida Boulevard Area 238m 4 bedrooms 3 bathrooms Maids room with bathroom Ultra super lux Furnished Price 3000$",
    "ad_index": 1
  },
  {
    "property_type": "apartment",
    "transaction_type": "rent",
    "price": 90000,
    "currency": "EGP",
    "bedrooms": 3,
    "compound_name": "Villette",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "Apartment for rent in villette sodice Area 188m 3 bedro
[truncated — 5,711 chars total]
```

</details>


---

### Batch 5/5


**Input**

<details>
<summary>▶ Show input text (175 words, 1070 chars, 3874 tokens)</summary>

```
--- AD 1 (from: +20 11 43299229, date: 2025-04-01T07:00:00) ---
موجود حصرى 294م في الرحاب
دور تالت اسانسير 
في المرحله السابعه 
تشطيبات خاصه 
مطلوب 15.500.000
📸📸📸📸📸📸

--- AD 2 (from: +20 11 43299229, date: 2025-04-01T07:00:00) ---
موجود شاليه في ستيلا مارينا الساحل الشمالي
مساحه 120م بجاردن 
متشطب 
مطلوب 3.500.000
📸📸📸📸📸📸📸

--- AD 3 (from: +20 11 43299229, date: 2025-04-01T06:53:00) ---
شقه للبيع 133م
في مونتن فيو 
دور تانى اسانسير 
تشطيبات خاصه 
مطلوب 8.600.000 تفاوض 
📸📸📸📸📸📸

--- AD 4 (from: +20 11 43299229, date: 2025-04-01T07:00:00) ---
فيلا حصرى نموذج y
ارض 740م
مبانى 437م
تشطيبات خاصه 
حمام سباحه 
مطلوب 50 مليون 
📸📸📸📸📸📸📸

--- AD 5 (from: +20 15 52187570, date: 2025-04-01T10:15:00) ---
بد
[truncated — 1,069 chars total]
```

</details>


**Output**

<details>
<summary>▶ Show output text (260 words, 2385 chars, 951 tokens)</summary>

```
[
  {
    "property_type": "apartment",
    "transaction_type": "sale",
    "price": 15500000,
    "currency": "EGP",
    "bedrooms": null,
    "compound_name": "Rehab City",
    "city": "New Cairo",
    "district": "5th Settlement",
    "ad_snippet": "موجود حصرى 294م في الرحاب المرحله السابعه تشطيبات خاصه مطلوب 15.500.000",
    "ad_index": 1
  },
  {
    "property_type": "chalet",
    "transaction_type": "sale",
    "price": 3500000,
    "currency": "EGP",
    "bedrooms": null,
    "compound_name": null,
    "city": "North Coast",
    "district": null,
    "ad_snippet": "موجود شاليه في ستيلا مارينا الساحل الشمالي مساحه 120م بجاردن متشطب مطلوب 3.500.000",
    "ad_index": 2
  },
  {
    "prop
[truncated — 2,385 chars total]
```

</details>


---

### Run Summary


**Per-Batch Overview**

| batch | msgs | est_ads | extracted | in_tok | out_tok | th_tok | ca_tok | cost | latency_s | api_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 3 | 15 | 20 | 4704 | 3113 | 0 | 0 | $0.00172 | 7.78 | 7.78 |
| 2 | 3 | 15 | 15 | 4475 | 2231 | 0 | 0 | $0.00134 | 6.94 | 6.94 |
| 3 | 14 | 15 | 14 | 5028 | 2269 | 0 | 0 | $0.00141 | 7.21 | 7.21 |
| 4 | 15 | 15 | 15 | 4692 | 2104 | 0 | 0 | $0.00131 | 5.53 | 5.53 |
| 5 | 7 | 7 | 7 | 3874 | 951 | 0 | 0 | $0.00077 | 3.99 | 3.99 |

**Totals**

| msgs_in | est_ads | extracted | total_s | batches |
| --- | --- | --- | --- | --- |
| 42 | 67 | 71 | 31.46 | 5 |

**Averages per Batch**

| avg_latency_s | avg_api_s | avg_in_tok | avg_out_tok | avg_in_words | avg_out_words | avg_extracted | ads/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6.29 | 6.29 | 4555 | 2134 | 466 | 680 | 14.2 | 2.26 |

**Token Breakdown**

| type | total_tokens | total_cost | avg_per_batch |
| --- | --- | --- | --- |
| input | 22773 | $0.00228 | 4555 |
| output | 10668 | $0.00427 | 2134 |
| thinking | 0 | $0.00000 | 0 |
| cache_read | 0 | $0.00000 | 0 |

**Total run cost: $0.006544**


**Daily Cost Status**

| date | spent | limit |
| --- | --- | --- |
| 2026-04-08 | 0.0291 | 2.0 |

**Filter Stats**

| system | too_short | blocklist | no_keywords | passed |
| --- | --- | --- | --- | --- |
| 3 | 0 | 7 | 1 | 42 |

**Listings inserted:** 71


============================================================
