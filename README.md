# Prof. Postmark - Your Remote Teacher (or just an AI)

> **Heads-Up!** This project was whipped up for the **Postmark Challenge: Inbox Innovators**. Truth be told, it'd be even *more* awesome with a job queue humming in the background, but hey, it rocks as is!
>
> *A Little Dev Vent:* Confession time – I wrestled with this beast for over 10 hours, tangoed with every major AI agent (Claude, GPT, Gemini, you name it!), and had a *truly* character-building (read: painful) dance with Cursor. Future development? Let's just say Prof. Postmark is taking a well-deserved nap for now. 😅 Bro, it was a journey!

Imagine you are a teacher collecting final exams via email and scoring them. Now, the assistant does this for you. The system can dynamically improve for similar cases. JUST IMAGINE MORE—or maybe you already need a system like this. Let me know!

**Prof. Postmark** isn't just another app; it's your intelligent photo evaluation pal, ready to dish out professional feedback and scores for photography submissions. Powered by OpenAI's GPT-4 Vision model and a snazzy custom image annotation engine, it zips through photos, cooks up detailed written feedback, and slaps on visual annotations that look like a teacher went to town with a red pen (but, like, in a cool, digital way). Built on an asynchronous FastAPI backend, it jams with Postmark for a slick email-to-AI-to-email experience.

## 🎯 Superpowers Unleashed (Key Features)

* **AI Brainiac Analysis**: Taps into OpenAI GPT-4o Vision for a deep-dive photo critique, all guided by some seriously detailed instructions. Think of it as your personal art connoisseur, but way faster!

* **Visual Flair (Annotations)**: Rocks a custom sketch-style annotation engine (`ImageAnnotator`) using Pillow that makes digital feedback look hand-drawn. Art on top of art, my friend!

* **Pro-Level Scoring**: Rolls out a 5-category scoring system: Composition & Balance, Focus & Depth, Lighting & Contrast, Color Harmony, and Visual Impact & Mood. Fair grades for all, no cap!

* **Automated Feedback Guru**: Magically generates detailed written feedback, complete with a score justification table and crystal-clear annotation explanations. Who knew robots could be such good teachers? For real!

* **Email Ninja Integration**: Masters the entire workflow – from snagging emails with photo attachments via Postmark webhooks to zapping back fully scored and annotated results. Your inbox just got a PhD!

* **Built to Scale (Architecture)**: Cooked up with FastAPI for speedy asynchronous processing and designed to handle hiccups like a champ. Ready for the rush, bro!

* **Image Polish & Shine**: Processes and scales images (JPEG, PNG) to the perfect dimensions for analysis, all while keeping that aspect ratio sacred. Non-square pics get their longest edge at 1200px, and square ones become a neat 800x800px. Tidy!

* **Webhook Security Guard**: Keeps your Postmark webhooks safe and sound by validating them with a secret token. No funny business allowed, ya heard?!

## 🏆 What's the Secret Sauce? (What Makes This Special)

### Intelligent Photo CSI (Crime Scene Investigation... but for pics!)

Prof. Postmark's AI doesn't just guess; it follows a comprehensive rulebook (`assets/instructions.txt`):

* **Composition & Balance** (30 pts): Scrutinizes the rule of thirds, subject placement, leading lines, negative space, and visual oomph. It's all about that visual harmony, bro!

