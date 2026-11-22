"""SAMPLE (mock) majors and courses for every Grinnell major except Computer
Science and Mathematics. Nothing here is catalog data: major names are real,
everything else (course numbers, titles, prerequisites, offerings, routes and
descriptions) is invented for the demo. ``build_sample_data.py`` turns this
into ``data/sample_courses.json`` and ``data/sample_programs.json``.

Course line:   ID[=CROSS-LIST][(credits)] | Title | F, S or FS | prerequisite | one sentence
Prerequisite:  ``-`` (none), ``A & B`` (all) or ``A or B`` (any).
Group:         (kind, id, label, count, [options]); kind is ``all``, ``choose``,
               ``also-all`` or ``also-choose`` (cognates: required, no major credit).
Route:         eight terms separated by ``/``; course ids and group ids, ``-`` for none.
"""

MAJORS = [
    # ------------------------------------------------------------ Humanities
    dict(id="ARH", name="Art History", division="Humanities", style="hum", courses="""
ARH-103 | Introduction to Art History | FS | - | Surveys painting, sculpture and architecture from antiquity to the present, with attention to how images carry meaning.
ARH-211 | Art of the Ancient Mediterranean | F | ARH-103 | Examines the art and architecture of Egypt, Greece and Rome in their political and religious settings.
ARH-214 | Medieval and Renaissance Art | S | ARH-103 | Traces European art from illuminated manuscripts to the workshops of fifteenth-century Italy and Flanders.
ARH-221 | European Art from Baroque to Impressionism | F | ARH-103 | Follows three centuries of European painting and sculpture, from court patronage to the independent exhibition.
ARH-231 | Modern and Contemporary Art | S | ARH-103 | Considers the major movements of the twentieth and twenty-first centuries and the debates that shaped them.
ARH-233 | Arts of East Asia | F | ARH-103 | Introduces the painting, ceramics and built environments of China, Korea and Japan.
ARH-250 | Methods of Art History | FS | ARH-103 | Introduces the questions art historians ask, from formal analysis and iconography to social history and critical theory.
ARH-320 | Seminar: Art and Empire | F | ARH-250 | Investigates how empires have collected, displayed and produced art, and how artists have answered back.
ARH-325 | Seminar: Museums and Collecting | S | ARH-250 | Studies the museum as an institution: how collections are formed, interpreted and contested.
ARH-360 | Seminar: Image and Devotion | F | ARH-250 | Explores sacred images across several traditions and the practices of looking, touching and veneration around them.
ARH-365 | Seminar: Photography and Modernity | S | ARH-250 | Considers photography from its invention to the digital image as both an art form and a social technology.
ARH-495 | Senior Seminar in Art History | FS | ARH-250 | Majors design and complete an independent research project and present it to the department.
""", groups=[
        ("all", "arh-foundations", "Foundations", None, ["ARH-103", "ARH-250"]),
        ("choose", "arh-surveys", "Period and area survey", 3, ["ARH-211", "ARH-214", "ARH-221", "ARH-231", "ARH-233", "CLS-248"]),
        ("choose", "arh-seminars", "Art History seminar", 2, ["ARH-320", "ARH-325", "ARH-360", "ARH-365"]),
        ("all", "arh-capstone", "Senior seminar", None, ["ARH-495"]),
        ("also-all", "arh-studio", "Also required: studio course", None, ["ART-111"]),
    ], route="ARH-103 / arh-surveys / ARH-250 ART-111 / arh-surveys / arh-surveys / arh-seminars / ARH-495 arh-seminars / -"),

    dict(id="CHI", name="Chinese", division="Humanities", style="lang", courses="""
CHI-101 | Beginning Chinese I | F | - | Introduces spoken Mandarin and the writing system through daily practice in listening, speaking, reading and character writing.
CHI-102 | Beginning Chinese II | S | CHI-101 | Continues the first-year sequence, extending vocabulary and grammar for everyday conversation and short written texts.
CHI-221 | Intermediate Chinese I | F | CHI-102 | Builds fluency through longer dialogues, short essays and a growing stock of characters.
CHI-222 | Intermediate Chinese II | S | CHI-221 | Completes the intermediate sequence with authentic readings, presentations and regular composition.
CHI-230 | Chinese Cinema in Translation | S | - | Surveys films from mainland China, Hong Kong and Taiwan and the histories they reflect; taught in English.
CHI-277 | Modern China through Literature | F | - | Reads fiction and essays from the late Qing to the present as a window on social change; taught in English.
CHI-288 | Classical Chinese Thought in Translation | S | - | Introduces Confucian, Daoist and Legalist texts and their long afterlives; taught in English.
CHI-331 | Advanced Chinese: Media and Society | F | CHI-222 | Uses news, television and online writing to develop advanced reading and discussion skills.
CHI-332 | Advanced Chinese: Short Fiction | S | CHI-222 | Reads modern short stories in the original, with attention to style, register and translation.
CHI-341 | Readings in Classical Chinese | F | CHI-222 | Introduces the grammar of the classical language through short passages of philosophy, history and poetry.
CHI-461 | Seminar: Translation Workshop | S | CHI-222 | Students translate literary and documentary texts and study the choices translators make.
CHI-495 | Senior Project in Chinese | FS | CHI-222 | Majors carry out a sustained research or translation project using Chinese-language sources.
""", groups=[
        ("all", "chi-language", "Language sequence", None, ["CHI-101", "CHI-102", "CHI-221", "CHI-222"]),
        ("choose", "chi-culture", "Literature and culture in translation", 1, ["CHI-230", "CHI-277", "CHI-288"]),
        ("choose", "chi-advanced", "Advanced Chinese", 3, ["CHI-331", "CHI-332", "CHI-341", "CHI-461"]),
        ("all", "chi-capstone", "Senior project", None, ["CHI-495"]),
    ], route="CHI-101 / CHI-102 / CHI-221 chi-culture / CHI-222 / chi-advanced / chi-advanced / chi-advanced / CHI-495"),

    dict(id="CLS", name="Classics", division="Humanities", style="hum", courses="""
CLS-101 | Classical Mythology | FS | - | Reads the major myths of Greece and Rome in ancient sources and follows their retellings in later art and literature.
CLS-242 | The Greek World from Homer to Alexander | F | - | Surveys Greek history and culture from the Bronze Age to the conquests of Alexander.
CLS-244 | Rome: Republic and Empire | S | - | Follows Rome from a city-state on the Tiber to a Mediterranean empire, using literary and material evidence.
CLS-248=ARH-248 | Greek Archaeology and Art | S | - | Studies the material culture of the Greek world from the Bronze Age to the Hellenistic kingdoms through excavated sites and objects.
CLS-250 | Ancient Drama | F | CLS-101 | Reads Greek tragedy and comedy with attention to staging, festival context and modern performance.
CLS-255 | Gender in Antiquity | S | - | Examines how Greek and Roman societies imagined gender, family and the body.
LAT-103 | Elementary Latin | F | - | Introduces Latin grammar and vocabulary with the aim of reading continuous prose by the end of the term.
LAT-222 | Intermediate Latin: Prose and Poetry | S | LAT-103 | Reads selections from Cicero, Catullus and Vergil while reviewing grammar.
GRE-101 | Elementary Greek | F | - | Introduces the forms and syntax of classical Attic Greek through graded readings.
GRE-222 | Intermediate Greek: Homer | S | GRE-101 | Reads selections from the Iliad or the Odyssey and introduces epic dialect and meter.
CLS-310 | Seminar: Epic and Its Afterlives | F | CLS-242 | Studies ancient epic and its reception from late antiquity to contemporary fiction.
CLS-325 | Seminar: Law and Society in Rome | S | CLS-244 | Uses legal texts, speeches and inscriptions to study how Romans argued about property, family and status.
CLS-340 | Seminar: Athenian Democracy and Its Critics | S | CLS-242 | Examines the institutions of democratic Athens alongside the thinkers who attacked and defended them.
CLS-495 | Senior Seminar in Classics | FS | CLS-242 & CLS-244 | Majors pursue an independent research project on a shared theme and present it publicly.
""", groups=[
        ("all", "cls-foundations", "Foundations", None, ["CLS-101", "CLS-242", "CLS-244"]),
        ("choose", "cls-language", "Greek or Latin", 2, ["LAT-103", "LAT-222", "GRE-101", "GRE-222"]),
        ("choose", "cls-topics", "Topics in classical culture", 1, ["CLS-248", "CLS-250", "CLS-255"]),
        ("choose", "cls-seminars", "Classics seminar", 2, ["CLS-310", "CLS-325", "CLS-340"]),
        ("all", "cls-capstone", "Senior seminar", None, ["CLS-495"]),
    ], route="CLS-101 cls-language / cls-language / CLS-242 / CLS-244 cls-topics / cls-seminars / cls-seminars / CLS-495 / -"),

    dict(id="ENG", name="English", division="Humanities", style="hum", courses="""
ENG-120 | Literary Analysis | FS | - | Introduces the close reading of poetry, fiction and drama and the craft of writing about literature.
ENG-121 | Introduction to Shakespeare | FS | - | Reads a selection of comedies, histories and tragedies with attention to language and performance.
ENG-205 | The Craft of Fiction | F | ENG-120 | A workshop in short fiction: students read published stories as writers and draft and revise their own.
ENG-206 | The Craft of Poetry | S | ENG-120 | A workshop in poetry that pairs the study of form and line with weekly writing.
ENG-223 | The Tradition of English Literature I | F | ENG-120 | Surveys literature in English from the medieval period through the seventeenth century.
ENG-224 | The Tradition of English Literature II | S | ENG-120 | Surveys British literature from the Restoration to the early twentieth century.
ENG-227=AMS-227 | American Literary Traditions | F | ENG-120 | Reads American writing from the colonial period to the present and asks what has counted as an American tradition.
ENG-229 | Global Anglophone Literature | S | ENG-120 | Studies fiction and poetry in English from Africa, South Asia and the Caribbean.
ENG-273 | Literature and the Environment | F | ENG-120 | Considers how writers have imagined land, climate and nonhuman life, from pastoral to climate fiction.
ENG-290 | Introduction to Literary Theory | FS | ENG-120 | Introduces the major schools of literary and cultural theory and puts them to work on shared texts.
ENG-325 | Seminar: Studies in the Novel | F | ENG-290 | Follows the novel as a form across two centuries, with one long novel read slowly at the center of the term.
ENG-332 | Seminar: Poetry and Poetics | S | ENG-290 | Studies a small group of poets in depth alongside their essays, letters and critics.
ENG-349 | Seminar: Race and American Narrative | F | ENG-290 | Examines how American fiction and memoir have constructed and contested ideas of race.
ENG-385 | Writing Seminar: Fiction | S | ENG-205 | An advanced workshop in which each student completes a portfolio of revised stories.
ENG-495 | Senior Seminar in English | FS | ENG-290 | Majors write a substantial critical or creative project and workshop it with their peers.
""", groups=[
        ("all", "eng-foundations", "Foundations", None, ["ENG-120", "ENG-290"]),
        ("choose", "eng-early", "Early literature", 1, ["ENG-121", "ENG-223"]),
        ("choose", "eng-electives", "200-level English elective", 3, ["ENG-121", "ENG-205", "ENG-206", "ENG-223", "ENG-224", "ENG-227", "ENG-229", "ENG-273"]),
        ("choose", "eng-seminars", "English seminar", 2, ["ENG-325", "ENG-332", "ENG-349", "ENG-385"]),
        ("all", "eng-capstone", "Senior seminar", None, ["ENG-495"]),
    ], route="ENG-120 / eng-early / ENG-290 eng-electives / eng-electives / eng-electives eng-seminars / eng-seminars / - / ENG-495"),

    dict(id="FRN", name="French and Francophone Studies", division="Humanities", style="lang", courses="""
FRN-101 | Introductory French I | F | - | Develops basic speaking, listening, reading and writing skills in French through daily practice.
FRN-102 | Introductory French II | S | FRN-101 | Continues the introductory sequence and introduces short texts from across the French-speaking world.
FRN-221 | Intermediate French I | F | FRN-102 | Reviews and extends grammar while building confidence in conversation and composition.
FRN-222 | Intermediate French II | S | FRN-221 | Prepares students for advanced work through film, short fiction and sustained writing in French.
FRN-235 | Paris and the Francophone City | S | - | Studies Paris, Dakar and Montreal as sites of migration, protest and artistic invention; taught in English.
FRN-241 | Francophone Cinema | F | - | Surveys film from France, West Africa and Quebec; taught in English.
FRN-303 | French Civilization: Revolution to Republic | F | FRN-222 | Follows French political and cultural history from 1789 to the present through documents, images and film.
FRN-305 | Contemporary Francophone Cultures | S | FRN-222 | Examines language, identity and politics in the French-speaking Caribbean, Maghreb and sub-Saharan Africa.
FRN-312 | Introduction to French Literature | F | FRN-222 | Introduces literary analysis in French through poetry, theater and prose from several centuries.
FRN-328 | Seminar: Caribbean and African Voices in French | S | FRN-222 | Reads novels and essays by Francophone writers on colonialism, memory and language.
FRN-350 | Advanced Composition and Translation | S | FRN-222 | Refines written French through stylistic exercises and translation in both directions.
FRN-495 | Senior Seminar in French | FS | FRN-222 | Majors complete and present a research project written in French.
""", groups=[
        ("all", "frn-language", "Language sequence", None, ["FRN-101", "FRN-102", "FRN-221", "FRN-222"]),
        ("choose", "frn-culture", "Francophone culture in translation", 1, ["FRN-235", "FRN-241"]),
        ("choose", "frn-advanced", "Advanced French", 3, ["FRN-303", "FRN-305", "FRN-312", "FRN-328", "FRN-350"]),
        ("all", "frn-capstone", "Senior seminar", None, ["FRN-495"]),
    ], route="FRN-101 / FRN-102 / FRN-221 frn-culture / FRN-222 / frn-advanced / frn-advanced / frn-advanced / FRN-495"),

    dict(id="GRM", name="German Studies", division="Humanities", style="lang", courses="""
GRM-101 | Introductory German I | F | - | Introduces German for everyday communication, with equal weight on speaking, listening, reading and writing.
GRM-102 | Introductory German II | S | GRM-101 | Continues the introductory sequence with short readings on contemporary life in German-speaking countries.
GRM-221 | Intermediate German I | F | GRM-102 | Strengthens grammar and vocabulary through film, journalism and discussion.
GRM-222 | Intermediate German II | S | GRM-221 | Moves toward advanced work with longer texts and regular essays in German.
GRM-240 | German Film | S | - | Surveys German cinema from Expressionism to the present; taught in English.
GRM-245 | Berlin: Capital of the Twentieth Century | F | - | Uses one city to study empire, dictatorship, division and reunification; taught in English.
GRM-302 | Contemporary Issues in German | F | GRM-222 | Builds advanced speaking and writing skills around current debates in the German-language press.
GRM-310 | Readings in German Literature | S | GRM-222 | Introduces literary analysis in German through short prose, drama and poetry.
GRM-315 | Migration and Identity in German-Speaking Europe | F | GRM-222 | Studies literature, film and policy debates on migration and belonging.
GRM-372 | Seminar: Weimar Culture | S | GRM-222 | Examines the art, film and political writing of the Weimar Republic.
GRM-495 | Senior Seminar in German Studies | FS | GRM-222 | Majors research and write a capstone essay in German and present it to the department.
""", groups=[
        ("all", "grm-language", "Language sequence", None, ["GRM-101", "GRM-102", "GRM-221", "GRM-222"]),
        ("choose", "grm-culture", "German culture in translation", 1, ["GRM-240", "GRM-245"]),
        ("choose", "grm-advanced", "Advanced German", 3, ["GRM-302", "GRM-310", "GRM-315", "GRM-372"]),
        ("all", "grm-capstone", "Senior seminar", None, ["GRM-495"]),
    ], route="GRM-101 / GRM-102 / GRM-221 grm-culture / GRM-222 / grm-advanced / grm-advanced / grm-advanced / GRM-495"),

    dict(id="MUS", name="Music", division="Humanities", style="perf", courses="""
MUS-101 | Fundamentals of Music | FS | - | Teaches notation, scales, intervals and basic keyboard skills to students with little or no formal training.
MUS-120(1) | Performance Ensemble | FS | - | Rehearses and performs in one of the department's ensembles; may be repeated for credit.
MUS-112 | Harmony and Musicianship I | F | - | Introduces tonal harmony, voice leading and ear training through writing, singing and keyboard work.
MUS-116 | Music, Culture, Context | FS | - | Asks how music works in social life, drawing on examples from many traditions and periods.
MUS-213 | Harmony and Musicianship II | S | MUS-112 | Continues the study of harmony into chromaticism and larger forms, with continued aural training.
MUS-215 | Introduction to Composition | F | MUS-112 | Students write short pieces for small ensembles and hear them read by performers.
MUS-219 | Electronic Music | S | MUS-112 | Covers recording, synthesis and sequencing in the studio, alongside the history of electronic sound.
MUS-261 | Western Music to 1750 | F | MUS-116 | Surveys European art music from chant to the late Baroque in its cultural setting.
MUS-262 | Western Music since 1750 | S | MUS-116 | Follows art music from the Classical style through the twentieth century and beyond.
MUS-268 | Regional Studies in World Music | F | MUS-116 | Studies the music of one region in depth, combining listening, reading and hands-on performance.
MUS-270 | Jazz Traditions | S | - | Traces jazz from its roots to the present through recordings, biography and social history.
MUS-322 | Seminar: Advanced Analysis | F | MUS-213 | Applies several analytical methods to works from the eighteenth century to the present.
MUS-325 | Seminar: Music and Politics | S | MUS-261 | Examines censorship, patronage, protest and propaganda in music across several periods.
MUS-360 | Seminar: Opera and Society | S | MUS-262 | Studies a handful of operas closely as drama, music and social event.
MUS-495 | Senior Project in Music | FS | MUS-213 | Majors prepare a recital, composition portfolio or research paper with a faculty mentor.
""", groups=[
        ("all", "mus-theory", "Theory and musicianship", None, ["MUS-112", "MUS-213"]),
        ("all", "mus-history", "History and culture", None, ["MUS-116", "MUS-261", "MUS-262"]),
        ("choose", "mus-electives", "Music elective", 1, ["MUS-215", "MUS-219", "MUS-268", "MUS-270"]),
        ("choose", "mus-seminars", "Music seminar", 2, ["MUS-322", "MUS-325", "MUS-360"]),
        ("all", "mus-capstone", "Senior project", None, ["MUS-495"]),
    ], route="MUS-112 MUS-116 / MUS-213 / MUS-261 / MUS-262 / mus-electives mus-seminars / mus-seminars / - / MUS-495"),

    dict(id="PHI", name="Philosophy", division="Humanities", style="hum", courses="""
PHI-101 | Introduction to Philosophy | FS | - | Introduces central questions about knowledge, reality, freedom and the good life through classic and recent texts.
PHI-102 | Symbolic Logic | FS | - | Teaches the formal languages of sentential and predicate logic and their use in evaluating arguments.
PHI-231 | Ancient Greek Philosophy | F | PHI-101 | Reads the Presocratics, Plato and Aristotle on nature, knowledge and virtue.
PHI-233 | Early Modern Philosophy | S | PHI-101 | Follows debates about mind, matter and knowledge from Descartes to Hume.
PHI-242 | Ethical Theory | F | PHI-101 | Compares consequentialist, deontological and virtue-based accounts of right action.
PHI-253 | Philosophy of Mind | S | PHI-101 | Examines consciousness, mental representation and the relation between mind and brain.
PHI-256 | Philosophy of Science | F | PHI-101 | Asks what distinguishes scientific explanation, how theories are confirmed and how they change.
PHI-263=POL-263 | Political Theory | S | PHI-101 or POL-101 | Reads major works of political thought on justice, liberty, authority and equality.
PHI-264 | Philosophy of Race and Gender | F | PHI-101 | Examines what race and gender are, and what follows for questions of justice and identity.
PHI-336 | Seminar: Kant | F | PHI-233 | A close reading of the Critique of Pure Reason and its reception.
PHI-352 | Seminar: Metaethics | S | PHI-242 | Investigates whether moral claims can be true, known or motivating.
PHI-371 | Seminar: Minds and Machines | F | PHI-253 | Considers whether machines can think, understand or be held responsible.
PHI-393 | Seminar: Contemporary Epistemology | S | PHI-233 | Studies recent work on knowledge, justification, testimony and disagreement.
PHI-495 | Senior Seminar in Philosophy | FS | PHI-231 & PHI-233 | Majors write and defend a substantial essay on a topic of their choosing.
""", groups=[
        ("all", "phi-foundations", "Foundations", None, ["PHI-101", "PHI-102"]),
        ("all", "phi-history", "History of philosophy", None, ["PHI-231", "PHI-233"]),
        ("choose", "phi-topics", "Value, mind and knowledge", 2, ["PHI-242", "PHI-253", "PHI-256", "PHI-263", "PHI-264"]),
        ("choose", "phi-seminars", "Philosophy seminar", 2, ["PHI-336", "PHI-352", "PHI-371", "PHI-393"]),
        ("all", "phi-capstone", "Senior seminar", None, ["PHI-495"]),
    ], route="PHI-101 / PHI-102 / PHI-231 / PHI-233 phi-topics / phi-topics phi-seminars / phi-seminars / - / PHI-495"),

    dict(id="REL", name="Religious Studies", division="Humanities", style="hum", courses="""
REL-104 | Introduction to the Study of Religion | FS | - | Asks what religion is and how scholars study it, using case studies from several traditions.
REL-211 | The Hebrew Bible | F | - | Reads the Hebrew Bible as literature and as a record of ancient Israel, with attention to modern scholarship.
REL-214 | Christian Traditions | S | - | Surveys the history, texts and practices of Christianity from its origins to the present.
REL-216 | Islam: Texts and Communities | F | - | Introduces the Qur'an, law, mysticism and the diversity of Muslim life across regions.
REL-220 | Buddhist Traditions | S | - | Follows Buddhist thought and practice from early India across Asia and into the modern West.
REL-225 | Religions of South Asia | F | - | Studies Hindu, Jain, Sikh and Muslim traditions of the subcontinent and their interactions.
REL-241 | Religion in the United States | S | REL-104 | Examines religious pluralism, revival and conflict in American public life.
REL-268 | Religion, Ethics and Environment | F | REL-104 | Considers how religious communities understand and respond to environmental change.
REL-311 | Theory and Method in the Study of Religion | FS | REL-104 | Reads the theorists who shaped the field and tests their approaches against particular cases.
REL-326 | Seminar: Mysticism | S | REL-311 | Compares accounts of mystical experience and asks how they can be interpreted.
REL-355 | Seminar: Religion and Law | F | REL-311 | Studies how courts and states define religion, and how religious traditions understand law.
REL-362 | Seminar: Ritual and Performance | S | REL-311 | Uses ethnography and theory to study ritual as embodied action.
REL-495 | Senior Seminar in Religious Studies | FS | REL-311 | Majors develop an independent research project and present it at a department colloquium.
""", groups=[
        ("all", "rel-foundations", "Foundations", None, ["REL-104", "REL-311"]),
        ("choose", "rel-traditions", "Religious tradition", 3, ["REL-211", "REL-214", "REL-216", "REL-220", "REL-225"]),
        ("choose", "rel-themes", "Religion and society", 1, ["REL-241", "REL-268"]),
        ("choose", "rel-seminars", "Religious Studies seminar", 2, ["REL-326", "REL-355", "REL-362"]),
        ("all", "rel-capstone", "Senior seminar", None, ["REL-495"]),
    ], route="REL-104 / rel-traditions / rel-traditions / rel-traditions rel-themes / REL-311 / rel-seminars / REL-495 rel-seminars / -"),

    dict(id="RUS", name="Russian", division="Humanities", style="lang", courses="""
RUS-101 | Beginning Russian I | F | - | Introduces the Cyrillic alphabet, basic grammar and everyday conversation.
RUS-102 | Beginning Russian II | S | RUS-101 | Continues the first-year sequence, completing the case system and introducing short readings.
RUS-221 | Intermediate Russian I | F | RUS-102 | Reviews grammar and expands vocabulary through film clips, songs and short stories.
RUS-222 | Intermediate Russian II | S | RUS-221 | Develops reading and discussion skills with unadapted texts and regular writing.
RUS-247 | The Russian Short Story | F | - | Reads short fiction from Pushkin to the present; taught in English.
RUS-251 | Russian and Soviet Film | S | - | Surveys cinema from the montage school to contemporary directors; taught in English.
RUS-313 | Advanced Russian: Reading the Press | F | RUS-222 | Uses newspapers, broadcasts and online media to build advanced comprehension.
RUS-331 | Advanced Russian: Conversation and Composition | S | RUS-222 | Focuses on spoken fluency and stylistically varied writing.
RUS-345 | Readings in Russian Poetry | F | RUS-222 | Introduces Russian verse from the Golden Age to the twentieth century in the original.
RUS-389 | Seminar: Tolstoy and Dostoevsky | S | RUS-222 | Reads major works by the two novelists, partly in Russian, with attention to their philosophical stakes.
RUS-495 | Senior Seminar in Russian | FS | RUS-222 | Majors complete a research project that draws on Russian-language sources.
""", groups=[
        ("all", "rus-language", "Language sequence", None, ["RUS-101", "RUS-102", "RUS-221", "RUS-222"]),
        ("choose", "rus-culture", "Russian culture in translation", 1, ["RUS-247", "RUS-251"]),
        ("choose", "rus-advanced", "Advanced Russian", 3, ["RUS-313", "RUS-331", "RUS-345", "RUS-389"]),
        ("all", "rus-capstone", "Senior seminar", None, ["RUS-495"]),
    ], route="RUS-101 / RUS-102 / RUS-221 rus-culture / RUS-222 / rus-advanced / rus-advanced / rus-advanced / RUS-495"),

    dict(id="SPN", name="Spanish", division="Humanities", style="lang", courses="""
SPN-101 | Introductory Spanish I | F | - | Develops basic communication skills in Spanish through daily speaking, listening, reading and writing.
SPN-102 | Introductory Spanish II | S | SPN-101 | Continues the introductory sequence with more complex structures and short cultural readings.
SPN-221 | Intermediate Spanish I | F | SPN-102 | Reviews grammar and builds vocabulary through film, news and conversation.
SPN-222 | Intermediate Spanish II | S | SPN-221 | Prepares students for advanced courses with short literary texts and regular essays.
SPN-243 | Latinx Cultures in the United States | F | - | Studies literature, music and film by Latinx artists and the communities they come from; taught in English.
SPN-250 | Spain Today | S | - | Examines politics, regional identity and popular culture in contemporary Spain; taught in English.
SPN-311 | Constructing Identities in Latin America | F | SPN-222 | Reads essays, fiction and film on nation, race and belonging from independence to the present.
SPN-314 | Modern Spanish Narrative | S | SPN-222 | Follows the Spanish novel and short story from realism through the post-Franco period.
SPN-320 | Cultures of Spain | F | SPN-222 | Surveys the history, art and languages of the Iberian Peninsula.
SPN-343 | The Art of Language | S | SPN-222 | An advanced study of Spanish grammar and style through close analysis and writing.
SPN-379 | Seminar: Borders and Migration | F | SPN-222 | Studies narratives of crossing, exile and return in the Spanish-speaking world.
SPN-495 | Senior Seminar in Spanish | FS | SPN-222 | Majors research, write and present a capstone essay in Spanish.
""", groups=[
        ("all", "spn-language", "Language sequence", None, ["SPN-101", "SPN-102", "SPN-221", "SPN-222"]),
        ("choose", "spn-culture", "Hispanic cultures in translation", 1, ["SPN-243", "SPN-250"]),
        ("choose", "spn-advanced", "Advanced Spanish", 3, ["SPN-311", "SPN-314", "SPN-320", "SPN-343", "SPN-379"]),
        ("all", "spn-capstone", "Senior seminar", None, ["SPN-495"]),
    ], route="SPN-101 / SPN-102 / SPN-221 spn-culture / SPN-222 / spn-advanced / spn-advanced / spn-advanced / SPN-495"),

    dict(id="ART", name="Studio Art", division="Humanities", style="studio", courses="""
ART-111 | Introduction to the Studio | FS | - | Introduces the materials, methods and vocabulary of studio practice across two and three dimensions.
ART-134 | Drawing | FS | - | Develops observational drawing through line, value and composition in a range of media.
ART-236 | Print Media | F | ART-111 | Covers relief, intaglio and screen printing and the idea of the multiple.
ART-238 | Painting | S | ART-111 | Introduces oil and acrylic painting, color mixing and the construction of pictorial space.
ART-240 | Ceramics | F | ART-111 | Teaches hand-building, wheel throwing and glazing as approaches to functional and sculptural form.
ART-242 | Sculpture | S | ART-111 | Explores wood, metal and found materials and the relation of objects to space.
ART-246 | Digital Media | F | ART-111 | Uses image editing, video and code as tools for making art.
ART-248 | Photography | S | ART-111 | Covers camera technique, lighting and editing alongside the history of the photographic image.
ART-310 | Advanced Studio: Site and Installation | F | ART-111 & ART-134 | Students make work for particular places and audiences, on and off campus.
ART-315 | Advanced Studio: Contemporary Practices | S | ART-111 & ART-134 | Students develop a self-directed body of work in conversation with current art.
ART-320 | Advanced Studio: Image and Sequence | F | ART-111 & ART-134 | Explores series, books and time-based work across print, photography and video.
ART-495 | Senior Exhibition Seminar | FS | ART-111 & ART-134 | Majors produce and install a body of work for the senior exhibition and write an artist statement.
""", groups=[
        ("all", "art-foundations", "Foundations", None, ["ART-111", "ART-134"]),
        ("choose", "art-media", "Studio medium", 3, ["ART-236", "ART-238", "ART-240", "ART-242", "ART-246", "ART-248"]),
        ("choose", "art-advanced", "Advanced studio", 2, ["ART-310", "ART-315", "ART-320"]),
        ("all", "art-capstone", "Senior exhibition", None, ["ART-495"]),
        ("also-all", "art-history", "Also required: art history", None, ["ARH-103"]),
    ], route="ART-111 / ART-134 ARH-103 / art-media / art-media / art-media art-advanced / art-advanced / - / ART-495"),

    dict(id="THD", name="Theatre and Dance", division="Humanities", style="perf", courses="""
THD-104 | Contemporary Dance Technique | S | - | Builds strength, alignment and movement vocabulary in contemporary dance.
THD-111 | Introduction to Performance Studies | FS | - | Introduces theatre, dance and everyday performance as objects of study and as ways of knowing.
THD-115 | Theatrical Design and Technology | F | - | Introduces scenic, lighting and costume design and the crafts that realize them.
THD-117 | Introduction to Acting | FS | - | Develops the actor's voice, body and imagination through exercises, scenes and monologues.
THD-201 | World Theatre History | F | THD-111 | Surveys performance traditions from several continents and the societies that produced them.
THD-210 | Directing | S | THD-117 | Covers script analysis, staging and work with actors, ending in a directed scene.
THD-225 | Choreography and Composition | F | THD-104 | Students create short dances while studying structure, space and time.
THD-235 | Playwriting | S | THD-111 | A workshop in writing for the stage, from short scenes to a one-act play.
THD-240 | Scenic and Lighting Design | S | THD-115 | Takes design projects from concept through drafting, models and light plots.
THD-303 | Seminar: Performance Theory | F | THD-201 | Reads theories of performance, spectatorship and embodiment alongside live and recorded work.
THD-310 | Studio: Devised Performance | S | THD-111 & THD-117 | An ensemble creates an original piece from research, improvisation and collaborative writing.
THD-340 | Seminar: Dance, Body and Culture | F | THD-201 | Studies dance as social practice across cultures and periods.
THD-495 | Senior Capstone in Theatre and Dance | FS | THD-201 | Majors complete a performance, design or research project and reflect on it in writing.
""", groups=[
        ("all", "thd-foundations", "Foundations", None, ["THD-111", "THD-115", "THD-117", "THD-201"]),
        ("choose", "thd-practice", "Studio practice", 2, ["THD-104", "THD-210", "THD-225", "THD-235", "THD-240"]),
        ("choose", "thd-advanced", "Advanced seminar or studio", 2, ["THD-303", "THD-310", "THD-340"]),
        ("all", "thd-capstone", "Senior capstone", None, ["THD-495"]),
    ], route="THD-111 THD-117 / thd-practice / THD-115 THD-201 / thd-practice / thd-advanced / thd-advanced / - / THD-495"),

    # --------------------------------------------------------------- Science
    dict(id="BCM", name="Biological Chemistry", division="Science", style="lab", courses="""
BCM-150 | Molecules of Life | FS | - | Introduces the chemistry of proteins, nucleic acids, lipids and sugars for students curious about the molecular basis of biology.
BCM-262 | Introduction to Biological Chemistry | S | BIO-251 & CHM-221 | Covers the structure and function of biological macromolecules, enzyme catalysis and the central pathways of metabolism.
BCM-310 | Biophysical Chemistry | F | BCM-262 | Applies thermodynamics, kinetics and spectroscopy to biological molecules.
BCM-330 | Protein Structure and Function | F | BCM-262 | Examines how proteins fold, bind and catalyze, using structures from the current literature.
BCM-340 | Nucleic Acids and Gene Regulation | S | BCM-262 | Studies the chemistry of DNA and RNA and the molecular machinery that controls gene expression.
BCM-345 | Enzyme Kinetics and Mechanism | S | BCM-262 | Works through how enzymes achieve their rates and specificity, with quantitative analysis of kinetic data.
BCM-355 | Metabolism and Disease | F | BCM-262 | Follows metabolic pathways and their regulation, and what goes wrong in diabetes, cancer and inherited disorders.
BCM-360 | Laboratory Methods in Biochemistry | S | BCM-262 | A project-based laboratory in protein purification, assays and molecular cloning.
BCM-372 | Chemical Biology | F | BCM-262 & CHM-222 | Uses synthetic molecules as probes of living systems, from drug design to imaging.
BCM-495 | Senior Seminar in Biological Chemistry | FS | BCM-262 | Majors read, present and critique current research, and write a review article.
""", groups=[
        ("all", "bcm-core", "Core", None, ["BCM-262"]),
        ("choose", "bcm-advanced", "Advanced biological chemistry", 3, ["BCM-310", "BCM-330", "BCM-340", "BCM-345", "BCM-355", "BCM-360", "BCM-372"]),
        ("all", "bcm-capstone", "Senior seminar", None, ["BCM-495"]),
        ("also-all", "bcm-biology", "Also required: biology", None, ["BIO-150", "BIO-251"]),
        ("also-all", "bcm-chemistry", "Also required: chemistry", None, ["CHM-129", "CHM-221", "CHM-222"]),
    ], route="BIO-150 CHM-129 / BIO-251 / CHM-221 / CHM-222 BCM-262 / bcm-advanced / bcm-advanced / bcm-advanced / BCM-495"),

    dict(id="BIO", name="Biology", division="Science", style="lab", courses="""
BIO-150 | Introduction to Biological Inquiry | FS | - | Students learn how biologists ask and answer questions by designing and carrying out their own investigations.
BIO-240 | Animal Behavior | F | BIO-150 | Examines how and why animals behave as they do, from mechanisms to evolutionary function.
BIO-251 | Molecules, Cells and Organisms | FS | BIO-150 & CHM-129 | Covers cell structure, metabolism, genetics and the molecular basis of physiology.
BIO-252 | Organisms, Evolution and Ecology | FS | BIO-251 | Studies the diversity of life, the processes of evolution and the interactions of organisms with their environments.
BIO-305 | Plant Diversity and Evolution | F | BIO-252 | Surveys the major plant lineages and the evidence for their relationships, with field and herbarium work.
BIO-325 | Microbiology | S | BIO-251 | Introduces bacteria, archaea and viruses: their physiology, genetics and roles in health and ecosystems.
BIO-334 | Animal Physiology | F | BIO-251 | Compares how animals solve problems of respiration, circulation, water balance and movement.
BIO-345 | Advanced Genetics | S | BIO-251 | Examines gene structure, inheritance and genomics using classical and molecular approaches.
BIO-363 | Neurobiology | F | BIO-251 | Covers the cellular and molecular basis of nervous system function, from ion channels to circuits.
BIO-365 | Conservation Biology | S | BIO-252 | Applies population biology and ecology to the protection of species and habitats.
BIO-368 | Ecology | F | BIO-252 | Studies populations, communities and ecosystems, with field projects at the college's prairie research area.
BIO-373 | Mechanisms of Evolution | S | BIO-252 | Examines selection, drift and speciation using population genetics and case studies.
BIO-495 | Senior Research Seminar in Biology | FS | BIO-252 | Majors present their own or published research and write a research proposal.
""", groups=[
        ("all", "bio-core", "Core", None, ["BIO-150", "BIO-251", "BIO-252"]),
        ("choose", "bio-upper", "Upper-level biology", 4, ["BIO-305", "BIO-325", "BIO-334", "BIO-345", "BIO-363", "BIO-365", "BIO-368", "BIO-373"]),
        ("all", "bio-capstone", "Senior seminar", None, ["BIO-495"]),
        ("also-all", "bio-chemistry", "Also required: chemistry", None, ["CHM-129"]),
    ], route="BIO-150 CHM-129 / BIO-251 / BIO-252 / bio-upper / bio-upper / bio-upper / bio-upper / BIO-495"),

    dict(id="CHM", name="Chemistry", division="Science", style="lab", courses="""
CHM-129 | General Chemistry | FS | - | Introduces atomic structure, bonding, stoichiometry, equilibrium and thermodynamics.
CHM-210 | Inorganic and Analytical Chemistry | S | CHM-129 | Covers periodic trends, coordination chemistry and the quantitative analysis of solutions.
CHM-221 | Organic Chemistry I | F | CHM-129 | Introduces the structure, reactivity and synthesis of carbon compounds.
CHM-222 | Organic Chemistry II | S | CHM-221 | Continues organic chemistry with carbonyl compounds, aromatic systems and multi-step synthesis.
CHM-325 | Advanced Organic Chemistry | F | CHM-222 | Examines reaction mechanisms, stereochemistry and modern synthetic methods.
CHM-330 | Instrumental Analysis | S | CHM-210 | Covers the theory and practice of spectroscopy, chromatography and electrochemical methods.
CHM-332 | Environmental Chemistry | F | CHM-210 | Applies chemical principles to air, water and soil, with field sampling and analysis.
CHM-358 | Advanced Inorganic Chemistry | S | CHM-210 | Studies bonding, symmetry and reactivity in transition-metal and main-group compounds.
CHM-363 | Physical Chemistry I | F | CHM-222 & MAT-133 | Develops thermodynamics and chemical kinetics from first principles.
CHM-364 | Physical Chemistry II | S | CHM-363 | Introduces quantum mechanics and its application to atomic and molecular spectroscopy.
CHM-390 | Materials Chemistry | F | CHM-222 | Examines polymers, semiconductors and nanomaterials and how structure determines their properties.
CHM-495 | Senior Seminar in Chemistry | FS | CHM-363 | Majors present current research from the literature and write a critical review.
""", groups=[
        ("all", "chm-core", "Core", None, ["CHM-129", "CHM-210", "CHM-221", "CHM-222", "CHM-363", "CHM-364"]),
        ("choose", "chm-advanced", "Advanced chemistry", 2, ["CHM-325", "CHM-330", "CHM-332", "CHM-358", "CHM-390"]),
        ("all", "chm-capstone", "Senior seminar", None, ["CHM-495"]),
        ("also-all", "chm-calculus", "Also required: calculus", None, ["MAT-131", "MAT-133"]),
    ], route="CHM-129 MAT-131 / CHM-210 MAT-133 / CHM-221 / CHM-222 / CHM-363 chm-advanced / CHM-364 chm-advanced / - / CHM-495"),

    dict(id="PHY", name="Physics", division="Science", style="lab", courses="""
PHY-116 | The Universe and Its Structure | FS | - | A descriptive introduction to astronomy and cosmology for students in any field.
PHY-131 | General Physics I | F | MAT-131 | Introduces mechanics: motion, forces, energy, momentum and rotation.
PHY-132 | General Physics II | S | PHY-131 & MAT-133 | Continues with electricity, magnetism, circuits and optics.
PHY-220 | Electronics | F | PHY-132 | Covers analog and digital circuits through design projects at the bench.
PHY-232 | Modern Physics | F | PHY-132 | Introduces special relativity, quantum ideas and the structure of atoms and nuclei.
PHY-234 | Classical Mechanics | F | PHY-132 | Develops Newtonian and Lagrangian mechanics, oscillations and central-force motion.
PHY-310 | Computational Physics | S | PHY-232 | Uses numerical methods and simulation to solve problems that resist pen-and-paper solutions.
PHY-335 | Electromagnetic Theory | S | PHY-234 | Develops electrostatics, magnetostatics and Maxwell's equations using vector calculus.
PHY-337 | Optics and Waves | S | PHY-232 | Studies interference, diffraction, polarization and lasers, with laboratory projects.
PHY-340 | Astrophysics | F | PHY-232 | Applies physics to stars, galaxies and cosmology.
PHY-360 | Solid State Physics | S | PHY-232 | Examines crystal structure, electrons in solids and the physics of semiconductors.
PHY-456 | Quantum Mechanics | F | PHY-232 & PHY-234 | Develops the formal theory of quantum mechanics and applies it to simple systems.
PHY-462 | Advanced Laboratory | FS | PHY-232 | Students carry out and report on a series of open-ended experiments in modern physics.
""", groups=[
        ("all", "phy-core", "Core", None, ["PHY-131", "PHY-132", "PHY-232", "PHY-234", "PHY-335"]),
        ("choose", "phy-advanced", "Advanced physics", 2, ["PHY-220", "PHY-310", "PHY-337", "PHY-340", "PHY-360", "PHY-456"]),
        ("all", "phy-capstone", "Advanced laboratory", None, ["PHY-462"]),
        ("also-all", "phy-calculus", "Also required: calculus", None, ["MAT-131", "MAT-133"]),
    ], route="MAT-131 / MAT-133 / PHY-131 / PHY-132 / PHY-232 PHY-234 / PHY-335 phy-advanced / phy-advanced / PHY-462"),

    dict(id="PSY", name="Psychology", division="Science", style="quant", courses="""
PSY-113 | Introduction to Psychology | FS | - | Surveys the scientific study of behavior and mind, from the brain to social life.
PSY-214 | Social Psychology | F | PSY-113 | Examines how other people shape attitudes, judgment and behavior.
PSY-225 | Research Methods | FS | PSY-113 | Teaches experimental and correlational design, measurement and the reporting of results.
PSY-233 | Developmental Psychology | S | PSY-113 | Follows cognitive, social and emotional change from infancy through adolescence.
PSY-243 | Learning and Behavior | F | PSY-113 | Studies conditioning, reinforcement and their applications.
PSY-246 | Brain and Behavior | S | PSY-113 | Introduces the neural basis of perception, motivation, memory and emotion.
PSY-248 | Psychopathology | F | PSY-113 | Examines the description, causes and treatment of psychological disorders.
PSY-260 | Cognitive Psychology | S | PSY-113 | Covers attention, memory, language and decision making.
PSY-317 | Advanced Social Psychology | S | PSY-225 | Students design and run an original study on a current question in social psychology.
PSY-332 | Advanced Developmental Psychology | F | PSY-225 | Examines current research on development, with an observational research project.
PSY-336 | Advanced Behavioral Neuroscience | S | PSY-225 | Reads primary literature on the neural mechanisms of behavior and practices laboratory techniques.
PSY-348 | Seminar in Clinical Science | F | PSY-225 | Evaluates the evidence for psychological treatments and how it is produced.
PSY-360 | Advanced Cognitive Psychology | S | PSY-225 | Students replicate and extend a published experiment on memory or attention.
PSY-495 | Senior Seminar in Psychology | FS | PSY-225 | Majors integrate their coursework around a contested question and write a review paper.
""", groups=[
        ("all", "psy-foundations", "Foundations", None, ["PSY-113", "PSY-225"]),
        ("choose", "psy-core", "200-level psychology", 3, ["PSY-214", "PSY-233", "PSY-243", "PSY-246", "PSY-248", "PSY-260"]),
        ("choose", "psy-advanced", "Advanced psychology", 2, ["PSY-317", "PSY-332", "PSY-336", "PSY-348", "PSY-360"]),
        ("all", "psy-capstone", "Senior seminar", None, ["PSY-495"]),
    ], route="PSY-113 / psy-core / PSY-225 psy-core / psy-core / psy-advanced / psy-advanced / - / PSY-495"),

    # -------------------------------------------------------- Social Studies
    dict(id="ANT", name="Anthropology", division="Social Studies", style="soc", courses="""
ANT-104 | Anthropological Inquiry | FS | - | Introduces the four fields of anthropology and the ways anthropologists study human variation.
ANT-205 | Human Evolution | F | ANT-104 | Examines the fossil, genetic and archaeological evidence for the origins of our species.
ANT-210 | Illness, Healing and Culture | S | ANT-104 | Studies how societies understand sickness and organize care.
ANT-225 | Archaeology of North America | F | ANT-104 | Surveys the continent's deep history from the first peoples to the colonial era.
ANT-238 | Language and Culture | S | ANT-104 | Explores how language shapes identity, power and everyday interaction.
ANT-246 | Environmental Anthropology | F | ANT-104 | Considers how communities live with, know and contest their environments.
ANT-253 | Anthropology of Food | S | ANT-104 | Uses food to study exchange, ritual, labor and inequality.
ANT-280 | Theories of Culture | FS | ANT-104 | Traces the history of anthropological thought through its central debates.
ANT-290 | Ethnographic Research Methods | FS | ANT-104 | Students practice observation, interviewing and field notes in a local research project.
ANT-310 | Seminar: Migration and Belonging | F | ANT-280 | Reads ethnographies of movement, borders and citizenship.
ANT-325 | Seminar: Bioarchaeology | S | ANT-280 | Studies what human remains reveal about health, labor and identity in the past.
ANT-355 | Seminar: Anthropology of the State | F | ANT-280 | Examines bureaucracy, law and policing as lived experience.
ANT-375 | Seminar: Experimental Ethnography | S | ANT-280 | Explores film, sound and creative writing as forms of anthropological knowledge.
ANT-495 | Senior Thesis Seminar in Anthropology | FS | ANT-280 & ANT-290 | Majors write a thesis based on original field, laboratory or archival research.
""", groups=[
        ("all", "ant-foundations", "Foundations", None, ["ANT-104", "ANT-280", "ANT-290"]),
        ("choose", "ant-areas", "200-level anthropology", 3, ["ANT-205", "ANT-210", "ANT-225", "ANT-238", "ANT-246", "ANT-253"]),
        ("choose", "ant-seminars", "Anthropology seminar", 2, ["ANT-310", "ANT-325", "ANT-355", "ANT-375"]),
        ("all", "ant-capstone", "Senior thesis", None, ["ANT-495"]),
    ], route="ANT-104 / ant-areas / ANT-280 ant-areas / ANT-290 ant-areas / ant-seminars / ant-seminars / ANT-495 / -"),

    dict(id="ECN", name="Economics", division="Social Studies", style="quant", courses="""
ECN-111 | Introduction to Economics | FS | - | Introduces how markets work, when they fail, and how the economy as a whole grows and fluctuates.
ECN-205 | Current Economic Issues | S | ECN-111 | Applies introductory tools to debates on trade, inequality, health care and climate policy.
ECN-215 | Labor Economics | F | ECN-111 | Studies wages, employment, unions and discrimination in the labor market.
ECN-226 | Environmental Economics | S | ECN-111 | Examines pollution, natural resources and the design of environmental policy.
ECN-230 | Economic Development | F | ECN-111 | Asks why some countries are rich and others poor, and what policies change that.
ECN-245 | Money and Banking | S | ECN-111 | Covers financial institutions, central banking and monetary policy.
ECN-280 | Microeconomic Analysis | FS | ECN-111 & MAT-131 | Develops the theory of consumers, firms and markets using calculus.
ECN-282 | Macroeconomic Analysis | FS | ECN-111 | Builds models of growth, unemployment and inflation and uses them to evaluate policy.
ECN-286 | Econometrics | FS | ECN-280 | Teaches regression analysis and causal inference with economic data.
ECN-326 | Seminar in Industrial Organization | F | ECN-280 | Studies competition, market power and antitrust.
ECN-338 | Seminar in Applied Game Theory | S | ECN-280 | Uses strategic models to analyze bargaining, auctions and cooperation.
ECN-366 | Seminar in International Trade | F | ECN-282 | Examines why countries trade, who gains and how trade policy is made.
ECN-374 | Seminar in Public Finance | S | ECN-286 | Analyzes taxation, public spending and social insurance, with an empirical research paper.
""", groups=[
        ("all", "ecn-core", "Core", None, ["ECN-111", "ECN-280", "ECN-282", "ECN-286"]),
        ("choose", "ecn-fields", "200-level field course", 2, ["ECN-205", "ECN-215", "ECN-226", "ECN-230", "ECN-245"]),
        ("choose", "ecn-seminars", "Economics seminar", 2, ["ECN-326", "ECN-338", "ECN-366", "ECN-374"]),
        ("also-all", "ecn-calculus", "Also required: calculus", None, ["MAT-131"]),
    ], route="ECN-111 MAT-131 / ecn-fields / ECN-280 / ECN-282 ecn-fields / ECN-286 / ecn-seminars / ecn-seminars / -"),

    dict(id="HIS", name="History", division="Social Studies", style="soc", courses="""
HIS-100 | Historical Methods | FS | - | Introduces how historians find, read and argue from evidence, organized around one topic chosen by the instructor.
HIS-201=LAS-201 | Colonial Latin America | F | - | Follows the Americas from the eve of conquest to the wars of independence.
HIS-212 | The United States to 1877 | F | - | Surveys North America from colonization through Reconstruction.
HIS-214 | The United States since 1877 | S | - | Follows the United States from the Gilded Age to the present.
HIS-222 | Modern Europe, 1789 to the Present | S | - | Traces revolution, industrialization, war and integration in European history.
HIS-235 | Britain and Empire | F | - | Studies the rise and unraveling of the British Empire and its effects at home and abroad.
HIS-242 | East Asia since 1600 | S | - | Compares the modern histories of China, Japan and Korea.
HIS-261 | Africa since 1800 | F | - | Examines the slave trades, colonial rule, independence and the postcolonial state.
HIS-268 | The Modern Middle East | S | - | Follows the region from the late Ottoman period to the present.
HIS-311 | Seminar: The American West | F | HIS-100 | Reads recent scholarship on land, migration and myth in the West.
HIS-325 | Seminar: Revolution and Memory in Europe | S | HIS-100 | Studies how revolutions have been remembered, commemorated and argued over.
HIS-334 | Seminar: Decolonization | F | HIS-100 | Compares the end of empire in Asia, Africa and the Caribbean.
HIS-342 | Seminar: Oral History and Public Memory | S | HIS-100 | Students conduct interviews and produce a public history project.
""", groups=[
        ("all", "his-methods", "Methods", None, ["HIS-100"]),
        ("choose", "his-americas", "History of the Americas", 2, ["HIS-201", "HIS-212", "HIS-214"]),
        ("choose", "his-world", "History of Europe, Asia, Africa or the Middle East", 3, ["HIS-222", "HIS-235", "HIS-242", "HIS-261", "HIS-268"]),
        ("choose", "his-seminars", "History seminar", 2, ["HIS-311", "HIS-325", "HIS-334", "HIS-342"]),
    ], route="HIS-100 / his-americas / his-americas / his-world / his-world / his-world his-seminars / his-seminars / -"),

    dict(id="POL", name="Political Science", division="Social Studies", style="soc", courses="""
POL-101 | Introduction to Political Science | FS | - | Introduces the study of power, institutions and political behavior in the United States and abroad.
POL-216 | American Political Institutions | F | POL-101 | Examines Congress, the presidency and the bureaucracy and how they interact.
POL-219 | Constitutional Law and Politics | S | POL-101 | Reads landmark Supreme Court decisions on federal power and individual rights.
POL-237 | Empirical Political Analysis | FS | POL-101 | Teaches research design and the use of quantitative and qualitative evidence in political science.
POL-250 | Politics of International Relations | F | POL-101 | Introduces theories of war, cooperation and international order.
POL-251 | International Political Economy | S | POL-101 | Studies the politics of trade, finance and development.
POL-255 | Comparative Democracies | F | POL-101 | Compares electoral systems, parties and welfare states across established democracies.
POL-262 | Politics of Development | S | POL-101 | Examines state building, inequality and reform in the Global South.
POL-310 | Seminar: Courts and Rights | F | POL-237 | Asks when courts protect rights and when they do not.
POL-319 | Seminar: Parties and Polarization | S | POL-237 | Studies the causes and consequences of partisan division.
POL-352 | Seminar: United States Foreign Policy | F | POL-237 | Analyzes how foreign policy is made and debated, through historical cases.
POL-355 | Seminar: Democratic Backsliding | S | POL-237 | Compares how democracies erode and how they recover.
""", groups=[
        ("all", "pol-foundations", "Foundations", None, ["POL-101", "POL-237"]),
        ("choose", "pol-american", "American politics", 1, ["POL-216", "POL-219"]),
        ("choose", "pol-international", "International relations", 1, ["POL-250", "POL-251"]),
        ("choose", "pol-comparative", "Comparative politics or political theory", 1, ["POL-255", "POL-262", "POL-263"]),
        ("choose", "pol-elective", "200-level politics elective", 1, ["POL-216", "POL-219", "POL-250", "POL-251", "POL-255", "POL-262", "POL-263"]),
        ("choose", "pol-seminars", "Political Science seminar", 2, ["POL-310", "POL-319", "POL-352", "POL-355"]),
    ], route="POL-101 / pol-american / POL-237 pol-international / pol-comparative / pol-elective / pol-seminars / pol-seminars / -"),

    dict(id="SOC", name="Sociology", division="Social Studies", style="soc", courses="""
SOC-111 | Introduction to Sociology | FS | - | Introduces the sociological study of groups, institutions and inequality.
SOC-220 | Sociology of Global Development | F | SOC-111 | Examines theories of development and the institutions that shape global inequality.
SOC-240 | Social Movements | S | SOC-111 | Studies why movements emerge, how they organize and when they succeed.
SOC-248 | Self and Society | F | SOC-111 | Introduces social psychology from a sociological point of view: identity, interaction and emotion.
SOC-260 | Sociology of the Family | S | SOC-111 | Examines how families are formed, how they vary and how policy shapes them.
SOC-265 | Sociology of Health and Illness | F | SOC-111 | Studies the social causes of illness and the organization of medical care.
SOC-270=GWS-270 | Gender and Society | S | SOC-111 or GWS-111 | Examines gender as a social structure in work, family, schooling and the state.
SOC-275 | Race and Ethnicity in America | F | SOC-111 | Analyzes how racial categories are made and how they organize opportunity.
SOC-285 | Contemporary Sociological Theory | FS | SOC-111 | Reads the major theoretical traditions and applies them to current problems.
SOC-291 | Methods of Empirical Investigation | FS | SOC-111 | Teaches survey, interview and observational research, ending in a research proposal.
SOC-320 | Seminar: Inequality and Education | F | SOC-285 | Examines how schools reproduce and disrupt inequality.
SOC-350 | Seminar: Organizations and Work | S | SOC-285 | Studies workplaces, professions and the changing employment relationship.
SOC-360 | Seminar: Urban Sociology | F | SOC-291 | Students study segregation, housing and neighborhood change with a local data project.
SOC-390 | Seminar: Culture and Consumption | S | SOC-291 | Examines taste, markets and identity through original qualitative research.
""", groups=[
        ("all", "soc-foundations", "Foundations", None, ["SOC-111", "SOC-285", "SOC-291"]),
        ("choose", "soc-topics", "200-level sociology", 3, ["SOC-220", "SOC-240", "SOC-248", "SOC-260", "SOC-265", "SOC-270", "SOC-275"]),
        ("choose", "soc-seminars", "Sociology seminar", 2, ["SOC-320", "SOC-350", "SOC-360", "SOC-390"]),
    ], route="SOC-111 / soc-topics / SOC-285 soc-topics / SOC-291 soc-topics / soc-seminars / soc-seminars / - / -"),

    # ------------------------------------------------------ Interdisciplinary
    dict(id="AMS", name="American Studies", division="Interdisciplinary", style="hum", courses="""
AMS-130 | Introduction to American Studies | FS | - | Introduces the interdisciplinary study of the United States through texts, images, music and places.
AMS-235 | Popular Culture in the United States | F | AMS-130 | Studies film, television, sport and advertising as evidence of social change.
AMS-240 | Race, Place and Memory | S | AMS-130 | Examines monuments, museums and neighborhoods as sites where the past is argued over.
AMS-245 | The American Landscape | F | AMS-130 | Considers how prairies, suburbs and wilderness have been imagined and remade.
AMS-255 | Immigration and Belonging | S | AMS-130 | Follows debates over who counts as American, from the nineteenth century to the present.
AMS-260 | Methods in American Studies | FS | AMS-130 | Practices archival research, visual analysis and oral history on shared case studies.
AMS-320 | Seminar: The Midwest in the American Imagination | F | AMS-260 | Reads fiction, journalism and history about the region and tests them against local archives.
AMS-335 | Seminar: Music and Social Movements | S | AMS-260 | Studies the songs and performers tied to labor, civil rights and antiwar organizing.
AMS-345 | Seminar: The Public Humanities | S | AMS-260 | Students design an exhibit, podcast or digital project with a community partner.
AMS-495 | Senior Project in American Studies | FS | AMS-260 | Majors complete an interdisciplinary research or public project and present it.
""", groups=[
        ("all", "ams-foundations", "Foundations", None, ["AMS-130", "AMS-260"]),
        ("choose", "ams-topics", "American Studies topics", 2, ["AMS-235", "AMS-240", "AMS-245", "AMS-255"]),
        ("choose", "ams-related", "Related course in another department", 2, ["HIS-212", "HIS-214", "ENG-227", "SOC-275", "POL-216", "REL-241", "MUS-270", "FMS-155"]),
        ("choose", "ams-seminars", "American Studies seminar", 2, ["AMS-320", "AMS-335", "AMS-345"]),
        ("all", "ams-capstone", "Senior project", None, ["AMS-495"]),
    ], route="AMS-130 / ams-topics / AMS-260 ams-related / ams-topics / ams-related ams-seminars / ams-seminars / - / AMS-495"),

    dict(id="GWS", name="Gender, Women's and Sexuality Studies", division="Interdisciplinary", style="hum", courses="""
GWS-111 | Introduction to Gender, Women's and Sexuality Studies | FS | - | Introduces gender and sexuality as categories of analysis and as lived experience.
GWS-211 | Foundations of LGBTQ Studies | F | GWS-111 | Surveys the history, politics and scholarship of LGBTQ communities.
GWS-225 | Bodies, Health and Justice | S | GWS-111 | Examines reproductive politics, disability and access to care.
GWS-235 | Feminist and Queer Media | F | GWS-111 | Studies film, television and online culture made by and about women and queer people.
GWS-249 | Feminist and Queer Theory | FS | GWS-111 | Reads the major theoretical texts of the field and the debates among them.
GWS-255 | Transnational Feminisms | S | GWS-111 | Compares feminist movements across borders and the tensions among them.
GWS-324 | Seminar: Critical Race Feminisms | F | GWS-249 | Studies Black, Indigenous, Latina and Asian American feminist thought.
GWS-333 | Seminar: Sexuality, Law and the State | S | GWS-249 | Examines how law regulates intimacy, family and identity.
GWS-345 | Seminar: Gender and Technology | F | GWS-249 | Asks how technologies from the contraceptive pill to the algorithm shape gender.
GWS-495 | Senior Seminar in Gender, Women's and Sexuality Studies | FS | GWS-249 | Majors complete a research or community-based project and present it.
""", groups=[
        ("all", "gws-foundations", "Foundations", None, ["GWS-111", "GWS-249"]),
        ("choose", "gws-topics", "Gender, Women's and Sexuality Studies topics", 2, ["GWS-211", "GWS-225", "GWS-235", "GWS-255"]),
        ("choose", "gws-related", "Related course in another department", 2, ["SOC-270", "PHI-264", "CLS-255", "ANT-210", "SOC-260", "ENG-229"]),
        ("choose", "gws-seminars", "Seminar", 2, ["GWS-324", "GWS-333", "GWS-345"]),
        ("all", "gws-capstone", "Senior seminar", None, ["GWS-495"]),
    ], route="GWS-111 / gws-topics / GWS-249 gws-topics / gws-related / gws-seminars / gws-related gws-seminars / - / GWS-495"),

    dict(id="LAS", name="Latin American Studies", division="Interdisciplinary", style="soc", courses="""
LAS-111 | Introduction to Latin American Studies | FS | - | Introduces the region's histories, cultures and politics from several disciplines.
LAS-221 | Modern Latin America | S | LAS-111 | Follows revolution, dictatorship and democratization from independence to the present.
LAS-230 | Indigenous Peoples and the State | F | LAS-111 | Examines Indigenous movements, rights and autonomy in the Andes and Mesoamerica.
LAS-242 | Caribbean Worlds | S | LAS-111 | Studies slavery, migration and cultural exchange across the islands and their diasporas.
LAS-255 | Cities of Latin America | F | LAS-111 | Uses Mexico City, Bogota and Sao Paulo to study urban growth, informality and culture.
LAS-260 | Political Economy of Latin America | S | LAS-111 | Analyzes commodity booms, debt and social policy.
LAS-275 | Research Methods in Area Studies | FS | LAS-111 | Introduces archival, ethnographic and quantitative approaches to studying a region.
LAS-320 | Seminar: Memory and Human Rights | F | LAS-275 | Studies truth commissions, trials and memorials after state violence.
LAS-335 | Seminar: Borderlands | S | LAS-275 | Examines the border between the United States and Mexico as a region with its own history.
LAS-350 | Seminar: Environment and Extraction | F | LAS-275 | Follows conflicts over mining, oil and forests and the communities involved.
LAS-495 | Senior Project in Latin American Studies | FS | LAS-275 | Majors complete an interdisciplinary research project, normally using sources in Spanish or Portuguese.
""", groups=[
        ("all", "las-foundations", "Foundations", None, ["LAS-111", "LAS-275"]),
        ("choose", "las-topics", "Latin American Studies topics", 3, ["HIS-201", "LAS-221", "LAS-230", "LAS-242", "LAS-255", "LAS-260"]),
        ("choose", "las-seminars", "Latin American Studies seminar", 2, ["LAS-320", "LAS-335", "LAS-350"]),
        ("all", "las-capstone", "Senior project", None, ["LAS-495"]),
        ("also-choose", "las-language", "Also required: Spanish", 2, ["SPN-101", "SPN-102", "SPN-221", "SPN-222"]),
    ], route="LAS-111 las-language / las-language las-topics / LAS-275 las-topics / las-topics / las-seminars / las-seminars / - / LAS-495"),
]

