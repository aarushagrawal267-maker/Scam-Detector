# Outreach Plan: who to contact, when, and how

*Research done 2026-11-17. Every contact below says whether it was verified, where, and when.
Contact details change, so **re-check each one on the official site the week you send anything.***

> **Rules for every email**
> 1. The student sends it from **their own** email address, with a parent or teacher in CC.
> 2. Nothing is sent until the student, and a parent or teacher, have read and approved that one email.
> 3. Only claim what is true **on the day you send it**: real results, real users, real workshops.
> 4. One personal email per organisation. No mass mailing and no automatic follow-ups.
>    Follow up once, by hand, after about 3 weeks if there is no reply.

## When to contact anyone: project milestones

Outreach only makes sense once you have something real to show. These milestones are used in the table below.

| Milestone | What it means | Evidence you can show |
|---|---|---|
| **M1: Honest model results** | Baseline and advanced models trained; evaluated on a test set; results reported per language and per scam type, including the miss rate | `reports/` results table, GitHub repo |
| **M2: Working prototype + ethics approval** | Website and/or Telegram bot works end to end. A school ethics committee (IRB) has approved the user-testing plan | Demo link, approved consent forms (`docs/PILOT_PROTOCOL.md`) |
| **M3: Pilot results** | At least 5 older adults tested it under supervision; you changed the design because of what you saw | Anonymous usability findings, before/after screenshots |
| **M4: Community workshop delivered** | At least one real awareness workshop run with a partner organisation | Date, organisation, number of participants, anonymous feedback |

## Organisations