* **Focus & Depth** (20 pts): Dials in on sharpness, depth of field, and how well that background pops (or doesn't). Crystal clear, or a bit fuzzy? We'll find out!

* **Lighting & Contrast** (20 pts): Investigates light direction, the full range of tones, and those moody shadow details. Lights, camera, analysis!

* **Color Harmony** (15 pts): Checks out color balance, whether the palette sings together, and overall tone control (yep, grayscale too!). A symphony of colors, my dude!

* **Visual Impact & Mood** (15 pts): Gauges the emotional punch, storytelling power, and sheer artistic awesomeness. Does it make you go "Whoa, bro!"?

### Next-Level Visual Feedback (Because seeing is believing!)

* **Sketch-tastic Annotation Engine**: The `ImageAnnotator` class whips up annotations that look like they were sketched by a friendly (and slightly caffeinated) art teacher.

* **Smarty-Pants Coordinate Calc**: Annotations land exactly where they should, adapting to the (scaled) image size like a chameleon, all thanks to clever inset and placement rules. Precision is key, my G!

* **Helpful Visual Cues**: Can overlay rule of thirds grids, draw lines to show compositional flow or where the light's coming from, and circle those all-important focal points. Your friendly guide to a better photo, no doubt!

* **Teacher's Pet Comments**: Drops insightful text comments right onto the image, super readable thanks to custom fonts (`GochiHand-Regular.ttf`) and cool shadow effects. Feedback never looked so good, fam!

* **Layer Cake Rendering**: Annotations, scores, and comments are neatly stacked on different layers before being served up as one awesome composite image. Deliciously organized, like a perfect seven-layer dip!

### Image Processing Wizardry (Abracadabra, your pic is perfect!)

* **Aspect Ratio Guardian**: Images are scaled without any weird stretching or squishing. Nobody likes a distorted photo, that's just facts!

* **One Size Fits Most (Smartly!)**: Non-square images max out at 1200px on their longest side, while square snaps become a perfect 800x800px. This makes them just right for the AI and keeps annotations looking sharp. Fair and square, always!

* **Universal Translator (Format)**: Images get converted to RGB JPEG for smooth processing and output. Speaking the lingua franca of photos, worldwide!

## 🔄 The Grand Tour: Workflow Adventure! (Buckle Up!)

 1. **Mail Call!**: An email, complete with a photo masterpiece (or work-in-progress), lands in the configured Postmark inbox. "You've got mail!"

 2. **Webhook Alert!**: Postmark pings the FastAPI app with a webhook. The game is afoot, Sherlock!

 3. **ID, Please! (Request Validation)**: The system checks the webhook's secret token. "Password?" (Hint: It's in your `.env`!)

 4. **Deconstructing the Email**: Incoming webhook data is sliced and diced to pull out sender info, subject, body, and those precious attachments. Like a digital surgeon!

 5. **Checkpoint Charlie (Input Validation)**:

    * Is it a "PING"? (Health check alert!) If so, a friendly "PONG" is volleyed back. Game on!

    * Attachment aboard? (No attachment, no party, unless it's a PING, bro).

    * Is it a legit image (JPEG, PNG) and not too chonky (default 5MB limit)? Size matters!

    * If validation fails, a polite "oops, my bad" email is sent. We're not monsters.

 6. **Image Makeover Time**: The attached image is decoded, given a resize, and standardized. Glow-up sequence activated!

 7. **AI Brainstorm Sesh**:

    * The polished image, along with the student's message and the AI's marching orders from `assets/instructions.txt`, is beamed up to OpenAI's GPT-4o model. "Beam me up, Scotty!"

    * The AI chews on it and spits back text feedback (scoring table included!) and a Python script to jazz up the image with annotations. "The results are in!"

 8. **Annotation Script Action! (Danger Zone! 💣)**:

    * The Python script from OpenAI gets run by the `AIAnalysisService`. **(MEGA IMPORTANT SECURITY WARNING: This uses `exec()` and is like playing with fire in production without a proper sandbox! Seriously, bro, be careful!)**

    * This script tells the `ImageAnnotator` how to doodle on the image. Let the art begin!

 9. **Crafting the Feedback Masterpiece**: An email is put together with the AI's insightful text (Markdown spiffed up into HTML) and the newly annotated image as an attachment. Chef's kiss!

10. **And... It's Off!**: The feedback email is launched back to the student via Postmark. Mission accomplished, agent!

## 🏗️ Under the Hood: System Architecture (The Blueprint!)

### The Nuts & Bolts (Core Components)

The project's like a well-organized toolbox, or maybe a legendary loot drop:

```
prof-postmark/
├── app.py                          # Main app entry point (where the magic starts for Uvicorn)
├── requirements.txt                # The shopping list of project dependencies (gotta have 'em)
├── .env                            # Your secret config file (shhh, it's a secret to everybody!)
├── assets/
│   └── instructions.txt            # The AI's instruction manual (the sacred texts!)
└── src/
    ├── api/
    │   ├── main.py                 # FastAPI app, routes, & webhook security guard (the bouncer)
    │   └── webhook_handler.py      # The conductor of the email processing orchestra (maestro!)
    ├── core/
    │   ├── configuration.py        # App config central (all the knobs and dials, tune 'em up!)
    │   └── domain_models.py        # Data blueprints (Pydantic style, keeping it classy)
    ├── services/
    │   ├── ai_analysis_service.py  # The OpenAI whisperer & analysis brain (the big thinker!)
    │   ├── email_parser.py         # The email decoder ring (cracking the code!)
    │   ├── email_service.py        # The outbound email dispatcher (via Postmark, special delivery!)
    │   ├── image_processor.py      # The image beautifier & standardizer (make it pop!)
    │   ├── validation_service.py   # The bouncer for email content & attachments (velvet rope status)
    │   └── image_annotation/
    │       ├── annotator.py        # The custom image doodling engine (the artist within!)
    │       └── font/               # Fancy fonts live here (GochiHand-Regular.ttf, lookin' good!)
    └── tests/
        └── test_system.py          # Where we check if everything's still awesome (QA crew!)

```

### Tech Stack Highlights (The Magic Ingredients - Level Up Your App!)

* **Backend Powerhouse**: FastAPI (Fast and, dare we say, furious! Lightning speed, bro!)

* **Speedy Web Server**: Uvicorn (Servin' it up hot and fresh!)

* **AI Smarts**: OpenAI GPT-4o Vision (Straight from the future, or a sci-fi movie!)

* **Image Ninja**: Pillow (PIL Fork) (Your photo's best friend, always there for ya!)

* **Email Courier**: Postmark (Delivering your emails, rain or shine, like a postal hero!)

* **Config King**: `python-dotenv` (For all your environment variable needs, keep 'em secret, keep 'em safe!)

* **HTML Whisperer (for emails)**: `BeautifulSoup4` (Tidying up those messy email bodies!)

* **Markdown Maestro**: `Mistune` (Turning plain feedback into pretty HTML, like magic!)

* **Async Ace**: `aiofiles`, `asyncio` (Juggling tasks like a pro, thanks FastAPI! Multitasking FTW!)

## 🚀 Blast Off! (Quick Start - Let's Get This Party Started!)

### 1. Get the Goods (Installation - Assemble Your Crew!)

```
git clone <repo-url>
cd prof-postmark
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### 2. Spill the Beans (Environment Configuration - The Secret Handshake!)

Create a `.env` file in your project root (don't commit this, bro!):

```
# Needed for the AI to work its magic (the mana potion!)
OPENAI_API_KEY="your-openai-api-key-goes-here"

# Needed for email fun & webhook safety (the shield and sword!)
POSTMARK_API_KEY="your-postmark-server-token-here"
WEBHOOK_SECRET_TOKEN="your-super-secret-webhook-token-here" # Keeps the /webhook endpoint safe and sound!

# Optional: Who's sending these awesome emails? (Your superhero alias!)
DOMAIN="yourdomain.com" # Used if FROM_EMAIL isn't fully qualified (backup plan!)
FROM_EMAIL="prof@yourdomain.com" # Your official Prof. Postmark email addy!

```

### 3. Run the Gauntlet (Tests - Time to Prove Yourself!)

Make sure your `.env` is set up, especially that `OPENAI_API_KEY` if you're brave enough for live AI tests!

```
# Activate your virtual sidekick
source venv/bin/activate

# Unleash the test suite!
pytest src/tests/test_system.py -v

```

The `test_openai_script_generation` in `src/tests/test_system.py` actually calls the OpenAI API. If `OPENAI_API_KEY` is missing, it'll chicken out (i.e., be skipped).

## 🔧 Let's Get This Thing Running! (System Operation)

### Dev Mode (The Playground!)

```
# Activate your trusty virtual environment
source venv/bin/activate

# Fire up the dev server (from the project root, my dude)
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

```

Or, if you're feeling old school, run `app.py`:

```
python app.py

```

Your API docs are now live at `http://127.0.0.1:8000/docs` and `http://127.0.0.1:8000/redoc`. Go check 'em out!

### Production Mode (Showtime, Baby!)

```
# Activate the virtual environment (you know the drill)
source venv/bin/activate

# Set your environment variables (or let the .env file do the heavy lifting)
# export OPENAI_API_KEY="your-super-secret-api-key"
# export POSTMARK_API_KEY="your-amazing-postmark-key"
# ...and the rest of 'em!

# Launch the production server! To infinity and beyond!
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

```

### Docker Mode (Containerize Your Awesomeness!)

```
# Build that Docker image like a pro
docker build -t prof-postmark .

# Run your Docker container (make sure .env is there, or pass the vars, bro)
docker run -p 8000:8000 \
  --env-file .env \
  prof-postmark

```

Or, if you like to live on the edge and pass vars directly:

```
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key-for-docker" \
  -e POSTMARK_API_KEY="your-postmark-key-for-docker" \
  # ...you get the idea!
  prof-postmark

```

## 🌐 API Endpoints (The Secret Passages!)

Prof. Postmark opens these doors for you:

* **`GET /`**: Basic "Is this thing on?" health check.

  * **Responds With**: `{"message": "Prof. Postmark is running!", "status": "healthy", "version": "2.0.0"}` (Yep, it's alive!)

* **`GET /health`**: The full physical! Detailed health check.

  * **Responds With**: Service status, version, AI model deets, and a list of its cool features. (Healthy as a horse!)

* **`POST /webhook?token=<YOUR_WEBHOOK_SECRET_TOKEN>`**: The main event! This is where Postmark sends the email goodies.

  * **Security First!**: Needs a valid `token` in the query string that matches your `WEBHOOK_SECRET_TOKEN`. No token, no entry!

  * **What's in the Box? (Request Body)**: The JSON payload from Postmark's webhook.

  * **The Verdict (Response)**: JSON telling you if it was a success, a "meh, kinda success," or an "oops, error!"

## 💡 How It *Really* Works (The Gory Details, Kinda)

### 1. Email Touchdown & The Great Unpacking

* Emails fly in from Postmark as JSON packages to the `/webhook` door.

* `EmailParsingService` is like a master unboxer: grabs sender info, subject, body (giving HTML a good scrub with BeautifulSoup), and attachments (Base64 decoded, of course!).

### 2. The Validation Gauntlet

* `ValidationService` plays gatekeeper:

  * "PING" request? "PONG" back at ya! (It's a health thing).

  * Got attachments? (Unless it's a PING, pics or it didn't happen!).

  * Is the file a legit image (JPEG, PNG) and not elephant-sized (default 5MB)?

  * Fail any of these, and a "sorry, not sorry (but kinda sorry)" email goes out.

### 3. Image Extreme Makeover

* `ImageProcessingService` grabs the first good-looking attachment:

  * Opens it with Pillow (the image whisperer).

  * Figures out the best new size:

    * Square pics? Boom, 800x800px.

    * Not square? Longest side hits 1200px, the other side follows suit proportionally.

  * Resizes with `PILImage.Resampling.LANCZOS` (fancy!).

  * Converts to 'RGB' and saves as a high-quality JPEG into a byte stream.

  * This new, shiny `ProcessedImage` holds the precious image bytes and its new deets.

### 4. AI Brainstorm & The Annotation Spell

* `AIAnalysisService` gets to work:

  * Consults the ancient scrolls (`assets/instructions.txt`) – these tell the AI *exactly* how to score, what to draw, how to talk, and even how to write the Python annotation spell.

  * Temporarily saves the scaled image (it's camera shy).

  * Converts this temp image to Base64 (for secure AI travel).

  * Sends a care package to the OpenAI GPT-4o model, including:

    * The sacred instructions.

    * The user's plea (e.g., "Rate my pic, oh wise AI!").

    * The Base64 image.

  * The AI ponders, then sends back:

    * Wise words of feedback (Markdown style, with a scoring table).

    * A Python spell to draw annotations on the image.

  * Our service carefully extracts the feedback and the Python spell.

### 5. Casting the Annotation Spell (Handle With Care!)

* **SECURITY KLAXON! 🚨**: The Python spell (code) from the AI gets run using `exec()`. This is like handing a stranger the keys to your house, car, and secret cookie stash. **NOT SAFE for the wild internet (production) without a super-strong magic cage (sandbox)!**

* The `_execute_script` in `AIAnalysisService`:

  * Builds a temporary magic workshop.

  * Places the scaled image (`temp_image.jpg`) on the altar.

  * Prepares the ritual tools: `Image` (from Pillow) and an `ImageAnnotator` (our friendly art spirit) ready to work on `temp_image.jpg`.

  * Chants the AI-generated Python spell! This spell commands the `ImageAnnotator` to draw grids, circles, lines, and all sorts of helpful marks, just like the ancient scrolls (`assets/instructions.txt`) foretold.

  * The spell is supposed to create an enchanted artifact: `annotated_output.jpg`.

  * The bytes of this newly annotated image are captured.

### 6. The Grand Email Finale

* `EmailService` takes the stage:

  * Transforms the AI's Markdown feedback into dazzling HTML using `Mistune` (tables and all!).

  * Assembles the `EmailResponse` package.

  * If the annotation spell worked, the enchanted `annotated_feedback.jpg` is tucked in as an attachment.

  * Sends the whole shebang back to the user via Postmark, even replying to the original email thread! Smooth.

## 📊 Show Me the Money! (Example Output - from original README)

### Score Breakdown (The Report Card!)

| Category              | Max Points | Score  | Notes                                         |
| --------------------- | ---------- | ------ | --------------------------------------------- |
| Composition & Balance | 30         | 24     | Strong rule of thirds, minor distractions     |
| Focus & Depth         | 20         | 16     | Sharp subject, good depth of field            |
| Lighting & Contrast   | 20         | 18     | Excellent natural lighting                    |
| Color Harmony         | 15         | 12     | Good palette, could be more cohesive          |
| Visual Impact & Mood  | 15         | 13     | Engaging subject, strong storytelling         |
| **Total**             | **100**    | **83** | **Confident shot with professional quality!** |

### Visual Annotations (The Doodles of Wisdom!)

* Numbered points highlighting the good, the bad, and the artsy.

* Sketchy lines showing how your eye *should* travel.

* A handy rule of thirds grid overlay.

* Teacher comments that are actually helpful (and look cool!).

* A snazzy score presentation in the corner.

## 🧪 Testing, Testing, 1-2-3! (Development & QA)

* **System Boot Camp**: `src/tests/test_system.py` puts the whole thing through its paces – email parsing, image wrangling for all shapes and sizes, validation checks, and a full mock workflow (we don't *actually* send emails in tests, that'd be chaos!).

* **Live AI Daredevil Test**: `test_openai_script_generation` bravely calls the *actual* OpenAI API. Only for the bold with an `OPENAI_API_KEY`!

* **Mocking Magic**: We use a bit of hocus pocus (patching) in tests to pretend `email_service.send_feedback_response` is sending emails.

* **Image Formats**: Loves JPEGs and PNGs for input. Spits out JPEGs.

## 🔧 Tweaking the Machine (Configuration Details)

### The AI's Bible (`assets/instructions.txt`)

This file is the **BOSS**. It tells the AI everything:

* **Image Sizing 101**: How we prep the images.

* **`ImageAnnotator`'s Toolbox**: Which drawing spells are available (`add_rule_of_thirds_grid()`, `add_annotation_point()`, etc.).

* **Response Etiquette**: How to format feedback, the score table, the Python spell, and those crucial annotation explanations.

* **Code of Conduct (for AI-generated Python)**: No `import` statements allowed in its spells! We provide the magic tools.

* **The Sacred Python Template**: The exact structure its spell must follow.

* **What to Draw?**: Guidance on marking up the main subject, negative space, light, etc.

* **The Scoring Rubric**: How points are awarded, category by category.

* **Where to Draw? (Coordinate Rules)**: How to place annotations neatly, respecting borders (4% inset, like a fancy picture frame).

* **Scoreboard Placement**: Exactly where that final score should appear, depending on the pic's shape.

* **Feedback Tone Control**: How to sound encouraging or like a tough critic based on the score.

* **Explaining Yourself (for Annotations)**: How to describe *why* each mark was made.

### Pimp My Ride (Customization Options)

* **Scoring & Doodles**: Dive into `assets/instructions.txt` to change criteria, points, drawing styles, or the AI's whole personality.

* **Image Resizing**: Tinker with `src/services/image_processor.py` if you have different size preferences.

* **Validation Rules**: Edit `src/core/configuration.py` to change file size limits or allowed types.

* **Email Makeover**: Rewrite error messages and feedback structure in `src/services/email_service.py`.

* **Annotation Bling**: Change fonts, colors, and line styles in `src/services/image_annotation/annotator.py`.

## 📈 Performance Stats (As Per the Original Scroll)

* **Speed Run**: \~3-5 seconds per image (but the AI can be a diva and take its sweet time).

* **Accuracy**: Aims to be as good as a real-life photo sensei.

* **Scalability**: Async power means it can handle a crowd, though that `exec()` spell could be a chokepoint.

* **Cost Savvy**: Smart API use (the original README mentioned caching for dev, which is a pro gamer move!).

## 🎓 Making the World a Better Place, One Photo at a Time (Educational Impact)

This system isn't just code; it's a revolution in photo education, offering:

* **Fair & Square Feedback**: No more "my teacher likes blue" – just consistent, objective grading.

* **Deep Dive Analysis**: Goes way beyond what most auto-tools can do. It *gets* art, man.

* **Learn by Seeing**: Those hand-drawn-style annotations make complex ideas click.

* **Instant Gratification**: Speedy feedback means faster learning. Level up your photo skills, stat!

## ⚠️ **!! ULTRA MEGA DANGER ZONE WARNING !!** ⚠️

> **Listen Up, Bro!** This system runs Python code cooked up by OpenAI using `exec` (check `src/services/ai_analysis_service.py`). This is like juggling chainsaws while riding a unicycle on a tightrope. **NOT SAFE** for production or if you're sharing this code, unless you build a seriously strong magic cage (sandbox) around it. The AI is smart, but its code could theoretically be twisted into something gnarly. **Tread VERY carefully!** You've been warned!

## 📄 License & Legal Mumbo Jumbo

MIT License. Go nuts, use it for learning, use it for business, just have fun!

The cool font, `GochiHand-Regular.ttf`, is under the SIL Open Font License, Version 1.1. Basically:

* Use it, change it, share it – all good.

* Don't sell the font by itself, though. That's not cool.

* Bundle it with your software? Sure, just include the copyright and license. And don't use its special reserved names for your own font creations.

* If you make a new font based on it, that new font also has to be OFL. Share the love!

**Crafted with ❤️ for the love of photography and supercharged by some seriously futuristic AI. Peace out!** ✌️
