# One-device distributor comparison

Prepared **12 November 2026** for **one device**, as requested. The two lists contain the same five items: the Reverse TFT Feather, SCD30, VEML7700, DS3231, and one SparkFun Qwiic cable assortment.

Reference merchandise subtotal: **$115.75 at either distributor**, using retrieved USD listing prices. Shipping, taxes, local batteries, and enclosure are excluded. This is a price comparison, not a checkout quotation. Stock observations and exact product links are in [the BOM](../BOM.md) and [the master CSV](../bom.csv).

## Digi-Key

[Add the five comparison items to a Digi-Key cart](https://www.digikey.com/classic/ordering/fastadd.aspx?newcart=false&part1=1528-5691-ND&qty1=1&part2=1528-4867-ND&qty2=1&part3=1528-2891-ND&qty3=1&part4=1528-5188-ND&qty4=1&part5=1568-15081-ND&qty5=1).

This link uses Digi-Key's documented FastAdd format. It **adds** one of each item to the current cart; use an empty cart for a clean comparison, and avoid opening it repeatedly because quantities can accumulate. It does not place an order. Automated verification returned HTTP 403, so successful population of all five lines has not been confirmed in a browser session. No saved/shared cart ID has been created.

Fallback: upload [digikey-one-device.csv](digikey-one-device.csv) using **Upload a List** on [Digi-Key's cart page](https://www.digikey.com/ordering/shoppingcart), mapping the part-number, quantity, and customer-reference columns.

Source: [Digi-Key FastAdd documentation](https://forum.digikey.com/t/digikey-fastadd-bulk-add-parts-into-a-digikey-cart-via-third-party-tooling-and-urls/61356/1).

## Mouser

The import is prepared; **a saved Mouser cart/share link has not yet been created**. Completing that step requires an interactive browser connection or authorized Mouser API access. The current web tool can read the catalogue but cannot submit this import and save/share the resulting cart.

Upload [mouser-one-device.csv](mouser-one-device.csv) into [Mouser's Price and Availability Assistant](https://www.mouser.com/en/price-availability/), map the columns, and add the five matched lines to the cart. Alternatively paste the contents of [mouser-copy-paste.txt](mouser-copy-paste.txt) using the **Mouser OR Mfr. # | Qty. 1** format. The plain-text file has no header and uses commas, which Mouser supports.

After the cart is populated, its **Share** control generates the saved cart access link. [Mouser cart sharing documentation](https://www.mouser.com/en/tools/ProjectCartSharing).

## Scope and order checks

- **Batteries stay local:** one protected rechargeable 1S pack and one CR1220 per device, both bought in Israel.
- **Cable assortment is shared:** it supplies the prototype connections. Do not multiply the assortment by student count. The eventual class order needs three QT-to-QT cables per device plus spares, with lengths chosen after enclosure layout.
- **USB cables are excluded** from both distributor lists as requested; use existing data cables for programming.
- **No separate screen** is needed; the Feather includes it. The RTC is required.
- Select **Israel** as the shipping destination and recheck stock, delivery eligibility, currency, and final costs. Region-specific Mouser listings can differ; Israel eligibility has not been verified through checkout.
- Use the exact assembled breakout part numbers. In particular, Digi-Key's VEML7700 SKU is **1528-2891-ND**, and its current SparkFun assortment SKU is **1568-15081-ND**.

The battery switch was removed from these imports in v0.2. The physical cart, if you previously imported v0.1, must also have its 3064 line removed. No purchase or payment has been submitted.