# Sample courses that belong to no mock major (college-wide, or subjects without a major here).
EXTRAS = dict(style="hum", courses="""
TUT-100 | First-Year Tutorial | F | - | A small writing-intensive seminar on a topic chosen by the instructor, who also serves as the student's first adviser.
FYE-100(1) | First-Year Experience | FS | - | Weekly sessions on navigating college life, academic planning and campus resources.
EDU-101 | Educational Principles | FS | - | Introduces the history, philosophy and politics of schooling in the United States.
FMS-155 | Introduction to Film Studies | FS | - | Teaches the vocabulary of film form and the major approaches to film history and criticism.
GDS-111 | Introduction to Global Development Studies | FS | - | Introduces competing ideas of development and the institutions that pursue them.
""")

# Second and third sentences, picked by department style and course level.
STYLE_SENTENCES = {
    "hum": {
        "intro": ["No previous coursework in the field is assumed, and frequent short essays build the habits of close reading and argument.",
                  "Class meetings are mostly discussion, and writing assignments move from brief responses to a longer paper.",
                  "Open to all students; the course emphasizes careful reading, discussion and analytical writing."],
        "mid": ["Students write several analytical essays and lead discussion at least once.",
                "Assignments include response papers, a class presentation and a final essay.",
                "Lecture and discussion alternate, and students complete a research-based paper by the end of the term."],
        "upper": ["Enrollment is limited, and each student writes a substantial research paper developed over the semester.",
                  "Students take turns leading discussion and finish with a seminar paper presented to the class.",
                  "The course is reading-intensive and ends with an independent research essay."],
    },
    "lang": {
        "intro": ["Class meets four days a week and is conducted in the language as far as possible.",
                  "Small-group practice sessions with a language assistant supplement regular class meetings.",
                  "Daily homework, short quizzes and oral practice keep the pace steady throughout the term."],
        "mid": ["Regular written work and oral presentations are required.",
                "Readings, screenings and discussion are supported by short papers.",
                "Students complete weekly writing assignments and a final project."],
        "upper": ["The course is conducted in the language, and students write and present a final paper.",
                  "Discussion and all written work are in the language.",
                  "Students lead discussion and complete a research paper drawing on original-language sources."],
    },
    "lab": {
        "intro": ["Three class meetings and one laboratory each week.",
                  "A weekly three-hour laboratory introduces experimental design and data analysis.",
                  "Lecture, problem solving and a weekly laboratory are closely integrated."],
        "mid": ["Includes a weekly laboratory, with formal lab reports.",
                "Class meetings are paired with a weekly three-hour laboratory.",
                "Problem sets and laboratory work carry equal weight."],
        "upper": ["Students read the primary literature and complete an extended laboratory or field project.",
                  "Includes a project-based laboratory and a final written report in journal format.",
                  "Class discussion centers on recent papers, and the laboratory supports an independent project."],
    },
    "studio": {
        "intro": ["Studio sessions combine demonstrations, hands-on projects and group critique.",
                  "No experience is required; students complete a series of projects and take part in critiques.",
                  "Class time is spent working in the studio, with regular critiques and visits to the college's art collection."],
        "mid": ["Students complete four or five projects and present them in critique.",
                "Technical demonstrations lead into self-directed projects and group critiques.",
                "Studio work is supported by readings, artist talks and a sketchbook."],
        "upper": ["Students work independently toward a coherent body of work, with weekly critiques.",
                  "Individual studio visits, readings and critiques structure the semester.",
                  "The course ends with a public installation of student work."],
    },
    "perf": {
        "intro": ["Class combines practical work with listening, viewing and short written reflections.",
                  "No previous training is required; attendance at several campus performances is expected.",
                  "Regular practice outside class is expected, along with short written assignments."],
        "mid": ["Students complete practical projects alongside readings and a short research paper.",
                "Class time is divided between studio work and discussion.",
                "Assignments include weekly exercises, a midterm project and a final showing or paper."],
        "upper": ["Students present work in progress throughout the term and complete a final project.",
                  "Each student leads a session and completes a substantial final paper or performance.",
                  "The course combines close study with a culminating public presentation."],
    },
    "soc": {
        "intro": ["Lectures and discussion introduce key concepts, and students write several short papers.",
                  "No background is assumed; assignments include reading responses, two exams and a short paper.",
                  "Students practice reading evidence critically and writing clear, well-supported arguments."],
        "mid": ["Students write two essays and complete a small research project.",
                "Readings combine classic studies with recent research, and students write a final paper.",
                "Assignments include discussion leadership, short papers and a final exam."],
        "upper": ["Enrollment is limited, and each student completes an original research paper.",
                  "Students lead discussion on the readings and present a seminar paper.",
                  "The seminar is organized around student research, developed in stages over the term."],
    },
    "quant": {
        "intro": ["Lectures are paired with problem sets, and two exams and a final are given.",
                  "No background is assumed; regular problem sets develop quantitative reasoning.",
                  "Students work with data and simple models from the first week."],
        "mid": ["Problem sets, a data project and exams are required.",
                "Students analyze data with statistical software and write up their findings.",
                "The course combines lecture with hands-on work and a short empirical paper."],
        "upper": ["Students read current research and complete an original empirical project.",
                  "The course ends with a research paper and presentation.",
                  "Enrollment is limited; students present papers from the literature and write a research report."],
    },
}

