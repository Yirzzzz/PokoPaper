import type { PaperCard, ReadingMemory } from "@/types";

type TypeMeta = {
  label: string;
  chipClassName: string;
  panelClassName: string;
};

type PokemonCompanion = {
  dexId: number;
  name: string;
  spriteUrl: string;
};

function isMeaningfulValue(value: string | null | undefined): value is string {
  if (!value) return false;
  const normalized = value.trim().toLowerCase();
  return normalized.length > 0 && normalized !== "unknown" && normalized !== "unknown author";
}

const TYPE_MAP: Array<{
  keywords: string[];
  meta: TypeMeta;
}> = [
  {
    keywords: ["llm", "nlp", "language", "transformer"],
    meta: {
      label: "超能系",
      chipClassName: "border-fuchsia-400/30 bg-fuchsia-400/10 text-fuchsia-200",
      panelClassName: "border-fuchsia-400/20 bg-fuchsia-400/8",
    },
  },
  {
    keywords: ["cv", "vision", "image", "multimodal"],
    meta: {
      label: "电系",
      chipClassName: "border-amber-300/30 bg-amber-300/10 text-amber-100",
      panelClassName: "border-amber-300/20 bg-amber-300/8",
    },
  },
  {
    keywords: ["rag", "retrieval", "search"],
    meta: {
      label: "钢系",
      chipClassName: "border-sky-300/30 bg-sky-300/10 text-sky-100",
      panelClassName: "border-sky-300/20 bg-sky-300/8",
    },
  },
  {
    keywords: ["agent", "planning", "tool"],
    meta: {
      label: "龙系",
      chipClassName: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
      panelClassName: "border-emerald-300/20 bg-emerald-300/8",
    },
  },
  {
    keywords: ["theory", "math", "proof", "reasoning"],
    meta: {
      label: "幽灵系",
      chipClassName: "border-slate-300/30 bg-slate-300/10 text-slate-100",
      panelClassName: "border-slate-300/20 bg-slate-300/8",
    },
  },
];

const DEFAULT_TYPE_META: TypeMeta = {
  label: "一般系",
  chipClassName: "border-black/10 bg-white/55 text-slate-900",
  panelClassName: "border-black/10 bg-white/55",
};

const KANTO_POKEMON = [
  "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard", "Squirtle", "Wartortle",
  "Blastoise", "Caterpie", "Metapod", "Butterfree", "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto",
  "Pidgeot", "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok", "Pikachu", "Raichu", "Sandshrew",
  "Sandslash", "Nidoran-F", "Nidorina", "Nidoqueen", "Nidoran-M", "Nidorino", "Nidoking", "Clefairy",
  "Clefable", "Vulpix", "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish", "Gloom",
  "Vileplume", "Paras", "Parasect", "Venonat", "Venomoth", "Diglett", "Dugtrio", "Meowth", "Persian",
  "Psyduck", "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag", "Poliwhirl", "Poliwrath",
  "Abra", "Kadabra", "Alakazam", "Machop", "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel",
  "Tentacool", "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash", "Slowpoke", "Slowbro",
  "Magnemite", "Magneton", "Farfetch'd", "Doduo", "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder",
  "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee", "Hypno", "Krabby", "Kingler", "Voltorb",
  "Electrode", "Exeggcute", "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan", "Lickitung",
  "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey", "Tangela", "Kangaskhan", "Horsea", "Seadra",
  "Goldeen", "Seaking", "Staryu", "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz", "Magmar",
  "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras", "Ditto", "Eevee", "Vaporeon", "Jolteon", "Flareon",
  "Porygon", "Omanyte", "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax", "Articuno", "Zapdos",
  "Moltres", "Dratini", "Dragonair", "Dragonite", "Mewtwo", "Mew",
];

function hashText(text: string): number {
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) % 2147483647;
  }
  return hash;
}

export function getPaperTypeMeta(
  value: string | null | undefined,
  tags: string[] = [],
): TypeMeta {
  const cleanValue = isMeaningfulValue(value) ? value : "";
  const cleanTags = tags.filter((tag) => isMeaningfulValue(tag));
  const text = `${cleanValue} ${cleanTags.join(" ")}`.toLowerCase();
  return TYPE_MAP.find((item) => item.keywords.some((keyword) => text.includes(keyword)))?.meta ?? DEFAULT_TYPE_META;
}

export function formatDexNumber(index: number): string {
  return `No.${String(index + 1).padStart(3, "0")}`;
}

export function getCaptureStage(status: string, progressPercent: number): string {
  const lowerStatus = status.toLowerCase();
  if (lowerStatus.includes("processing")) {
    return "解析中";
  }
  if (progressPercent < 10) {
    return "待收服";
  }
  if (progressPercent >= 85) {
    return "已掌握";
  }
  if (progressPercent >= 20) {
    return "训练中";
  }
  return "已收录";
}

export function getEvolutionStage(progressPercent: number): string {
  if (progressPercent >= 85) {
    return "完全进化";
  }
  if (progressPercent >= 35) {
    return "进化中";
  }
  return "初始形态";
}

export function getMemoryStage(memory: ReadingMemory): string {
  if (memory.progress_percent >= 85) {
    return "已掌握";
  }
  if (memory.progress_percent >= 35) {
    return "训练中";
  }
  return "刚收录";
}

export function getPaperAffinity(paper: PaperCard): string {
  if (isMeaningfulValue(paper.category)) {
    return paper.category;
  }
  const firstTag = paper.tags?.find((tag) => isMeaningfulValue(tag));
  return firstTag ?? "未设系别";
}

export function getPokemonCompanion(paper: Pick<PaperCard, "id" | "title">): PokemonCompanion {
  const hash = hashText(`${paper.id}:${paper.title}`);
  const dexId = (hash % 151) + 1;
  const name = KANTO_POKEMON[dexId - 1];
  return {
    dexId,
    name,
    spriteUrl: `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-i/red-blue/${dexId}.png`,
  };
}