| Organisation | What they actually do (1 line) | Contact (verified? source, date) | Appropriate ask | Earliest sensible time | Response realism |
|---|---|---|---|---|---|
| **CERT-In: general** | India's national computer emergency response team (MeitY). Handles cyber-security incidents, alerts and advisories. | `info@cert-in.org.in`: **VERIFIED.** The official contact page lists it for *"vulnerability report, security alerts, or any other technical questions/feedback related to cyber security"* ([cert-in.org.in contact page](https://www.cert-in.org.in/s2cMainServlet?pageid=CONTACTUS), 2026-11-17). **Never use `incident@cert-in.org.in`**: it is only for real incident reports. | A short question: are there cyber-safety awareness resources or student programmes this project should align its advice with? | After **M3** | Low. It is a national incident-response body, and student projects are not its job. |
| **CERT-In: training / awareness** | CERT-In's Cyber Capacity Building group runs trainings and awareness sessions. | `training@cert-in.org.in`: **PARTLY VERIFIED.** It appears on a CERT-In-operated government site (Cyber Swachhta Kendra) as the address for *registering* for specific 2021 trainings ([csk.gov.in CSAM page](https://www.csk.gov.in/announcements/csam.html), 2026-11-17). It is not listed on CERT-In's current contact page, and it may be a registration inbox rather than a general one. | Information about awareness programmes (e.g. Cyber Security Awareness Month) that a student-led senior-citizen workshop could join | After **M4** | Low |
| **CERT-In: "collaboration@"** | n/a | `collaboration@cert-in.org.in`: **NOT VERIFIED.** It was not found on any official or third-party page. **Do not use.** | n/a | n/a | n/a |
| **I4C / CyberDost** (Ministry of Home Affairs) | I4C coordinates the national response to cybercrime. CyberDost is its public-awareness social-media channel. | `cyberdost@mha.gov.in`: **NOT VERIFIED.** It was found only on a third-party directory. `i4c.mha.gov.in` and `cybercrime.gov.in` refused connections from this environment on 2026-11-17. The 1930 helpline and cybercrime.gov.in **are** confirmed on an official DoT page (Sanchar Saathi, see below). | Feedback on whether the bot's "what to do" advice matches official reporting guidance (1930 / cybercrime.gov.in) | After **M3**, once the address is verified on i4c.mha.gov.in | Very low. A public tip on CyberDost's verified social accounts is more realistic than email. |
| **Sanchar Saathi: Chakshu** (Dept. of Telecommunications) | Citizens report *suspected* fraud calls, SMS and WhatsApp messages. There is a new beta option to report suspicious web links. | **VERIFIED.** The official page says Chakshu lets citizens report *"suspected fraud communications… through Call, SMS or WhatsApp"*, and: *"If you have already lost money, please report at cyber crime helpline 1930 or cybercrime.gov.in."* Reports are for communications from the last 30 days ([sancharsaathi.gov.in/sfc](https://sancharsaathi.gov.in/sfc/), 2026-11-17). | **This is not an outreach target.** It is a reporting channel the bot should *point users to*. This wording is already reflected in `scam_detector/messages.py`. | Now (as advice inside the app) | n/a |
| **DSCI**: Data Security Council of India (set up by NASSCOM) | Industry body for data protection and cyber security. Runs public-awareness programmes. | `info@dsci.in`: **VERIFIED** as the address for *"general queries"* ([dsci.in/content/contact-us](https://www.dsci.in/content/contact-us), 2026-11-17). | Feedback on how usable the tool is for senior citizens. Ask whether a student workshop could complement Meri Digital Suraksha sessions. | After **M3** | Medium-low. The best fit of all the national bodies (see below). |
| **DSCI: Meri Digital Suraksha** | *"Joint cyber security awareness initiative by DSCI and Optiv for senior citizens."* Runs in-person community sessions and virtual webinars, and offers an awareness guide (English, Hindi, Kannada) and "The Online Fraud Files" infographics. **VERIFIED** ([dsci.in/content/meri-digital-suraksha](https://www.dsci.in/content/meri-digital-suraksha), 2026-11-17). | No programme-specific email on the page. Use `info@dsci.in` and name the programme in the subject line. | Same as above. Also: **use their Hindi guide in your own workshops** (with credit), so you don't contradict an established programme. | After **M3** | Medium-low |
| **National Consumer Helpline** (Dept. of Consumer Affairs) | **A complaint (grievance) channel.** The page heading reads *"Your Grievances, Our Redressal"*. It registers consumer complaints and forwards them to companies. Contact: toll-free 1915, WhatsApp/SMS +91 8800001915. No email is listed ([consumerhelpline.gov.in](https://consumerhelpline.gov.in/), 2026-11-17). | n/a | **Do not send project material here.** It is for consumer complaints, not research or partnerships. | **Never** | n/a |
| **RBI**: Reserve Bank of India | India's central bank. Its Consumer Education and Protection Department (CEPD) handles complaints about banks (via CPGRAMS) and consumer education. | **No research or partnership address exists.** The official contact page offers a web form and `helpdoc@rbi.org.in`, which is shown as *"Contact us on…"* in the footer and for visually challenged users ([rbi.org.in contact page](https://www.rbi.org.in/Scripts/contactus.aspx), 2026-11-17). Do not invent one. | **No direct outreach.** RBI does not evaluate or endorse software. Instead, **use and cite RBI's own BE(A)WARE booklet** (7 Mar 2022) on fraudsters' methods in your workshop material ([press release](https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=53372), [booklet PDF](https://rbidocs.rbi.org.in/rdocs/content/pdfs/BEAWARE07032022.pdf)). | Never directly. Approach banks' local financial-literacy work after **M4**. | n/a |
| **RBI Kehta Hai** | RBI's public-awareness campaign | **NOT VERIFIED.** The site (rbikehtahai.rbi.org.in) showed only a CAPTCHA page on 2026-11-17. | Use as reference material only, after checking it yourself. | n/a | n/a |
| **Local bank branch / financial-literacy centre** | Many banks run local financial-literacy camps | Find in person at your nearest branch | Ask whether you can co-run a 30-minute scam-awareness session for seniors at a camp | After **M3–M4** | **Medium-high.** Local and personal contact works far better than national email. |
| **Local senior-citizen organisations** (senior citizens' forums, residents' welfare associations, temples/gurdwaras/churches, day-care centres for older people) | Places where your actual users already gather | Find in person, through family and your school | Supervised usability test (M2: needs ethics approval first), then a workshop | After **M2** | **High.** This is where real impact and real data come from. |

### What this means

- **The national bodies are long shots.** CERT-In, I4C and RBI are not set up to give feedback on student projects. A polite email *after* you have pilot results is fine, but don't build your plan around a reply.
- **DSCI's Meri Digital Suraksha is the closest match** in purpose: senior citizens, Hindi materials, community sessions. Read their guide before contacting them, and frame your project as *complementing* their work.
- **Local organisations are where the project succeeds or fails.** Put most of your outreach effort there.

## Academic researchers (verified only)

Only researchers whose work in a relevant area appears on an **official institutional page** are listed. Fewer names is safer than guessed ones.

| Name | Institution / Department | Official page (checked 2026-11-17) | Evidence of relevant research | Email (only if printed on the official page) | Why contact them |
|---|---|---|---|---|---|
| **Mainack Mondal** | IIT Kharagpur, Dept. of Computer Science & Engineering (Assistant Professor) | [cse.iitkgp.ac.in/~mainack](https://cse.iitkgp.ac.in/~mainack/) | The page says: *"I design, implement and analyze usable private and secure online systems."* He teaches *Usable Security and Privacy (CS60081)* ([course page](https://cse.iitkgp.ac.in/~mainack/courses/2024-autumn/usesec)). | Shown only as an image on the page. Copy it by hand from the page; **do not guess it**. | Usable security: whether warnings and explanations actually help non-expert users. This matches your "does explanation improve elderly users' understanding" question. |
| **Ponnurangam Kumaraguru ("PK")** | IIIT Hyderabad, Computer Science (Professor). The same page also says he is currently a Visiting Scientist at ANRF, Govt. of India. | [precog.iiit.ac.in/bio](https://precog.iiit.ac.in/bio/) | Research in *"Privacy and Security in Online Social Media, Cyber Security, Social Computing"*. His CMU PhD was in *"anti-phishing research"*. His current focus is *"responsible & safe AI, and applied machine learning & NLP."* | `pk.guru@iiit.ac.in` (printed on the page) | Phishing and cyber-security work in India. Highly cited and very busy, so keep the ask very small. |
| **Mayank Singh** | IIT Gandhinagar, Dept. of Computer Science & Engineering. He leads the LINGO Research Group. An IITGN-hosted page says *"Assistant Professor"*; his personal site says Associate Professor, so check his title. | [IITGN event page (sites.google.com/iitgn.ac.in)](https://sites.google.com/iitgn.ac.in/event/home). The official CSE faculty directory returned 403 from this environment. | Research areas listed include *"Indic Large Language Models (LLMs)… and Code-Mixed NLP."* | None printed on that page (only a workshop address). Find it on the official IITGN directory yourself. | Hindi–English code-mixed NLP, the core technical challenge of your Hinglish messages |

**Not listed because they couldn't be verified:**
- **HCI for older adults:** no Indian researcher's *official* profile page that names older adults as a research focus was found.
  - Pushpendra Singh (IIIT-Delhi, HCI for low-resource settings) has a related 2025 arXiv paper on older adults. His official page ([iiitd.edu.in/~pushpendra](https://www.iiitd.edu.in/~pushpendra/)) does not mention older adults, so he is not listed as an older-adults researcher.
  - Look at your local university's psychology, social-work or design department for this angle.

**How to write to a professor:**
- Read 1–2 of their recent papers first.
- Ask **one** specific question that takes 10 minutes to answer, e.g. "Is a character n-gram baseline a fair comparison for code-mixed text?"
- Never ask for co-authorship, endorsement or a letter of recommendation in a first email.

## Email templates (not drafts: fill in only what is true)

`[square brackets]` = fill in. Delete any sentence that isn't true yet. Each template is under 200 words.

> **Before sending any of these:** your own email address · parent or teacher in CC · approved by you **and** that adult · contact address re-checked on the official site that week.

### 1. Academic researcher

**Subject:** High-school research question: detecting Hinglish scam messages

Dear Professor [Last name],

I am [Name], a Class [X] student at [School], [City]. I read your paper "[title]" and found [one specific point] useful for my project.

I am building a tool that flags scam SMS/WhatsApp messages in English, Hindi and Hinglish for older adults. So far I have [e.g., trained a TF-IDF + logistic regression baseline and a fine-tuned MuRIL model, evaluated on N messages]. On real messages it misses [X]% of scams, with the most misses in [category/language]. My code and results are public: [GitHub link].

My one question: [specific question, e.g., "For code-mixed text, would you expect character n-grams or a multilingual transformer to generalise better to new scam wording, and how would you test that fairly?"]

Even a two-line answer would help me a great deal. Thank you for your time.

Sincerely,
[Name] · [School] · cc: [Teacher/Parent name]

### 2. CERT-In (training / awareness)

**Subject:** Student digital-safety workshop for senior citizens: request for guidance

Dear CERT-In Team,

I am [Name], a Class [X] student at [School], [City]. With my teacher [Name], I have run [N] supervised scam-awareness sessions for senior citizens at [organisation]. The sessions use a small classifier I built that explains why a message may be a scam and points people to 1930, cybercrime.gov.in and Chakshu. It is a student project, not a certified security product, and its results can be wrong.

Could you tell me whether CERT-In has awareness material or a programme (e.g., Cyber Security Awareness Month) that a school-led senior-citizen session could follow or align with? I want to make sure my advice matches official guidance.

Thank you,
[Name] · [School] · cc: [Teacher name]

### 3. DSCI (Meri Digital Suraksha)

**Subject:** Meri Digital Suraksha: student project for senior citizens, request for feedback

Dear DSCI Team,

I am [Name], a Class [X] student at [School], [City]. I read about Meri Digital Suraksha and your awareness guide for senior citizens.

I have built a simple tool that tells older adults, in Hindi or English, whether a forwarded message looks like a scam and what to do next. In a supervised test with [N] older adults (with ethics approval and consent), [real finding, e.g., "4 of 5 could check a message on their own in under a minute, but several misread the yellow 'suspicious' result, so I redesigned it"].

Would someone from the programme be willing to give brief feedback on whether the advice and design suit senior citizens? I would also like to know whether a student-led session could complement your community sessions.

Thank you,
[Name] · [School] · [demo link] · cc: [Teacher name]

### 4. Local senior-citizen organisation

**Subject:** Free 30-minute session on spotting phone scams: request to visit

Dear [Name / Secretary],

I am [Name], a Class [X] student at [School], [City]. Many older people near us receive fake bank, KYC and "digital arrest" messages. With my teacher [Name], I have prepared a free 30-minute session in [Hindi/English] on how to spot these scams. It includes the official helplines (1930, cybercrime.gov.in), a printed one-page guide, and an optional chance to try a simple message-checking tool I built.

We never ask anyone for bank details, OTPs or personal messages. Any testing of the tool happens only with written consent and my school's approval.

Could we find a convenient date in [month]? I am happy to meet first to explain.

Thank you,
[Name] · [Phone of supervising teacher] · cc: [Teacher name]

## Outreach tracker

Copy this table into `docs/impact_log` or a spreadsheet. Only fill in "Response" when a reply actually arrives.

| Organisation | Recipient | Department | Verified email | Source + date checked | Date sent | Purpose | Subject | Status | Response | Response date | Next action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | not sent | | | |