# SAMPLE descriptions for the real Computer Science, Mathematics and Statistics courses. The
# catalog facts for these courses (titles, credits, prerequisites, offerings) stay in
# grinnell_catalog.json; only these descriptions are mock, written for the demo.
CATALOG_DESCRIPTIONS = {
    "CSC-105": "Looks at how computing shapes work, privacy, creativity and public life. Students experiment with the underlying technologies and write about their social effects; no programming background is expected.",
    "CSC-151": "A first course in computer science that teaches problem solving through functional programming. Students work in pairs on daily labs, building programs from small functions and learning to reason about recursion and data.",
    "CSC-161": "Continues the introductory sequence with imperative programming in a low-level language. Labs cover memory, pointers, arrays and linked structures, along with the tools programmers use to build and test software.",
    "CSC-205": "Introduces computational approaches to human language, including parsing, language models and the evaluation of language technologies. Students build small systems and consider what they do and do not capture about language.",
    "CSC-207": "Develops object-oriented design alongside the core data structures and algorithms of computer science. Students implement lists, trees, hash tables and graphs and analyze their running time.",
    "CSC-208": "Covers the mathematics that computer science depends on: logic, proof, sets, relations, counting and graphs. Students practice writing rigorous arguments and connect each topic to programs.",
    "CSC-211": "Explains how a computer executes a program, from digital logic and machine instructions up to the processor and memory hierarchy. Students design simple hardware components and write assembly code.",
    "CSC-213": "Studies how operating systems manage processes, memory and files, and how programs can run correctly in parallel. Labs involve building pieces of a system and writing concurrent code.",
    "CSC-214": "A half-semester introduction to how computer systems and networks are attacked and defended. Students study common vulnerabilities, basic cryptography and the practice of secure design.",
    "CSC-216": "A half-semester introduction to how computers communicate, from local links to the global internet. Students examine the layered protocols and write simple networked programs.",
    "CSC-232": "A half-semester introduction to designing technology around the people who use it. Students observe users, prototype interfaces and evaluate them.",
    "CSC-261": "Surveys the central ideas of artificial intelligence, including search, knowledge representation, reasoning under uncertainty and machine learning. Students implement several techniques and discuss their limits.",
    "CSC-262": "Examines how computers extract information from images, covering image formation, filtering, features and recognition. Programming projects apply the mathematics to real photographs.",
    "CSC-281": "Alumni working in computing visit to talk about their careers and the choices that led to them. Students reflect on their own plans in short written responses.",
    "CSC-282": "A short, hands-on course in the tools and habits of working programmers on Unix systems. Topics include the shell, build tools, debugging and idiomatic C.",
    "CSC-301": "Teaches the design and analysis of efficient algorithms, including divide and conquer, greedy methods, dynamic programming and graph algorithms. Students prove correctness and running-time bounds and meet the limits of efficient computation.",
    "CSC-312": "Students learn how programming languages work by building interpreters and compilers. Topics include parsing, type checking, code generation and runtime support.",
    "CSC-313": "A deeper study of operating system design for students who have completed the systems course. Sample entry: the advising guide names this course, and the catalog does not yet describe it.",
    "CSC-315": "Considers the social consequences of algorithmic decision making and the responsibilities of those who build such systems. Sample entry: the advising guide names this course, and the catalog does not yet describe it.",
    "CSC-324": "Students work in teams on a substantial software project for a real client. The course covers requirements, design, testing, version control and the practices that keep a team productive.",
    "CSC-326": "Students who have completed the software design course lead project teams in it. They practice mentoring, planning and technical leadership and reflect on what works.",
    "CSC-341": "Studies what can and cannot be computed, using finite automata, grammars and Turing machines. The course closes with complexity classes and the question of which problems are efficiently solvable.",
    "CSC-395": "An advanced special-topics course on the theory and design of modern programming languages. Students study type systems and language semantics and apply them in programming projects.",
    "MAT-123": "The first half of a two-semester path through single-variable calculus that reviews functions along the way. Covers limits, derivatives and their applications at a measured pace.",
    "MAT-124": "Completes the two-semester path through first-semester calculus. Covers integration and its applications while continuing to strengthen work with functions.",
    "MAT-125": "Introduces mathematical modeling with functions for first-year students. Linear, exponential and periodic models are fitted to data and used to answer questions from the sciences and social sciences.",
    "MAT-131": "A first course in calculus covering limits, derivatives, integrals and the fundamental theorem that links them. Applications are drawn from the natural and social sciences.",
    "MAT-133": "Continues single-variable calculus with techniques and applications of integration, sequences and series. The course ends with an introduction to functions of several variables.",
    "MAT-208": "Covers the mathematics that computer science depends on: logic, proof, sets, relations, counting and graphs. Students practice writing rigorous arguments and connect each topic to programs.",
    "MAT-215": "Introduces vectors, matrices, linear systems, vector spaces and linear transformations. Students move between computation and proof and see applications in geometry and data.",
    "MAT-218": "A transition to proof-based mathematics through discrete topics such as combinatorics, graph theory and number theory. Students learn to read, write and critique proofs.",
    "MAT-220": "Studies ordinary differential equations and the systems they model. Analytical, qualitative and numerical methods are developed side by side.",
    "MAT-222": "A transition to proof-based mathematics organized around the foundations of analysis and algebra. Students learn to read, write and critique proofs.",
    "MAT-306": "Students build and analyze mathematical models of problems from biology, economics and physics. Projects emphasize choosing assumptions, testing a model against data and communicating results.",
    "MAT-313": "Studies algorithms for approximating solutions to mathematical problems, including root finding, interpolation, integration and linear systems. Students analyze error and implement the methods.",
    "MAT-314": "A second course in applied mathematics whose topic changes from year to year. Recent themes include optimization, partial differential equations and dynamical systems.",
    "MAT-316": "A rigorous treatment of the real numbers, sequences, continuity, differentiation and integration. Students write proofs of the theorems that calculus relies on.",
    "MAT-317": "Continues the study of analysis with a topic chosen by the instructor, such as measure theory, complex analysis or metric spaces. Students present proofs at the board and write up a final project.",
    "MAT-321": "Introduces groups, rings and fields and the structure-preserving maps between them. The emphasis is on abstraction and proof.",
    "MAT-322": "Continues the study of abstract algebra with a topic chosen by the instructor, such as Galois theory, representation theory or algebraic number theory. Regular problem sets lead to a final presentation.",
    "MAT-330": "Students carry out data science projects from question to communication, working with messy, real data sets. Topics include data wrangling, visualization, modeling and reproducible workflows.",
    "MAT-335": "Develops probability theory with calculus: random variables, distributions, expectation and limit theorems. The course lays the groundwork for mathematical statistics.",
    "MAT-336": "Builds the theory of statistical inference on probability, covering estimation, hypothesis testing and regression. Students connect the theory to data analysis.",
    "MAT-444": "A capstone seminar for senior majors on a topic that draws together several areas of mathematics. Students read advanced material and present it to one another.",
    "STA-209": "Introduces statistical thinking with real data: study design, exploratory analysis, inference and regression. Students use statistical software throughout and complete a data analysis project.",
    "STA-230": "Introduces the tools of data science, including data wrangling, visualization and reproducible analysis in a programming environment. Students complete projects with data they collect or find.",
    "STA-270": "Introduces methods for predicting outcomes from data, such as regression, classification and resampling. Students compare models and learn to judge how well predictions generalize.",
    "STA-309": "Teaches how to plan experiments and analyze their results, including factorial and blocked designs. Students design and run an experiment of their own.",
    "STA-310": "Extends regression to multiple predictors, categorical outcomes and correlated data. Students fit, check and interpret models in case studies.",
    "STA-330": "Students carry out data science projects from question to communication, working with messy, real data sets. Topics include data wrangling, visualization, modeling and reproducible workflows.",
    "STA-335": "Develops probability theory with calculus: random variables, distributions, expectation and limit theorems. The course lays the groundwork for mathematical statistics.",
    "STA-336": "Builds the theory of statistical inference on probability, covering estimation, hypothesis testing and regression. Students connect the theory to data analysis.",
    "STA-340": "Introduces the Bayesian approach to inference, in which prior beliefs are updated with data. Students fit models by simulation and compare the results with classical methods.",
    "STA-350": "Covers advanced topics in statistical modeling, such as generalized linear models and models for dependent data. Students work through the theory and apply it to substantial data sets.",
    "STA-370": "Studies the main methods of machine learning, both supervised and unsupervised, with attention to the mathematics behind them. Students implement and evaluate methods on real data.",
}

