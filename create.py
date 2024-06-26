from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Research on Shoes for Plus-Size Nurses', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        body = body.replace('’', "'").replace('“', '"').replace('”', '"')
        self.multi_cell(0, 10, body)
        self.ln()

pdf = PDF()

pdf.add_page()

# Section 1
pdf.chapter_title("1. Info on Shoes a Plus-Size Nurse Might Want to Wear, and Why")

info_section = """\
**Clove Shoes**
- Features: Clove shoes are specifically designed for healthcare workers, offering excellent support, comfort, and ease of maintenance. They have a snug fit that aligns the body and provides more support, making them ideal for long shifts.
- Why: Plus-size nurses need shoes that offer maximum support to prevent foot and joint pain. Clove shoes provide ergonomic design and immediate comfort without the need for a break-in period. They are also easy to clean and come in various colors.
- Proof: Nurses appreciate Clove shoes for their body alignment and support during long shifts. One nurse stated, "My body feels aligned, have more support. It only takes one day to get used to them. New shoes you usually have to break them in before they feel comfortable. I didn't have to do that with cloves".
- Link: [Clove Sneakers](https://goclove.com/products/womens-classic)

**Skechers Sport Women’s Premium-Premix Slip-On Sneaker**
- Features: These shoes feature a slip-on design, rubber soles, padded collars, and air-cushioned footbeds.
- Why: The slip-on design and cushioning are convenient for plus-size nurses who need shoes that are easy to wear and provide comfort during long hours of standing and walking.
- Proof: The slip-on feature and cushioned design help absorb shock and provide comfort, which is crucial for nurses who spend long hours on their feet.
- Link: [Skechers Sport Women's Premium-Premix Slip-On Sneaker](https://www.amazon.com/Skechers-Womens-Premium-Premix-Slip-Sneaker/dp/B0012DHVIK)

**Dansko Women’s Professional Clog**
- Features: Known for their wide toe boxes, durable leather uppers, and shock-absorbing rubber outsoles, Dansko clogs offer superior stability and support.
- Why: The wide toe box and robust arch support are ideal for plus-size nurses who need extra room and stability to accommodate their feet and additional weight.
- Proof: Nurses recommend Dansko clogs for their comfort and support. One nurse mentioned, "The wide toe box and the shock-absorbing rubber outsole make these shoes very comfortable for long shifts".
- Link: [Dansko Women's Professional Clog](https://www.amazon.com/Dansko-Professional-Black-Oiled-Leather/dp/B000XQRU4G)

**HOKA ONE ONE Bondi 8**
- Features: These shoes provide excellent cushioning, a breathable upper, and a memory foam ankle cradle. They are lightweight and offer good support in the heel and ankle.
- Why: HOKA Bondi 8 shoes are great for plus-size nurses who need substantial cushioning and support to reduce fatigue and pain during long shifts. They are recommended by the American Podiatric Medical Association (APMA).
- Proof: A nurse commented, "The Bondi 8’s have much more support in the heel and ankle. I usually wear those when I’m working three days in a row".
- Link: [HOKA ONE ONE Bondi 8](https://www.hoka.com/en/us/womens-road/bondi-8/1110518.html)
"""

pdf.chapter_body(info_section)

# Section 2
pdf.chapter_title("2. What Plus-Size People Look for in Shoes")

look_for_section = """\
**Support and Cushioning**:
- Plus-size individuals prioritize shoes with enhanced support and cushioning to manage additional weight and reduce the risk of foot and joint pain. Memory foam insoles, cushioned midsoles, and reinforced arches are crucial features.
- Proof: A reviewer mentioned, "The shoes have a breathable upper knit material which is great to keep your feet cool during warmer weather and during exercise. I love the roomy toe box and how soft and comfortable yet supportive the insoles and Rabbit Foam Outsole make the shoes feel".

**Wide Toe Boxes**:
- Shoes with wide toe boxes are essential to provide extra room and prevent discomfort. This feature helps avoid blisters and offers a more comfortable fit.
- Proof: "Wide width consideration is very important, especially for those with large feet. Finding shoes that accommodate wide feet without compromising on style is crucial".

**Durability**:
- Durable materials like high-quality leather or synthetic fabrics are important to withstand daily wear and tear. Plus-size individuals often need shoes that can handle more stress without wearing out quickly.
- Proof: "These shoes have a durable rubber outsole which keeps the bottom of the shoe from wearing away quickly".

**Breathability**:
- Breathable materials help keep feet dry and comfortable, reducing the risk of blisters and foot infections. Mesh and knit uppers are particularly beneficial for maintaining foot health.
- Proof: "The breathable upper knit material keeps feet cool, and the shoes are very comfortable for daily walks and athleisure outfits".
"""

pdf.chapter_body(look_for_section)

# Section 3
pdf.chapter_title("3. Different Weights and Professions: What They Look for in Shoes")

professions_section = """\
**By Weight**:
- **Moderately Overweight**: Individuals in this category look for shoes with good arch support and moderate cushioning. Lightweight materials and flexibility are important to prevent foot fatigue.
- **Heavily Overweight**: Heavily overweight individuals need maximum cushioning and support. Shoes with reinforced soles, strong arch support, and extra-wide designs are essential to distribute weight evenly and provide stability.

**By Profession**:
- **Nurses**: Plus-size nurses need shoes that offer all-day comfort, non-slip soles for safety, and easy-to-clean materials. Brands like Clove, Skechers, and Dansko are popular for their ergonomic designs and durability.
  - Links: 
    - [Clove Sneakers](https://goclove.com/products/womens-classic)
    - [Skechers Sport Women's Premium-Premix Slip-On Sneaker](https://www.amazon.com/Skechers-Womens-Premium-Premix-Slip-Sneaker/dp/B0012DHVIK)
    - [Dansko Women's Professional Clog](https://www.amazon.com/Dansko-Professional-Black-Oiled-Leather/dp/B000XQRU4G)
    - [HOKA ONE ONE Bondi 8](https://www.hoka.com/en/us/womens-road/bondi-8/1110518.html)
- **Office Workers**: Plus-size office workers often prioritize stylish yet comfortable shoes that provide good support for prolonged sitting and occasional walking. They may prefer shoes with a professional appearance and moderate cushioning.
  - Example: Tory Burch Minnie ballet flats are popular among office workers for their stylish design and comfort.
- **Retail Workers**: Retail workers require shoes that offer extensive cushioning and support for long hours of standing and walking. Slip-resistant soles and durable materials are also important.
  - Example: Kizik shoes, known for their slip-on design and support, are a great option for retail workers.
- **Fitness Professionals**: Plus-size fitness professionals need shoes with excellent shock absorption and stability. Features like breathable materials, strong arch support, and flexible designs are critical to handle high-impact activities.
  - Example: Nike Air Zoom Pegasus 36 provides excellent cushioning and stability, which is beneficial for plus-size runners. The shoe's high resiliency sock liner and full-length Zoom air unit offer a smooth, responsive ride.
"""

pdf.chapter_body(professions_section)

# Save PDF
pdf_output_path = "Shoes_for_Plus_Size_Nurses.pdf"
pdf.output(pdf_output_path)

print(f"PDF generated and saved as {pdf_output_path}")
