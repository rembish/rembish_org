import { useNavigate, useParams } from "react-router-dom";
import {
  BiGlobe,
  BiCodeAlt,
  BiJoystick,
  BiTestTube,
  BiLinkExternal,
  BiLogoGithub,
  BiSolidStar,
} from "react-icons/bi";
import { SiNpm, SiPypi } from "react-icons/si";

interface Package {
  name: string;
  npmUrl: string;
  githubUrl: string;
}

interface Project {
  title: string;
  description: string;
  logo?: string;
  starred?: boolean;
  features: string[];
  techStack: string[];
  status: "active" | "completed" | "alpha" | "beta" | "sunset";
  links: { label: string; url: string; icon: React.ComponentType }[];
  packages?: Package[];
}

type TabType = "web" | "modules" | "games" | "experiments";

const webProjects: Project[] = [
  {
    title: "rembish.org",
    description:
      "This very website! What started as a simple portfolio page grew into a full personal travel and life management platform — trip planning, flight and drone tracking, encrypted vault, photo galleries, meme feed, and more. Built entirely with Claude AI.",
    starred: true,
    features: [
      "Interactive travel map with 193 UN countries, 330 TCC, and 265 NM UN+ destinations",
      "Drone flights — Telegram bot upload, geocoded locations, battery telemetry, anomaly detection",
      "Flight tracking with AeroDataBox lookup, statistics, and Flighty import",
      "Encrypted vault for passports, visas, travel documents, loyalty programs, and vaccinations",
      "Photo galleries — Instagram albums, cosplay gallery, and country-based world map",
      "Trip planner with TripClimate integration, travel advisories, and vacation balance",
      "Meme feed — Telegram capture with AI triage via Claude Haiku",
      "iOS app API — Bearer token auth with direct drone flight and meme upload endpoints",
    ],
    techStack: [
      "React",
      "TypeScript",
      "Vite",
      "FastAPI",
      "SQLAlchemy",
      "Google Cloud",
    ],
    status: "active",
    links: [
      { label: "Website", url: "https://rembish.org", icon: BiLinkExternal },
      {
        label: "GitHub",
        url: "https://github.com/rembish/rembish_org",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "TripClimate",
    description:
      "A travel planning tool that shows what awaits before you book. Layers cultural events, sporting events, public holidays, weather, seasonality, visa requirements, and travel warnings into an interactive calendar. Includes a world map, destination Compass, browsable Event Guide, and personalized settings for units and passport country. Covers 250+ countries.",
    starred: true,
    features: [
      "423 curated festivals across 167 countries: Ramadan, Carnival, Songkran, Holi, Nyepi, Oktoberfest, and more",
      "194 sporting events: F1, Grand Slams, marathons, Olympics, cycling tours",
      "Public holidays for 249 countries with 3-tier resolution fallback",
      "Historical weather averages, extreme condition alerts, closed seasons, and seasonality indicators",
      "Visa requirements — personalized by passport country with GeoIP-based detection",
      "Travel advisories from US State Dept, Canada, UK FCDO, and Germany",
      "Travel Score — Explorer/Chill modes to surface trips that match your style",
      "Compass — destination ranking by month, weather preference, and travel vibe",
      "Event Guide — browsable directory of 1,490 festivals, sports events, and holidays with descriptions and photos",
      "World choropleth map with zoom/pan, multiple view modes, and biome overlays",
      "User preferences: temperature/precipitation units and passport country, persisted locally",
    ],
    techStack: ["Python 3.12+", "FastAPI", "Alpine.js", "Google Cloud Run"],
    status: "beta",
    links: [
      {
        label: "Website",
        url: "https://tripclimate.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Entry Conditions",
    description:
      "A verified, primary-source dataset of passport × destination entry requirements — plus the web app that serves it. For any passport and destination it answers what you need to enter — visa-free, eVisa, visa-on-arrival, ETA, full visa, or no admission — with a verbatim quote from an official government source behind every verified answer. Flat-file and database-free: the cell data is the source of truth, and the entire site is generated from it.",
    starred: true,
    features: [
      "213 passports × 250 destinations of verified entry requirements",
      "Answers any passport × destination pair: visa-free, eVisa, visa-on-arrival, ETA, full visa, or no admission",
      "Every verified cell backed by a verbatim quote from an official government source",
      "Strict verification contract — a cell counts as verified only when its official source was fetched live and quoted",
      "Flat-file architecture, no database — the YAML cell data is the single source of truth, everything downstream is generated",
      "Interactive per-passport world map built on a custom Entry Conditions TopoJSON of 250 destinations",
      "Multi-tier fetch ladder (httpx → headless Chromium → Cloudflare/WAF escalation) for sourcing official pages",
      "Per-passport pages with dynamic OG share cards",
    ],
    techStack: [
      "SvelteKit",
      "TypeScript",
      "Vite",
      "Python 3.12",
      "TopoJSON",
      "Google Cloud Run",
    ],
    status: "beta",
    links: [
      {
        label: "Website",
        url: "https://entryconditions.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Portolan",
    description:
      "Google Flights answers cheapest A→B. Rome2Rio works city-pair. Nobody visualizes the backtrack cost of living outside a hub — or the orphan status of genuinely remote destinations like Comoros, Bhutan, Tuvalu, or Nauru. Portolan does. Color-codes every zone on the globe by air-hop distance from any chosen origin, with country panels covering all surface transport, land border crossings, ferry routes, 31 maritime chokepoints, and a personal visa overlay across ~40,000 passport × destination pairs.",
    starred: true,
    features: [
      "Global air reachability map: BFS over the full flight route graph colors every zone by hop count from any chosen origin — instantly revealing which destinations are genuinely remote vs. merely off the beaten path",
      "~220–250 zones rather than ~195 countries — non-contiguous territories (Alaska, Greenland, Canary Islands, Réunion, Kaliningrad) get their own zone so the isolation signal is geographically accurate",
      "Country panel: air connectivity summary, all surface transport modes and operators, land border crossings with open/restricted/closed status sourced from OpenStreetMap and Wikidata SPARQL",
      "31 maritime chokepoints — Bosporus, Suez, Malacca, Strait of Hormuz, Panama, and 26 others — each with transit context in the country panel",
      "Visa matrix from passport-index-dataset: ~40,000 passport × destination cells, visa-free / on-arrival / e-visa / required, with a searchable passport selector that overlays your personal access across the map",
      "Ferry routes and international lake crossings as a dedicated overlay layer alongside mainline rail arcs and airport icons",
      "Click an airport to see every direct connection; click a second airport to build a multi-leg chain with a per-leg route panel showing IATA codes, duration, and operators",
      "Static architecture: Python pipeline (Polars, DuckDB, NetworkX) emits precomputed JSON + TopoJSON to CDN — no backend, no database, sub-100ms global loads",
    ],
    techStack: [
      "Svelte 5",
      "Vite",
      "MapLibre GL JS",
      "Python 3.12",
      "Polars",
      "DuckDB",
      "NetworkX",
      "GCP Cloud Run",
      "Cloudflare CDN",
    ],
    status: "beta",
    links: [
      {
        label: "Website",
        url: "https://portolanmap.com",
        icon: BiLinkExternal,
      },
      {
        label: "GitHub",
        url: "https://github.com/rembish/portolanmap_com",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "Should I Ape?",
    description:
      "A crypto Major Arcana oracle. Ask the 22-card tarot deck whether to buy, hold, or sell — it knows as much as your analyst does. Draws three cards (Setup → Force → Outcome), weighs them against live Binance market data and your zodiac sign, and delivers a verdict: Ape In, Hodl, or Get Out.",
    features: [
      "22-card Major Arcana deck with upright and reversed meanings",
      "Three-card spread: Setup → Force → Outcome weighted against your zodiac sign",
      "Live Binance 24h market signal — no API key required",
      "Deterministic readings — same seed always produces the same cards",
      "Stable shareable URLs — intent + coin + seed encoded in an 18-character pronounceable string",
      "Dynamic OG image generation per share code for rich link previews",
      "Responsible use page at /when-it-stops addressing compulsive trading and market distress",
    ],
    techStack: [
      "Python 3.12+",
      "FastAPI",
      "Jinja2",
      "Pillow",
      "Binance API",
      "Google Cloud Run",
    ],
    status: "active",
    links: [
      {
        label: "Website",
        url: "https://shouldiape.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Deploy Horoscope",
    description:
      "Should I deploy today? Let the stars decide. A deterministic deployment oracle that answers the eternal question using your zodiac sign, moon phase, Mercury retrograde status, planetary positions, and the iron law that Fridays are always red. No database. No real astrology. Now with a JSON API.",
    features: [
      "12 zodiac signs with optional birthdate for extra cosmic calibration",
      "Deterministic SHA-256 scores — same inputs always produce the same result",
      "Animated SVG natal chart with zodiac ring, house sectors, and aspect lines",
      "Two-month deployment calendar with progressive color reveals",
      "Stable shareable URLs — date encoded as mystical spell-words, no DB needed",
      "JSON API with rate limiting for integrations and bots",
      "OG share card PNG generation for rich link previews",
      "Special-day themes: Halloween, Christmas, birthday, Friday the 13th, and more",
    ],
    techStack: ["Python 3.12+", "FastAPI", "Jinja2", "Pillow", "SVG"],
    status: "active",
    links: [
      {
        label: "Website",
        url: "https://deployhoroscope.com",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Deploy Tarot",
    description:
      "Should I deploy today? Let the cards decide. A tarot-based deploy advisor born from 5 hours of vibecoding that accidentally hit HN front page and gathered ~10k active users. Pick your role and deployment intent, draw from the full 78-card deck, and receive your verdict. No database. No real mysticism. The anxiety it surfaces might be real though.",
    starred: true,
    features: [
      "Full 78-card deck — 22 Major Arcana and 56 Minor Arcana with upright and reversed meanings",
      "Quick read (3 cards) and full Celtic Cross spread (10 cards)",
      "Role and intent selector — 8 roles × 9 intents for personalized cosmic context",
      "Stable shareable URLs — entire reading encoded as arcane spell-words, no DB needed",
      "Browsable card reference at /cards with individual card pages",
      "Zero server state — all session context lives in two browser cookies",
      "Viral HN front page hit: ~10k active users, 68k+ events in first days",
    ],
    techStack: ["Python 3.12+", "FastAPI", "Jinja2", "Google Cloud Run"],
    status: "active",
    links: [
      {
        label: "Website",
        url: "https://deploytarot.com",
        icon: BiLinkExternal,
      },
      {
        label: "HN Discussion",
        url: "https://news.ycombinator.com/item?id=47535586",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "Am I Free?",
    description:
      "A web application that helps you plan your vacation days by calculating working days spent on trips, excluding weekends and public holidays automatically.",
    logo: "/amifree-logo.svg",
    features: [
      "Calculate vacation days needed for trips",
      "Exclude weekends and public holidays automatically",
      "Track multiple trips throughout the year",
      "View remaining vacation days",
      "What-if calculator for planning future trips",
      "Support for multiple countries",
    ],
    techStack: [
      "React",
      "TypeScript",
      "Vite",
      "Mantine UI",
      "FastAPI",
      "SQLAlchemy",
      "MySQL",
      "Google Cloud",
    ],
    status: "sunset",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/amifree",
        icon: BiLogoGithub,
      },
    ],
  },
];

const moduleProjects: Project[] = [
  {
    title: "pydjirecord",
    description:
      "A Python 3.10+ parser for DJI drone flight log files (.txt binary format). Handles format versions 1–14 with XOR and AES-256-CBC decryption. Built as a rewrite of the Rust dji-log-parser, with improvements: zero-coordinate backfill from OSD GPS frames, accurate video/photo/distance stats from raw telemetry, and local keychain caching for the DJI API.",
    starred: true,
    features: [
      "Parse DJI flight logs across format versions 1–14",
      "XOR + AES-256-CBC decryption with DJI API keychain fetching",
      "Multiple output formats: JSON, GeoJSON, KML, CSV, hardware report",
      "Zero-coordinate backfill from OSD GPS telemetry frames",
      "Accurate photo count, video time, and distance from raw records",
      "Flight anomaly detection with RED/AMBER/GREEN severity levels",
    ],
    techStack: ["Python 3.10+", "PyCryptodome", "httpx"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/pydjirecord",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/pydjirecord/",
        icon: SiPypi,
      },
      {
        label: "Docs",
        url: "https://rembish.github.io/pydjirecord/",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "xcodeproj-creator",
    description:
      "A Python library and CLI tool that generates Xcode .xcodeproj bundles from scratch — on Linux or any platform, no macOS required. Ideal for CI/CD pipelines and cross-platform build automation where you need to programmatically produce valid Xcode projects for iOS and macOS apps.",
    starred: true,
    features: [
      "Generate full Xcode projects on Linux or any non-macOS platform",
      "Supports object model v56 (all Xcode versions) and v77 (Xcode 16+ with filesystem-sync groups)",
      "Multiple product types: iOS App, Framework, Static Library, Unit Tests, UI Tests, App Extensions",
      "Configurable build settings, deployment targets, Swift versions, and team IDs",
      "Shell script build phases, asset catalogs, and resource management",
      "Both Python API and CLI (xcodeproj-create command)",
    ],
    techStack: ["Python 3.12+"],
    status: "beta",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/xcodeproj-creator",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/xcodeproj-creator/",
        icon: SiPypi,
      },
    ],
  },
  {
    title: "TopoJSON Maps",
    description:
      "Three open-source TopoJSON world maps built from Natural Earth 10m shapefiles — one for each major travel tracking system, plus a standard ISO baseline. All published on npm and available via CDN.",
    starred: true,
    features: [
      "ISO A2 — 250 polygons keyed by ISO 3166-1 alpha-2 codes, overseas territories as separate polygons",
      "TCC — 330 destinations matching the Travelers' Century Club list (no equivalent existed before)",
      "NM UN+ — 265 regions matching the NomadMania UN+ destination list",
      "Full and markers variants: tiny territories rendered as point markers in compact builds",
      "Transcontinental splits, disputed territories, island extractions, Antarctic claim sectors",
    ],
    techStack: ["Python", "Shapely", "GeoPandas", "mapshaper", "TopoJSON"],
    status: "active",
    links: [],
    packages: [
      {
        name: "@rembish/iso-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/iso-topojson",
        githubUrl: "https://github.com/rembish/iso-topojson",
      },
      {
        name: "@rembish/tcc-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/tcc-topojson",
        githubUrl: "https://github.com/rembish/tcc-topojson",
      },
      {
        name: "@rembish/nm-unp-topojson",
        npmUrl: "https://www.npmjs.com/package/@rembish/nm-unp-topojson",
        githubUrl: "https://github.com/rembish/nm-unp-topojson",
      },
    ],
  },
  {
    title: "fit",
    description:
      "A Python library for reading and writing Garmin FIT files — the binary format used by fitness devices to record activities, workouts, and health data. Fully ported to modern Python and given a proper new release in 2026.",
    features: [
      "Read and write .fit activity files",
      "Supports all standard FIT message types",
      "Dynamic and composite bit-packed fields",
      "Plugin system for custom message and file types",
      "Context-manager API with stream support",
    ],
    techStack: ["Python 3.9+"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/fit",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/fit/",
        icon: SiPypi,
      },
    ],
  },
  {
    title: "wadlib",
    description:
      "A Python 3.12+ library and CLI toolkit for reading, writing, and analysing id Software WAD files — the format used by Doom, Doom II, Heretic, Hexen, Strife, and derivative source-port mods. Supports IWAD base files and PWAD patches with a zipfile-style archive API and full lump-level access.",
    features: [
      "Read and write IWAD and PWAD files across all id Software games",
      "Layer multiple PWADs on top of an IWAD — PWAD lumps shadow base WAD lumps by name",
      "zipfile-style archive interface: read, write, append, replace, and extract lumps",
      "Full WAD writer for building custom maps and assets from scratch",
      "wadcli command-line tool for inspection and extraction",
      "Built-in lump validation and type-safe lump definitions",
    ],
    techStack: ["Python 3.12+"],
    status: "active",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/wadlib",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/wadlib/",
        icon: SiPypi,
      },
      {
        label: "Docs",
        url: "https://rembish.github.io/wadlib/",
        icon: BiLinkExternal,
      },
    ],
  },
  {
    title: "cfb",
    description:
      "A Python library for reading the internal structure of old-style Microsoft Office files. The .doc, .xls, and .ppt formats are actually containers full of streams and folders — this library lets you open them and navigate what's inside. The foundation that Miette is built on.",
    features: [
      "Open and inspect old Office file containers",
      "Navigate internal folders and data streams",
      "File-like reading interface",
      "Handles malformed or unusual files gracefully",
    ],
    techStack: ["Python 3.8+"],
    status: "beta",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/cfb",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/cfb/",
        icon: SiPypi,
      },
    ],
  },
  {
    title: "Miette",
    description:
      "A lightweight Python library for reading old-style Word documents (.doc files). Extracts plain text with a simple, familiar interface. Revived in 2026 after more than a decade of quiet — fully rewritten for modern Python.",
    features: [
      "Read legacy Word .doc files",
      "Extract all plain text content",
      "Simple file-like API",
      "Minimal dependencies",
    ],
    techStack: ["Python 3.8+"],
    status: "alpha",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/Miette",
        icon: BiLogoGithub,
      },
      {
        label: "PyPI",
        url: "https://pypi.org/project/miette/",
        icon: SiPypi,
      },
    ],
  },
  {
    title: "TextAtAnyCost",
    description:
      "One of my oldest and most popular open source projects. A PHP library that pulls plain text out of old document formats — Word files, PDFs, PowerPoint slides, RTF, and more. Born in 2009 and finally given a proper v1.0.0 release in 2026.",
    starred: true,
    features: [
      "Extract text from PDF files",
      "Read old and new Word documents (.doc and .docx)",
      "Extract text from PowerPoint presentations",
      "Handle RTF and OpenDocument formats",
      "No extra software needed — pure PHP",
    ],
    techStack: ["PHP 8.3+"],
    status: "completed",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/TextAtAnyCost",
        icon: BiLogoGithub,
      },
    ],
  },
];

const gameProjects: Project[] = [
  {
    title: "Witchspace",
    description:
      "A free reimplementation of Elite Plus (1991), the PC version of David Braben and Ian Bell's Elite, written in assembly by Chris Sawyer. Witchspace rebuilds it routine by routine as portable C and runs it on today's computers and in the browser: trading, combat, missions, docking, hyperspace, the AdLib music. None of the original is included; it reads the game's data from your copy, or from the one the Internet Archive preserves.",
    starred: true,
    features: [
      "The whole game rebuilt from the original's machine code: the galaxy, markets, ships and their AI, combat, the station screens, saving and loading, and the AdLib music driver",
      "Checked against the original running in an x86 emulator: each routine must leave the same memory, draw the same primitives and make the same sounds, byte for byte",
      "Whole-game tests boot the original, fly from the title into space, and compare the title screen frame by frame",
      "A deterministic C99 core that says what to draw, not how, so another renderer could draw the same stream its own way",
      "Plays in the browser, with commanders kept between visits and .CDR saved games to import and export",
    ],
    techStack: ["C99", "SDL2", "WebAssembly", "Ghidra", "Unicorn", "Python"],
    status: "completed",
    links: [
      {
        label: "Play",
        url: "https://rembish.github.io/witchspace/",
        icon: BiJoystick,
      },
      {
        label: "GitHub",
        url: "https://github.com/rembish/witchspace",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "BlockOut",
    description:
      "The 3D Tetris for DOS (California Dreams, 1989), decompiled and ported to portable C and SDL2. The game logic is reconstructed faithfully from the original; the rendering, input and sound are new. Runs on Linux, Windows and macOS, and in the browser, including on phones. No original files are needed to play.",
    features: [
      "Piece sets, the random number generator and its reroll quirk, wall kicks, rotation, gravity, scoring and every timing, in the original's timer ticks",
      "A differential test runs the original in the Unicorn CPU emulator and compares the complete game state with the port on every frame",
      "The original's 1989 demo AI, ported and playing",
      "Touch controls with an eight-way pad and six rotation buttons; native builds for Windows, macOS and Linux",
    ],
    techStack: ["C", "SDL2", "WebAssembly", "Ghidra", "Unicorn", "Python"],
    status: "completed",
    links: [
      {
        label: "Play",
        url: "https://rembish.github.io/blockout-revamp/",
        icon: BiJoystick,
      },
      {
        label: "GitHub",
        url: "https://github.com/rembish/blockout-revamp",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "Welltris",
    description:
      "Alexey Pajitnov's three-dimensional follow-up to Tetris (Spectrum HoloByte, 1989): pieces slide down the four walls of a well onto its floor, where full rows and columns clear. A decompilation of the DOS version, ported to C and SDL2, with new artwork as a homage: the original's Moscow became Prague.",
    features: [
      "Game logic decompiled from WELLTRIS.EXE: the Turbo C random number generator, rotation quirks, wall freezing and thawing, gravity on the original's 187 Hz timer, scoring and level ups",
      "Compared with the original in an emulator after every pass of the play loop, using random keys and a search bot that clears lines",
      "Mutation tests break the core in 15 ways and check the comparison catches each one",
      "Prague pictures for the five speeds; on-screen controls for phones and tablets",
    ],
    techStack: ["C99", "SDL2", "WebAssembly", "Ghidra", "Unicorn", "Python"],
    status: "beta",
    links: [
      {
        label: "Play",
        url: "https://rembish.github.io/welltris-revamp/",
        icon: BiJoystick,
      },
      {
        label: "GitHub",
        url: "https://github.com/rembish/welltris-revamp",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "King (Кинг)",
    description:
      "The trick-taking card game that Komsomolskaya Pravda gave its readers in 1993, on half the PCs of the former USSR: four players, 32 cards, 14 games. A decompilation of the full variant, KING2.EXE, ported to C and SDL2 and drawn with the original's own cards and fonts, read from your copy.",
    features: [
      "The Turbo Pascal random number generator and every call to it, the deal, the computer players' contract choices and search, and the scoring",
      "Whole games recorded from the original in an emulator and replayed through the port deal by deal, random numbers included",
      "Mutation tests break the core in 22 ways and check the replays catch each one",
      "A global table of millionaires, served from Cloudflare",
    ],
    techStack: ["C", "SDL2", "WebAssembly", "Ghidra", "Unicorn", "Cloudflare"],
    status: "beta",
    links: [
      { label: "Play", url: "https://king.rembi.sh/", icon: BiJoystick },
      {
        label: "GitHub",
        url: "https://github.com/rembish/king-card-game",
        icon: BiLogoGithub,
      },
    ],
  },
  {
    title: "Color Lines",
    description:
      "Gamos's Color Lines (Moscow, 1992), the game of every mom and dad in the 90s: a 9×9 board, balls of seven colours, lines of five vanish. A decompilation of LINES.EXE ported to C and SDL2, with the original's pictures fetched from the Internet Archive or read from your copy.",
    features: [
      "Where new balls land, the line check and the score, which depends on how long you thought and is computed in Turbo Pascal's 6-byte Reals, reproduced bit for bit",
      "Games recorded from the original in an emulator and compared turn by turn, including the moves the original refuses",
      "Mutation tests break the core in 20 ways and check the comparison catches each one",
      "A global Top Ten, served from Cloudflare",
    ],
    techStack: ["C", "SDL2", "WebAssembly", "Ghidra", "Unicorn", "Cloudflare"],
    status: "beta",
    links: [
      { label: "Play", url: "https://lines.rembi.sh/", icon: BiJoystick },
      {
        label: "GitHub",
        url: "https://github.com/rembish/color-lines-game",
        icon: BiLogoGithub,
      },
    ],
  },
];

const experimentProjects: Project[] = [
  {
    title: "fruit-fly",
    description:
      "A fly that lives on your desktop, driven by the complete brain of a real fruit fly: the FlyWire connectome of adult Drosophila melanogaster, 139,255 neurons and about 34 million synapses, simulated live while the sprite buzzes over your windows. No scripted behaviour: when it dodges your cursor, your cursor reached its looming-detector neurons and they fired the giant fiber escape neuron, the same circuit a living fly uses to dodge a rolled-up newspaper.",
    features: [
      "Whole-brain leaky integrate-and-fire simulation in real time, following Shiu et al. 2024 (Nature): weights from synapse counts, signs from predicted neurotransmitters",
      "Retinotopic eyes: 785 + 796 real eye columns and 6,670 mapped photoreceptors, each driven by the pixels its column sees, so an approaching cursor looms",
      "Takeoffs, landings, saccades and escapes come from descending neurons reaching threshold, logged as they fire",
      "Poke the circuit: type a population (GF, MDN, DNa02_L and 32 more) and watch the body answer",
      "Honest science notes: what is real, what is corrected (photoreceptor histamine), and what is approximated",
      "Linux (GTK), macOS (Cocoa) and Windows backends over a shared brain and cairo-drawn sprite",
    ],
    techStack: [
      "Python",
      "NumPy",
      "cairo",
      "FlyWire connectome",
      "GTK",
      "Cocoa",
      "Win32",
    ],
    status: "alpha",
    links: [
      {
        label: "GitHub",
        url: "https://github.com/rembish/fruit-fly",
        icon: BiLogoGithub,
      },
    ],
  },
];

function getStatusLabel(status: Project["status"]) {
  switch (status) {
    case "active":
      return "Active";
    case "completed":
      return "Completed";
    case "alpha":
      return "Alpha";
    case "beta":
      return "Beta";
    case "sunset":
      return "Sunset";
  }
}

export default function Projects() {
  const { tab } = useParams<{ tab?: string }>();
  const navigate = useNavigate();

  const activeTab: TabType =
    tab === "modules" || tab === "games" || tab === "experiments" ? tab : "web";
  const projects = {
    web: webProjects,
    modules: moduleProjects,
    games: gameProjects,
    experiments: experimentProjects,
  }[activeTab];

  return (
    <section id="projects" className="projects">
      <div className="container">
        <div className="section-title">
          <h2>Projects</h2>
          <p>Hobby projects and side experiments</p>
        </div>

        <div className="travel-tabs">
          <button
            className={`travel-tab ${activeTab === "web" ? "active" : ""}`}
            onClick={() => navigate("/projects/web")}
          >
            <BiGlobe /> Web
          </button>
          <button
            className={`travel-tab ${activeTab === "modules" ? "active" : ""}`}
            onClick={() => navigate("/projects/modules")}
          >
            <BiCodeAlt /> Modules
          </button>
          <button
            className={`travel-tab ${activeTab === "games" ? "active" : ""}`}
            onClick={() => navigate("/projects/games")}
          >
            <BiJoystick /> Games
          </button>
          <button
            className={`travel-tab ${activeTab === "experiments" ? "active" : ""}`}
            onClick={() => navigate("/projects/experiments")}
          >
            <BiTestTube /> Experiments
          </button>
        </div>

        <div className="projects-list">
          {projects.map((project) => (
            <article key={project.title} className="project-card">
              <div className="project-header">
                <h3>
                  {project.logo ? (
                    <img src={project.logo} alt="" className="project-logo" />
                  ) : null}
                  {project.title}
                  {project.starred ? (
                    <BiSolidStar
                      className="project-star"
                      title="Popular project"
                    />
                  ) : null}
                </h3>
                <span className={`project-status status-${project.status}`}>
                  {getStatusLabel(project.status)}
                </span>
              </div>

              <p className="project-description">{project.description}</p>

              <div className="project-features">
                <h4>
                  <BiCodeAlt /> Features
                </h4>
                <ul>
                  {project.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>

              <div className="project-tech">
                <h4>
                  <BiGlobe /> Tech Stack
                </h4>
                <div className="tech-tags">
                  {project.techStack.map((tech) => (
                    <span key={tech} className="tech-tag">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {(project.links.length > 0 || project.packages) && (
                <div className="project-links">
                  {project.links.map(({ label, url, icon: Icon }) => (
                    <a
                      key={label}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Icon /> {label}
                    </a>
                  ))}
                  {project.packages && (
                    <ul className="project-packages">
                      {project.packages.map(({ name, npmUrl, githubUrl }) => (
                        <li key={name}>
                          <code>{name}</code>
                          <span className="package-links">
                            <a
                              href={githubUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <BiLogoGithub /> GitHub
                            </a>
                            <a
                              href={npmUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <SiNpm /> npm
                            </a>
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </article>
          ))}
        </div>

        <div className="github-profile">
          <a
            href="https://github.com/rembish"
            target="_blank"
            rel="noopener noreferrer"
          >
            <BiLogoGithub /> More projects on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}
