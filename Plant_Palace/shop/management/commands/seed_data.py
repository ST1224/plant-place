"""
Management command to seed Plant Palace database with categories and products.
Run: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shop.models import Category, Product


CATEGORIES = [
    {"name": "Fruit Plants",    "slug": "fruit-plants",    "description": "Fresh fruit-bearing plants for your garden."},
    {"name": "Flowering Plants","slug": "flowering-plants","description": "Beautiful flowering plants to brighten your space."},
    {"name": "Medicinal Plants","slug": "medicinal-plants","description": "Plants with healing and medicinal properties."},
    {"name": "Indoor Plants",   "slug": "indoor-plants",   "description": "Perfect plants for indoor spaces and offices."},
    {"name": "Aromatic Plants", "slug": "aromatic-plants", "description": "Fragrant herbs and aromatic plants."},
]

PRODUCTS = [
    # ── Fruit Plants ──
    {"name": "Guava",         "img": "guava.jpg",         "cat": "fruit-plants",    "price": 120, "stock": 30, "desc": "Sweet tropical guava plant, easy to grow and highly productive."},
    {"name": "Mango",         "img": "mango.jpg",         "cat": "fruit-plants",    "price": 250, "stock": 20, "desc": "Classic Alphonso mango sapling. Bears delicious fruit in 2–3 years."},
    {"name": "Lemon Tree",    "img": "lemon_tree.jpg",    "cat": "fruit-plants",    "price": 150, "stock": 25, "desc": "Dwarf lemon tree, ideal for pots. Produces tangy, juicy lemons year-round."},
    {"name": "Papaya",        "img": "papaya.jpg",        "cat": "fruit-plants",    "price": 80,  "stock": 40, "desc": "Fast-growing papaya plant. Rich in vitamins and great for home gardens."},
    {"name": "Pineapple",     "img": "pineapple.jpg",     "cat": "fruit-plants",    "price": 110, "stock": 18, "desc": "Tropical pineapple plant. Thrives in warm climates with minimal care."},
    {"name": "Amla",          "img": "amla.jpg",          "cat": "fruit-plants",    "price": 130, "stock": 22, "desc": "Indian gooseberry – a superfood plant packed with Vitamin C."},
    {"name": "Chikoo",        "img": "chikoo.jpg",        "cat": "fruit-plants",    "price": 140, "stock": 15, "desc": "Sapodilla (chikoo) plant bearing sweet, caramel-flavoured fruits."},
    {"name": "Jackfruit",     "img": "jackfruit.jpg",     "cat": "fruit-plants",    "price": 200, "stock": 12, "desc": "Giant jackfruit sapling. A nutritious meat alternative loved across India."},
    {"name": "Apple",         "img": "apple.jpg",         "cat": "fruit-plants",    "price": 350, "stock": 10, "desc": "Himalayan apple variety adaptable to varied climates."},
    {"name": "Jamun",         "img": "Jamun.jpg",         "cat": "fruit-plants",    "price": 160, "stock": 14, "desc": "Indian blackberry (jamun) with juicy, antioxidant-rich fruits."},
    {"name": "Kokum",         "img": "kokum.jpg",         "cat": "fruit-plants",    "price": 175, "stock": 10, "desc": "Coastal kokum plant used in cooking and traditional medicine."},
    {"name": "Sitaphal",      "img": "sitaphal.jpg",      "cat": "fruit-plants",    "price": 190, "stock": 8,  "desc": "Custard apple (sitaphal) with creamy sweet flesh."},
    {"name": "Kavath",        "img": "Kavath.jpg",        "cat": "fruit-plants",    "price": 155, "stock": 12, "desc": "Wood apple (kavath) with aromatic, nutritious fruit."},
    {"name": "Miracle Fruit", "img": "miracle_fruit.jpg", "cat": "fruit-plants",    "price": 280, "stock": 6,  "desc": "Rare miracle fruit that makes sour foods taste sweet."},

    # ── Flowering Plants ──
    {"name": "Rose (Red)",           "img": "rose_red.jpg",             "cat": "flowering-plants", "price": 90,  "stock": 50, "desc": "Classic red rose – the symbol of love. Fragrant and long-lasting blooms."},
    {"name": "Button Rose (White)",  "img": "button_rose_white.jpg",    "cat": "flowering-plants", "price": 85,  "stock": 45, "desc": "Delicate white button roses, perfect for bouquets and garden borders."},
    {"name": "Miniature Rose",       "img": "miniature_rose.jpg",       "cat": "flowering-plants", "price": 75,  "stock": 40, "desc": "Compact miniature rose ideal for pots and windowsills."},
    {"name": "Mogra",                "img": "mogra.jpg",                "cat": "flowering-plants", "price": 70,  "stock": 55, "desc": "Arabian jasmine (mogra) with heavenly fragrance and white blooms."},
    {"name": "Daisy",                "img": "daisy.jpg",                "cat": "flowering-plants", "price": 60,  "stock": 60, "desc": "Cheerful white daisies that brighten any garden or balcony."},
    {"name": "Peacock Flower",       "img": "peacock_flower.jpg",       "cat": "flowering-plants", "price": 95,  "stock": 30, "desc": "Vibrant peacock flower (Gulmohar) known for its stunning orange-red blooms."},
    {"name": "Night Flowering Jasmine","img":"night_flowering_jasmine.jpg","cat":"flowering-plants","price": 100, "stock": 35, "desc": "Parijat – blooms at night with intoxicating fragrance."},
    {"name": "Krishna Kamal",        "img": "krishna_kamal.jpg",        "cat": "flowering-plants", "price": 120, "stock": 20, "desc": "Passionflower (Krishna Kamal) with exotic, intricate blooms."},
    {"name": "Hydrangea Macrophylla","img": "hydrangea_macrophylla.jpg","cat": "flowering-plants", "price": 180, "stock": 15, "desc": "Lush hydrangea with large clusters of blue or pink flowers."},
    {"name": "Aster (Peach)",        "img": "aster_peach.jpg",          "cat": "flowering-plants", "price": 65,  "stock": 40, "desc": "Soft peach aster flowers that bloom abundantly in cooler months."},
    {"name": "Aster (White)",        "img": "aster_white.jpg",          "cat": "flowering-plants", "price": 65,  "stock": 40, "desc": "Pure white aster flowers – elegant and easy to grow."},
    {"name": "Celosia Cockscomb",    "img": "celosia_cockscomb.jpg",    "cat": "flowering-plants", "price": 55,  "stock": 50, "desc": "Vibrant velvety cockscomb flowers in bold reds and yellows."},
    {"name": "Galphimia Glauca",     "img": "galphimiaGlauca.jpg",      "cat": "flowering-plants", "price": 90,  "stock": 25, "desc": "Golden shower shrub with cheerful yellow blooms year-round."},
    {"name": "Flame of the Forest",  "img": "flame.jpg",                "cat": "flowering-plants", "price": 220, "stock": 10, "desc": "Brilliant orange flame-of-the-forest tree sapling."},

    # ── Medicinal Plants ──
    {"name": "Aloe Vera (Burgersfortenis)","img":"aloe_burgersfortenis.jpg","cat":"medicinal-plants","price":80, "stock": 35, "desc": "Medicinal aloe vera variety with thick, gel-rich leaves."},
    {"name": "Insulin Plant",        "img": "insulin.jpg",              "cat": "medicinal-plants", "price": 70,  "stock": 30, "desc": "Costus plant traditionally used to help regulate blood sugar levels."},
    {"name": "Miracle Leaf",         "img": "miracle_leaf.jpg",         "cat": "medicinal-plants", "price": 60,  "stock": 40, "desc": "Patharchatta – leaves known for treating kidney and digestive issues."},
    {"name": "Curry Leaves",         "img": "curryleaves.jpg",           "cat": "medicinal-plants", "price": 50,  "stock": 60, "desc": "Essential Indian kitchen herb with many medicinal benefits."},
    {"name": "Betel Leaves",         "img": "betel_leaves.jpg",         "cat": "medicinal-plants", "price": 55,  "stock": 45, "desc": "Paan leaves used in traditional remedies and cultural rituals."},
    {"name": "Hadjod",               "img": "hadjod.jpg",               "cat": "medicinal-plants", "price": 90,  "stock": 20, "desc": "Bone-setter plant (cissus) known for aiding fracture healing."},
    {"name": "Krishna Tulsi",        "img": "KrishnaTulsi.jpg",         "cat": "medicinal-plants", "price": 45,  "stock": 70, "desc": "Purple-leafed holy basil with potent immune-boosting properties."},
    {"name": "Henna",                "img": "henna.jpg",                "cat": "medicinal-plants", "price": 60,  "stock": 35, "desc": "Mehndi plant used for natural hair dye, skin care, and cooling."},
    {"name": "Kesavardhini",         "img": "kesavardhini.jpg",         "cat": "medicinal-plants", "price": 75,  "stock": 25, "desc": "Traditional herb used for hair growth and scalp health."},

    # ── Indoor Plants ──
    {"name": "Areca Palm",           "img": "areca_palm.jpg",           "cat": "indoor-plants",    "price": 250, "stock": 20, "desc": "Elegant air-purifying areca palm, perfect for living rooms."},
    {"name": "Lucky Bamboo",         "img": "lucky_bamboo.jpg",         "cat": "indoor-plants",    "price": 150, "stock": 30, "desc": "Low-maintenance lucky bamboo symbolising good fortune."},
    {"name": "Fern",                 "img": "fern.jpg",                 "cat": "indoor-plants",    "price": 80,  "stock": 40, "desc": "Lush Boston fern – a classic indoor plant that loves humidity."},
    {"name": "Green Fern Mini",      "img": "greenfernmini.jpg",        "cat": "indoor-plants",    "price": 65,  "stock": 50, "desc": "Compact mini fern, ideal for desks, shelves, and terrariums."},
    {"name": "Aglaonema Red Valentine","img":"aglaonema_red_valentine.jpg","cat":"indoor-plants",  "price": 200, "stock": 15, "desc": "Striking red-leaf aglaonema – a bold statement plant for indoors."},
    {"name": "Aralia",               "img": "aralia.jpg",               "cat": "indoor-plants",    "price": 180, "stock": 18, "desc": "Decorative aralia with deeply lobed leaves and graceful form."},
    {"name": "White Butterfly",      "img": "white_butterfly.jpg",      "cat": "indoor-plants",    "price": 120, "stock": 25, "desc": "Syngonium 'White Butterfly' – trailing plant with heart-shaped leaves."},
    {"name": "Dwarf Schefflera Variegated","img":"dwarfscheffler avarigated.jpg","cat":"indoor-plants","price":170,"stock":20,"desc":"Compact variegated umbrella plant, excellent for indoor décor."},
    {"name": "Garden Croton",        "img": "garden_corton.jpg",        "cat": "indoor-plants",    "price": 130, "stock": 30, "desc": "Colourful croton with vibrant multi-toned foliage."},
    {"name": "Ficus Panda Golden",   "img": "ficus panda golden.jpg",   "cat": "indoor-plants",    "price": 200, "stock": 12, "desc": "Golden panda ficus – a cheerful, easy-care indoor bonsai-style plant."},
    {"name": "Cordyline Baby Doll",  "img": "cordyline_baby_doll.jpg",  "cat": "indoor-plants",    "price": 160, "stock": 15, "desc": "Compact cordyline with striking pink and green foliage."},
    {"name": "Cordyline Rubra",      "img": "cordyline rubma.jpg",      "cat": "indoor-plants",    "price": 175, "stock": 12, "desc": "Deep red cordyline that adds dramatic tropical colour indoors."},
    {"name": "Euphorbia Tirucalli",  "img": "euphorbia_tirucalli.jpg",  "cat": "indoor-plants",    "price": 95,  "stock": 28, "desc": "Pencil cactus – a unique succulent-like plant for bright spots."},
    {"name": "Milk Wine Lily",       "img": "milk_wine_lily.jpg",       "cat": "indoor-plants",    "price": 140, "stock": 20, "desc": "Crinum lily with elegant white flowers tinged with wine-red."},
    {"name": "Painted Nettle",       "img": "painted_nettle.jpg",       "cat": "indoor-plants",    "price": 60,  "stock": 45, "desc": "Coleus (painted nettle) with brilliantly patterned foliage."},
    {"name": "Sitar's Gold",         "img": "sitars_gold.jpg",          "cat": "indoor-plants",    "price": 145, "stock": 18, "desc": "Golden-leafed ornamental plant that adds warmth to any interior."},
    {"name": "Graptophyllum Pictum", "img": "graptophyllum_pictum.jpg", "cat": "indoor-plants",    "price": 110, "stock": 22, "desc": "Caricature plant with beautiful marbled leaves."},
    {"name": "Erathimum Variegated", "img": "erathimum varigated.jpg",  "cat": "indoor-plants",    "price": 125, "stock": 20, "desc": "Variegated eranthemum with striking bicoloured leaves."},
    {"name": "Erathimum Black Magic","img": "erathimum blackmagic.jpg", "cat": "indoor-plants",    "price": 130, "stock": 15, "desc": "Dark purple 'Black Magic' eranthemum – a dramatic foliage plant."},
    {"name": "Chocolate Soldier",    "img": "choclate_solider.jpg",     "cat": "indoor-plants",    "price": 115, "stock": 20, "desc": "Fuzzy kalanchoe (chocolate soldier) with soft velvety leaves."},

    # ── Aromatic Plants ──
    {"name": "Lemongrass",           "img": "lemonGrass.jpg",           "cat": "aromatic-plants",  "price": 55,  "stock": 60, "desc": "Fragrant lemongrass for teas, cooking, and natural mosquito repellent."},
    {"name": "Peppermint",           "img": "peppermint.jpg",           "cat": "aromatic-plants",  "price": 50,  "stock": 55, "desc": "Cool and refreshing peppermint plant for teas and aromatherapy."},
    {"name": "Rosemary",             "img": "rosemary.jpg",             "cat": "aromatic-plants",  "price": 65,  "stock": 45, "desc": "Mediterranean rosemary herb, great for cooking and landscaping."},
    {"name": "Marwa",                "img": "marwa.jpg",                "cat": "aromatic-plants",  "price": 50,  "stock": 50, "desc": "Sweet marjoram (marwa) with soothing aroma and culinary uses."},
    {"name": "Patta Ajwain",         "img": "pattaajwain.jpg",          "cat": "aromatic-plants",  "price": 45,  "stock": 65, "desc": "Indian borage (ajwain) leaf used as a cough and cold remedy."},
]


class Command(BaseCommand):
    help = "Seed the database with Plant Palace categories and products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing products and categories before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing data."))

        # ── Create categories ──
        cat_map = {}
        for c in CATEGORIES:
            obj, created = Category.objects.get_or_create(
                slug=c["slug"],
                defaults={"name": c["name"], "description": c["description"]},
            )
            cat_map[c["slug"]] = obj
            status = "created" if created else "exists"
            self.stdout.write(f"  Category [{status}]: {obj.name}")

        # ── Create products ──
        created_count = 0
        for p in PRODUCTS:
            cat = cat_map.get(p["cat"])
            img_path = f"shop/images/{p['img']}"
            slug = slugify(p["name"])

            # Ensure unique slug
            base_slug, counter = slug, 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            obj, created = Product.objects.get_or_create(
                product_name=p["name"],
                defaults={
                    "slug": slug,
                    "category": cat,
                    "description": p["desc"],
                    "price": p["price"],
                    "stock": p["stock"],
                    "image": img_path,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Product [created]: {obj.product_name}")
            else:
                self.stdout.write(f"  Product [exists]:  {obj.product_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seeding complete — {created_count} products created across {len(CATEGORIES)} categories."
            )
        )