# Fictional instructor names: every pairing is invented. KNOWN_REAL lists real Grinnell faculty
# names that must never appear; the build fails if a generated name matches one.
FIRST_NAMES = """Adaeze Akira Alejandra Amara Anders Anika Arjun Beatriz Bolaji Camille Chidi Dalia Darius
Desmond Eleni Emeka Esperanza Farid Fatima Gabriela Hana Henrik Imani Ingrid Isamu Jamila Javier Katarzyna
Kwame Laila Leilani Lucia Malik Marisol Mateo Mei-Ling Miriam Nadia Naveen Ngozi Nikolai Noor Oluwaseun Paloma
Priya Rafael Renata Rohan Sanjay Selim Siobhan Sofia Tariq Tomasz Thandiwe Valentina Wei Yusuf Zainab Zofia
Bridget Callum Dorothea Elliot Greta Harlan Josephine Marcus Naomi Owen Rosalind Theodore Winona""".split()

LAST_NAMES = """Abara Achterberg Adeyemi Akhmetova Alvarenga Amundsen Aoki Arriaga Asante Bakshi Balogun Barzani
Bekele Belmonte Bergstrom Bhattacharya Brandvold Cabrera Castellanos Chaudhry Chikwanha Cisneros Dalgaard Danso
Delacroix Demir Dlamini Eastman Echeverria Ekstrom Farahani Fitzwilliam Fonseca Fujimoto Gallardo Gebremariam
Goldfarb Grunewald Halvorsen Haddad Hoang Holloway Ibekwe Iglesias Ishikawa Jablonski Jankowski Kalinowski
Kamara Kapoor Keawe Khoury Kimathi Kovalenko Kuroda Lachance Lindqvist Madrigal Mahlangu Marchetti Mbatha
Medrano Moreau Mukherjee Nakamura Navarrete Ndiaye Nordahl Novak Nwosu Obradovic Okonjo Olawale Osei Paredes
Petrosyan Pham Quispe Rahimi Ramaswamy Rojas Rosenthal Saetang Sandoval Sarkisian Sato Schreiber Sepulveda
Shrestha Silvestri Sorensen Takahashi Tavares Tembo Thorvaldsen Tran Umarov Valdivia Vandermeer Varga
Villanueva Watanabe Whitcombe Wijaya Yamamoto Yeboah Zamora Zielinski Zubiri Ahlgren Bontemps Calloway
Draper-Singh Elmasry Featherstone Gutierrez-Holm Hakimi Iwasaki Jurado Kettering Lomasi Mwangi Nakashima
Oyelaran Pellegrino Quintanilla Ravensworth Sithebe Tanaka-Ruiz Udoka Vasquez-Lang Wachira Xiong Yilmaz""".split()

KNOWN_REAL = """Samuel Rebelsky|Shawn Ong|Jerod Weinman|Charlie Curtsinger|Peter-Michael Osera|Henry Walker|John Stone
|Janet Davis|Barbara Johnson|Fernanda Eliott|Eric Autry|Nicole Eikmeier|Leah Perlmutter|Marc Chamberland
|Christopher French|Joseph Mileti|Jennifer Paulhus|Karen Shuman|Shonda Kuiper|Jeffrey Jonkman|Royce Wolf
|Emily Moore|Thomas Moore|Jeffrey Blanchard|Kesho Scott|Erik Simpson|Sarah Purcell|Karla Erickson
|Ross Haenfler|Vida Praitis|Leslie Gregg-Jolly|Mark Levandoski|Elaine Marzluff|Stephen Sieck|Paul Tjossem
|Charles Cunningham|Monessa Cummins|Timothy Arner|Shanna Benjamin|Dean Bakopoulos|Ralph Savarese|Jin Feng
|Todd Armstrong|Kelly Herold|Jeremy Chen|Lee Running|Andrew Kaufman|John Rommereim|Tony Perman|Tammy Nyden
|Johanna Meehan|John Fennell|Henry Rietz|Tyler Roberts|Caleb Elfenbein|William Ferguson|Bradley Graham
|Keith Brouhard|Wayne Moyer|Barbara Trish|Danielle Lussier|Peter Hanson|Jon Andelson|Monty Roper
|David Lopatto|Ann Ellis|Laura Sinnett|Asani Seawell|Christopher Ralston|David Cook-Martin|Sharon Quinsaat
|Astrid Henry|Lakesia Johnson|Leah Allen|Michael Guenther|Pablo Silva|Edward Cohn|Albert Lacson
|Mirzam Perez|Valerie Benoist|Yvette Aparicio|David Harrison|Philippe Moisan|Vance Byrd|Daniel Reynolds
|Justin Thomas|Lesley Wright|Jenny Anger|Vincent Eckhart|Jackie Brown|Kathryn Jacobson|Benjamin DeRidder
|Shannon Hinsa-Leasure|Clark Lindgren|Nancy Rempel-Clower|Mark Schneider|Eliza Willis|Xavier Escandell
|Joshua Sandquist|Idelle Cooper|Elizabeth Queathem|Heriberto Hernandez-Soto|Erick Leggans|Lee Sharpe
|Andrew Mobley|Raynard Kington|Anne Harris|George Drake""".replace("\n", "").split("|")
